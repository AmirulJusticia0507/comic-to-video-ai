from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    storage_endpoint_url: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket_name: str = "comic-videos"

    ai_provider_api_key: str = ""
    ai_provider_base_url: str = "https://griphubrouter.web.id/v1"
    ai_provider_model: str = ""
    ai_video_model: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
