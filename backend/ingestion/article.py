"""Fetch + extract a web article (Medium, Substack, blogs) via trafilatura.

trafilatura handles most article pages cleanly. If extraction returns None
(paywalled/blocked), the caller should fall back to user-pasted content.
"""

import trafilatura

def fetch_article(url: str) -> str | None:
    """Return clean article text, or None if extraction fails."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    return trafilatura.extract(downloaded)  # strips nav/boilerplate
