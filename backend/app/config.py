from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://idp:idp@localhost:5432/idp"

    llm_provider: Literal["gemma", "openai"] = "gemma"

    gemma_base_url: str = "http://localhost:11434"
    gemma_model: str = "gemma3:12b"
    gemma_api_key: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-5"

    sample_storage_dir: str = "storage/samples"
    max_sample_bytes: int = 10 * 1024 * 1024  # 10 MB
    hint_max_chars: int = 1000


settings = Settings()
