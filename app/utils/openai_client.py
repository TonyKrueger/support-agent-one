import os
import logging
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from app.config.settings import settings  # Import settings to use the properly loaded API key

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
        # First try to get the API key from settings
        try:
            api_key = settings.OPENAI_API_KEY
        except (AttributeError, ImportError):
            # Fall back to direct environment variable access
            api_key = os.getenv("OPENAI__API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            logger.error("OpenAI API key not found in settings or environment variables")
            raise ValueError("OpenAI API key not found. Please set OPENAI__API_KEY in your .env file")
        
        _openai_client = OpenAI(api_key=api_key)
    
    return _openai_client 