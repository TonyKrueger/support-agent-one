import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from supabase import create_client
from dotenv import load_dotenv
import uuid

# Import our new components
from app.utils.text_chunker import chunk_text, ChunkingStrategy
from app.utils.embedding_pipeline import process_text, process_document as pipeline_process_document
from app.services.document_storage import DocumentStorage
from app.utils.openai_client import get_openai_client

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        """
        Initialize the document service with Supabase and OpenAI clients.
        """
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase environment variables not set")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        self.supabase = create_client(supabase_url, supabase_key)
        self.openai = get_openai_client()
        
        # Initialize our new document storage service
        self.document_storage = DocumentStorage()
        
        # Constants
        self.DOCUMENTS_TABLE = "documents"
        self.DOCUMENT_CHUNKS_TABLE = "document_chunks"
        self.EMBEDDING_MODEL = "text-embedding-3-small"
        self.SIMILARITY_THRESHOLD = 0.7
        self.MAX_RESULTS = 5
        self.DEFAULT_CHUNK_SIZE = 1000
        self.DEFAULT_CHUNK_OVERLAP = 200
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding vector for a text using OpenAI's embedding model.
        
        Args:
            text: The text to create an embedding for
            
        Returns:
            A list of floats representing the embedding vector
        """
        try:
            response = self.openai.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents relevant to a query using vector similarity.
        
        Args:
            query: The search query
            limit: Maximum number of documents to return
            
        Returns:
            A list of document dictionaries
        """
        try:
            # Create embedding for the query
            query_embedding = self.create_embedding(query)
            
            # Perform vector search using our document storage service
            documents = self.document_storage.search_documents(
                query_embedding=query_embedding,
                limit=min(limit, self.MAX_RESULTS),
                similarity_threshold=self.SIMILARITY_THRESHOLD
            )
            
            # Log the number of documents found
            logger.info(f"Found {len(documents)} relevant documents for query: {query}")
            
            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            doc_id: The document ID
            
        Returns:
            The document dictionary or None if not found
        """
        try:
            return self.document_storage.get_document(doc_id)
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None

    def store_document(
        self, 
        title: str, 
        content: str, 
        metadata: Dict[str, Any] = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        chunking_strategy: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Store a document in the database with chunks and embeddings.
        
        Args:
            title: The document title
            content: The document content
            metadata: Additional metadata for the document
            chunk_size: Size of text chunks (defaults to class default)
            chunk_overlap: Overlap between chunks (defaults to class default)
            chunking_strategy: Strategy for chunking text (defaults to simple)
            
        Returns:
            The document object if successful, None otherwise
        """
        try:
            # Set default values if not provided
            chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
            chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP
            content_type = metadata.get("content_type", "text") if metadata else "text"
            
            # Process the document through our pipeline
            chunks, embeddings = process_text(
                text=content,
                content_type=content_type,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunking_strategy=chunking_strategy
            )
            
            # Generate unique ID
            doc_id = str(uuid.uuid4())
            
            # Prepare chunk metadata
            chunk_metadata_list = []
            for i in range(len(chunks)):
                chunk_meta = {
                    "document_id": doc_id,
                    "chunk_index": i,
                    "title": title
                }
                if metadata:
                    # Create a copy to avoid modifying the original
                    chunk_meta.update(metadata.copy())
                chunk_metadata_list.append(chunk_meta)
            
            # Store document and chunks atomically
            document, stored_chunks = self.document_storage.store_document_with_chunks(
                title=title,
                content=content,
                chunks=chunks,
                embeddings=embeddings,
                metadata=metadata or {},
                chunk_metadata_list=chunk_metadata_list,
                doc_id=doc_id
            )
            
            logger.info(f"Document stored successfully with ID: {doc_id} and {len(stored_chunks)} chunks")
            return document
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            return None
    
    def update_document(
        self, 
        doc_id: str, 
        title: str = None, 
        content: str = None, 
        metadata: Dict[str, Any] = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        chunking_strategy: str = None,
        replace_chunks: bool = True
    ) -> bool:
        """
        Update an existing document and its chunks.
        
        Args:
            doc_id: The document ID
            title: The new document title (optional)
            content: The new document content (optional)
            metadata: The new document metadata (optional)
            chunk_size: Size of text chunks (defaults to class default)
            chunk_overlap: Overlap between chunks (defaults to class default)
            chunking_strategy: Strategy for chunking text (defaults to simple)
            replace_chunks: Whether to replace existing chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing document
            existing_doc = self.get_document_by_id(doc_id)
            if not existing_doc:
                logger.error(f"Document with ID {doc_id} not found")
                return False
            
            # Set default values if not provided
            chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
            chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP
            
            # Prepare content type
            if metadata and metadata.get("content_type"):
                content_type = metadata.get("content_type")
            elif existing_doc.get("metadata", {}).get("content_type"):
                content_type = existing_doc["metadata"]["content_type"]
            else:
                content_type = "text"
            
            # Process chunks and embeddings only if content is provided
            chunks = None
            embeddings = None
            chunk_metadata_list = None
            
            if content is not None:
                # Process the document content to generate new chunks and embeddings
                chunks, embeddings = process_text(
                    text=content,
                    content_type=content_type,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunking_strategy=chunking_strategy
                )
                
                # Prepare chunk metadata
                chunk_metadata_list = []
                for i in range(len(chunks)):
                    # Start with existing metadata
                    if existing_doc.get("metadata"):
                        chunk_meta = existing_doc["metadata"].copy()
                    else:
                        chunk_meta = {}
                    
                    # Update with new metadata
                    if metadata:
                        chunk_meta.update(metadata)
                    
                    # Add chunk-specific metadata
                    chunk_meta.update({
                        "document_id": doc_id,
                        "chunk_index": i,
                        "title": title or existing_doc.get("title", "")
                    })
                    
                    chunk_metadata_list.append(chunk_meta)
            
            # Update document and chunks
            updated_doc, updated_chunks = self.document_storage.update_document_with_chunks(
                doc_id=doc_id,
                title=title,
                content=content,
                chunks=chunks,
                embeddings=embeddings,
                metadata=metadata,
                chunk_metadata_list=chunk_metadata_list,
                replace_chunks=replace_chunks
            )
            
            if chunks:
                logger.info(f"Document with ID {doc_id} updated with {len(updated_chunks)} chunks")
            else:
                logger.info(f"Document with ID {doc_id} metadata updated")
                
            return True
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the database and its chunks.
        
        Args:
            doc_id: The document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.document_storage.delete_document(doc_id)
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all documents with pagination.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            A list of document dictionaries
        """
        try:
            response = self.supabase.table(self.DOCUMENTS_TABLE).select("id,title,metadata,created_at").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error getting all documents: {response.error}")
                return []
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting all documents: {str(e)}")
            return []
    
    # New methods for chunk management
    
    def create_document_chunks(
        self, 
        document_id: str, 
        text: str,
        chunk_size: int = None,
        chunk_overlap: int = None,
        chunking_strategy: str = None,
        content_type: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        Create chunks for an existing document.
        
        Args:
            document_id: The document ID
            text: The text to chunk
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            chunking_strategy: Strategy for chunking text
            content_type: Type of content
            
        Returns:
            List of created chunk records
        """
        try:
            # Get existing document
            document = self.get_document_by_id(document_id)
            if not document:
                logger.error(f"Document with ID {document_id} not found")
                return []
            
            # Process text through our pipeline
            chunks, embeddings = process_text(
                text=text,
                content_type=content_type,
                chunk_size=chunk_size or self.DEFAULT_CHUNK_SIZE,
                chunk_overlap=chunk_overlap or self.DEFAULT_CHUNK_OVERLAP,
                chunking_strategy=chunking_strategy
            )
            
            # Prepare chunk metadata
            chunk_metadata_list = []
            for i in range(len(chunks)):
                chunk_meta = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "title": document.get("title", "")
                }
                
                # Include existing document metadata
                if document.get("metadata"):
                    chunk_meta.update(document["metadata"].copy())
                
                chunk_metadata_list.append(chunk_meta)
            
            # Store chunks
            stored_chunks = self.document_storage.store_document_chunks(
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata_list=chunk_metadata_list
            )
            
            logger.info(f"Created {len(stored_chunks)} chunks for document {document_id}")
            return stored_chunks
        except Exception as e:
            logger.error(f"Error creating document chunks: {str(e)}")
            return []
    
    def update_document_chunks(
        self, 
        document_id: str, 
        text: str,
        replace_existing: bool = True,
        chunk_size: int = None,
        chunk_overlap: int = None,
        chunking_strategy: str = None,
        content_type: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        Update chunks for an existing document.
        
        Args:
            document_id: The document ID
            text: The text to chunk
            replace_existing: Whether to replace existing chunks
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            chunking_strategy: Strategy for chunking text
            content_type: Type of content
            
        Returns:
            List of updated chunk records
        """
        try:
            # Delete existing chunks if requested
            if replace_existing:
                self.delete_document_chunks(document_id)
            
            # Create new chunks
            return self.create_document_chunks(
                document_id=document_id,
                text=text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunking_strategy=chunking_strategy,
                content_type=content_type
            )
        except Exception as e:
            logger.error(f"Error updating document chunks: {str(e)}")
            return []
    
    def delete_document_chunks(self, document_id: str) -> bool:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.document_storage.delete_document_chunks(document_id)
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            return False
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            List of chunk records
        """
        try:
            return self.document_storage.get_document_chunks(document_id)
        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}")
            return []
    
    # Bulk operations for multiple documents
    
    def bulk_store_documents(
        self, 
        documents: List[Dict[str, Any]],
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Store multiple documents in batch.
        
        Args:
            documents: List of document dictionaries with title, content, and metadata
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of stored document records
        """
        try:
            stored_documents = []
            
            for doc in documents:
                title = doc.get("title")
                content = doc.get("content")
                metadata = doc.get("metadata", {})
                
                if not title or not content:
                    logger.warning("Skipping document without title or content")
                    continue
                
                # Store document
                document = self.store_document(
                    title=title,
                    content=content,
                    metadata=metadata,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                if document:
                    stored_documents.append(document)
            
            logger.info(f"Stored {len(stored_documents)} documents in bulk")
            return stored_documents
        except Exception as e:
            logger.error(f"Error in bulk document storage: {str(e)}")
            return [] 