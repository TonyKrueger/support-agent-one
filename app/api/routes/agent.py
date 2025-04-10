from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, List, Any, Optional
import logging

from app.services.agent_service import SupportAgent
from app.api.dependencies import get_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/query", response_model=Dict[str, Any])
async def process_query(
    query: str = Body(..., embed=True),
    doc_type: Optional[str] = Body(None, embed=True),
    agent: SupportAgent = Depends(get_agent)
):
    """Process a user query and return a support agent response.
    
    Args:
        query: The user's question
        doc_type: Optional document type to limit search
        
    Returns:
        Dict with answer and relevant document sources
    """
    try:
        logger.info(f"Processing query: {query}")
        response = agent.process_query(query, doc_type)
        return response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_history(agent: SupportAgent = Depends(get_agent)):
    """Get the conversation history.
    
    Returns:
        List of conversation messages
    """
    try:
        return agent.get_conversation_history()
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation history: {str(e)}")

@router.post("/clear", response_model=Dict[str, bool])
async def clear_conversation(agent: SupportAgent = Depends(get_agent)):
    """Clear the conversation history.
    
    Returns:
        Success status
    """
    try:
        agent.clear_conversation()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")

@router.post("/save", response_model=Dict[str, bool])
async def save_conversation(
    filepath: str = Body(..., embed=True),
    agent: SupportAgent = Depends(get_agent)
):
    """Save conversation to a file.
    
    Args:
        filepath: Path where to save the conversation
        
    Returns:
        Success status
    """
    try:
        success = agent.save_conversation(filepath)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving conversation: {str(e)}")

@router.post("/load", response_model=Dict[str, bool])
async def load_conversation(
    filepath: str = Body(..., embed=True),
    agent: SupportAgent = Depends(get_agent)
):
    """Load conversation from a file.
    
    Args:
        filepath: Path of the saved conversation
        
    Returns:
        Success status
    """
    try:
        success = agent.load_conversation(filepath)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error loading conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading conversation: {str(e)}") 