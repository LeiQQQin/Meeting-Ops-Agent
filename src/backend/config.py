"""
Application configuration using pydantic-settings.
Values are loaded from environment variables or a .env file.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    database_url: str = "sqlite+aiosqlite:///./meeting_ops.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # File upload
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 100

    # GitHub connector
    github_token: str = ""
    github_default_repo: str = ""

    # Jira connector
    jira_server_url: str = ""
    jira_user_email: str = ""
    jira_api_token: str = ""
    jira_default_project_key: str = "PROJ"

    # Slack connector
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_default_channel: str = "#general"

    # Notion connector
    notion_api_key: str = ""
    notion_default_database_id: str = ""

    # Scheduler
    followup_check_interval_hours: int = 24
    risk_check_interval_hours: int = 48


@lru_cache
def get_settings() -> Settings:
    return Settings()
