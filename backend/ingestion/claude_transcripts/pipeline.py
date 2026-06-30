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


def run(sleep_between: float = 1.0) -> None:
    sessions = get_client().clean_all_sessions()
    done = get_distilled_session_ids()
    print(f"{len(sessions)} sessions found · {len(done)} already distilled\n")

    for s in sessions:
        if s["session_id"] in done:
            print(f"  skip   {s['project']:24} ({s['session_id'][:8]}) — already distilled")
            continue

        print(f"  distill {s['project']:24} ({s['session_id'][:8]}) · {len(s['turns'])} turns …", flush=True)
        cards = distill_conversation(s["conversation"])
        written = save_cards(s, cards)
        print(f"          -> {written} cards saved")
        time.sleep(sleep_between)  # be gentle with the free model's rate limit

    print("\nDone.")


if __name__ == "__main__":
    run()
