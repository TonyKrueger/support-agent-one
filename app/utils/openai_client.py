import os
import logging
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Cache the client instance
_openai_client = None

def get_openai_client() -> OpenAI:
    """
    Get or create an OpenAI client instance.
    
    Returns:
        OpenAI client instance
    """
    global _openai_client
    
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        _openai_client = OpenAI(api_key=api_key)
    
    return _openai_client 