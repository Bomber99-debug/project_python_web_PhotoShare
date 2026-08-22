"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for PhotoShare."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/photoshare",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    cloudinary_name: str = Field(default="", alias="CLOUDINARY_NAME")
    cloudinary_api_key: str = Field(default="", alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", alias="CLOUDINARY_API_SECRET")

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
