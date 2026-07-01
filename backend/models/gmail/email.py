"""Pydantic model for a chunk of a newsletter/email.

Like Notion notes, newsletters are curated content — kept verbatim and only
chunked for retrieval, not LLM-distilled.
"""

from uuid import uuid4

from pydantic import BaseModel, Field


class EmailChunk(BaseModel):
    """One retrieval-sized chunk of an email, kept verbatim."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    message_id: str = Field(description="the email's RFC822 Message-ID (stable, for dedup)")
    sender: str
    subject: str
    date: str = ""
    chunk_index: int = 0
    content: str = Field(description="the email body text, verbatim")
    tags: list[str] = Field(default_factory=list)
    source: str = "gmail"
