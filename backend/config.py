import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env BEFORE the settings classes below read os.getenv() as their defaults.
load_dotenv()


class LLMSettings(BaseSettings):
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    embeddings_model: str = ""
    api_key: str | None = os.getenv("LLM_API_KEY")

class DistillationLLMSettings(BaseSettings):
    # Cheap, reliable OpenAI model for distilling transcripts into insight cards.
    dis_llm_model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "LLM_API_KEY"
    temperature: float = 0.0


class GmailSettings(BaseSettings):
    # IMAP access via an app password (needs 2FA enabled on the Google account).
    imap_host: str = "imap.gmail.com"
    address: str | None = os.getenv("GMAIL_ADDRESS")
    app_password: str | None = os.getenv("GMAIL_APP_PASSWORD")
    since_days: int = 90  # how far back to look


# The only senders we ingest — your AI/tech newsletters. Edit this list.
NEWSLETTER_SENDERS: list[str] = [
     "the-ai-report@mail.beehiiv.com",
     "futureblueprint@mail.beehiiv.com",
     "decodingaimagazine@substack.com",
]
