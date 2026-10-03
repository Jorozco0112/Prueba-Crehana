"""Configuration read from environment variables (or a `.env` file) (DEC-042).

Each component loads only what it needs: the migration job, for example, does not need
the JWT secret.
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://todo:todo@localhost:5432/todo"


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=30, gt=0)


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()
