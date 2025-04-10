"""
Document Retrieval Tests

This script tests the document retrieval system.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Load environment variables from .env file
load_dotenv()

from app.services.document_processor import process_document
from app.services.document_retrieval import (
    retrieve_relevant_chunks,
    format_retrieval_results,
    create_context_from_results,
    search_and_format_query
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def setup_test_documents():
    """Create test documents for retrieval testing."""
    try:
        logger.info("Setting up test documents...")
        
        # Create test documents with different content and metadata
        documents = [
            {
                "title": "Product Manual",
                "content": """
                This is a product manual for the XYZ-1000 device.
                The XYZ-1000 is a high-performance computing device designed for enterprise use.
                It features 32GB of RAM, 1TB SSD storage, and a dedicated GPU.
                To reset the device, press and hold the power button for 10 seconds.
                For technical support, contact support@example.com.
                """,
                "metadata": {"category": "manual", "product_id": "XYZ-1000"}
            },
            {
                "title": "Troubleshooting Guide",
                "content": """
                Common issues with the XYZ-1000 device:
                
                1. Device won't power on:
                   - Check power connection
                   - Ensure the power button is pressed firmly
                   - Verify the outlet has power
                
                2. Blue screen errors:
                   - Update device drivers
                   - Check for hardware conflicts
                   - Run diagnostic tools
                
                3. Overheating:
                   - Clean cooling vents
                   - Ensure proper ventilation
                   - Check internal fans
                """,
                "metadata": {"category": "troubleshooting", "product_id": "XYZ-1000"}
            },
            {
                "title": "Company Information",
                "content": """
                About Our Company:
                
                Founded in 2010, Example Corp is a leading provider of enterprise hardware solutions.
                Our mission is to deliver high-quality, reliable products for businesses of all sizes.
                
                We have offices in New York, London, and Tokyo, with over 500 employees worldwide.
                Our customer support team is available 24/7 to assist with any issues.
                
                For investment opportunities, please contact investor@example.com.
                """,
                "metadata": {"category": "company", "department": "corporate"}
            }
        ]
        
        # Process each document
        processed_docs = []
        for doc in documents:
            document, chunks = process_document(
                title=doc["title"],
                content=doc["content"],
                metadata=doc["metadata"],
                chunk_size=200,
                chunk_overlap=50
            )
            processed_docs.append((document, chunks))
            logger.info(f"Processed document: {doc['title']} with {len(chunks)} chunks")
            
        return processed_docs
        
    except Exception as e:
        logger.error(f"Failed to set up test documents: {str(e)}")
        raise


def test_basic_retrieval():
    """Test basic document retrieval functionality."""
    try:
        logger.info("Testing basic document retrieval...")
        
        # Test different queries
        test_queries = [
            "How do I reset the XYZ-1000 device?",
            "What should I do if my device overheats?",
            "Who founded the company?",
            "What are the specs of the XYZ-1000?",
            "How do I contact technical support?",
        ]
        
        for query in test_queries:
            logger.info(f"Testing query: {query}")
            
            # Retrieve relevant chunks
            results = retrieve_relevant_chunks(
                query=query,
                limit=3,
                threshold=0.5
            )
            
            logger.info(f"Retrieved {len(results)} chunks for query: {query}")
            
            # Check for some results
            assert len(results) > 0, f"No results found for query: {query}"
            
            # Log the results
            for i, result in enumerate(results):
                similarity = result.get("similarity", 0)
                content_preview = result.get("content", "")[:100] + "..."
                logger.info(f"Result {i+1}: Similarity: {similarity:.4f}, Content: {content_preview}")
                
        logger.info("✅ Basic retrieval test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic retrieval test failed: {str(e)}")
        return False


def test_filtered_retrieval():
    """Test retrieval with metadata filters."""
    try:
        logger.info("Testing filtered retrieval...")
        
        # Test queries with filters
        test_cases = [
            {
                "query": "How to troubleshoot device issues?",
                "filters": {"category": "troubleshooting"},
                "description": "Filter by troubleshooting category"
            },
            {
                "query": "What are the specs of the device?",
                "filters": {"product_id": "XYZ-1000"},
                "description": "Filter by product ID"
            },
            {
                "query": "Tell me about the company",
                "filters": {"category": "company"},
                "description": "Filter by company category"
            }
        ]
        
        for case in test_cases:
            query = case["query"]
            filters = case["filters"]
            description = case["description"]
            
            logger.info(f"Testing: {description} - Query: {query}")
            
            # Retrieve with filters
            results = retrieve_relevant_chunks(
                query=query,
                limit=3,
                threshold=0.5,
                filters=filters
            )
            
            logger.info(f"Retrieved {len(results)} chunks with filters: {filters}")
            
            # Check for some results
            assert len(results) > 0, f"No results found for query with filters: {filters}"
            
            # Verify filters were applied correctly
            for result in results:
                metadata = result.get("metadata", {})
                for key, value in filters.items():
                    assert metadata.get(key) == value, f"Filter not applied correctly: {key}={value}"
                    
        logger.info("✅ Filtered retrieval test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Filtered retrieval test failed: {str(e)}")
        return False


def test_context_creation():
    """Test creating context from retrieval results."""
    try:
        logger.info("Testing context creation...")
        
        # Retrieve results for a query
        query = "How do I troubleshoot the XYZ-1000 device?"
        results = retrieve_relevant_chunks(query, limit=5)
        
        # Format the results
        formatted_results = format_retrieval_results(results)
        
        # Create context with different max lengths
        for max_length in [500, 1000, 2000]:
            context = create_context_from_results(results, max_length=max_length)
            logger.info(f"Created context with max_length={max_length}, actual length={len(context)}")
            
            # Verify context length
            assert len(context) <= max_length, f"Context exceeds max length: {len(context)} > {max_length}"
            
            # Verify context contains some content
            assert len(context) > 0, "Context is empty"
            
            # Verify source markers are included
            assert "[Document" in context, "Source markers not found in context"
            
        logger.info("✅ Context creation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Context creation test failed: {str(e)}")
        return False


def test_search_and_format():
    """Test the complete search and format flow."""
    try:
        logger.info("Testing search and format flow...")
        
        # Test queries
        test_queries = [
            "How do I reset my device?",
            "What are the specs of the XYZ-1000?",
            "Tell me about the company history",
        ]
        
        for query in test_queries:
            logger.info(f"Testing complete flow with query: {query}")
            
            # Run the complete flow
            context = search_and_format_query(
                query=query,
                limit=3,
                threshold=0.5,
                max_context_length=2000
            )
            
            logger.info(f"Generated context (length={len(context)})")
            
            # Log a preview of the context
            preview = context[:200] + ("..." if len(context) > 200 else "")
            logger.info(f"Context preview: {preview}")
            
            # Verify context is not empty
            assert len(context) > 0, f"Empty context generated for query: {query}"
            
        logger.info("✅ Search and format flow test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Search and format flow test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all document retrieval tests."""
    logger.info("Starting document retrieval tests...")
    
    try:
        # First, set up test documents
        setup_test_documents()
        
        # Run the tests
        basic_retrieval_success = test_basic_retrieval()
        filtered_retrieval_success = test_filtered_retrieval()
        context_creation_success = test_context_creation()
        search_format_success = test_search_and_format()
        
        # Summary
        logger.info("\n--- Document Retrieval Test Results ---")
        logger.info(f"Basic Retrieval: {'✅ PASS' if basic_retrieval_success else '❌ FAIL'}")
        logger.info(f"Filtered Retrieval: {'✅ PASS' if filtered_retrieval_success else '❌ FAIL'}")
        logger.info(f"Context Creation: {'✅ PASS' if context_creation_success else '❌ FAIL'}")
        logger.info(f"Search & Format: {'✅ PASS' if search_format_success else '❌ FAIL'}")
        
        success = all([
            basic_retrieval_success,
            filtered_retrieval_success,
            context_creation_success,
            search_format_success
        ])
        
        logger.info(f"\nOverall Test Status: {'✅ PASSED' if success else '❌ FAILED'}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Document retrieval tests failed during setup: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 