from app.config import settings
from app.llm.base import LLMClient
from app.llm.gemma import GemmaClient
from app.llm.openai_gpt import OpenAIClient


def get_llm() -> LLMClient:
    if settings.llm_provider == "gemma":
        return GemmaClient()
    if settings.llm_provider == "openai":
        return OpenAIClient()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
