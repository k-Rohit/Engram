"""Split Notion pages into retrieval-sized NoteChunks (markdown-aware)."""

from langchain_text_splitters import MarkdownTextSplitter

from backend.models.notion.note import NoteChunk

# Markdown-aware recursive splitter: breaks on headings/paragraphs first, then
# smaller boundaries. chunk_size/overlap are tuned for retrieval granularity
# (notes are short) — not for fitting an LLM context window.
_splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=150)


def split_page(page: dict) -> list[NoteChunk]:
    """Turn one page ({page_id, title, content}) into ordered NoteChunks."""
    content = (page.get("content") or "").strip()
    if not content:
        return []
    return [
        NoteChunk(
            page_id=page["page_id"],
            title=page["title"],
            chunk_index=i,
            content=chunk,
        )
        for i, chunk in enumerate(_splitter.split_text(content))
    ]
