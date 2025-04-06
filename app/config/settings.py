import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI settings
    openai_api_key: str = Field(...)
    
    # Supabase settings
    supabase_url: str = Field(...)
    supabase_key: str = Field(...)
    supabase_service_key: Optional[str] = Field(None)
    
    # Application settings
    log_level: str = Field("info")
    environment: str = Field("development")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Initialize settings
settings = Settings()

# Configure logging
import logfire
from logfire import configure_logfire

configure_logfire(level=settings.log_level.upper())
logfire.info("Application settings loaded", environment=settings.environment) 