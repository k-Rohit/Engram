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
import json
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


# Local ledger of doc-keys already sent to Cognee. Needed because Cognee does
# NOT dedup content on remember() — so we track what's in the graph ourselves.
LEDGER_PATH = Path(__file__).resolve().parents[2] / "cognee_ingested.json"


def _gather_claude() -> list[tuple[str, str]]:
    return [(f"card:{c['id']}", _card_doc(c)) for c in _cards()]


def _gather_notion() -> list[tuple[str, str]]:
    out = []
    for p in get_notion_client().extract_workspace():
        if (p.get("content") or "").strip():
            out.append((f"notion:{p['page_id']}", _page_doc(p)))
    return out


def _gather_gmail() -> list[tuple[str, str]]:
    return [
        (f"gmail:{e['message_id']}", _email_doc(e))
        for e in get_gmail_client().fetch_from_senders(NEWSLETTER_SENDERS)
    ]


_GATHER = {"claude": _gather_claude, "notion": _gather_notion, "gmail": _gather_gmail}


def _gather_all_docs() -> list[tuple[str, str]]:
    """(key, doc) for every current source doc. `key` uniquely identifies a doc."""
    return _gather_claude() + _gather_notion() + _gather_gmail()


def _load_ledger() -> set[str]:
    return set(json.loads(LEDGER_PATH.read_text())) if LEDGER_PATH.exists() else set()


def _save_ledger(keys: set[str]) -> None:
    LEDGER_PATH.write_text(json.dumps(sorted(keys)))


async def build_graph() -> None:
    """FULL rebuild: prune everything, re-ingest all sources, reset the ledger.
    Use only for a clean start or an embedding-model change."""
    configure()
    items = _gather_all_docs()
    print(f"full rebuild: {len(items)} docs into '{DATASET}'…")
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    await cognee.remember([doc for _, doc in items], dataset_name=DATASET)
    _save_ledger({key for key, _ in items})
    print(f"done — {len(items)} docs ingested, ledger reset.")


async def sync(source: str | None = None) -> dict:
    """INCREMENTAL: only docs NOT already in the graph pass through remember().

    source: "claude" | "notion" | "gmail" | None (all). Returns {source, total, added}.
    """
    configure()
    ingested = _load_ledger()
    items = _GATHER[source]() if source in _GATHER else _gather_all_docs()
    new = [(k, d) for k, d in items if k not in ingested]
    print(f"[sync {source or 'all'}] {len(items)} docs · {len(new)} new")
    if new:
        await cognee.remember([doc for _, doc in new], dataset_name=DATASET)
        _save_ledger(ingested | {key for key, _ in new})
    return {"source": source or "all", "total": len(items), "added": len(new)}


def backfill_ledger() -> None:
    """Mark all CURRENT source docs as already-ingested (no remember). Run once so
    sync() knows the contents of a graph that was built before the ledger existed."""
    items = _gather_all_docs()
    _save_ledger({key for key, _ in items})
    print(f"ledger backfilled with {len(items)} keys (no ingestion).")


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
    # python cognee_client.py            -> incremental sync (only new docs)
    # python cognee_client.py build      -> full rebuild (prune + all)
    # python cognee_client.py backfill   -> register current docs without ingesting
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd == "build":
        asyncio.run(build_graph())
    elif cmd == "backfill":
        backfill_ledger()
    else:
        asyncio.run(sync())
