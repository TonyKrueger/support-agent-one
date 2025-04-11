"""
Document Processor Module

This module handles document processing, including text extraction,
chunking, embedding generation, and storage in the vector database.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator, Union
from pathlib import Path

# Import our new components
from app.utils.text_chunker import chunk_text, ChunkingStrategy
from app.utils.embedding_pipeline import process_text, process_document as pipeline_process_document
from app.services.document_storage import DocumentStorage, DocumentStorageError
from app.services.document_service import DocumentService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessingError(Exception):
    """Custom exception for document processing errors."""
    pass


def extract_text_from_file(file_path: Union[str, Path]) -> str:
    """
    Extract text content from a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content
        
    Raises:
        DocumentProcessingError: If file type is unsupported or extraction fails
    """
    file_path = Path(file_path)
    
    try:
        logger.debug(f"Extracting text from {file_path}")
        
        if not file_path.exists():
            raise DocumentProcessingError(f"File does not exist: {file_path}")
        
        extension = file_path.suffix.lower()
        
        # Handle different file types
        if extension == '.txt':
            return _extract_from_text_file(file_path)
        elif extension == '.md':
            return _extract_from_text_file(file_path)
        elif extension in ['.pdf']:
            return _extract_from_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return _extract_from_docx(file_path)
        elif extension in ['.html', '.htm']:
            return _extract_from_html(file_path)
        else:
            raise DocumentProcessingError(f"Unsupported file type: {extension}")
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        raise DocumentProcessingError(f"Failed to extract text: {str(e)}")


def _extract_from_text_file(file_path: Path) -> str:
    """Extract text from plain text files (txt, md)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def _extract_from_pdf(file_path: Path) -> str:
    """Extract text from PDF files."""
    try:
        import PyPDF2
        
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text.append(page.extract_text())
                
        return "\n\n".join(text)
    except ImportError:
        raise DocumentProcessingError("PyPDF2 library is required for PDF processing")


def _extract_from_docx(file_path: Path) -> str:
    """Extract text from Word documents."""
    try:
        import docx
        
        doc = docx.Document(file_path)
        return "\n\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)
    except ImportError:
        raise DocumentProcessingError("python-docx library is required for DOCX processing")


def _extract_from_html(file_path: Path) -> str:
    """Extract text from HTML files."""
    try:
        from bs4 import BeautifulSoup
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()
                
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing whitespace
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Remove blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
    except ImportError:
        raise DocumentProcessingError("BeautifulSoup4 library is required for HTML processing")


def extract_text_from_string(content: str, content_type: str = 'text') -> str:
    """
    Extract text from a string based on content type.
    
    Args:
        content: Raw content string
        content_type: Type of content ('text', 'html', etc.)
        
    Returns:
        Extracted text content
        
    Raises:
        DocumentProcessingError: If content type is unsupported or extraction fails
    """
    try:
        logger.debug(f"Extracting text from string content of type {content_type}")
        
        if content_type == 'text':
            return content
        elif content_type == 'html':
            try:
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script_or_style in soup(["script", "style"]):
                    script_or_style.extract()
                    
                text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text
            except ImportError:
                raise DocumentProcessingError("BeautifulSoup4 library is required for HTML processing")
        elif content_type == 'md' or content_type == 'markdown':
            # For markdown, we can use the text directly or optionally convert to plain text
            return content
        else:
            raise DocumentProcessingError(f"Unsupported content type: {content_type}")
            
    except Exception as e:
        logger.error(f"Error extracting text from string content: {str(e)}")
        raise DocumentProcessingError(f"Failed to extract text from string: {str(e)}")


# Legacy chunking function - replaced with text_chunker.py utility
# Kept for backward compatibility
def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separator: str = '\n'
) -> List[str]:
    """
    Legacy function that now uses the centralized text chunker utility.
    
    Args:
        text: The text to split into chunks
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks
        separator: Preferred separator for chunk boundaries
        
    Returns:
        List of text chunks
    """
    logger.debug("Using legacy chunk_text function (redirecting to new utility)")
    
    # Map separator to appropriate chunking strategy
    if separator == '\n':
        strategy = ChunkingStrategy.SIMPLE
    elif separator == '\n\n':
        strategy = ChunkingStrategy.PARAGRAPH
    else:
        strategy = ChunkingStrategy.SIMPLE
    
    # Use the new centralized text chunker
    return chunk_text(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy
    )


