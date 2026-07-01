"""Pydantic model for a chunk of a Notion note.

Unlike Claude transcripts (noisy logs that need heavy LLM distillation), Notion
notes are already human-curated — so we PRESERVE the text verbatim and only
chunk it for retrieval. No problem/solution extraction, no rewriting.
"""

from uuid import uuid4

from pydantic import BaseModel, Field


class NoteChunk(BaseModel):
    """One retrieval-sized chunk of a Notion page, kept in the user's own words."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    page_id: str
    title: str
    chunk_index: int = Field(description="0-based position of this chunk within the page")
    content: str = Field(description="the note text, verbatim (not rewritten)")
    tags: list[str] = Field(default_factory=list)
    source: str = "notion"
