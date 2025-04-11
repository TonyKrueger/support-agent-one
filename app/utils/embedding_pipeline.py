"""
Embedding Pipeline Utility

This module provides a pipeline for processing documents into chunks and embeddings,
with efficient batching and caching support.
"""

import time
from typing import List, Dict, Any, Optional, Tuple, Union
import hashlib

from app.utils.text_chunker import chunk_text, ChunkingStrategy
from app.services.openai_service import get_embeddings
from app.utils.logger import get_logger
from app.config.ai_settings import ai_settings

logger = get_logger(__name__)

# Simple in-memory cache for embeddings
# In production, consider using Redis or another distributed cache
_embedding_cache = {}
_cache_hits = 0
_cache_misses = 0

# Default batch size for embedding API calls
DEFAULT_BATCH_SIZE = 20


def process_text(
    text: str,
    content_type: str = "text",
    chunk_size: int = None,
    chunk_overlap: int = None,
    chunking_strategy: str = None,
    use_cache: bool = True
) -> Tuple[List[str], List[List[float]]]:
    """
    Process text through the full pipeline: chunking and embedding generation.
    
    Args:
        text: The text to process
        content_type: Type of content (text, markdown, html, etc.)
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Size of overlap between chunks
        chunking_strategy: Strategy to use for chunking
        use_cache: Whether to use embedding cache
        
    Returns:
        Tuple of (list of text chunks, list of embeddings)
    """
    logger.debug(f"Processing text of type {content_type} through embedding pipeline")
    
    # Use default values if not provided
    chunk_size = chunk_size or ai_settings.chunk_size
    chunk_overlap = chunk_overlap or ai_settings.chunk_overlap
    chunking_strategy = chunking_strategy or ChunkingStrategy.SIMPLE
    
    # Step 1: Generate chunks
    chunks = chunk_text(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=chunking_strategy,
        content_type=content_type
    )
    
    if not chunks:
        logger.warning("No chunks were generated from the text")
        return [], []
    
    logger.debug(f"Generated {len(chunks)} chunks from text")
    
    # Step 2: Generate embeddings
    embeddings = generate_embeddings(chunks, use_cache=use_cache)
    
    return chunks, embeddings


def generate_embeddings(
    texts: List[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
    use_cache: bool = True
) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks with batching and caching.
    
    Args:
        texts: List of text chunks to generate embeddings for
        batch_size: Number of texts to process in each batch
        use_cache: Whether to use the embedding cache
        
    Returns:
        List of embedding vectors
    """
    global _cache_hits, _cache_misses
    
    if not texts:
        return []
    
    all_embeddings = []
    uncached_texts = []
    uncached_indices = []
    
    # Check cache first
    if use_cache:
        for i, text in enumerate(texts):
            cache_key = _get_cache_key(text)
            if cache_key in _embedding_cache:
                all_embeddings.append(_embedding_cache[cache_key])
                _cache_hits += 1
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                _cache_misses += 1
    else:
        uncached_texts = texts
        uncached_indices = list(range(len(texts)))
    
    # Process uncached texts in batches
    if uncached_texts:
        embeddings_by_index = {}
        
        for i in range(0, len(uncached_texts), batch_size):
            batch = uncached_texts[i:i+batch_size]
            batch_indices = uncached_indices[i:i+batch_size]
            
            # Generate embeddings for this batch
            batch_embeddings = get_embeddings(batch)
            
            # Store results by original index
            for j, embedding in enumerate(batch_embeddings):
                original_index = batch_indices[j]
                embeddings_by_index[original_index] = embedding
                
                # Update cache
                if use_cache:
                    cache_key = _get_cache_key(uncached_texts[j])
                    _embedding_cache[cache_key] = embedding
            
            # Sleep briefly between large batches to avoid rate limits
            if i + batch_size < len(uncached_texts):
                time.sleep(0.1)
        
        # Prepare full results list
        if use_cache:
            # We need to merge cached and new embeddings
            for i in range(len(texts)):
                if i in embeddings_by_index:
                    all_embeddings.append(embeddings_by_index[i])
        else:
            # Just use the new embeddings in order
            all_embeddings = [embeddings_by_index[i] for i in range(len(texts))]
    
    logger.debug(f"Generated {len(all_embeddings)} embeddings (cache hits: {_cache_hits}, misses: {_cache_misses})")
    return all_embeddings


def process_document(
    document_id: str,
    title: str,
    content: str,
    content_type: str = "text",
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = None,
    chunk_overlap: int = None,
    chunking_strategy: str = None
) -> Tuple[List[str], List[List[float]], List[Dict[str, Any]]]:
    """
    Process a document through chunking and embedding with metadata preparation.
    
    Args:
        document_id: The document ID
        title: Document title
        content: Raw document content
        content_type: Type of content
        metadata: Optional metadata for the document
        chunk_size: Maximum size of each chunk
        chunk_overlap: Size of overlap between chunks
        chunking_strategy: Strategy to use for chunking
        
    Returns:
        Tuple of (list of text chunks, list of embeddings, list of chunk metadata)
    """
    # Process text through chunking and embedding
    chunks, embeddings = process_text(
        text=content,
        content_type=content_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=chunking_strategy
    )
    
    # Prepare chunk metadata
    chunk_metadata = []
    for i in range(len(chunks)):
        chunk_meta = {
            "document_id": document_id,
            "chunk_index": i,
            "title": title
        }
        if metadata:
            # Create a copy to avoid modifying the original
            chunk_meta.update(metadata.copy())
        chunk_metadata.append(chunk_meta)
    
    return chunks, embeddings, chunk_metadata


def _get_cache_key(text: str) -> str:
    """Generate a cache key for a text string."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def clear_embedding_cache():
    """Clear the embedding cache."""
    global _embedding_cache, _cache_hits, _cache_misses
    _embedding_cache = {}
    _cache_hits = 0
    _cache_misses = 0
    logger.debug("Embedding cache cleared")


def get_cache_stats() -> Dict[str, int]:
    """Get statistics about the embedding cache."""
    return {
        "cache_size": len(_embedding_cache),
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses
    } 