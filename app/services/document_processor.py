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

from app.services.openai_service import get_embeddings
from app.services.supabase_service import store_document, store_document_chunks
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


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separator: str = '\n'
) -> List[str]:
    """
    Split text into overlapping chunks of specified size.
    
    Args:
        text: The text to split into chunks
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks in characters
        separator: Preferred separator for chunk boundaries
        
    Returns:
        List of text chunks
    """
    logger.debug(f"Chunking text into chunks of size {chunk_size} with {chunk_overlap} overlap")
    
    if not text:
        return []
        
    # Split text by separator
    splits = text.split(separator)
    
    # Handle case where text doesn't contain the separator
    if len(splits) == 1:
        # Use a simple character-based chunking
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for split in splits:
        split_size = len(split) + len(separator)
        
        # If adding this split would exceed the chunk size and we already have content,
        # finish the current chunk and start a new one
        if current_size + split_size > chunk_size and current_chunk:
            chunks.append(separator.join(current_chunk))
            
            # Keep overlapping content for the next chunk
            overlap_splits = []
            overlap_size = 0
            
            # Work backwards to include content up to chunk_overlap size
            for item in reversed(current_chunk):
                item_size = len(item) + len(separator)
                if overlap_size + item_size <= chunk_overlap:
                    overlap_splits.insert(0, item)
                    overlap_size += item_size
                else:
                    break
                    
            current_chunk = overlap_splits
            current_size = overlap_size
            
        # Add the current split to the chunk
        current_chunk.append(split)
        current_size += split_size
        
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(separator.join(current_chunk))
        
    return chunks


def process_document(
    title: str,
    content: str,
    content_type: str = 'text',
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process a document through the entire pipeline: extract, chunk, embed, and store.
    
    Args:
        title: Document title
        content: Raw document content
        content_type: Type of content ('text', 'html', 'md', etc.)
        metadata: Optional metadata for the document
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks in characters
        
    Returns:
        Tuple of (document record, list of chunk records)
        
    Raises:
        DocumentProcessingError: If any step in the pipeline fails
    """
    try:
        logger.info(f"Processing document: {title}")
        
        # Extract text
        extracted_text = extract_text_from_string(content, content_type)
        
        # Store document
        document = store_document(title, extracted_text, metadata)
        document_id = document["id"]
        logger.debug(f"Stored document with ID: {document_id}")
        
        # Chunk text
        chunks = chunk_text(
            extracted_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        logger.debug(f"Created {len(chunks)} chunks from document")
        
        if not chunks:
            logger.warning(f"No chunks were created from document: {title}")
            return document, []
            
        # Generate embeddings
        embeddings = get_embeddings(chunks)
        logger.debug(f"Generated {len(embeddings)} embeddings")
        
        # Prepare chunk metadata
        chunk_metadata = []
        for i in range(len(chunks)):
            chunk_meta = {"chunk_index": i}
            if metadata:
                chunk_meta.update(metadata)
            chunk_metadata.append(chunk_meta)
            
        # Store chunks with embeddings
        stored_chunks = store_document_chunks(
            document_id,
            chunks,
            embeddings,
            chunk_metadata
        )
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
    chunk_overlap: int = 200
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process a file through the entire pipeline: extract, chunk, embed, and store.
    
    Args:
        file_path: Path to the file
        title: Optional document title (defaults to filename if not provided)
        metadata: Optional metadata for the document
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks in characters
        
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
        }
        
        if metadata:
            file_metadata.update(metadata)
            
        # Store document
        document = store_document(title, extracted_text, file_metadata)
        document_id = document["id"]
        logger.debug(f"Stored document with ID: {document_id}")
        
        # Chunk text
        chunks = chunk_text(
            extracted_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        logger.debug(f"Created {len(chunks)} chunks from file")
        
        if not chunks:
            logger.warning(f"No chunks were created from file: {file_path}")
            return document, []
            
        # Generate embeddings
        embeddings = get_embeddings(chunks)
        logger.debug(f"Generated {len(embeddings)} embeddings")
        
        # Prepare chunk metadata
        chunk_metadata = []
        for i in range(len(chunks)):
            chunk_meta = {"chunk_index": i, **file_metadata}
            chunk_metadata.append(chunk_meta)
            
        # Store chunks with embeddings
        stored_chunks = store_document_chunks(
            document_id,
            chunks,
            embeddings,
            chunk_metadata
        )
        logger.info(f"Stored {len(stored_chunks)} document chunks with embeddings")
        
        return document, stored_chunks
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise DocumentProcessingError(f"Failed to process file: {str(e)}") 