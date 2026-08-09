"""
Application Settings Manager.
Loads environment variables from the .env file using Pydantic Settings.
Includes SMTP configuration for real email delivery (Gmail, SendGrid, Outlook, etc.).
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "AI Recruitment Platform"
    PORT: int = 8000
    
    # MongoDB Atlas Database Config
    MONGODB_URI: str = ""
    DATABASE_NAME: str = "ai_recruitment"
    
    # Security & JWT Configuration
    JWT_SECRET: str = "super_secret_jwt_key_2026_recruit_ai_platform"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days

    # SMTP Real Email Dispatcher Settings
    SMTP_HOST: Optional[str] = None
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_EMAIL: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: str = "AI Recruitment Platform"
    FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True

    # AI Service Keys (Optional for Phase 1)
    GEMINI_API_KEY: str = ""

    # Configure Pydantic to read from .env file automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore unknown env variables
    )


# Global instance of settings to be imported across the app
settings = Settings()
