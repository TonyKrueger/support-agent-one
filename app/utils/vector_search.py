import logging
from typing import List, Dict, Any, Optional, Union
import os

import openai
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=openai_api_key)
embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for the given text using OpenAI's embeddings API.
    
    Args:
        text (str): The text to generate embedding for
        
    Returns:
        List[float]: The embedding vector
    """
    try:
        response = openai_client.embeddings.create(
            model=embedding_model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise


def search_documents(
    query: str,
    doc_type: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict[Any, Any]]:
    """Search for documents that match the query using vector similarity search.
    
    Args:
        query (str): The search query
        doc_type (Optional[str]): Filter by document type
        limit (int): Maximum number of results to return
        similarity_threshold (float): Minimum similarity score (0-1)
        
    Returns:
        List[Dict[Any, Any]]: List of matching documents with metadata
    """
    try:
        # Generate embedding for the query
        embedding = generate_embedding(query)
        
        # Build the query
        documents_query = supabase.table("documents")
        
        # Add document type filter if specified
        if doc_type:
            documents_query = documents_query.eq("doc_type", doc_type)
        
        # Execute the query with vector search
        result = documents_query.select(
            "id, title, content, metadata, doc_type, created_at, embedding_similarity"
        ).order(
            "embedding <-> '.embedding'::text::vector",
            desc=False  # Lower distance means higher similarity
        ).limit(limit).execute()
        
        # Filter by similarity threshold and post-process results
        documents = []
        for doc in result.data:
            # Calculate similarity score (invert distance to get similarity)
            # Note: This assumes that embedding_similarity is exposed correctly
            similarity = 1 - doc.get("embedding_similarity", 0)
            
            # Skip if below threshold
            if similarity < similarity_threshold:
                continue
            
            # Add similarity score to document
            doc["similarity"] = similarity
            
            # Remove embedding from result to reduce payload size
            if "embedding" in doc:
                del doc["embedding"]
            
            documents.append(doc)
        
        return documents
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise


def retrieve_document_by_id(document_id: str) -> Dict[Any, Any]:
    """Retrieve a document by its ID.
    
    Args:
        document_id (str): The document ID
        
    Returns:
        Dict[Any, Any]: The document with metadata
    """
    try:
        result = supabase.table("documents").select(
            "id, title, content, metadata, doc_type, created_at"
        ).eq("id", document_id).execute()
        
        if not result.data:
            raise ValueError(f"Document with ID {document_id} not found")
        
        return result.data[0]
    
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise


def hybrid_search(
    query: str,
    doc_type: Optional[str] = None,
    limit: int = 5,
    full_text_weight: float = 0.3,
    vector_weight: float = 0.7
) -> List[Dict[Any, Any]]:
    """Perform hybrid search combining vector similarity and full-text search.
    
    Args:
        query (str): The search query
        doc_type (Optional[str]): Filter by document type
        limit (int): Maximum number of results to return
        full_text_weight (float): Weight for full-text search results (0-1)
        vector_weight (float): Weight for vector similarity results (0-1)
        
    Returns:
        List[Dict[Any, Any]]: List of matching documents with metadata
    """
    try:
        # Generate embedding for the query
        embedding = generate_embedding(query)
        
        # Execute hybrid search query
        sql = f"""
        WITH vector_search AS (
            SELECT 
                id, 
                1 - (embedding <=> '{embedding}') AS vector_score
            FROM documents 
            WHERE 1=1
            {f"AND doc_type = '{doc_type}'" if doc_type else ""}
            ORDER BY vector_score DESC
            LIMIT {limit * 2}
        ),
        text_search AS (
            SELECT 
                id,
                ts_rank(to_tsvector('english', content), to_tsquery('english', '{' '.join(query.split())}:*')) AS text_score
            FROM documents
            WHERE 1=1
            {f"AND doc_type = '{doc_type}'" if doc_type else ""}
            AND to_tsvector('english', content) @@ to_tsquery('english', '{' '.join(query.split())}:*')
            ORDER BY text_score DESC
            LIMIT {limit * 2}
        ),
        combined AS (
            SELECT 
                d.id,
                d.title,
                d.content,
                d.metadata,
                d.doc_type,
                d.created_at,
                COALESCE(vs.vector_score, 0) * {vector_weight} + COALESCE(ts.text_score, 0) * {full_text_weight} AS combined_score
            FROM documents d
            LEFT JOIN vector_search vs ON d.id = vs.id
            LEFT JOIN text_search ts ON d.id = ts.id
            WHERE vs.id IS NOT NULL OR ts.id IS NOT NULL
            ORDER BY combined_score DESC
            LIMIT {limit}
        )
        SELECT * FROM combined;
        """
        
        result = supabase.rpc("run_sql", {"sql": sql}).execute()
        
        return result.data
    
    except Exception as e:
        logger.error(f"Error performing hybrid search: {str(e)}")
        raise 