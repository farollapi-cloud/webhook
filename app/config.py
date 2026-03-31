from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    backend_public_url: str = "http://localhost:8000"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/webhook_saas"

    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    auth_client_id: str = "admin"
    auth_client_secret: str = "change-me-admin-secret"

    webhook_max_body_bytes: int = 512 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
