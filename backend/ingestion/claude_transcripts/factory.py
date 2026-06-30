"""Singleton factory for the Claude transcripts client."""

from functools import lru_cache

from backend.ingestion.claude_transcripts.client import ClaudeTranscriptsClient


@lru_cache(maxsize=1)
def get_client() -> ClaudeTranscriptsClient:
    """Return the process-wide singleton ClaudeTranscriptsClient."""
    return ClaudeTranscriptsClient()
