"""Markaziy konfiguratsiya — barcha sozlamalar shu yerdan o'qiladi."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ── Telegram bot ────────────────────────────────────
    bot_token: str = ""
    bot_username: str = ""

    # ── Guruh ───────────────────────────────────────────
    group_chat_id: int = 0

    # ── Boshliq (birinchi super admin) ──────────────────
    owner_id: int = 0

    # ── Mini App ────────────────────────────────────────
    webapp_url: str = ""
    frontend_origin: str = "*"

    # ── Xavfsizlik ──────────────────────────────────────
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # ── Baza ────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./iqtm.db"

    # ── Rejim ───────────────────────────────────────────
    debug: bool = True

    @field_validator("group_chat_id", "owner_id", mode="before")
    @classmethod
    def _int_or_zero(cls, v):
        """Placeholder yoki bo'sh qiymat → 0 (ilova ishga tushaveradi)."""
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
