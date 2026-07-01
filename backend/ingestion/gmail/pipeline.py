"""Gmail pipeline: fetch selected newsletters -> chunk -> save to Supabase.

Verbatim (no LLM distillation). Idempotent by Message-ID: emails already stored
are skipped.

Run directly:  python backend/ingestion/gmail/pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.config import NEWSLETTER_SENDERS
from backend.ingestion.gmail.factory import get_client as get_gmail_client
from backend.ingestion.gmail.chunker import split_email
from backend.db.supabase_client import get_ingested_message_ids, save_emails


def run() -> None:
    if not NEWSLETTER_SENDERS:
        print("No senders configured — add addresses to NEWSLETTER_SENDERS in config.py")
        return

    emails = get_gmail_client().fetch_from_senders(NEWSLETTER_SENDERS)
    done = get_ingested_message_ids()
    print(f"\n{len(emails)} emails from {len(NEWSLETTER_SENDERS)} senders · {len(done)} already ingested\n")

    for mail in emails:
        if mail["message_id"] in done:
            print(f"  skip   {mail['subject'][:45]} — already ingested")
            continue
        chunks = split_email(mail)
        if not chunks:
            continue
        written = save_emails(chunks)
        print(f"  saved  {mail['subject'][:45]} -> {written} chunks")

    print("\nDone.")


if __name__ == "__main__":
    run()
