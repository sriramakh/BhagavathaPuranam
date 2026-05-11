from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bhagavatha Puranam"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/bhagavatha.db"
    storage_dir: str = "./storage"

    image_provider: str = "grok-imagine"
    grok_api_key: str = ""
    grok_image_model: str = "grok-imagine-image"
    grok_chat_model: str = "grok-4-1-fast"

    content_domain: str = "bhagavatham"
    mythology_mode: bool = True
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
