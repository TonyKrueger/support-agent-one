"""Common fixtures for tests."""

import os
import pytest
from openai import OpenAI
from supabase import create_client
import logfire

# Make sure we're using test environment
os.environ["ENVIRONMENT"] = "test"

@pytest.fixture
def supabase_client():
    """Create and return a Supabase client for testing."""
    from app.config.settings import settings
    
    client = create_client(settings.supabase_url, settings.supabase_key)
    return client

@pytest.fixture
def openai_client():
    """Create and return an OpenAI client for testing."""
    from app.config.settings import settings
    
    client = OpenAI(api_key=settings.openai_api_key)
    return client

@pytest.fixture
def configure_logfire():
    """Configure logfire for testing."""
    from app.config.settings import settings
    
    # Configure with test level
    logfire.configure(level="DEBUG")
    return settings 