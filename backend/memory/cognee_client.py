"""Unified Cognee graph — the second brain.

- Claude transcripts: clean -> distill -> cards (in Supabase, because distilling
  is expensive and worth persisting) -> fed here.
- Notion & Gmail: fetched and handed STRAIGHT to remember(). Cognee chunks,
  extracts entities, and dedups natively — no chunking/Supabase glue needed.

Build:  python backend/memory/cognee_client.py
Ask:    from backend.memory.cognee_client import ask
"""

import os
import sys
import asyncio
from pathlib import Path

os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv()

import cognee

from backend.config import NEWSLETTER_SENDERS
from backend.db.supabase_client import get_client
from backend.ingestion.notion.factory import get_client as get_notion_client
from backend.ingestion.gmail.factory import get_client as get_gmail_client

DATASET = "engram"
DATA_DIR = str(Path(__file__).resolve().parents[2] / "cognee_data")


def configure() -> None:
    cognee.config.set_llm_api_key(os.getenv("LLM_API_KEY"))
    cognee.config.set_llm_model("openai/gpt-4o-mini")
    cognee.config.set_embedding_model("openai/text-embedding-3-small")
    cognee.config.set_embedding_dimensions(1536)  # 3-small is 1536-dim
    cognee.config.data_root_directory(DATA_DIR)


def _card_doc(c: dict) -> str:
    return (
        f"[Source: claude_code] [Project: {c['project']}] [Kind: {c['kind']}]\n"
        f"{c['title']}\nQ: {c.get('question', '')}\nA: {c['answer']}"
    )


def _page_doc(p: dict) -> str:
    return f"[Source: notion] [Title: {p['title']}]\n\n{p['content']}"


def _email_doc(e: dict) -> str:
    return f"[Source: gmail] [From: {e['sender']}] [Subject: {e['subject']}]\n\n{e['body']}"


def _cards() -> list[dict]:
    try:
        return (
            get_client().table("cards").select("*")
            .eq("project", "Arxiv_Paper_Curator").execute().data
        )
    except Exception:
        return []


async def build_graph(reset: bool = True) -> None:
    """Build the unified graph from all three sources (Cognee does the chunking)."""
    configure()

    card_docs = [_card_doc(c) for c in _cards()]                      # Claude (Supabase)
    pages = get_notion_client().extract_workspace()                  # Notion (direct)
    page_docs = [_page_doc(p) for p in pages if (p.get("content") or "").strip()]
    emails = get_gmail_client().fetch_from_senders(NEWSLETTER_SENDERS)  # Gmail (direct)
    email_docs = [_email_doc(e) for e in emails]

    docs = card_docs + page_docs + email_docs
    print(f"ingesting {len(card_docs)} cards + {len(page_docs)} Notion pages "
          f"+ {len(email_docs)} emails = {len(docs)} docs into '{DATASET}'…")

    if reset:
        # Native full reset — required when embedding dimensions change (rebuilds
        # the vector store at the new dim). Not rm -rf.
        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)

    await cognee.remember(docs, dataset_name=DATASET)
    print("done — unified graph built.")


async def ask(query: str, session_id: str | None = None) -> dict:
    """Unified recall across the whole brain. Returns {answer, sources}.

    `session_id` gives multi-turn conversational memory — Cognee's session cache
    keeps prior turns so follow-ups like "both"/"that" resolve.
    """
    import re

    configure()
    results = await cognee.recall(
        query, datasets=[DATASET], context_profile="qa",
        include_references=True, session_id=session_id,
    )
    text = "\n\n".join(getattr(r, "text", "") for r in results if getattr(r, "text", ""))
    if "Evidence:" in text:
        answer, evidence = text.split("Evidence:", 1)
    else:
        answer, evidence = text, ""
    sources = sorted({s.strip() for s in re.findall(r"\[Source: ([^\]]+)\]", evidence)})
    return {"answer": answer.strip() or "Nothing relevant found in your memory yet.", "sources": sources}


if __name__ == "__main__":
    asyncio.run(build_graph())
