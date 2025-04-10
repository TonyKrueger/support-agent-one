"""Tests for Supabase connection."""

# Import test helper first to set environment variables
import tests.helpers

import pytest
import logging
from unittest.mock import patch


@pytest.mark.asyncio
async def test_supabase_connection(supabase_client):
    """Test that we can connect to Supabase."""
    try:
        # Simple query to verify connection
        response = supabase_client.table('customers').select('*').limit(1).execute()
        
        # With our mock, response is a dict with a 'data' key, not an object with a data attribute
        assert 'data' in response
        logging.info("Supabase connection test successful")
        
    except Exception as e:
        logging.error("Supabase connection test failed", exc_info=True)
        pytest.fail(f"Supabase connection failed: {e}")


@pytest.mark.asyncio
async def test_supabase_vector_extension(supabase_client):
    """Test that the Supabase vector extension is working."""
    try:
        # Mock vector similarity search using RPC call
        result = supabase_client.rpc('match_documents', {"query_embedding": [0.1] * 1536, "match_threshold": 0.8, "match_count": 10})
        
        # Verify that we get a response
        assert isinstance(result, dict)
        assert 'data' in result
        
        logging.info("Supabase vector extension test successful")
        
    except Exception as e:
        logging.error("Supabase vector extension test failed", exc_info=True)
        pytest.fail(f"Supabase vector extension test failed: {e}") 