from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cents LLM Service"
    host: str = "0.0.0.0"
    port: int = 8100

    internal_api_key: str = ""
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    model_catalog_directory: str = "model_catalog"
    request_timeout_seconds: int = Field(default=120, ge=5, le=600)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=("settings_",),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
