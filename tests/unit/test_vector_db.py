"""Tests for the vector database utility."""

import pytest
import logfire

from app.utils.vector_db import VectorDB


@pytest.fixture
def vector_db():
    """Create and return a vector database utility instance."""
    return VectorDB()


@pytest.mark.asyncio
async def test_vector_db_initialization(vector_db):
    """Test that the vector database utility initializes correctly."""
    assert vector_db is not None
    assert vector_db.openai_client is not None
    assert vector_db.supabase is not None
    logfire.info("Vector database utility initialization test successful")


@pytest.mark.asyncio
async def test_generate_embedding(vector_db):
    """Test generating an embedding."""
    embedding = await vector_db._generate_embedding("This is a test query")
    
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0  # Embeddings should have dimensions
    assert all(isinstance(x, float) for x in embedding)
    
    logfire.info("Generate embedding test successful", embedding_dimension=len(embedding))


@pytest.mark.asyncio
async def test_vector_search(vector_db):
    """Test searching for documents in the vector database."""
    results = await vector_db.search("test query", limit=2)
    
    assert results is not None
    assert isinstance(results, list)
    assert len(results) > 0  # Should have at least one result
    
    # Verify the structure of the results
    for result in results:
        assert "id" in result
        assert "document_id" in result
        assert "content" in result
        assert "similarity" in result
    
    logfire.info("Vector search test successful", result_count=len(results)) 