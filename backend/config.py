import os
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    embeddings_model: str = ""
    api_key: str | None = os.getenv("LLM_API_KEY")

class DistillationLLMSettings(BaseSettings):
    # Free OpenRouter model used to distill transcripts into insight cards.
    dis_llm_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.0
