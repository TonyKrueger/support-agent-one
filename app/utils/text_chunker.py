"""
Text Chunking Utility

This module provides centralized functions for splitting text into chunks
with different strategies based on content type.
"""

import re
from typing import List, Dict, Any, Optional, Union, Callable

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default parameters
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class ChunkingStrategy:
    """Enum-like class for chunking strategies"""
    SIMPLE = "simple"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    MARKDOWN = "markdown"


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    strategy: str = ChunkingStrategy.SIMPLE,
    content_type: str = "text"
) -> List[str]:
    """
    Split text into overlapping chunks using the specified strategy.
    
    Args:
        text: The text to split into chunks
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks in characters
        strategy: Chunking strategy to use
        content_type: Type of content (text, markdown, html, etc.)
        
    Returns:
        List of text chunks
    """
    logger.debug(f"Chunking text using {strategy} strategy")
    
    if not text:
        return []
    
    # Select chunking strategy based on content type if not explicitly provided
    if strategy == ChunkingStrategy.SIMPLE:
        if content_type == "markdown" or content_type == "md":
            strategy = ChunkingStrategy.MARKDOWN
        elif content_type == "html":
            strategy = ChunkingStrategy.PARAGRAPH
    
    # Apply the appropriate chunking strategy
    if strategy == ChunkingStrategy.SIMPLE:
        return chunk_by_separator(text, chunk_size, chunk_overlap, '\n')
    elif strategy == ChunkingStrategy.SENTENCE:
        return chunk_by_sentence(text, chunk_size, chunk_overlap)
    elif strategy == ChunkingStrategy.PARAGRAPH:
        return chunk_by_separator(text, chunk_size, chunk_overlap, '\n\n')
    elif strategy == ChunkingStrategy.MARKDOWN:
        return chunk_markdown(text, chunk_size, chunk_overlap)
    elif strategy == ChunkingStrategy.SEMANTIC:
        # This is a placeholder - semantic chunking requires additional logic
        return chunk_by_separator(text, chunk_size, chunk_overlap, '\n')
    else:
        logger.warning(f"Unknown chunking strategy: {strategy}, falling back to simple")
        return chunk_by_separator(text, chunk_size, chunk_overlap, '\n')


def chunk_by_separator(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separator: str
) -> List[str]:
    """
    Split text into chunks based on a separator.
    
    Args:
        text: The text to split
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        separator: Separator to use for chunking
        
    Returns:
        List of text chunks
    """
    # Split text by separator
    splits = text.split(separator)
    
    # Handle case where text doesn't contain the separator
    if len(splits) == 1:
        return chunk_by_character(text, chunk_size, chunk_overlap)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for split in splits:
        # Account for the separator in size calculations
        split_size = len(split) + len(separator)
        
        # If adding this split would exceed the chunk size and we already have content,
        # finish the current chunk and start a new one
        if current_size + split_size > chunk_size and current_chunk:
            chunks.append(separator.join(current_chunk))
            
            # Keep overlapping content for the next chunk
            overlap_splits = []
            overlap_size = 0
            
            # Work backwards through current chunk to include content up to chunk_overlap size
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


def chunk_by_character(
    text: str,
    chunk_size: int,
    chunk_overlap: int
) -> List[str]:
    """
    Split text into chunks based on character count.
    
    Args:
        text: The text to split
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
        
    chunks = []
    start = 0
    
    while start < len(text):
        # Take a chunk of maximum size
        end = min(start + chunk_size, len(text))
        
        # If this is not the first chunk and we're not at the end, adjust for overlap
        if start > 0:
            start = max(0, start - chunk_overlap)
            
        # Extract the chunk and add to results
        chunks.append(text[start:end])
        
        # Move to the next chunk starting position
        start = end
        
    return chunks


def chunk_by_sentence(
    text: str,
    chunk_size: int,
    chunk_overlap: int
) -> List[str]:
    """
    Split text into chunks based on sentences.
    
    Args:
        text: The text to split
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Simple sentence splitter - can be improved for better sentence detection
    sentence_endings = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_endings, text)
    
    return chunk_by_items(sentences, chunk_size, chunk_overlap, " ")


def chunk_markdown(
    text: str,
    chunk_size: int,
    chunk_overlap: int
) -> List[str]:
    """
    Split markdown text into chunks, trying to preserve headers and structure.
    
    Args:
        text: The markdown text to split
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Split by headers (##, ###, etc.) but keep the headers with their content
    header_pattern = r'(#{1,6}\s+[^\n]+\n)'
    sections = re.split(header_pattern, text)
    
    # Group headers with their content
    grouped_sections = []
    i = 0
    while i < len(sections):
        if i+1 < len(sections) and re.match(header_pattern, sections[i]):
            grouped_sections.append(sections[i] + sections[i+1])
            i += 2
        else:
            grouped_sections.append(sections[i])
            i += 1
    
    return chunk_by_items(grouped_sections, chunk_size, chunk_overlap, "\n")


def chunk_by_items(
    items: List[str],
    chunk_size: int,
    chunk_overlap: int,
    join_str: str = ""
) -> List[str]:
    """
    Generic function to chunk a list of items with overlap.
    
    Args:
        items: List of text items to chunk
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        join_str: String to use when joining items
        
    Returns:
        List of text chunks
    """
    chunks = []
    current_chunk = []
    current_size = 0
    
    for item in items:
        item_size = len(item) + len(join_str) if current_chunk else len(item)
        
        # If adding this item would exceed the chunk size and we already have content,
        # finish the current chunk and start a new one
        if current_size + item_size > chunk_size and current_chunk:
            chunks.append(join_str.join(current_chunk))
            
            # Calculate how many items to keep for overlap
            overlap_items = []
            overlap_size = 0
            
            for overlap_item in reversed(current_chunk):
                overlap_item_size = len(overlap_item) + len(join_str)
                if overlap_size + overlap_item_size <= chunk_overlap:
                    overlap_items.insert(0, overlap_item)
                    overlap_size += overlap_item_size
                else:
                    break
                    
            current_chunk = overlap_items
            current_size = overlap_size
            
        # Add the current item to the chunk
        current_chunk.append(item)
        current_size += item_size
        
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(join_str.join(current_chunk))
        
    return chunks 