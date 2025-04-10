"""
Document Processor Tests

This script tests the document processing pipeline.
"""

import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Load environment variables from .env file
load_dotenv()

from app.services.document_processor import (
    extract_text_from_file,
    extract_text_from_string,
    chunk_text,
    process_document,
    process_file
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def test_text_extraction():
    """Test text extraction from different sources."""
    try:
        logger.info("Testing text extraction...")
        
        # Test string extraction
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Hello World</h1>
                <p>This is a <b>test</b> document.</p>
                <script>console.log("This should be removed");</script>
            </body>
        </html>
        """
        
        extracted_text = extract_text_from_string(html_content, 'html')
        logger.info(f"Extracted from HTML string: {extracted_text}")
        assert "Hello World" in extracted_text
        assert "This is a test document." in extracted_text
        assert "console.log" not in extracted_text
        
        # Create a test text file
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w+', delete=False) as f:
            f.write("This is a test text file.\nIt has multiple lines.\nAnd should be extracted correctly.")
            test_file = f.name
            
        try:
            extracted_text = extract_text_from_file(test_file)
            logger.info(f"Extracted from text file: {extracted_text}")
            assert "This is a test text file." in extracted_text
            assert "It has multiple lines." in extracted_text
            assert "And should be extracted correctly." in extracted_text
            
            logger.info("✅ Text extraction test passed")
            return True
        finally:
            # Clean up the test file
            os.unlink(test_file)
            
    except Exception as e:
        logger.error(f"❌ Text extraction test failed: {str(e)}")
        return False


def test_text_chunking():
    """Test text chunking functionality."""
    try:
        logger.info("Testing text chunking...")
        
        # Create a test text with multiple paragraphs
        text = "\n".join([f"This is paragraph {i} with some text content." for i in range(1, 21)])
        
        # Test with different chunk sizes and overlaps
        chunk_configs = [
            (100, 20),  # Small chunks, small overlap
            (500, 100),  # Medium chunks, medium overlap
            (1000, 200)  # Large chunks, large overlap
        ]
        
        for chunk_size, chunk_overlap in chunk_configs:
            chunks = chunk_text(text, chunk_size, chunk_overlap)
            logger.info(f"Created {len(chunks)} chunks with size={chunk_size}, overlap={chunk_overlap}")
            
            # Verify that chunks cover the entire text
            if len(chunks) > 1:
                # Check for overlap between consecutive chunks
                for i in range(len(chunks) - 1):
                    current_chunk_end = chunks[i][-50:]  # Last 50 chars of current chunk
                    next_chunk_start = chunks[i + 1][:50]  # First 50 chars of next chunk
                    
                    # Find some common text in the overlap region
                    common_text = False
                    for word in current_chunk_end.split():
                        if len(word) > 3 and word in next_chunk_start:
                            common_text = True
                            break
                            
                    assert common_text, f"No overlap found between chunks {i} and {i+1}"
            
        logger.info("✅ Text chunking test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Text chunking test failed: {str(e)}")
        return False


def test_document_processing():
    """Test full document processing pipeline."""
    try:
        logger.info("Testing document processing pipeline...")
        
        # Process a simple text document
        title = "Test Document"
        content = "This is a test document.\n\n" + "\n".join([f"Paragraph {i} with test content." for i in range(1, 10)])
        metadata = {"category": "test", "tags": ["test", "example"]}
        
        document, chunks = process_document(
            title=title,
            content=content,
            content_type='text',
            metadata=metadata,
            chunk_size=200,
            chunk_overlap=50
        )
        
        logger.info(f"Processed document with ID: {document['id']}")
        logger.info(f"Created {len(chunks)} chunks with embeddings")
        
        assert document["title"] == title
        assert len(chunks) > 0
        
        # Verify chunk metadata
        for chunk in chunks:
            assert "chunk_index" in chunk["metadata"]
            assert chunk["metadata"]["category"] == "test"
            assert "tags" in chunk["metadata"]
            
        logger.info("✅ Document processing test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Document processing test failed: {str(e)}")
        return False


def test_file_processing():
    """Test file processing pipeline."""
    try:
        logger.info("Testing file processing pipeline...")
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w+', delete=False) as f:
            f.write("This is a test file for processing.\n\n")
            for i in range(1, 10):
                f.write(f"Paragraph {i} with some example content for testing vector embeddings.\n\n")
            test_file = f.name
            
        try:
            # Process the file
            document, chunks = process_file(
                file_path=test_file,
                title="Test File",
                metadata={"category": "test_files"},
                chunk_size=200,
                chunk_overlap=50
            )
            
            logger.info(f"Processed file with document ID: {document['id']}")
            logger.info(f"Created {len(chunks)} chunks with embeddings")
            
            assert document["title"] == "Test File"
            assert len(chunks) > 0
            
            # Verify chunk metadata
            for chunk in chunks:
                assert "chunk_index" in chunk["metadata"]
                assert "filename" in chunk["metadata"]
                assert chunk["metadata"]["source"] == "file"
                assert chunk["metadata"]["extension"] == ".txt"
                assert chunk["metadata"]["category"] == "test_files"
                
            logger.info("✅ File processing test passed")
            return True
            
        finally:
            # Clean up the test file
            os.unlink(test_file)
            
    except Exception as e:
        logger.error(f"❌ File processing test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all document processor tests."""
    logger.info("Starting document processor tests...")
    
    extraction_success = test_text_extraction()
    chunking_success = test_text_chunking()
    doc_process_success = test_document_processing()
    file_process_success = test_file_processing()
    
    # Summary
    logger.info("\n--- Document Processor Test Results ---")
    logger.info(f"Text Extraction: {'✅ PASS' if extraction_success else '❌ FAIL'}")
    logger.info(f"Text Chunking: {'✅ PASS' if chunking_success else '❌ FAIL'}")
    logger.info(f"Document Processing: {'✅ PASS' if doc_process_success else '❌ FAIL'}")
    logger.info(f"File Processing: {'✅ PASS' if file_process_success else '❌ FAIL'}")
    
    success = all([extraction_success, chunking_success, doc_process_success, file_process_success])
    logger.info(f"\nOverall Test Status: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 