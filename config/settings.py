"""Configuration loader for DevResearch Daily Briefing."""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    TIMEZONE: str = "Asia/Karachi"
    DIGEST_TIME: str = "10:00"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'devresearch.db'}"

    # LLM
    LLM_PROVIDER: str = "heuristic"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL: str = "heuristic"

    # Mail
    MAIL_PROVIDER: str = "console"
    MAIL_FROM: str = "DevResearch Daily <daily@devresearch.local>"
    MAIL_RECIPIENTS: str = "user@example.com"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True

    # Resend / SendGrid
    RESEND_API_KEY: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None

    # Search APIs
    TAVILY_API_KEY: Optional[str] = None
    NEWSAPI_API_KEY: Optional[str] = None

    # IMAP
    IMAP_ENABLED: bool = False
    IMAP_SERVER: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_USER: Optional[str] = None
    IMAP_PASSWORD: Optional[str] = None
    IMAP_FOLDER: str = "INBOX"

    # Server
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def recipient_list(self) -> List[str]:
        if not self.MAIL_RECIPIENTS:
            return []
        return [r.strip() for r in self.MAIL_RECIPIENTS.split(",") if r.strip()]


settings = Settings()
