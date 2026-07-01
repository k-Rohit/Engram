"""Singleton factory for the Gmail client."""

from functools import lru_cache

from backend.ingestion.gmail.client import GmailClient


@lru_cache(maxsize=1)
def get_client() -> GmailClient:
    """Return the process-wide singleton GmailClient."""
    return GmailClient()
