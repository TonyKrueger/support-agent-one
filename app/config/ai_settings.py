"""
AI Configuration Settings

This module provides configuration settings for AI model interactions.
These settings can be adjusted based on the specific needs of the application.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any


class AISettings(BaseSettings):
    """Configuration settings for AI model interactions."""
    
    # Model settings
    model: str = "gpt-4-turbo"
    embedding_model: str = "text-embedding-3-small"
    
    # Generation parameters
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, ge=1, le=8000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    
    # Streaming settings
    stream_enabled: bool = True
    stream_chunk_size: int = Field(default=20, ge=1, le=100)
    
    # Context window management
    max_context_length: int = Field(default=4000, ge=100, le=8000)
    max_conversation_messages: int = Field(default=10, ge=1, le=100)
    
    # Moderation settings
    moderation_enabled: bool = True
    moderation_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Response caching
    enable_caching: bool = False
    cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400)  # 1 hour default
    
    # Rate limiting
    rate_limit_requests: int = Field(default=60, ge=1)  # requests per minute
    
    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"


# Create a singleton instance
ai_settings = AISettings() 