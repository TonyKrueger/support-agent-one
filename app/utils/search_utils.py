import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

import openai
from app.services.client import init_supabase_client
from app.config.settings import settings  # Import settings for consistent API key access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    openai_api_key = settings.OPENAI_API_KEY
except (AttributeError, ImportError):
    openai_api_key = os.environ.get("OPENAI__API_KEY") or os.environ.get("OPENAI_API_KEY")

if not openai_api_key:
    logger.error("OpenAI API key not found in settings or environment variables")
    raise ValueError("OpenAI API key not found. Please set OPENAI__API_KEY in your .env file")

openai_client = openai.OpenAI(api_key=openai_api_key)

# Constants
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
SIMILARITY_THRESHOLD = 0.7
MAX_RESULTS = 5

def get_embedding(text: str) -> List[float]:
    """
    Get an embedding vector for the provided text using OpenAI's embeddings API
    
    Args:
        text: The text to get an embedding for
        
    Returns:
        A list of floats representing the embedding vector
    """
    try:
        # Truncate long text to fit embedding model's context window
        truncated_text = text[:8191]  # text-embedding-3-small has 8K token limit
        
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=truncated_text
        )
        
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        raise

def search_documents(
    query: str, 
    doc_type: Optional[str] = None,
    threshold: float = SIMILARITY_THRESHOLD,
    limit: int = MAX_RESULTS
) -> List[Dict[str, Any]]:
    """
    Search for documents similar to the query using vector similarity
    
    Args:
        query: The search query
        doc_type: Optional filter for document type
        threshold: Minimum similarity threshold (0-1)
        limit: Maximum number of results to return
        
    Returns:
        List of document objects with similarity scores
    """
    try:
        # Get embedding for the query
        query_embedding = get_embedding(query)
        
        # Initialize Supabase client
        supabase = init_supabase_client()
        
        # Prepare RPC call
        rpc_params = {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": limit
        }
        
        # Execute query with or without type filter
        if doc_type:
            results = supabase.rpc(
                "match_documents", 
                rpc_params
            ).eq("type", doc_type).execute()
        else:
            results = supabase.rpc(
                "match_documents", 
                rpc_params
            ).execute()
        
        # Extract and return data
        if results.data:
            return results.data
        return []
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise

def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results into a readable string
    
    Args:
        results: List of search result documents
        
    Returns:
        A formatted string of search results
    """
    if not results:
        return "No relevant documents found."
    
    formatted = "Here are the most relevant documents:\n\n"
    
    for i, doc in enumerate(results):
        formatted += f"[{i+1}] "
        
        # Add title if available in metadata
        if doc.get('metadata') and doc['metadata'].get('title'):
            formatted += f"{doc['metadata']['title']}"
        
        # Add similarity score
        formatted += f" (Relevance: {doc.get('similarity', 0):.2f})\n"
        
        # Add content preview
        content = doc.get('content', '')
        preview = content[:200] + "..." if len(content) > 200 else content
        formatted += f"{preview}\n\n"
    
    return formatted

def search_and_format_query(
    query: str, 
    doc_type: Optional[str] = None,
    threshold: float = SIMILARITY_THRESHOLD,
    limit: int = MAX_RESULTS
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Perform a search and return both formatted results and raw results
    
    Args:
        query: The search query
        doc_type: Optional filter for document type
        threshold: Minimum similarity threshold (0-1)
        limit: Maximum number of results to return
        
    Returns:
        A tuple containing (formatted_results, raw_results)
    """
    try:
        results = search_documents(query, doc_type, threshold, limit)
        formatted_results = format_search_results(results)
        return formatted_results, results
    except Exception as e:
        logger.error(f"Error in search_and_format_query: {str(e)}")
        return f"Error performing search: {str(e)}", []

def store_document(
    content: str,
    doc_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a document in the database with its embedding
    
    Args:
        content: The document content
        doc_type: The document type (e.g., 'faq', 'kb_article', etc.)
        metadata: Optional metadata dictionary
        
    Returns:
        The created document record
    """
    try:
        # Generate embedding for the document
        embedding = get_embedding(content)
        
        # Initialize Supabase client
        supabase = init_supabase_client()
        
        # Create document object
        document = {
            "content": content,
            "embedding": embedding,
            "type": doc_type,
            "metadata": metadata or {}
        }
        
        # Insert document
        result = supabase.table("documents").insert(document).execute()
        
        if result.data:
            logger.info(f"Document stored successfully with ID: {result.data[0]['id']}")
            return result.data[0]
        else:
            logger.error("Failed to store document")
            raise Exception("Failed to store document")
            
    except Exception as e:
        logger.error(f"Error storing document: {str(e)}")
        raise 