"""
Environment Initialization Module

This module handles initialization of environment variables to ensure consistency
across different access patterns in the application.
"""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def initialize_environment():
    """
    Initialize environment variables for the application.
    
    This function ensures that environment variables are loaded consistently,
    particularly handling the case of API keys that are accessed both through
    Pydantic settings (with double underscores) and directly (with single underscores).
    """
    # Load .env file
    load_dotenv()
    
    # --- OpenAI API Key --- #
    # Ensure both formats are available for the OpenAI API key
    if "OPENAI__API_KEY" in os.environ and "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = os.environ["OPENAI__API_KEY"]
        logger.debug("Set OPENAI_API_KEY from OPENAI__API_KEY")
    elif "OPENAI_API_KEY" in os.environ and "OPENAI__API_KEY" not in os.environ:
        os.environ["OPENAI__API_KEY"] = os.environ["OPENAI_API_KEY"]
        logger.debug("Set OPENAI__API_KEY from OPENAI_API_KEY")
    
    # --- Supabase --- #
    # Ensure both formats are available for Supabase connection
    if "SUPABASE__URL" in os.environ and "SUPABASE_URL" not in os.environ:
        os.environ["SUPABASE_URL"] = os.environ["SUPABASE__URL"]
    elif "SUPABASE_URL" in os.environ and "SUPABASE__URL" not in os.environ:
        os.environ["SUPABASE__URL"] = os.environ["SUPABASE_URL"]
    
    if "SUPABASE__ANON_KEY" in os.environ and "SUPABASE_KEY" not in os.environ:
        os.environ["SUPABASE_KEY"] = os.environ["SUPABASE__ANON_KEY"]
    elif "SUPABASE_KEY" in os.environ and "SUPABASE__ANON_KEY" not in os.environ:
        os.environ["SUPABASE__ANON_KEY"] = os.environ["SUPABASE_KEY"]
    
    if "SUPABASE__SERVICE_KEY" in os.environ and "SUPABASE_SERVICE_KEY" not in os.environ:
        os.environ["SUPABASE_SERVICE_KEY"] = os.environ["SUPABASE__SERVICE_KEY"]
    elif "SUPABASE_SERVICE_KEY" in os.environ and "SUPABASE__SERVICE_KEY" not in os.environ:
        os.environ["SUPABASE__SERVICE_KEY"] = os.environ["SUPABASE_SERVICE_KEY"]
    
    # --- Embedding Model --- #
    if "OPENAI__EMBEDDING_MODEL" in os.environ and "EMBEDDING_MODEL" not in os.environ:
        os.environ["EMBEDDING_MODEL"] = os.environ["OPENAI__EMBEDDING_MODEL"]
    elif "EMBEDDING_MODEL" in os.environ and "OPENAI__EMBEDDING_MODEL" not in os.environ:
        os.environ["OPENAI__EMBEDDING_MODEL"] = os.environ["EMBEDDING_MODEL"]
        
    # Add additional environment variable synchronizations as needed 