"""Split emails into retrieval-sized EmailChunks."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.models.gmail.email import EmailChunk

# Emails aren't markdown; a recursive splitter on paragraphs/sentences is best.
_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)


def split_email(mail: dict) -> list[EmailChunk]:
    """Turn one email ({message_id, sender, subject, date, body}) into EmailChunks."""
    body = (mail.get("body") or "").strip()
    if not body:
        return []
    return [
        EmailChunk(
            message_id=mail["message_id"],
            sender=mail["sender"],
            subject=mail["subject"],
            date=mail.get("date", ""),
            chunk_index=i,
            content=chunk,
        )
        for i, chunk in enumerate(_splitter.split_text(body))
    ]
