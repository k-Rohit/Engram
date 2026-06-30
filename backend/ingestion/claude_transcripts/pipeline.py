"""Full Claude-transcript pipeline: clean -> distill -> save to Supabase.

Idempotent: sessions already in the `cards` table are skipped, so re-running
never re-distills (and never re-pays the LLM cost) for the same session.

Run directly:  python backend/ingestion/claude_transcripts/pipeline.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.ingestion.claude_transcripts.factory import get_client
from backend.ingestion.claude_transcripts.distiller import distill_conversation
from backend.db.supabase_client import get_distilled_session_ids, save_cards


def run(only_project: str | None = None, sleep_between: float = 1.0) -> None:
    sessions = get_client().clean_all_sessions()  # smallest-first
    if only_project:
        sessions = [s for s in sessions if s["project"] == only_project]
    done = get_distilled_session_ids()
    scope = f" for project '{only_project}'" if only_project else ""
    print(f"{len(sessions)} sessions{scope} · {len(done)} already distilled\n")

    for s in sessions:
        if s["session_id"] in done:
            print(f"  skip   {s['project']:24} ({s['session_id'][:8]}) — already distilled")
            continue

        print(f"  distill {s['project']:24} ({s['session_id'][:8]}) · {len(s['turns'])} turns …", flush=True)
        try:
            cards = distill_conversation(s["conversation"])
            written = save_cards(s, cards)
            print(f"          -> {written} cards saved")
        except Exception as e:
            # Don't let one bad session abort the whole run — it just won't be
            # marked done, so a later run retries it.
            print(f"          !! FAILED ({type(e).__name__}: {str(e)[:80]}) — will retry next run")
        time.sleep(sleep_between)

    print("\nDone.")


if __name__ == "__main__":
    # Optional CLI arg: a project name to ingest only that project first.
    #   python pipeline.py "Arxiv_Paper_Curator"   -> just Arxiv
    #   python pipeline.py                          -> everything (skips done)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    run(only_project=only)
