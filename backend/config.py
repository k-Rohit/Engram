"""Environment + Cognee configuration.

Import `configure_cognee()` once at app startup (before any remember/recall call).

Cognee 1.2.2 notes:
- Defaults to OpenAI for BOTH the LLM (openai/gpt-5-mini) and embeddings
  (openai/text-embedding-3-large), reading the LLM_API_KEY env var.
- Auth + multi-tenancy are ON by default. For a single-user hackathon, set
  ENABLE_BACKEND_ACCESS_CONTROL=false (env var) or every call needs a user.
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Single-user hackathon: disable Cognee's default auth/multi-tenancy.
# Must be set BEFORE cognee is imported/used anywhere.
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

LLM_API_KEY = os.getenv("LLM_API_KEY")
# Cognee uses OpenAI for embeddings by default; reuse the same OpenAI key.
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", LLM_API_KEY)

# Where Cognee stores its graph/vector/relational DBs.
# MUST be absolute — Cognee builds file:// URIs internally and a relative path
# fails with "relative path can't be expressed as a file URI".
COGNEE_DATA_DIR = str(Path(os.getenv("COGNEE_DATA_DIR", "./cognee_data")).resolve())


def configure_cognee() -> None:
    """Apply Cognee config from env. Call once at startup."""
    import cognee

    if LLM_API_KEY:
        cognee.config.set_llm_api_key(LLM_API_KEY)
    if EMBEDDING_API_KEY:
        cognee.config.set_embedding_api_key(EMBEDDING_API_KEY)
    cognee.config.data_root_directory(COGNEE_DATA_DIR)

    # TODO (optional): switch the LLM to Anthropic while keeping OpenAI embeddings:
    #   cognee.config.set_llm_provider("anthropic")
    #   cognee.config.set_llm_model("claude-sonnet-4-6")
    logger.info("Cognee configured (data dir: %s)", COGNEE_DATA_DIR)
