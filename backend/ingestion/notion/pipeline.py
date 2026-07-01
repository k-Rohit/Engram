"""Notion pipeline: read workspace -> markdown-chunk -> save to Supabase.

Notes are preserved verbatim (no LLM distillation). Idempotent at the page
level: pages already in the `notes` table are skipped.

Run directly:  python backend/ingestion/notion/pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.ingestion.notion.factory import get_client as get_notion_client
from backend.ingestion.notion.chunker import split_page
from backend.db.supabase_client import get_ingested_page_ids, save_notes


def run() -> None:
    pages = get_notion_client().extract_workspace()
    done = get_ingested_page_ids()
    print(f"\n{len(pages)} pages · {len(done)} already ingested\n")

    for page in pages:
        if page["page_id"] in done:
            print(f"  skip   {page['title'][:40]} — already ingested")
            continue

        chunks = split_page(page)
        if not chunks:
            print(f"  empty  {page['title'][:40]} — no text")
            continue

        written = save_notes(chunks)
        print(f"  saved  {page['title'][:40]} -> {written} chunks")

    print("\nDone.")


if __name__ == "__main__":
    run()
