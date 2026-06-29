from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_FILE = Path(__file__).with_name(".env")


class Settings(BaseSettings):
    bot_token: str = Field(alias="BOT_TOKEN")
    admin_ids: Annotated[list[int], NoDecode] = Field(
        default_factory=list, alias="ADMIN_IDS"
    )
    admin_usernames: Annotated[list[str], NoDecode] = Field(
        default_factory=list, alias="ADMIN_USERNAMES"
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///kino_bot.db", alias="DATABASE_URL"
    )
    main_channel_id: str | None = Field(default=None, alias="MAIN_CHANNEL_ID")
    log_file: str = Field(default="bot.log", alias="LOG_FILE")

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: str | list[int] | None) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        return [int(item.strip()) for item in value.split(",") if item.strip()]

    @field_validator("admin_usernames", mode="before")
    @classmethod
    def parse_admin_usernames(cls, value: str | list[str] | None) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [item.strip().lstrip("@").lower() for item in value if item.strip()]
        return [
            item.strip().lstrip("@").lower()
            for item in value.split(",")
            if item.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
