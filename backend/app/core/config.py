from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, loaded from env vars / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CareScribe"
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./carescribe.db"

    fhir_server_url: str = "http://localhost:8080/fhir"

    llm_mode: Literal["ollama", "mock"] = "mock"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"

    whisper_model_size: str = "small"
    whisper_device: str = "cpu"

    mlflow_tracking_uri: str | None = None

    api_cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
