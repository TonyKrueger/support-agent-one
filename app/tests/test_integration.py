"""
Integration Tests

This script tests the integration between OpenAI and Supabase services.
It validates that embeddings can be generated and stored, and that
vector similarity search functions correctly.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Load environment variables from .env file
load_dotenv()

from app.services.openai_service import get_embeddings, get_chat_completion
from app.services.supabase_service import (
    store_document,
    store_document_chunks,
    search_similar_chunks,
    test_connection
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def test_openai_connection():
    """Test connection to OpenAI API."""
    try:
        logger.info("Testing OpenAI API connection...")
        
        # Generate a simple completion as a test
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'OpenAI connection successful' if you can see this message."}
        ]
        
        response = get_chat_completion(messages, temperature=0)
        
        logger.info(f"OpenAI API response: {response}")
        assert "OpenAI connection successful" in response
        
        logger.info("✅ OpenAI API connection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ OpenAI API connection test failed: {str(e)}")
        return False


def test_supabase_connection():
    """Test connection to Supabase."""
    try:
        logger.info("Testing Supabase connection...")
        
        result = test_connection()
        assert result is True
        
        logger.info("✅ Supabase connection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase connection test failed: {str(e)}")
        return False


def test_embedding_storage():
    """Test generating embeddings and storing them in Supabase."""
    try:
        logger.info("Testing embedding generation and storage...")
        
        # Create a test document
        document_title = "Test Document"
        document_content = "This is a test document for embedding generation and storage."
        
        document = store_document(document_title, document_content)
        document_id = document["id"]
        
        logger.info(f"Created test document with ID: {document_id}")
        
        # Create test chunks
        chunks = [
            "This is a test document",
            "for embedding generation",
            "and storage in Supabase."
        ]
        
        # Generate embeddings
        embeddings = get_embeddings(chunks)
        
        assert len(embeddings) == len(chunks)
        assert len(embeddings[0]) == 1536  # OpenAI embedding dimension
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Store chunks with embeddings
        stored_chunks = store_document_chunks(document_id, chunks, embeddings)
        
        assert len(stored_chunks) == len(chunks)
        logger.info(f"Stored {len(stored_chunks)} document chunks with embeddings")
        
        logger.info("✅ Embedding generation and storage test passed")
        return True, document_id
        
    except Exception as e:
        logger.error(f"❌ Embedding generation and storage test failed: {str(e)}")
        return False, None


def test_vector_search(document_id):
    """Test vector similarity search."""
    try:
        if not document_id:
            logger.error("Cannot run vector search test without a valid document ID")
            return False
            
        logger.info("Testing vector similarity search...")
        
        # Generate embedding for a query
        query = "test embedding storage"
        query_embedding = get_embeddings([query])[0]
        
        # Search for similar chunks
        results = search_similar_chunks(query_embedding, limit=5)
        
        assert len(results) > 0
        
        logger.info(f"Found {len(results)} similar chunks:")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. Content: {result['content']} (Score: {result['similarity']})")
        
        logger.info("✅ Vector similarity search test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector similarity search test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all integration tests."""
    logger.info("Starting integration tests...")
    
    openai_success = test_openai_connection()
    supabase_success = test_supabase_connection()
    
    if openai_success and supabase_success:
        embedding_success, document_id = test_embedding_storage()
        
        if embedding_success:
            search_success = test_vector_search(document_id)
        else:
            search_success = False
    else:
        embedding_success = False
        search_success = False
    
    # Summary
    logger.info("\n--- Integration Test Results ---")
    logger.info(f"OpenAI Connection: {'✅ PASS' if openai_success else '❌ FAIL'}")
    logger.info(f"Supabase Connection: {'✅ PASS' if supabase_success else '❌ FAIL'}")
    logger.info(f"Embedding Storage: {'✅ PASS' if embedding_success else '❌ FAIL'}")
    logger.info(f"Vector Search: {'✅ PASS' if search_success else '❌ FAIL'}")
    
    success = all([openai_success, supabase_success, embedding_success, search_success])
    logger.info(f"\nOverall Test Status: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 