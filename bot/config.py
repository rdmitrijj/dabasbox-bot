"""Application configuration loaded from environment variables / .env file."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageBackend(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    bot_token: SecretStr = Field(..., description="Telegram Bot API token from @BotFather")
    admin_chat_id: int = Field(..., description="Chat ID that receives new order notifications")

    fsm_storage: StorageBackend = StorageBackend.MEMORY
    redis_url: str = "redis://localhost:6379/0"
    # How long an unfinished order survives in Redis (seconds). Ignored for memory storage.
    redis_state_ttl: int = 7 * 24 * 3600

    orders_log_path: str = "data/orders.jsonl"
    log_level: str = "INFO"

    @field_validator("bot_token")
    @classmethod
    def _token_format(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if ":" not in raw or not raw.split(":", 1)[0].isdigit():
            raise ValueError("BOT_TOKEN does not look like a Telegram bot token (expected '<digits>:<secret>')")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
