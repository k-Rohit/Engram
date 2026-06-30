"""Full Claude-transcript pipeline: clean -> distill -> save to Supabase.

Incremental & idempotent: a per-session watermark (`sessions.distilled_turns`)
records how many turns of each session have been distilled. Each run processes
ONLY the newly-appended turns — so continuing an existing session is captured,
old turns are never re-distilled (no duplicate cards, no wasted LLM cost).

Run directly:  python backend/ingestion/claude_transcripts/pipeline.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.ingestion.claude_transcripts.factory import get_client
from backend.ingestion.claude_transcripts.client import format_conversation
from backend.ingestion.claude_transcripts.distiller import distill_conversation
from backend.db.supabase_client import get_session_watermarks, save_cards, set_watermark


def run(only_project: str | None = None, sleep_between: float = 1.0) -> None:
    sessions = get_client().clean_all_sessions()  # smallest-first
    if only_project:
        sessions = [s for s in sessions if s["project"] == only_project]
    marks = get_session_watermarks()
    scope = f" for project '{only_project}'" if only_project else ""
    print(f"{len(sessions)} sessions{scope} · {len(marks)} with watermarks\n")

    for s in sessions:
        total = len(s["turns"])
        already = marks.get(s["session_id"], 0)
        new_turns = s["turns"][already:]

        if not new_turns:
            print(f"  skip    {s['project']:24} ({s['session_id'][:8]}) — no new turns")
            continue

        label = "distill " if already == 0 else "extend  "
        print(f"  {label}{s['project']:24} ({s['session_id'][:8]}) · "
              f"{len(new_turns)} new turns (had {already}/{total}) …", flush=True)
        try:
            cards = distill_conversation(format_conversation(new_turns))
            written = save_cards(s, cards)
            set_watermark(s["session_id"], s["project"], total)  # advance only on success
            print(f"          -> {written} cards saved · watermark -> {total}")
        except Exception as e:
            # One bad session won't abort the run; its watermark isn't advanced,
            # so the next run retries those turns.
            print(f"          !! FAILED ({type(e).__name__}: {str(e)[:80]}) — will retry next run")
        time.sleep(sleep_between)

    print("\nDone.")


if __name__ == "__main__":
    # Optional CLI arg: a project name to ingest only that project first.
    #   python pipeline.py "Arxiv_Paper_Curator"   -> just Arxiv
    #   python pipeline.py                          -> everything (only new turns)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    run(only_project=only)
