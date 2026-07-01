"""Unified Cognee graph: pull cards + notes from Supabase into ONE graph.

This is the "second brain" — every source lives in one graph so recall can
connect concepts across sources (Cognee's headline feature).

Ingest:  python backend/memory/cognee_client.py
Ask:     from backend.memory.cognee_client import ask
"""

import os
import sys
import asyncio
from pathlib import Path

# Single-user: no per-user access control (must be set before cognee is used).
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv()

import cognee

from backend.db.supabase_client import get_client

DATASET = "engram"
DATA_DIR = str(Path(__file__).resolve().parents[2] / "cognee_data")


def configure() -> None:
    cognee.config.set_llm_api_key(os.getenv("LLM_API_KEY"))
    # Cheap models: gpt-4o-mini for cognify/recall, small embeddings (6.5x cheaper).
    cognee.config.set_llm_model("openai/gpt-4o-mini")
    cognee.config.set_embedding_model("openai/text-embedding-3-small")
    cognee.config.set_embedding_dimensions(1536)  # 3-small is 1536-dim (not 3072)
    cognee.config.data_root_directory(DATA_DIR)


def _card_doc(c: dict) -> str:
    return (
        f"[Source: claude_code] [Project: {c['project']}] [Kind: {c['kind']}]\n"
        f"{c['title']}\nQ: {c.get('question', '')}\nA: {c['answer']}"
    )


def _note_doc(n: dict) -> str:
    return f"[Source: notion] [Title: {n['title']}]\n{n['content']}"


def _email_doc(e: dict) -> str:
    return f"[Source: gmail] [From: {e['sender']}] [Subject: {e['subject']}]\n{e['content']}"


def _rows(sb, table: str, **eq) -> list[dict]:
    """Fetch rows, tolerating a table that doesn't exist yet."""
    try:
        q = sb.table(table).select("*")
        for k, v in eq.items():
            q = q.eq(k, v)
        return q.execute().data
    except Exception:
        return []


async def ingest_unified() -> None:
    """Fresh single graph from Arxiv cards + Notion notes + Gmail newsletters."""
    configure()
    sb = get_client()
    cards = _rows(sb, "cards", project="Arxiv_Paper_Curator")
    notes = _rows(sb, "notes")
    emails = _rows(sb, "emails")
    docs = (
        [_card_doc(c) for c in cards]
        + [_note_doc(n) for n in notes]
        + [_email_doc(e) for e in emails]
    )

    print(f"clean slate + ingesting {len(cards)} Arxiv cards + {len(notes)} notes "
          f"+ {len(emails)} email chunks = {len(docs)} docs into ONE graph ('{DATASET}')…")
    await cognee.forget(everything=True)
    await cognee.remember(docs, dataset_name=DATASET)
    print("done — unified graph built.")


async def add_emails() -> None:
    """Append ONLY Gmail chunks to the existing graph — no forget, so you don't
    re-embed/re-cognify the cards + notes already in the graph (saves cost)."""
    configure()
    sb = get_client()
    emails = _rows(sb, "emails")
    if not emails:
        print("no emails in Supabase yet — run the gmail pipeline first.")
        return
    docs = [_email_doc(e) for e in emails]
    print(f"adding {len(docs)} email chunks to the existing graph (cards/notes untouched)…")
    await cognee.remember(docs, dataset_name=DATASET)  # NO forget => appends
    print("done.")


async def ask(query: str) -> str:
    """Unified recall across the whole brain (no dataset silo)."""
    configure()
    results = await cognee.recall(
        query, datasets=[DATASET], context_profile="qa", include_references=True
    )
    return "\n\n".join(getattr(r, "text", "") for r in results if getattr(r, "text", ""))


if __name__ == "__main__":
    asyncio.run(ingest_unified())
