"""Tests for the chat service."""

# Import test helper first to set environment variables
import tests.helpers

import pytest
import logfire

from app.services.chat_service import ChatService


@pytest.fixture
def chat_service(supabase_client):
    """Create and return a chat service instance."""
    # Create a chat service with a mocked Supabase client
    service = ChatService()
    # Replace the created client with our mock
    service.supabase = supabase_client
    return service


@pytest.fixture
def sample_messages():
    """Create sample messages for testing."""
    return [
        {"role": "user", "content": "Hello, I need help with my product."},
        {"role": "assistant", "content": "I'd be happy to help. What's the issue you're experiencing?"},
        {"role": "user", "content": "It's not turning on."}
    ]


@pytest.mark.asyncio
async def test_chat_service_initialization(chat_service):
    """Test that the chat service initializes correctly."""
    assert chat_service is not None
    assert chat_service.supabase is not None
    logfire.info("Chat service initialization test successful")


@pytest.mark.asyncio
async def test_get_conversation_history(chat_service):
    """Test getting conversation history."""
    # This is testing a placeholder method, so we're just checking it returns something
    history = await chat_service.get_conversation_history("test-customer-id")
    
    assert history is not None
    assert isinstance(history, list)
    assert len(history) > 0
    assert all(isinstance(msg, dict) for msg in history)
    assert all("role" in msg and "content" in msg for msg in history)
    
    logfire.info("Conversation history test successful", message_count=len(history))


@pytest.mark.asyncio
async def test_process_message(chat_service, sample_messages, monkeypatch):
    """Test processing a message.
    
    Note: This test patches the support_agent.run method to avoid making actual API calls.
    """
    from app.models.agent import SupportResult
    
    # Create a mock result for the agent
    mock_result = type('MockResult', (), {
        'data': SupportResult(
            support_response="This is a test response.",
            needs_followup=False,
            suggested_documents=["doc-123"]
        )
    })
    
    # Create a mock for the agent.run method
    async def mock_agent_run(*args, **kwargs):
        return mock_result
    
    # Apply the monkeypatch
    from app.models.agent import support_agent
    monkeypatch.setattr(support_agent, "run", mock_agent_run)
    
    # Run the test
    response = await chat_service.process_message(
        sample_messages,
        customer_id="test-customer-id",
        product_serial="test-serial"
    )
    
    # Verify the response
    assert response is not None
    assert "message" in response
    assert response["message"]["role"] == "assistant"
    assert response["message"]["content"] == "This is a test response."
    assert "needs_followup" in response
    assert "suggested_documents" in response
    
    logfire.info("Process message test successful", response=response) 