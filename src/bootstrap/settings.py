from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://mealdi:mealdi@localhost:5432/mealdi"
    sql_echo: bool = False

    jwt_secret: str = Field(default="development-only-change-me", min_length=24)
    jwt_issuer: str = "mealdi"
    jwt_audience: str = "mealdi-web"
    access_token_ttl_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_ttl_days: int = Field(default=14, ge=1, le=90)

    cors_origins: list[str] = ["http://localhost:8000"]
    cookie_secure: bool = False
    cookie_domain: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MEALDI_",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def reject_development_secret_in_production(self) -> Settings:
        if (
            self.environment == "production"
            and self.jwt_secret == "development-only-change-me"
        ):
            raise ValueError("MEALDI_JWT_SECRET must be set in production")

        return self
