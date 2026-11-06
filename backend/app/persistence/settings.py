"""Runtime settings for the persistence/auth layer (environment-driven)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .database import DEFAULT_DATABASE_URL


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    access_token_expire_minutes: int = 30

    @property
    def is_configured(self) -> bool:
        return bool(self.secret_key)


def get_settings() -> Settings:
    """Build settings from the environment, failing loudly when unconfigured.

    ``PETROLUMEN_SECRET_KEY`` is mandatory in production; the auth router will
    raise a clear 500-style startup error if it is missing.
    """
    return Settings(
        secret_key=os.getenv("PETROLUMEN_SECRET_KEY", ""),
        database_url=os.getenv("PETROLUMEN_DATABASE_URL", DEFAULT_DATABASE_URL),
        access_token_expire_minutes=int(os.getenv("PETROLUMEN_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    )
