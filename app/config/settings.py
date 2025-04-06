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
    supabase_db_password: Optional[str] = Field(None)
    
    # Testing settings
    test_mock_openai: Optional[bool] = Field(False)
    test_mock_supabase: Optional[bool] = Field(False)
    
    # Logging
    logfire_write_token: Optional[str] = Field(None)
    
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
import logging

# Set up logging based on environment
log_level = getattr(logging, settings.log_level.upper())
logging.basicConfig(level=log_level)
logging.info("Application settings loaded, environment=%s", settings.environment) 