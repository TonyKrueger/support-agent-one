"""
Supabase Service Module

This module provides wrapper functions for the Supabase client,
handling connections, data access, and vector operations.
"""

import os
from typing import List, Dict, Any, Optional, Union
import numpy as np

from supabase import create_client, Client
from postgrest.exceptions import APIError

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize the Supabase client
_supabase_client = None


def get_supabase_client() -> Client:
    """
    Get a configured Supabase client instance.
    
    Returns:
        Initialized Supabase client
    """
    global _supabase_client
    
    if _supabase_client is None:
        logger.debug("Initializing Supabase client")
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    
    return _supabase_client


class SupabaseServiceError(Exception):
    """Custom exception for Supabase service errors."""
    pass


def store_document(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a document in the documents table.
    
    Args:
        title: Document title
        content: Document content
        metadata: Optional metadata for the document
        
    Returns:
        The created document record
        
    Raises:
        SupabaseServiceError: If an error occurs during the operation
    """
    supabase = get_supabase_client()
    
    try:
        logger.debug(f"Storing document: {title}")
        
        data = {
            "title": title,
            "content": content,
            "metadata": metadata or {}
        }
        
        response = supabase.table("documents").insert(data).execute()
        
        if len(response.data) == 0:
            raise SupabaseServiceError("Failed to store document, no data returned")
        
        return response.data[0]
        
    except APIError as e:
        logger.error(f"Supabase error storing document: {str(e)}")
        raise SupabaseServiceError(f"Failed to store document: {str(e)}")


def store_document_chunks(
    document_id: str,
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Store document chunks with embeddings.
    
    Args:
        document_id: ID of the parent document
        chunks: List of text chunks
        embeddings: List of embedding vectors
        metadata: Optional list of metadata for each chunk
        
    Returns:
        List of created chunk records
        
    Raises:
        SupabaseServiceError: If an error occurs during the operation
    """
    supabase = get_supabase_client()
    
    if metadata is None:
        metadata = [{} for _ in chunks]
    
    if len(chunks) != len(embeddings) or len(chunks) != len(metadata):
        raise ValueError("Chunks, embeddings, and metadata must have the same length")
    
    try:
        logger.debug(f"Storing {len(chunks)} document chunks for document {document_id}")
        
        # Prepare data for insertion
        data = [
            {
                "document_id": document_id,
                "content": chunk,
                "embedding": embedding,
                "metadata": meta
            }
            for chunk, embedding, meta in zip(chunks, embeddings, metadata)
        ]
        
        # Insert chunks in batches to avoid request size limits
        batch_size = 50
        all_results = []
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            response = supabase.table("document_chunks").insert(batch).execute()
            all_results.extend(response.data)
        
        return all_results
        
    except APIError as e:
        logger.error(f"Supabase error storing document chunks: {str(e)}")
        raise SupabaseServiceError(f"Failed to store document chunks: {str(e)}")


def search_similar_chunks(
    query_embedding: List[float],
    limit: int = 5,
    threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """
    Search for document chunks similar to the query embedding.
    
    Args:
        query_embedding: The embedding vector to search for
        limit: Maximum number of results to return
        threshold: Similarity threshold (lower value = more results)
        
    Returns:
        List of document chunks with similarity scores
        
    Raises:
        SupabaseServiceError: If an error occurs during the operation
    """
    supabase = get_supabase_client()
    
    try:
        logger.debug(f"Searching for similar chunks with threshold {threshold}")
        
        # Using the <=> operator for cosine distance
        response = supabase.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": limit
            }
        ).execute()
        
        return response.data
        
    except APIError as e:
        logger.error(f"Supabase error searching similar chunks: {str(e)}")
        raise SupabaseServiceError(f"Failed to search similar chunks: {str(e)}")


def test_connection() -> bool:
    """
    Test the connection to Supabase.
    
    Returns:
        True if connection is successful
    
    Raises:
        SupabaseServiceError: If the connection test fails
    """
    supabase = get_supabase_client()
    
    try:
        logger.debug("Testing Supabase connection")
        
        # Simple query to test connection
        response = supabase.from_("documents").select("count", count="exact").limit(1).execute()
        
        logger.info(f"Supabase connection successful, documents count: {response.count}")
        return True
        
    except Exception as e:
        logger.error(f"Supabase connection test failed: {str(e)}")
        raise SupabaseServiceError(f"Failed to connect to Supabase: {str(e)}") 