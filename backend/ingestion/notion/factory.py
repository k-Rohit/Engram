"""Singleton factory for the Notion client."""

from functools import lru_cache

from backend.ingestion.notion.client import NotionClient


@lru_cache(maxsize=1)
def get_client() -> NotionClient:
    """Return the process-wide singleton NotionClient."""
    return NotionClient()
