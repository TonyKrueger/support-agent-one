"""Tests for OpenAI integration."""

import pytest
import logfire


@pytest.mark.asyncio
async def test_openai_connection(openai_client):
    """Test that we can connect to the OpenAI API."""
    try:
        # Make a simple models list request to verify the API key works
        models = openai_client.models.list()
        
        # Check that we got some models back
        assert len(models.data) > 0
        logfire.info("OpenAI connection test successful", model_count=len(models.data))
        
    except Exception as e:
        logfire.error("OpenAI connection test failed", error=str(e))
        pytest.fail(f"OpenAI connection failed: {e}")


@pytest.mark.asyncio
async def test_openai_embedding(openai_client):
    """Test that we can generate embeddings with OpenAI."""
    try:
        # Create a simple embedding
        response = openai_client.embeddings.create(
            input="Hello, world!",
            model="text-embedding-3-small"
        )
        
        # Check that we got an embedding back
        assert len(response.data) > 0
        assert len(response.data[0].embedding) > 0
        
        logfire.info(
            "OpenAI embedding test successful", 
            embedding_dimensions=len(response.data[0].embedding)
        )
        
    except Exception as e:
        logfire.error("OpenAI embedding test failed", error=str(e))
        pytest.fail(f"OpenAI embedding generation failed: {e}")


@pytest.mark.asyncio
async def test_openai_chat_completion(openai_client):
    """Test that we can generate chat completions with OpenAI."""
    try:
        # Create a simple chat completion
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=10
        )
        
        # Check that we got a response
        assert completion.choices[0].message.content
        
        logfire.info(
            "OpenAI chat completion test successful", 
            response=completion.choices[0].message.content
        )
        
    except Exception as e:
        logfire.error("OpenAI chat completion test failed", error=str(e))
        pytest.fail(f"OpenAI chat completion failed: {e}") 