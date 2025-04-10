"""Tests for the document processor service."""

import os
import tempfile
from pathlib import Path

import pytest
import logfire

# Import test helper first to set environment variables
import tests.helpers

from app.services.document_processor import DocumentProcessor


@pytest.fixture
def document_processor(supabase_client):
    """Create and return a document processor instance."""
    # Create a document processor with a mocked Supabase client
    processor = DocumentProcessor()
    # Replace the created client with our mock
    processor.supabase = supabase_client
    return processor


@pytest.fixture
def sample_text_file():
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp:
        temp.write("This is a sample text file for testing document processing.\n")
        temp.write("It contains multiple lines of text to test chunking.\n")
        temp.write("The document processor should be able to process this file.\n")
        temp_path = temp.name
    
    # Return the path for use in tests
    yield Path(temp_path)
    
    # Clean up after test
    os.unlink(temp_path)


@pytest.mark.asyncio
async def test_document_processor_initialization(document_processor):
    """Test that the document processor initializes correctly."""
    assert document_processor is not None
    assert document_processor.openai_client is not None
    assert document_processor.supabase is not None
    logfire.info("Document processor initialization test successful")


@pytest.mark.asyncio
async def test_text_extraction(document_processor, sample_text_file):
    """Test that text extraction works for a simple text file."""
    text = document_processor._extract_text(sample_text_file)
    
    assert text is not None
    assert len(text) > 0
    assert "sample text file" in text
    
    logfire.info("Text extraction test successful", text_length=len(text))


@pytest.mark.asyncio
async def test_text_chunking(document_processor):
    """Test that text chunking works correctly."""
    # Create a test text with repeating patterns to test chunking
    test_text = "Line " * 500  # Should be long enough to create multiple chunks
    
    chunks = document_processor._split_text(test_text, chunk_size=100, overlap=20)
    
    assert chunks is not None
    assert len(chunks) > 1  # Should have created multiple chunks
    
    # Test that chunks have the expected size (approximately)
    assert len(chunks[0]) <= 100
    
    # Test that the chunks overlap
    if len(chunks) >= 2:
        end_of_first = chunks[0][-20:]
        start_of_second = chunks[1][:20]
        assert end_of_first in chunks[1] or start_of_second in chunks[0]
    
    logfire.info("Text chunking test successful", chunk_count=len(chunks)) 