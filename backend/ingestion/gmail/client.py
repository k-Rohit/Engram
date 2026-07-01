"""Read selected newsletters from Gmail over IMAP.

Only fetches mail FROM the sender addresses you pass in (your AI/tech
newsletters), within the last `since_days`. Get the singleton via
factory.get_client().
"""

import sys
import email
import imaplib
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.config import GmailSettings


def _decode(value: str | None) -> str:
    """Decode a possibly MIME-encoded header (e.g. =?utf-8?...?=) to plain str."""
    if not value:
        return ""
    parts = []
    for text, enc in decode_header(value):
        if isinstance(text, bytes):
            parts.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            parts.append(text)
    return "".join(parts)


class GmailClient:
    """IMAP reader for a Gmail account. Read-only."""

    def __init__(self) -> None:
        s = GmailSettings()
        self.host = s.imap_host
        self.address = s.address
        self.password = s.app_password
        self.since_days = s.since_days

    def _connect(self) -> imaplib.IMAP4_SSL:
        mail = imaplib.IMAP4_SSL(self.host)
        mail.login(self.address, self.password)
        mail.select("INBOX")
        return mail

    def _get_body(self, msg: Message) -> str:
        """Prefer text/plain; fall back to extracting text from the HTML part."""
        plain, html = None, None
        for part in msg.walk() if msg.is_multipart() else [msg]:
            if part.get("Content-Disposition", "").startswith("attachment"):
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            text = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
            if part.get_content_type() == "text/plain":
                plain = text
            elif part.get_content_type() == "text/html":
                html = text

        if plain and plain.strip():
            return plain.strip()
        if html:
            import trafilatura  # already a dependency; great at newsletter HTML

            return (trafilatura.extract(html) or "").strip()
        return ""

    def fetch_from_senders(self, senders: list[str]) -> list[dict]:
        """Return {message_id, sender, subject, date, body} for each matching email."""
        if not senders:
            return []
        since = (datetime.now() - timedelta(days=self.since_days)).strftime("%d-%b-%Y")
        out: list[dict] = []
        mail = self._connect()
        try:
            for sender in senders:
                typ, data = mail.search(None, f'(FROM "{sender}" SINCE {since})')
                if typ != "OK":
                    continue
                for eid in data[0].split():
                    typ, msg_data = mail.fetch(eid, "(RFC822)")
                    if typ != "OK":
                        continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    body = self._get_body(msg)
                    if not body:
                        continue
                    out.append(
                        {
                            "message_id": _decode(msg.get("Message-ID")) or eid.decode(),
                            "sender": _decode(msg.get("From")),
                            "subject": _decode(msg.get("Subject")),
                            "date": _decode(msg.get("Date")),
                            "body": body,
                        }
                    )
        finally:
            mail.logout()
        return out
