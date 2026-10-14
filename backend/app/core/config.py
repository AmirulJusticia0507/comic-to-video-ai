from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    superadmin_email: str = ""
    superadmin_password: str = ""

    storage_endpoint_url: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket_name: str = "comic-videos"

    ai_provider_api_key: str = ""
    ai_provider_base_url: str = "https://griphubrouter.web.id/v1"
    ai_provider_model: str = ""
    ai_image_model: str = ""

    video_provider: str = "higgsfield"
    video_api_base_url: str = "https://api.higgsfield.ai"
    video_api_key_id: str = ""
    video_api_key_secret: str = ""
    video_model: str = "alibaba/wan-3.0-prime/image-to-video"
    video_duration_seconds: int = 5
    video_resolution: str = "720p"
    video_aspect_ratio: str = "adaptive"
    video_generate_audio: bool = False
    video_poll_interval_seconds: int = 5
    video_timeout_seconds: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
