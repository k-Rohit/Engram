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
"""

import os
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
