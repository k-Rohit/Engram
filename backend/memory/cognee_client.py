"""Unified Cognee graph — the second brain.

- Claude transcripts: clean -> distill -> cards (in Supabase, because distilling
  is expensive and worth persisting) -> fed here, WITH session dates.
- Notion & Gmail: fetched and handed STRAIGHT to remember(). Cognee chunks,
  extracts entities natively — no chunking/Supabase glue needed.
- Quick notes: captured straight from the UI via capture_note().
- The graph ledger (what's already ingested) lives in Supabase — Cognee does
  NOT dedup on remember(), so this record must be durable.

CLI:  python backend/memory/cognee_client.py [sync|build|backfill]
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv()

import cognee

from backend.config import NEWSLETTER_SENDERS
from backend.db.supabase_client import (
    add_ledger_keys,
    get_client,
    get_ledger_keys,
    get_unconsolidated_feedback_sessions,
    mark_feedback_consolidated,
    save_feedback,
)
from backend.ingestion.notion.factory import get_client as get_notion_client
from backend.ingestion.gmail.factory import get_client as get_gmail_client

DATASET = "engram"
DATA_DIR = str(Path(__file__).resolve().parents[2] / "cognee_data")
# How much answer feedback shapes future recall ranking (0 = ignore feedback).
FEEDBACK_INFLUENCE = 0.3

# Overrides Cognee's default QA prompt (which produces templated dumps or lazy
# one-liners like "Got it."). Forces direct, grounded, dated answers.
ENGRAM_SYSTEM_PROMPT = """You are the user's personal memory assistant. You are given excerpts from the user's own past conversations, notes, and reading.

Answer the user's question DIRECTLY and CONCISELY, in plain prose. Rules:
- Answer ONLY what was asked. If they ask "what did I ask about X", list the specific questions they asked about X.
- Address the user as "you". A few sentences or a short bullet list.
- Ground every statement in the provided memory; never invent. If the memory doesn't cover it, say so plainly.
- Memory excerpts carry [Date: ...] tags — use them when the question involves time ("recently", "last month", "when did I").
- Never reply with filler like "Got it." — always give substance or say the memory has nothing.
"""

# Old local ledger — kept only to migrate its keys into Supabase once.
LEGACY_LEDGER = Path(__file__).resolve().parents[2] / "cognee_ingested.json"


def configure() -> None:
    cognee.config.set_llm_api_key(os.getenv("LLM_API_KEY"))
    cognee.config.set_llm_model("openai/gpt-4o-mini")
    cognee.config.set_embedding_model("openai/text-embedding-3-small")
    cognee.config.set_embedding_dimensions(1536)  # 3-small is 1536-dim
    cognee.config.data_root_directory(DATA_DIR)


def _day(iso: str | None) -> str:
    """'2026-06-21T05:22:01.055Z' -> '2026-06-21' (empty-safe)."""
    return (iso or "")[:10]


# ---------- doc formats (dates included so temporal recall works) ----------

def _card_doc(c: dict) -> str:
    date = _day(c.get("session_date"))
    date_tag = f" [Date: {date}]" if date else ""
    return (
        f"[Source: claude_code] [Project: {c['project']}] [Kind: {c['kind']}]{date_tag}\n"
        f"{c['title']}\nQ: {c.get('question', '')}\nA: {c['answer']}"
    )


def _page_doc(p: dict) -> str:
    date = _day(p.get("last_edited"))
    date_tag = f" [Edited: {date}]" if date else ""
    return f"[Source: notion] [Title: {p['title']}]{date_tag}\n\n{p['content']}"


def _email_doc(e: dict) -> str:
    return (
        f"[Source: gmail] [From: {e['sender']}] [Subject: {e['subject']}] "
        f"[Date: {e.get('date', '')}]\n\n{e['body']}"
    )


def _cards() -> list[dict]:
    """ALL distilled cards, every project — one unified brain."""
    try:
        return get_client().table("cards").select("*").execute().data
    except Exception:
        return []


# ---------- gathering ----------

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


def _note_doc(n: dict) -> str:
    return f"[Source: note] [Date: {_day(n.get('created_at'))}]\n\n{n['text']}"


def _gather_notes() -> list[tuple[str, str]]:
    """Captured notes, from Supabase — so rebuilds don't destroy them."""
    try:
        rows = get_client().table("notes").select("*").execute().data
        return [(f"note:{n['id']}", _note_doc(n)) for n in rows]
    except Exception:
        return []


_GATHER = {"claude": _gather_claude, "notion": _gather_notion, "gmail": _gather_gmail}


def _gather_all_docs() -> list[tuple[str, str]]:
    """(key, doc) for every current source doc. `key` uniquely identifies a doc."""
    return _gather_claude() + _gather_notion() + _gather_gmail() + _gather_notes()


# ---------- ledger (Supabase-backed; migrates the old JSON file once) ----------

def _load_ledger() -> set[str]:
    keys = get_ledger_keys()
    if not keys and LEGACY_LEDGER.exists():
        legacy = set(json.loads(LEGACY_LEDGER.read_text()))
        if legacy:
            add_ledger_keys(sorted(legacy))
            print(f"migrated {len(legacy)} ledger keys from JSON -> Supabase")
        return legacy
    return keys


# ---------- build / sync ----------

async def build_graph() -> None:
    """FULL rebuild: prune everything, re-ingest all sources, reset the ledger.
    Use only for a clean start or an embedding-model change."""
    configure()
    items = _gather_all_docs()
    print(f"full rebuild: {len(items)} docs into '{DATASET}'…")
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    await cognee.remember([doc for _, doc in items], dataset_name=DATASET)
    # reset ledger to exactly this build
    sb = get_client()
    sb.table("graph_ledger").delete().neq("key", "").execute()
    add_ledger_keys([key for key, _ in items])
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
        add_ledger_keys([key for key, _ in new])
    return {"source": source or "all", "total": len(items), "added": len(new)}


