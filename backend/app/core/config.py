from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    DATABASE_URL: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    # OAuth scopes for Google services
    GOOGLE_OAUTH_SCOPES: list[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        # "https://www.googleapis.com/auth/gmail.readonly",  # For Phase 5: Gmail integration - will add back later
    ]

    # Anthropic API
    ANTHROPIC_API_KEY: str

    # JWT Secret
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Storage (local, s3, or supabase)
    STORAGE_TYPE: str = "local"  # 'local', 's3', or 'supabase'
    UPLOAD_DIR: str = "uploads"  # Local storage directory
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_EXTENSIONS: set[str] = {
        # PDFs
        ".pdf",
        # Images
        ".png", ".jpg", ".jpeg", ".webp",
        # Documents
        ".doc", ".docx"
    }
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"

    # App Settings
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:5173"  # Vite default port
    BACKEND_URL: str = "http://localhost:8000"


settings = Settings()
