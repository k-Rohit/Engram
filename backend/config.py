import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class LLMSettings(BaseSettings):
    llm_model = 'gpt-4o-mini'
    temperature = 0.0
    embeddings_model = ""
    api_key = os.getenv("LLM_API_KEY")
    
class DistillationLLMSettings(BaseSettings):
    dis_llm_model = ""