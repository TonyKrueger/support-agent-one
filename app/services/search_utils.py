"""
Utilities for document search and retrieval based on vector similarity
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union

from dotenv import load_dotenv
import openai
from supabase import create_client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase and OpenAI
try:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    
    logger.info("Initialized Supabase and OpenAI clients")
except Exception as e:
    logger.error(f"Error initializing clients: {e}")
    raise

def get_embedding(text: str) -> List[float]:
    """
    Generate an embedding for a given text using OpenAI's embedding model.
    
    Args:
        text (str): The text to generate an embedding for
        
    Returns:
        List[float]: The embedding vector
    """
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise

def search_documents(query: str, 
                    filters: Optional[Dict[str, Any]] = None, 
                    limit: int = 5, 
                    similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
    """
    Search for documents using vector similarity.
    
    Args:
        query (str): The search query
        filters (dict, optional): Additional filters to apply to the search
        limit (int, optional): Maximum number of documents to return
        similarity_threshold (float, optional): Minimum similarity score to include a result
        
    Returns:
        List[Dict]: A list of documents matching the query
    """
    try:
        # Generate embedding for search query
        query_embedding = get_embedding(query)
        
        # Build the query
        search_query = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": similarity_threshold,
                "match_count": limit
            }
        )
        
        # Apply additional filters if provided
        if filters:
            for key, value in filters.items():
                if value is not None:
                    search_query = search_query.eq(key, value)
        
        # Execute the query
        response = search_query.execute()
        
        if response.data:
            logger.info(f"Found {len(response.data)} relevant documents")
            return response.data
        else:
            logger.info("No relevant documents found")
            return []
            
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return []

def format_search_results(documents: List[Dict[str, Any]], 
                         query: str, 
                         max_tokens: int = 4000) -> str:
    """
    Format search results into a summarized context string.
    
    Args:
        documents (List[Dict]): The search results
        query (str): The original query
        max_tokens (int, optional): Maximum number of tokens to include
        
    Returns:
        str: Formatted context string
    """
    if not documents:
        return "No relevant documentation found."
    
    formatted_context = []
    total_chars = 0
    estimated_token_budget = max_tokens * 4  # Rough approximation of chars per token
    
    # Add each document to the context
    for i, doc in enumerate(documents, 1):
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        
        # Format document metadata
        meta_str = " | ".join([f"{k}: {v}" for k, v in metadata.items() if v])
        
        # Format document with its metadata
        doc_text = f"DOCUMENT {i} [{meta_str}]:\n{content}\n\n"
        
        # Check if we can add more without exceeding the token budget
        if total_chars + len(doc_text) > estimated_token_budget:
            break
            
        formatted_context.append(doc_text)
        total_chars += len(doc_text)
    
    # Join everything together
    return "\n".join(formatted_context)

def search_and_format_query(query: str, 
                           filters: Optional[Dict[str, Any]] = None, 
                           limit: int = 3) -> str:
    """
    End-to-end function to search documents and format results.
    
    Args:
        query (str): The search query
        filters (dict, optional): Additional filters to apply to the search
        limit (int, optional): Maximum number of documents to return
        
    Returns:
        str: Formatted context based on search results
    """
    try:
        # Log the search query and filters
        logger.info(f"Searching for documents with query: '{query}' and filters: {filters}")
        
        # Search for relevant documents
        documents = search_documents(query, filters, limit)
        
        # Format the search results
        formatted_results = format_search_results(documents, query)
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error in search_and_format_query: {e}")
        return f"Error retrieving relevant information: {str(e)}"

def store_document(content: str, 
                 doc_type: str = "conversation",
                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Store a document in the vector database.
    
    Args:
        content (str): The document content
        doc_type (str): The type of document
        metadata (dict, optional): Additional metadata for the document
        
    Returns:
        dict: The stored document information
    """
    try:
        # Generate embedding for the document
        embedding = get_embedding(content)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Store document in database
        response = supabase.table("documents").insert({
            "content": content,
            "embedding": embedding,
            "type": doc_type,
            "metadata": metadata
        }).execute()
        
        logger.info(f"Stored document with ID: {response.data[0]['id']}")
        
        return response.data[0]
    
    except Exception as e:
        logger.error(f"Error storing document: {e}")
        raise 