def backfill_ledger() -> None:
    """Mark all CURRENT source docs as already-ingested (no remember)."""
    items = _gather_all_docs()
    add_ledger_keys([key for key, _ in items])
    print(f"ledger backfilled with {len(items)} keys (no ingestion).")


# ---------- quick capture ----------

async def capture_note(text: str) -> dict:
    """'Remember this' — store a thought durably (Supabase) AND in the graph, dated."""
    configure()
    note_id = str(uuid4())
    created = datetime.now(timezone.utc).isoformat()
    row = {"id": note_id, "text": text.strip(), "created_at": created}
    get_client().table("notes").insert(row).execute()  # durable copy first
    await cognee.remember(_note_doc(row), dataset_name=DATASET)
    add_ledger_keys([f"note:{note_id}"])
    return {"ok": True, "key": f"note:{note_id}"}


# ---------- feedback loop ----------

async def record_feedback(
    session_id: str, question: str, answer: str, score: int, text: str = ""
) -> dict:
    """Rate an answer. Stored in Supabase (audit) AND pushed into Cognee session
    memory as a QAEntry with feedback — recall(feedback_influence>0) uses it,
    and consolidate_feedback() bridges it into the permanent graph."""
    configure()
    save_feedback(session_id, question, answer, score, text)
    entry = cognee.QAEntry(
        question=question,
        answer=answer,
        feedback_score=score,
        feedback_text=text or ("useful" if score > 0 else "not useful"),
    )
    await cognee.remember(entry, session_id=session_id)
    return {"ok": True}


async def consolidate_feedback() -> dict:
    """Run cognee.improve() over sessions with new feedback — bridges session
    memory + feedback weighting into the permanent graph. Costs LLM calls;
    run deliberately (endpoint / scheduled), not on every click."""
    configure()
    session_ids = get_unconsolidated_feedback_sessions()
    if not session_ids:
        return {"ok": True, "sessions": 0}
    await cognee.improve(dataset=DATASET, session_ids=session_ids)
    mark_feedback_consolidated(session_ids)
    return {"ok": True, "sessions": len(session_ids)}


# ---------- ask / stats ----------

async def ask(query: str, session_id: str | None = None) -> dict:
    """Unified recall across the whole brain. Returns {answer, sources}."""
    import re

    configure()
    results = await cognee.recall(
        query, datasets=[DATASET], context_profile="qa",
        include_references=True, session_id=session_id,
        feedback_influence=FEEDBACK_INFLUENCE,
        system_prompt=ENGRAM_SYSTEM_PROMPT,
    )
    text = "\n\n".join(getattr(r, "text", "") for r in results if getattr(r, "text", ""))
    if "Evidence:" in text:
        answer, evidence = text.split("Evidence:", 1)
    else:
        answer, evidence = text, ""
    sources = sorted({s.strip() for s in re.findall(r"\[Source: ([^\]]+)\]", evidence)})
    return {"answer": answer.strip() or "Nothing relevant found in your memory yet.", "sources": sources}


async def wall(n: int = 24) -> dict:
    """The Stacks — a browsable sample of the archive for rediscovery.

    Mixes distilled cards (questions you asked, concepts, decisions — from
    Supabase, no LLM cost) with entity concepts sampled from the graph itself
    (which include newsletter/notion-derived concepts).
    """
    import random

    cards = []
    try:
        rows = (
            get_client().table("cards")
            .select("kind,title,question,answer,project,session_date,created_at")
            .execute().data
        )
        random.shuffle(rows)
        for r in rows[: max(n - 8, n // 2)]:
            cards.append({
                "type": "card",
                "kind": r["kind"],
                "title": r["title"],
                "question": r.get("question") or r["title"],
                "answer": r["answer"],
                "project": r.get("project"),
                "date": _day(r.get("session_date") or r.get("created_at")),
            })
    except Exception:
        pass

    # Graph entity concepts (best-effort — includes gmail/notion-derived nodes).
    concepts: list[dict] = []
    try:
        configure()
        from cognee.infrastructure.databases.graph import get_graph_engine

        engine = await get_graph_engine()
        nodes, _ = await engine.get_graph_data()
        names = set()
        for node in nodes:
            props = node[1] if isinstance(node, (list, tuple)) and len(node) > 1 else (
                node if isinstance(node, dict) else {}
            )
            if not isinstance(props, dict):
                continue
            name = props.get("name")
            ntype = str(props.get("type", ""))
            if name and ntype == "Entity" and 3 <= len(str(name)) <= 48:
                names.add(str(name))
        for name in random.sample(sorted(names), min(8, len(names))):
            concepts.append({"type": "concept", "title": name,
                             "question": f"What do I know about {name}?"})
    except Exception:
        pass

    items = cards + concepts
    random.shuffle(items)
    return {"items": items[:n]}


def stats() -> dict:
    """Live counts for the UI, from the durable ledger."""
    keys = get_ledger_keys()
    by = {"card": 0, "notion": 0, "gmail": 0, "note": 0}
    for k in keys:
        prefix = k.split(":", 1)[0]
        if prefix in by:
            by[prefix] += 1
    return {
        "claude_cards": by["card"],
        "notion_pages": by["notion"],
        "gmail_issues": by["gmail"],
        "notes": by["note"],
        "total_docs": len(keys),
    }


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
