"""
Document Storage Service

This module handles the storage of documents and chunks in Supabase,
with transaction support and versioning.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

from app.utils.logger import get_logger
from app.services.supabase_service import get_supabase_client

logger = get_logger(__name__)


class DocumentStorageError(Exception):
    """Custom exception for document storage errors."""
    pass


class DocumentStorage:
    def __init__(self):
        """Initialize the document storage service."""
        self.supabase = get_supabase_client()
        
        # Constants
        self.DOCUMENTS_TABLE = "documents"
        self.DOCUMENT_CHUNKS_TABLE = "document_chunks"
        self.BATCH_SIZE = 100
    
    def store_document(
        self,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store a document in the database.
        
        Args:
            title: Document title
            content: Document content
            metadata: Additional metadata
            doc_id: Optional document ID (generated if not provided)
            
        Returns:
            The stored document record
            
        Raises:
            DocumentStorageError: If storing fails
        """
        try:
            # Generate a unique ID if not provided
            document_id = doc_id or str(uuid.uuid4())
            
            # Create document object
            document = {
                "id": document_id,
                "title": title,
                "content": content,
                "metadata": metadata or {},
                "version": 1  # Initial version
            }
            
            # Insert document into Supabase
            response = self.supabase.table(self.DOCUMENTS_TABLE).insert(document).execute()
            
            if hasattr(response, "error") and response.error:
                raise DocumentStorageError(f"Error storing document: {response.error}")
            
            if not response.data:
                raise DocumentStorageError("No data returned from document insert")
                
            stored_document = response.data[0]
            logger.info(f"Document stored successfully with ID: {document_id}")
            
            return stored_document
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise DocumentStorageError(f"Failed to store document: {str(e)}")
    
    def update_document(
        self,
        doc_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing document.
        
        Args:
            doc_id: Document ID
            title: New title (optional)
            content: New content (optional)
            metadata: New metadata (optional)
            
        Returns:
            The updated document record
            
        Raises:
            DocumentStorageError: If update fails
        """
        try:
            # Get existing document
            existing_doc = self.get_document(doc_id)
            if not existing_doc:
                raise DocumentStorageError(f"Document with ID {doc_id} not found")
            
            # Prepare update data
            update_data = {}
            
            if title is not None:
                update_data["title"] = title
            
            if content is not None:
                update_data["content"] = content
            
            if metadata is not None:
                # Merge with existing metadata if available
                if existing_doc.get("metadata"):
                    existing_metadata = existing_doc["metadata"]
                    merged_metadata = {**existing_metadata, **metadata}
                    update_data["metadata"] = merged_metadata
                else:
                    update_data["metadata"] = metadata
            
            # Increment version
            update_data["version"] = (existing_doc.get("version") or 0) + 1
            
            # Update document if there are changes
            if update_data:
                response = self.supabase.table(self.DOCUMENTS_TABLE).update(update_data).eq("id", doc_id).execute()
                
                if hasattr(response, "error") and response.error:
                    raise DocumentStorageError(f"Error updating document: {response.error}")
                
                if not response.data:
                    raise DocumentStorageError("No data returned from document update")
                    
                updated_document = response.data[0]
                logger.info(f"Document with ID {doc_id} updated successfully")
                
                return updated_document
            
            return existing_doc  # No changes to make
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise DocumentStorageError(f"Failed to update document: {str(e)}")
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            The document record or None if not found
        """
        try:
            response = self.supabase.table(self.DOCUMENTS_TABLE).select("*").eq("id", doc_id).execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error getting document: {response.error}")
                return None
            
            documents = response.data
            return documents[0] if documents else None
            
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None
    
    def delete_document(self, doc_id: str, delete_chunks: bool = True) -> bool:
        """
        Delete a document and optionally its chunks.
        
        Args:
            doc_id: Document ID
            delete_chunks: Whether to delete associated chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete associated chunks if requested
            if delete_chunks:
                self.delete_document_chunks(doc_id)
            
            # Delete the document
            response = self.supabase.table(self.DOCUMENTS_TABLE).delete().eq("id", doc_id).execute()
            
            if hasattr(response, "error") and response.error:
                raise DocumentStorageError(f"Error deleting document: {response.error}")
            
            deleted_count = len(response.data)
            if deleted_count > 0:
                logger.info(f"Document with ID {doc_id} deleted successfully")
                return True
            else:
                logger.warning(f"No document found with ID {doc_id} to delete")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    def store_document_chunks(
        self,
        document_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Store document chunks with their embeddings.
        
        Args:
            document_id: ID of the parent document
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata_list: List of metadata for each chunk
            
        Returns:
            List of stored chunk records
            
        Raises:
            DocumentStorageError: If storing fails
        """
        try:
            if len(chunks) != len(embeddings):
                raise DocumentStorageError(
                    f"Number of chunks ({len(chunks)}) doesn't match number of embeddings ({len(embeddings)})"
                )
            
            if metadata_list and len(chunks) != len(metadata_list):
                raise DocumentStorageError(
                    f"Number of chunks ({len(chunks)}) doesn't match number of metadata items ({len(metadata_list)})"
                )
            
            # Prepare chunk records
            chunk_records = []
            for i in range(len(chunks)):
                chunk_id = str(uuid.uuid4())
                chunk_record = {
                    "id": chunk_id,
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunks[i],
                    "embedding": embeddings[i],
                    "metadata": (metadata_list[i] if metadata_list else {}) or {}
                }
                chunk_records.append(chunk_record)
            
            # Store chunks in batches
            stored_chunks = []
            for i in range(0, len(chunk_records), self.BATCH_SIZE):
                batch = chunk_records[i:i+self.BATCH_SIZE]
                
                response = self.supabase.table(self.DOCUMENT_CHUNKS_TABLE).insert(batch).execute()
                
                if hasattr(response, "error") and response.error:
                    raise DocumentStorageError(f"Error storing document chunks: {response.error}")
                
                stored_chunks.extend(response.data)
            
            logger.info(f"Stored {len(stored_chunks)} chunks for document {document_id}")
            return stored_chunks
            
        except Exception as e:
            logger.error(f"Error storing document chunks: {str(e)}")
            raise DocumentStorageError(f"Failed to store document chunks: {str(e)}")
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of chunk records
        """
        try:
            response = self.supabase.table(self.DOCUMENT_CHUNKS_TABLE) \
                .select("id, document_id, chunk_index, content, metadata") \
                .eq("document_id", document_id) \
                .order("chunk_index") \
                .execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error getting document chunks: {response.error}")
                return []
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}")
            return []
    
    def delete_document_chunks(self, document_id: str) -> bool:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.table(self.DOCUMENT_CHUNKS_TABLE) \
                .delete() \
                .eq("document_id", document_id) \
                .execute()
            
            if hasattr(response, "error") and response.error:
                raise DocumentStorageError(f"Error deleting document chunks: {response.error}")
            
            deleted_count = len(response.data)
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            return False
    
    def store_document_with_chunks(
        self,
        title: str,
        content: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None,
        chunk_metadata_list: Optional[List[Dict[str, Any]]] = None,
        doc_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Store a document and its chunks atomically.
        
        Args:
            title: Document title
            content: Document content
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: Document metadata
            chunk_metadata_list: List of metadata for each chunk
            doc_id: Optional document ID
            
        Returns:
            Tuple of (document record, list of chunk records)
            
        Raises:
            DocumentStorageError: If storing fails
        """
        try:
            # Begin a pseudo-transaction
            # Note: For true transactions, consider using PostgreSQL functions via RPC
            
            # Store document first
            document = self.store_document(title, content, metadata, doc_id)
            document_id = document["id"]
            
            try:
                # Then store chunks
                chunks = self.store_document_chunks(
                    document_id,
                    chunks,
                    embeddings,
                    chunk_metadata_list
                )
                
                return document, chunks
                
            except Exception as chunk_error:
                # If storing chunks fails, try to delete the document
                logger.error(f"Error storing chunks, rolling back document: {str(chunk_error)}")
                self.delete_document(document_id, delete_chunks=False)
                raise
                
        except Exception as e:
            logger.error(f"Error in document with chunks transaction: {str(e)}")
            raise DocumentStorageError(f"Failed to store document with chunks: {str(e)}")
    
    def update_document_with_chunks(
        self,
        doc_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        chunks: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_metadata_list: Optional[List[Dict[str, Any]]] = None,
        replace_chunks: bool = True
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Update a document and its chunks.
        
        Args:
            doc_id: Document ID
            title: New title (optional)
            content: New content (optional)
            chunks: New text chunks (optional)
            embeddings: New embedding vectors (optional)
            metadata: New document metadata (optional)
            chunk_metadata_list: New chunk metadata list (optional)
            replace_chunks: Whether to replace existing chunks
            
        Returns:
            Tuple of (updated document record, list of chunk records)
            
        Raises:
            DocumentStorageError: If update fails
        """
        try:
            # Update document
            document = self.update_document(doc_id, title, content, metadata)
            
            # Update chunks if provided
            stored_chunks = []
            if chunks and embeddings:
                if replace_chunks:
                    # Delete existing chunks
                    self.delete_document_chunks(doc_id)
                
                # Store new chunks
                stored_chunks = self.store_document_chunks(
                    doc_id,
                    chunks,
                    embeddings,
                    chunk_metadata_list
                )
            else:
                # Get existing chunks
                stored_chunks = self.get_document_chunks(doc_id)
            
            return document, stored_chunks
            
        except Exception as e:
            logger.error(f"Error updating document with chunks: {str(e)}")
            raise DocumentStorageError(f"Failed to update document with chunks: {str(e)}")
    
    def search_documents(
        self,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using vector similarity.
        
        Args:
            query_embedding: The query embedding vector
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of matching document chunks with similarity scores
        """
        try:
            # Perform vector search using pgvector's cosine similarity
            response = self.supabase.rpc(
                "match_document_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": similarity_threshold,
                    "match_count": limit
                }
            ).execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error in vector search: {response.error}")
                return []
            
            results = response.data if response.data else []
            
            # Log the number of documents found
            logger.info(f"Found {len(results)} relevant document chunks")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return [] 