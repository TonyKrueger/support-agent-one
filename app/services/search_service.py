"""
Search Service Module

This module provides advanced document search capabilities including:
- Semantic search with relevance ranking
- Context retrieval for surrounding chunks
- Different search strategies for various use cases
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union

from app.services.document_service import DocumentService
from app.services.document_storage import DocumentStorage
from app.utils.embedding_pipeline import process_text
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    def __init__(self):
        """Initialize the search service."""
        self.document_service = DocumentService()
        self.document_storage = DocumentStorage()
        
        # Constants
        self.DEFAULT_LIMIT = 5
        self.DEFAULT_SIMILARITY_THRESHOLD = 0.7
        self.CONTEXT_WINDOW_SIZE = 1  # Number of chunks to include before/after matched chunk
    
    def search(
        self,
        query: str,
        limit: int = None,
        similarity_threshold: float = None,
        include_context: bool = False,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents relevant to a query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold
            include_context: Whether to include surrounding chunks for context
            metadata_filter: Metadata-based filter criteria
            
        Returns:
            List of search results with relevance scores
        """
        try:
            # Use default values if not provided
            limit = limit or self.DEFAULT_LIMIT
            similarity_threshold = similarity_threshold or self.DEFAULT_SIMILARITY_THRESHOLD
            
            # Create embedding for the query
            query_embedding = self.document_service.create_embedding(query)
            
            # Search for matching chunks
            results = self.document_storage.search_documents(
                query_embedding=query_embedding,
                limit=limit * 2 if include_context else limit,  # Request more results if we need context
                similarity_threshold=similarity_threshold
            )
            
            # Apply metadata filtering if specified
            if metadata_filter and results:
                results = self._filter_by_metadata(results, metadata_filter)
            
            # Add context if requested
            if include_context and results:
                results = self._add_context(results, limit)
            else:
                # Respect the original limit
                results = results[:limit]
            
            # Enhance results with document information
            enhanced_results = self._enhance_results(results)
            
            logger.info(f"Found {len(enhanced_results)} search results for query: {query}")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def _filter_by_metadata(
        self,
        results: List[Dict[str, Any]],
        metadata_filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter search results by metadata criteria.
        
        Args:
            results: Original search results
            metadata_filter: Metadata filter criteria
            
        Returns:
            Filtered search results
        """
        filtered_results = []
        
        for result in results:
            metadata = result.get("metadata", {})
            
            # Check if result's metadata matches all filter criteria
            matches = True
            for key, value in metadata_filter.items():
                if key not in metadata or metadata[key] != value:
                    matches = False
                    break
            
            if matches:
                filtered_results.append(result)
        
        return filtered_results
    
    def _add_context(
        self,
        results: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Add surrounding chunks to search results for context.
        
        Args:
            results: Original search results
            limit: Maximum number of final results to return
            
        Returns:
            Enhanced search results with context
        """
        if not results:
            return []
        
        # Group results by document
        results_by_doc = {}
        for result in results:
            doc_id = result.get("document_id")
            chunk_index = result.get("chunk_index")
            
            if not doc_id or chunk_index is None:
                continue
                
            if doc_id not in results_by_doc:
                results_by_doc[doc_id] = {}
                
            results_by_doc[doc_id][chunk_index] = result
        
        # Collect results with context
        context_results = []
        
        for doc_id, chunks in results_by_doc.items():
            # Get all chunks for this document
            doc_chunks = self.document_service.get_document_chunks(doc_id)
            
            # Create a map of chunk index to chunk
            chunk_map = {chunk.get("chunk_index", 0): chunk for chunk in doc_chunks}
            
            # Add context chunks for each result
            for chunk_index, result in chunks.items():
                # Add the original result
                context_results.append(result)
                
                # Add preceding chunks as context
                for i in range(1, self.CONTEXT_WINDOW_SIZE + 1):
                    prev_index = chunk_index - i
                    if prev_index in chunk_map and prev_index not in chunks:
                        prev_chunk = chunk_map[prev_index]
                        prev_chunk["is_context"] = True
                        prev_chunk["context_for"] = chunk_index
                        prev_chunk["context_position"] = "before"
                        context_results.append(prev_chunk)
                
                # Add following chunks as context
                for i in range(1, self.CONTEXT_WINDOW_SIZE + 1):
                    next_index = chunk_index + i
                    if next_index in chunk_map and next_index not in chunks:
                        next_chunk = chunk_map[next_index]
                        next_chunk["is_context"] = True
                        next_chunk["context_for"] = chunk_index
                        next_chunk["context_position"] = "after"
                        context_results.append(next_chunk)
        
        # Sort results by similarity score (highest first)
        context_results.sort(
            key=lambda x: x.get("similarity", 0) if not x.get("is_context", False) else 0,
            reverse=True
        )
        
        # Limit the final number of results
        return context_results[:limit]
    
    def _enhance_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance search results with additional document information.
        
        Args:
            results: Original search results
            
        Returns:
            Enhanced search results
        """
        if not results:
            return []
        
        # Group results by document ID
        doc_ids = set(result.get("document_id") for result in results if "document_id" in result)
        
        # Fetch document information for all IDs
        documents = {}
        for doc_id in doc_ids:
            doc = self.document_service.get_document_by_id(doc_id)
            if doc:
                documents[doc_id] = doc
        
        # Enhance each result with document info
        enhanced_results = []
        for result in results:
            doc_id = result.get("document_id")
            if doc_id in documents:
                # Add document information to result
                result["document_title"] = documents[doc_id].get("title", "")
                result["document_metadata"] = documents[doc_id].get("metadata", {})
            
            enhanced_results.append(result)
        
        return enhanced_results
    
    def search_by_strategy(
        self,
        query: str,
        strategy: str = "semantic",
        limit: int = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using different strategies.
        
        Args:
            query: The search query
            strategy: Search strategy (semantic, hybrid, exact)
            limit: Maximum number of results to return
            metadata_filter: Metadata-based filter criteria
            
        Returns:
            List of search results
        """
        if strategy == "semantic":
            # Default semantic search
            return self.search(
                query=query,
                limit=limit,
                include_context=False,
                metadata_filter=metadata_filter
            )
        elif strategy == "semantic_with_context":
            # Semantic search with surrounding context
            return self.search(
                query=query,
                limit=limit,
                include_context=True,
                metadata_filter=metadata_filter
            )
        elif strategy == "exact":
            # Exact text matching (non-semantic)
            # This is just a placeholder - implement with direct SQL query or similar
            logger.warning("Exact search not fully implemented yet")
            return self.search(
                query=query,
                limit=limit,
                metadata_filter=metadata_filter
            )
        elif strategy == "hybrid":
            # Hybrid approach combining semantic and exact matching
            # This is just a placeholder - implement with custom ranking logic
            logger.warning("Hybrid search not fully implemented yet")
            return self.search(
                query=query,
                limit=limit,
                metadata_filter=metadata_filter
            )
        else:
            logger.warning(f"Unknown search strategy: {strategy}")
            return self.search(
                query=query,
                limit=limit,
                metadata_filter=metadata_filter
            ) 