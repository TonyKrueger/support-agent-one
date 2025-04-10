import os
import logging
from typing import List, Dict, Any, Optional
import json
from supabase import create_client
from dotenv import load_dotenv
from app.utils.openai_client import get_openai_client
import uuid

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
        
        # Constants
        self.DOCUMENTS_TABLE = "documents"
        self.EMBEDDING_MODEL = "text-embedding-3-small"
        self.SIMILARITY_THRESHOLD = 0.75
        self.MAX_RESULTS = 5
    
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
            
            # Perform vector search using pgvector
            response = self.supabase.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": self.SIMILARITY_THRESHOLD,
                    "match_count": min(limit, self.MAX_RESULTS)
                }
            ).execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error in vector search: {response.error}")
                return []
            
            documents = response.data if response.data else []
            
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
            response = self.supabase.table(self.DOCUMENTS_TABLE).select("*").eq("id", doc_id).execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error getting document: {response.error}")
                return None
            
            documents = response.data
            return documents[0] if documents else None
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None

    def store_document(self, title: str, content: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Store a document in the database with its embedding.
        
        Args:
            title: The document title
            content: The document content
            metadata: Additional metadata for the document
            
        Returns:
            The document ID if successful, None otherwise
        """
        try:
            # Generate embedding for the document content
            embedding = self.create_embedding(content)
            
            # Create document object
            doc_id = str(uuid.uuid4())
            document = {
                "id": doc_id,
                "title": title,
                "content": content,
                "metadata": metadata or {},
                "embedding": embedding
            }
            
            # Insert document into Supabase
            response = self.supabase.table(self.DOCUMENTS_TABLE).insert(document).execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error storing document: {response.error}")
                return None
            
            logger.info(f"Document stored successfully with ID: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            return None
    
    def update_document(self, doc_id: str, title: str = None, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Update an existing document.
        
        Args:
            doc_id: The document ID
            title: The new document title (optional)
            content: The new document content (optional)
            metadata: The new document metadata (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing document
            existing_doc = self.get_document_by_id(doc_id)
            if not existing_doc:
                logger.error(f"Document with ID {doc_id} not found")
                return False
            
            # Prepare update data
            update_data = {}
            
            if title is not None:
                update_data["title"] = title
            
            if content is not None:
                update_data["content"] = content
                # Update embedding if content changes
                update_data["embedding"] = self.create_embedding(content)
            
            if metadata is not None:
                # Merge with existing metadata if available
                if existing_doc.get("metadata"):
                    existing_metadata = existing_doc["metadata"]
                    merged_metadata = {**existing_metadata, **metadata}
                    update_data["metadata"] = merged_metadata
                else:
                    update_data["metadata"] = metadata
            
            # Update document if there are changes
            if update_data:
                response = self.supabase.table(self.DOCUMENTS_TABLE).update(update_data).eq("id", doc_id).execute()
                
                if hasattr(response, "error") and response.error:
                    logger.error(f"Error updating document: {response.error}")
                    return False
                
                logger.info(f"Document with ID {doc_id} updated successfully")
                return True
            
            return True  # No changes to make
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the database.
        
        Args:
            doc_id: The document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.table(self.DOCUMENTS_TABLE).delete().eq("id", doc_id).execute()
            
            if hasattr(response, "error") and response.error:
                logger.error(f"Error deleting document: {response.error}")
                return False
            
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