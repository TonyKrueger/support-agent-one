"""
Document Retrieval Service

This module provides functions for retrieving documents and document chunks
based on semantic similarity using vector search.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from app.services.openai_service import get_embeddings
from app.services.supabase_service import search_similar_chunks
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentRetrievalError(Exception):
    """Custom exception for document retrieval errors."""
    pass


def retrieve_relevant_chunks(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve document chunks relevant to a natural language query.
    
    Args:
        query: Natural language query text
        limit: Maximum number of chunks to retrieve
        threshold: Similarity threshold (0.0 to 1.0)
        filters: Optional metadata filters to apply
        
    Returns:
        List of relevant document chunks with similarity scores
        
    Raises:
        DocumentRetrievalError: If retrieval fails
    """
    try:
        logger.info(f"Retrieving documents for query: {query}")
        
        # Generate embedding for the query
        query_embedding = get_embeddings([query])[0]
        logger.debug("Generated query embedding")
        
        # Search for similar chunks
        results = search_similar_chunks(
            query_embedding=query_embedding,
            limit=limit,
            threshold=threshold
        )
        
        # Apply additional filters if provided
        if filters and results:
            filtered_results = []
            for chunk in results:
                # Check if chunk metadata matches all filters
                if _matches_filters(chunk.get("metadata", {}), filters):
                    filtered_results.append(chunk)
            results = filtered_results
            
        logger.info(f"Retrieved {len(results)} relevant document chunks")
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise DocumentRetrievalError(f"Failed to retrieve documents: {str(e)}")


def _matches_filters(metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    """
    Check if metadata matches the specified filters.
    
    Args:
        metadata: The chunk metadata to check
        filters: The filters to apply
        
    Returns:
        True if metadata matches all filters, False otherwise
    """
    for key, value in filters.items():
        # Handle nested fields with dot notation (e.g. "product.category")
        if "." in key:
            parts = key.split(".")
            current = metadata
            for part in parts[:-1]:
                if part not in current:
                    return False
                current = current[part]
            if parts[-1] not in current or current[parts[-1]] != value:
                return False
        # Handle list membership for array fields
        elif isinstance(metadata.get(key), list):
            if value not in metadata[key]:
                return False
        # Simple equality for other fields
        elif metadata.get(key) != value:
            return False
    
    return True


def retrieve_by_product(
    query: str,
    product_id: str,
    limit: int = 5,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Retrieve document chunks specific to a product.
    
    Args:
        query: Natural language query text
        product_id: Product identifier to filter by
        limit: Maximum number of chunks to retrieve
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        List of relevant document chunks with similarity scores
    """
    filters = {"product_id": product_id}
    return retrieve_relevant_chunks(query, limit, threshold, filters)


def format_retrieval_results(
    results: List[Dict[str, Any]],
    include_metadata: bool = True,
    max_content_length: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Format retrieval results for presentation or further processing.
    
    Args:
        results: Raw retrieval results
        include_metadata: Whether to include metadata in the output
        max_content_length: Maximum length for content (truncated if longer)
        
    Returns:
        Formatted results with selected fields
    """
    formatted_results = []
    
    for result in results:
        # Extract relevant fields
        formatted_result = {
            "content": result["content"],
            "similarity": result["similarity"],
            "document_id": result["document_id"]
        }
        
        # Truncate content if needed
        if max_content_length and len(formatted_result["content"]) > max_content_length:
            formatted_result["content"] = formatted_result["content"][:max_content_length] + "..."
            
        # Include metadata if requested
        if include_metadata and "metadata" in result:
            formatted_result["metadata"] = result["metadata"]
            
        formatted_results.append(formatted_result)
        
    return formatted_results


def create_context_from_results(
    results: List[Dict[str, Any]],
    max_length: int = 4000
) -> str:
    """
    Create a consolidated context string from retrieval results for use in prompts.
    
    Args:
        results: Retrieval results
        max_length: Maximum length for the combined context
        
    Returns:
        Combined context string with source annotations
    """
    context_parts = []
    current_length = 0
    
    for i, result in enumerate(results):
        # Format the content with a source marker
        content = result["content"].strip()
        source_info = f"[Document {i+1}"
        
        # Add metadata information if available
        if "metadata" in result:
            metadata = result["metadata"]
            if "title" in metadata:
                source_info += f": {metadata['title']}"
            if "source" in metadata:
                source_info += f", Source: {metadata['source']}"
                
        source_info += "]"
        
        # Create the context entry with the source info
        context_entry = f"{content}\n{source_info}\n\n"
        
        # Check if adding this entry would exceed the maximum length
        if current_length + len(context_entry) > max_length:
            # If we already have some context, stop adding more
            if context_parts:
                break
            # If this is the first entry and it's too long, truncate it
            else:
                truncate_length = max_length - len(source_info) - 10
                truncated_content = content[:truncate_length] + "..."
                context_entry = f"{truncated_content}\n{source_info}\n\n"
                
        context_parts.append(context_entry)
        current_length += len(context_entry)
        
    return "".join(context_parts)


def search_and_format_query(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
    filters: Optional[Dict[str, Any]] = None,
    max_context_length: int = 4000
) -> str:
    """
    Complete search flow: search for relevant chunks and format them as context.
    
    Args:
        query: Natural language query
        limit: Maximum number of chunks to retrieve
        threshold: Similarity threshold
        filters: Optional metadata filters
        max_context_length: Maximum length for the combined context
        
    Returns:
        Formatted context string for use in prompts
        
    Raises:
        DocumentRetrievalError: If search or formatting fails
    """
    try:
        # Retrieve relevant chunks
        results = retrieve_relevant_chunks(
            query=query,
            limit=limit,
            threshold=threshold,
            filters=filters
        )
        
        # If no results found, return empty context
        if not results:
            logger.warning(f"No relevant documents found for query: {query}")
            return ""
            
        # Create context from results
        context = create_context_from_results(
            results=results,
            max_length=max_context_length
        )
        
        return context
        
    except Exception as e:
        logger.error(f"Error in search and format flow: {str(e)}")
        raise DocumentRetrievalError(f"Search and format failed: {str(e)}") 