import os
from typing import Any, List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "OFC HR Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ofc_hr.db"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Security & JWT
    JWT_SECRET_KEY: str = "super_secret_jwt_key_change_in_production_1234567890"
    JWT_REFRESH_SECRET_KEY: str = "super_secret_refresh_key_change_in_production_0987654321"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CSRF_SECRET_KEY: str = "csrf_secret_key_change_in_production"

    # Cookie Settings
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_SECURE: bool = False
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"

    # Rate Limiting (Requests per minute)
    RATE_LIMIT_PER_MINUTE: int = 1000
    AUTH_RATE_LIMIT_PER_MINUTE: int = 500

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "https://*.vercel.app"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> List[str]:
        if isinstance(value, str):
            if value.startswith("[") and value.endswith("]"):
                import json
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # SMTP / Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@ofchr.com"
    EMAILS_FROM_NAME: str = "OFC HR Platform"
    SMTP_ENABLED: bool = True

    # Google OAuth
    GOOGLE_CLIENT_ID: str = "google_client_id_placeholder"
    GOOGLE_CLIENT_SECRET: str = "google_client_secret_placeholder"

    # Okta SSO
    OKTA_CLIENT_ID: str = "okta_client_id_placeholder"
    OKTA_CLIENT_SECRET: str = "okta_client_secret_placeholder"
    OKTA_DOMAIN: str = "dev-okta.example.com"


settings = Settings()

