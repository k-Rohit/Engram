import os
from pydantic_settings import BaseSettings


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
