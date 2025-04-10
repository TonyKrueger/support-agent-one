"""Common fixtures for tests."""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Import test helpers to set up environment
import tests.helpers

# OpenAI mock classes
class MockOpenAIResponse:
    """Mock for OpenAI API responses."""
    def __init__(self, data=None, choices=None):
        self.data = data or []
        self.choices = choices or []
        
class MockOpenAIMessage:
    """Mock for OpenAI chat message."""
    def __init__(self, content="Hello, I'm a test response"):
        self.content = content

class MockOpenAIChoice:
    """Mock for OpenAI choice object."""
    def __init__(self, message=None):
        self.message = message or MockOpenAIMessage()

class MockEmbedding:
    """Mock for OpenAI embedding."""
    def __init__(self, embedding=None):
        self.embedding = embedding or [0.1] * 1536

# Mock for OpenAI client
class MockOpenAI:
    """Mock for OpenAI client."""
    def __init__(self, api_key=None):
        self.models = MagicMock()
        self.models.list = MagicMock(return_value=MockOpenAIResponse(data=[{"id": "gpt-4o"}]))
        
        self.embeddings = MagicMock()
        self.embeddings.create = MagicMock(
            return_value=MockOpenAIResponse(data=[MockEmbedding()])
        )
        
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = MagicMock(
            return_value=MockOpenAIResponse(
                choices=[MockOpenAIChoice()]
            )
        )

# Mock for Supabase client
class MockSupabase:
    """Mock for Supabase client."""
    def __init__(self, url=None, key=None):
        self.table = MagicMock()
        self.table.return_value = self
        
        self.from_ = MagicMock()
        self.from_.return_value = self
        
        self.select = MagicMock()
        self.select.return_value = self
        
        self.insert = MagicMock()
        self.insert.return_value = self
        
        self.update = MagicMock()
        self.update.return_value = self
        
        self.delete = MagicMock()
        self.delete.return_value = self
        
        self.order = MagicMock()
        self.order.return_value = self
        
        self.limit = MagicMock()
        self.limit.return_value = self
        
        self.execute = MagicMock()
        self.execute.return_value = {"data": []}
        
        self.rpc = MagicMock()
        self.rpc.return_value = {"data": []}
        
        self.storage = MagicMock()
        self.storage.from_.return_value.upload.return_value = {"path": "test_path"}
        
        self.auth = MagicMock()

@pytest.fixture
def supabase_client():
    """Create and return a mocked Supabase client for testing."""
    return MockSupabase()

@pytest.fixture
def openai_client():
    """Create and return a mocked OpenAI client for testing."""
    return MockOpenAI()

@pytest.fixture(autouse=True)
def mock_logfire():
    """Mock logfire to avoid making real external calls during tests."""
    with patch('logfire.configure'), \
         patch('logfire.info'), \
         patch('logfire.debug'), \
         patch('logfire.warning'), \
         patch('logfire.error'):
        yield

@pytest.fixture(autouse=True)
def mock_openai_client():
    """Mock OpenAI client globally to avoid real API calls during tests."""
    with patch('openai.OpenAI', MockOpenAI), \
         patch('openai.AsyncOpenAI', MockOpenAI), \
         patch('pydantic_ai.providers.openai.AsyncOpenAI', MockOpenAI):
        yield

@pytest.fixture(autouse=True)
def mock_supabase_client():
    """Mock Supabase client globally to avoid real API calls during tests."""
    with patch('supabase.create_client', return_value=MockSupabase()):
        yield

@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment variables for testing"""
    os.environ['OPENAI_API_KEY'] = 'sk-test-key'
    os.environ['SUPABASE_URL'] = 'https://example.supabase.co'  
    os.environ['SUPABASE_KEY'] = 'test-key'
    os.environ['TEST_MOCK_OPENAI'] = 'true'
    os.environ['TEST_MOCK_SUPABASE'] = 'true'
    yield 