def process_document(
    title: str,
    content: str,
    content_type: str = 'text',
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    chunking_strategy: str = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process a document through the entire pipeline: extract, chunk, embed, and store.
    
    Args:
        title: Document title
        content: Raw document content
        content_type: Type of content ('text', 'html', 'md', etc.)
        metadata: Optional metadata for the document
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks
        chunking_strategy: Strategy to use for chunking text
        
    Returns:
        Tuple of (document record, list of chunk records)
        
    Raises:
        DocumentProcessingError: If any step in the pipeline fails
    """
    try:
        logger.info(f"Processing document: {title}")
        
        # Initialize our document service
        document_service = DocumentService()
        
        # Extract text
        extracted_text = extract_text_from_string(content, content_type)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add content type to metadata
        if "content_type" not in metadata:
            metadata["content_type"] = content_type
        
        # Store document with chunks
        document = document_service.store_document(
            title=title,
            content=extracted_text,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy
        )
        
        if not document:
            raise DocumentProcessingError("Failed to store document")
        
        # Get document chunks
        stored_chunks = document_service.get_document_chunks(document["id"])
        logger.info(f"Stored {len(stored_chunks)} document chunks with embeddings")
        
        return document, stored_chunks
        
    except Exception as e:
        logger.error(f"Error processing document {title}: {str(e)}")
        raise DocumentProcessingError(f"Failed to process document: {str(e)}")


def process_file(
    file_path: Union[str, Path],
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    chunking_strategy: str = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process a file through the entire pipeline: extract, chunk, embed, and store.
    
    Args:
        file_path: Path to the file
        title: Optional document title (defaults to filename if not provided)
        metadata: Optional metadata for the document
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks
        chunking_strategy: Strategy to use for chunking text
        
    Returns:
        Tuple of (document record, list of chunk records)
        
    Raises:
        DocumentProcessingError: If any step in the pipeline fails
    """
    try:
        file_path = Path(file_path)
        
        # Use filename as title if not provided
        if title is None:
            title = file_path.stem
            
        logger.info(f"Processing file: {file_path}")
        
        # Extract text
        extracted_text = extract_text_from_file(file_path)
        
        # Add file metadata
        file_metadata = {
            "source": "file",
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "content_type": file_path.suffix.lower().lstrip('.')
        }
        
        if metadata:
            file_metadata.update(metadata)
        
        # Use the process_document function for the rest of the pipeline
        return process_document(
            title=title,
            content=extracted_text,
            content_type=file_metadata["content_type"],
            metadata=file_metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy
        )
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise DocumentProcessingError(f"Failed to process file: {str(e)}")


def process_existing_documents(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    limit: int = 100
) -> Tuple[int, int]:
    """
    Process existing documents to create chunks for documents without chunks.
    
    Args:
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks
        limit: Maximum number of documents to process
        
    Returns:
        Tuple of (number of documents processed, number of chunks created)
    """
    try:
        logger.info(f"Processing existing documents (up to {limit})")
        
        # Initialize services
        document_service = DocumentService()
        document_storage = DocumentStorage()
        
        # Get all documents
        documents = document_service.get_all_documents(limit=limit)
        
        if not documents:
            logger.info("No documents found to process")
            return 0, 0
        
        processed_count = 0
        total_chunks = 0
        
        for doc in documents:
            doc_id = doc["id"]
            
            # Check if document already has chunks
            existing_chunks = document_storage.get_document_chunks(doc_id)
            
            if existing_chunks:
                logger.debug(f"Document {doc_id} already has {len(existing_chunks)} chunks")
                continue
            
            # Get full document with content
            full_doc = document_service.get_document_by_id(doc_id)
            
            if not full_doc or "content" not in full_doc:
                logger.warning(f"Document {doc_id} has no content, skipping")
                continue
            
            # Process content type
            content_type = "text"
            if full_doc.get("metadata", {}).get("content_type"):
                content_type = full_doc["metadata"]["content_type"]
                
            # Create chunks for this document
            try:
                chunks = document_service.create_document_chunks(
                    document_id=doc_id,
                    text=full_doc["content"],
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    content_type=content_type
                )
                
                if chunks:
                    processed_count += 1
                    total_chunks += len(chunks)
                    logger.info(f"Created {len(chunks)} chunks for document {doc_id}")
                    
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {str(e)}")
                continue
        
        logger.info(f"Processed {processed_count} documents, created {total_chunks} chunks")
        return processed_count, total_chunks
        
    except Exception as e:
        logger.error(f"Error in process_existing_documents: {str(e)}")
        return 0, 0 