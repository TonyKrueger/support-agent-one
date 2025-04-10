"""
Application Settings

This module handles configuration settings for the application,
loading values from environment variables with sensible defaults.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogSettings(BaseModel):
    """Log configuration settings."""
    LEVEL: str = Field("INFO", description="Logging level")
    FORMAT: str = Field("json", description="Log format (json or text)")
    LOGFIRE_API_KEY: Optional[str] = Field(None, description="Logfire API key if used")


class OpenAISettings(BaseModel):
    """OpenAI API configuration."""
    API_KEY: str = Field(..., description="OpenAI API key")
    ORGANIZATION_ID: Optional[str] = Field(None, description="OpenAI organization ID")
    EMBEDDING_MODEL: str = Field("text-embedding-3-small", description="Model for generating embeddings")
    COMPLETION_MODEL: str = Field("gpt-4-turbo", description="Model for chat completions")
    TEMPERATURE: float = Field(0.7, description="Default temperature for completions")
    MAX_TOKENS: Optional[int] = Field(None, description="Default max tokens for completions")
    TIMEOUT_SECONDS: int = Field(30, description="API request timeout in seconds")


class SupabaseSettings(BaseModel):
    """Supabase configuration."""
    URL: str = Field(..., description="Supabase project URL")
    ANON_KEY: str = Field(..., description="Supabase anonymous API key")
    SERVICE_KEY: Optional[str] = Field(None, description="Supabase service key for admin access")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App and environment configuration
    APP_NAME: str = Field("support-agent", description="Application name")
    DEBUG: bool = Field(False, description="Debug mode")
    ENVIRONMENT: str = Field("development", description="deployment environment")
    
    # Service configurations
    LOG: LogSettings = Field(default_factory=LogSettings)
    OPENAI: OpenAISettings = Field(...)
    SUPABASE: SupabaseSettings = Field(...)
    
    # Shortcut properties for commonly used settings
    @property
    def OPENAI_API_KEY(self) -> str:
        return self.OPENAI.API_KEY
    
    @property
    def SUPABASE_URL(self) -> str:
        return self.SUPABASE.URL
    
    @property
    def SUPABASE_KEY(self) -> str:
        return self.SUPABASE.ANON_KEY
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )


# Create a global settings instance
settings = Settings()

# Configure logging
import logging

# Set up logging based on environment
log_level = getattr(logging, settings.LOG.LEVEL.upper())
logging.basicConfig(level=log_level)
logging.info("Application settings loaded, environment=%s", settings.ENVIRONMENT) 