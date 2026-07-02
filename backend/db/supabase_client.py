"""Supabase persistence for distilled cards.

Table `cards` is the source of truth for what's already been distilled — the
pipeline reads existing session_ids from here to skip re-distilling.

Run this SQL once in the Supabase SQL editor to create the table:

    create table if not exists public.cards (
        id          uuid primary key,
        session_id  text not null,
        project     text,
        source      text default 'claude_code',
        kind        text not null,
        title       text not null,
        question    text,
        answer      text not null,
        tags        text[] default '{}',
        created_at  timestamptz default now()
    );
    create index if not exists cards_session_id_idx on public.cards (session_id);

And this `sessions` watermark table (tracks how many turns of each session are
already distilled, so re-runs only process newly-appended turns):

    create table if not exists public.sessions (
        session_id      text primary key,
        project         text,
        distilled_turns int not null default 0,
        updated_at      timestamptz default now()
    );

The `graph_ledger` table records which docs are already in the Cognee graph
(Cognee does NOT dedup, so this must be durable — not a local file):

    create table if not exists public.graph_ledger (
        key        text primary key,
        source     text,
        created_at timestamptz default now()
    );

The `feedback` table stores answer ratings (also pushed into Cognee session
memory as QAEntry feedback for improve()):

    create table if not exists public.feedback (
        id            uuid primary key default gen_random_uuid(),
        session_id    text not null,
        question      text,
        answer        text,
        score         int not null,
        feedback_text text,
        consolidated  boolean default false,
        created_at    timestamptz default now()
    );

Migration for dates on cards (run once):

    alter table public.cards add column if not exists session_date timestamptz;

(Notion notes and Gmail newsletters are NOT stored here — they go straight to
Cognee's remember(), which chunks and dedups natively. So no notes/emails tables.)
"""

import os
from datetime import datetime, timezone
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

TABLE = "cards"


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Cached Supabase client using the service-role (secret) key for writes."""
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SECRET_KEY"]
    return create_client(url, key)


def get_distilled_session_ids() -> set[str]:
    """Session ids already distilled & stored — used to skip re-distillation."""
    res = get_client().table(TABLE).select("session_id").execute()
    return {row["session_id"] for row in res.data}


def get_session_watermarks() -> dict[str, int]:
    """{session_id: distilled_turns} — how many turns of each session are done."""
    res = get_client().table("sessions").select("session_id,distilled_turns").execute()
    return {row["session_id"]: row["distilled_turns"] for row in res.data}


def set_watermark(session_id: str, project: str, distilled_turns: int) -> None:
    """Upsert how many turns of a session have now been distilled."""
    get_client().table("sessions").upsert(
        {
            "session_id": session_id,
            "project": project,
            "distilled_turns": distilled_turns,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()


def save_cards(session: dict, cards: list) -> int:
    """Insert all cards for one session. Returns number of rows written."""
    if not cards:
        return 0
    rows = [
        {
            "id": c.id,
            "session_id": session["session_id"],
            "project": session["project"],
            "source": session["source"],
            "session_date": session.get("started_at"),
            "kind": c.kind,
            "title": c.title,
            "question": c.question,
            "answer": c.answer,
            "tags": c.tags,
        }
        for c in cards
    ]
    get_client().table(TABLE).insert(rows).execute()
    return len(rows)


# ---------- graph ledger (what's already in the Cognee graph) ----------

def get_ledger_keys() -> set[str]:
    """Doc-keys already ingested into the Cognee graph."""
    res = get_client().table("graph_ledger").select("key").execute()
    return {row["key"] for row in res.data}


def add_ledger_keys(keys: list[str]) -> None:
    """Record doc-keys as ingested. Key format: '<source>:<id>'."""
    if not keys:
        return
    rows = [{"key": k, "source": k.split(":", 1)[0]} for k in keys]
    get_client().table("graph_ledger").upsert(rows).execute()


# ---------- feedback ----------

def save_feedback(session_id: str, question: str, answer: str, score: int, text: str = "") -> None:
    get_client().table("feedback").insert(
        {
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "score": score,
            "feedback_text": text,
        }
    ).execute()


def get_unconsolidated_feedback_sessions() -> list[str]:
    """Session ids with feedback not yet bridged into the graph via improve()."""
    res = get_client().table("feedback").select("session_id").eq("consolidated", False).execute()
    return sorted({row["session_id"] for row in res.data})


def mark_feedback_consolidated(session_ids: list[str]) -> None:
    if not session_ids:
        return
    get_client().table("feedback").update({"consolidated": True}).in_("session_id", session_ids).execute()
