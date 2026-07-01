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

And this `notes` table for Notion note chunks (kept verbatim, not distilled):

    create table if not exists public.notes (
        id          uuid primary key,
        page_id     text not null,
        title       text,
        chunk_index int,
        content     text not null,
        tags        text[] default '{}',
        source      text default 'notion',
        created_at  timestamptz default now()
    );
    create index if not exists notes_page_id_idx on public.notes (page_id);

And this `emails` table for newsletter chunks (kept verbatim, not distilled):

    create table if not exists public.emails (
        id          uuid primary key,
        message_id  text not null,
        sender      text,
        subject     text,
        date        text,
        chunk_index int,
        content     text not null,
        tags        text[] default '{}',
        source      text default 'gmail',
        created_at  timestamptz default now()
    );
    create index if not exists emails_message_id_idx on public.emails (message_id);
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


def get_ingested_page_ids() -> set[str]:
    """Notion page_ids already chunked & stored — used to skip re-ingesting."""
    res = get_client().table("notes").select("page_id").execute()
    return {row["page_id"] for row in res.data}


def save_notes(chunks: list) -> int:
    """Insert Notion note chunks. Returns number of rows written."""
    if not chunks:
        return 0
    rows = [
        {
            "id": c.id,
            "page_id": c.page_id,
            "title": c.title,
            "chunk_index": c.chunk_index,
            "content": c.content,
            "tags": c.tags,
            "source": c.source,
        }
        for c in chunks
    ]
    get_client().table("notes").insert(rows).execute()
    return len(rows)


def get_ingested_message_ids() -> set[str]:
    """Gmail Message-IDs already chunked & stored — used to skip re-ingesting."""
    res = get_client().table("emails").select("message_id").execute()
    return {row["message_id"] for row in res.data}


def save_emails(chunks: list) -> int:
    """Insert email chunks. Returns number of rows written."""
    if not chunks:
        return 0
    rows = [
        {
            "id": c.id,
            "message_id": c.message_id,
            "sender": c.sender,
            "subject": c.subject,
            "date": c.date,
            "chunk_index": c.chunk_index,
            "content": c.content,
            "tags": c.tags,
            "source": c.source,
        }
        for c in chunks
    ]
    get_client().table("emails").insert(rows).execute()
    return len(rows)


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
