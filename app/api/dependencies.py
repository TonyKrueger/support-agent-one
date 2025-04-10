from fastapi import Depends
import logging
from functools import lru_cache
from typing import Annotated

from app.services.agent_service import SupportAgent
from app.services.document_service import DocumentService
from app.db.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache
def get_document_service():
    """
    Create and return a cached DocumentService instance.
    
    Returns:
        DocumentService: The document service instance
    """
    try:
        supabase = get_supabase_client()
        return DocumentService(supabase)
    except Exception as e:
        logger.error(f"Error creating DocumentService: {str(e)}")
        raise e

@lru_cache
def get_agent():
    """
    Create and return a cached SupportAgent instance.
    
    Returns:
        SupportAgent: The support agent instance
    """
    try:
        doc_service = get_document_service()
        return SupportAgent(doc_service)
    except Exception as e:
        logger.error(f"Error creating SupportAgent: {str(e)}")
        raise e 