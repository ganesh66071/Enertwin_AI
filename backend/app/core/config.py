"""Application configuration via environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/enertwin"

    # Firebase
    firebase_project_id: str = ""
    firebase_client_email: str = ""
    firebase_private_key: str = ""

    # LLM
    llm_api_key: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"

    # CORS
    frontend_url: str = "http://localhost:3000"

    # App
    debug: bool = True
    co2_emission_factor_kg_per_kwh: float = 0.68
    default_electricity_tariff: float = 8.2
    api_prefix: str = "/api"

    @property
    def cors_origins(self) -> List[str]:
        return [self.frontend_url, "http://127.0.0.1:3000"]

    @property
    def firebase_configured(self) -> bool:
        return bool(
            self.firebase_project_id
            and self.firebase_client_email
            and self.firebase_private_key
        )

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
