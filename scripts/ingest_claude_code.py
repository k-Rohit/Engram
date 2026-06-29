"""End-to-end: ingest real Claude Code transcripts into Cognee, then recall.

Usage:
    uv run python scripts/ingest_claude_code.py [encoded_project_dir] [question]

Defaults to the Langgraph project and a question about it. Keeps the run small
(few sessions / capped turns) so cognify stays fast and cheap.
"""

import asyncio
import sys

from backend.config import configure_cognee
from backend.ingestion import claude_code as cc

DEFAULT_PROJECT = "-Users-kumarrohit-Desktop-Langgraph"
DEFAULT_QUESTION = "What did I learn about python-dotenv and LangGraph?"
DATASET = "claude_code"


async def main() -> None:
    source_project = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROJECT
    question = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_QUESTION

    configure_cognee()
    import cognee

    print(f"\n[1/4] Clean slate (forget everything)…")
    await cognee.forget(everything=True)

    print(f"[2/4] Parsing transcripts for {source_project} …")
    docs = cc.parse_transcripts(
        source_project=source_project,
        max_sessions=3,
        max_turns_per_session=16,
    )
    print(f"      -> {len(docs)} session document(s), "
          f"{sum(len(d['text']) for d in docs)} chars total")

    print(f"[3/4] remember() each session into dataset '{DATASET}' (builds the graph)…")
    for i, d in enumerate(docs, 1):
        tag = f"[Source: claude_code] [Project: {cc.decode_project_name(d['project_dir'])}] [Session: {d['session']}]"
        await cognee.remember(f"{tag}\n\n{d['text']}", dataset_name=DATASET)
        print(f"      [{i}/{len(docs)}] remembered session {d['session']}")

    print(f"\n[4/4] recall(): {question!r}")
    results = await cognee.recall(
        question,
        datasets=[DATASET],
        context_profile="qa",
        include_references=True,
    )
    print(f"\n=== recall returned {len(results)} entr(ies) ===")
    for r in results:
        print(f"\n• {type(r).__name__}:")
        print("  ", getattr(r, "text", r))


if __name__ == "__main__":
    asyncio.run(main())
