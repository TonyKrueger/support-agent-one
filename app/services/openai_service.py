"""
OpenAI Service Module

This module provides wrapper functions for the OpenAI API, handling authentication,
request formatting, error handling, and retry logic.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

import openai
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config.settings import settings
from app.config.ai_settings import ai_settings
from app.utils.logger import get_logger
from app.utils.rate_limiter import rate_limiter

logger = get_logger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Constants
EMBEDDING_MODEL = ai_settings.embedding_model
COMPLETION_MODEL = ai_settings.model
MAX_TOKENS = ai_settings.max_tokens
EMBEDDING_DIMENSIONS = 1536


class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors."""
    pass


class RateLimitExceededError(OpenAIServiceError):
    """Exception for when the rate limit is exceeded."""
    
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Try again in {retry_after:.1f} seconds.")


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying API call after error: {retry_state.outcome.exception()}. "
        f"Attempt {retry_state.attempt_number}/{retry_state.retry_state.stop.get_stop_after_attempt()}"
    )
)
def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text strings.
    
    Args:
        texts: List of text strings to generate embeddings for
        
    Returns:
        List of embedding vectors (each as a list of floats)
        
    Raises:
        OpenAIServiceError: If an error occurs during the API call
        RateLimitExceededError: If the rate limit is exceeded
    """
    try:
        logger.debug(f"Generating embeddings for {len(texts)} text chunks")
        
        # Check rate limit before proceeding
        if not rate_limiter.check_rate_limit("embeddings"):
            retry_after = rate_limiter.get_retry_after("embeddings")
            logger.warning(f"Rate limit exceeded for embeddings. Retry after {retry_after} seconds.")
            raise RateLimitExceededError(retry_after)
        
        # Batch the requests to avoid exceeding API limits
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
            # Sleep briefly between large batches to avoid rate limits
            if i + batch_size < len(texts):
                time.sleep(0.5)
        
        logger.debug(f"Successfully generated {len(all_embeddings)} embeddings")
        return all_embeddings
        
    except openai.OpenAIError as e:
        logger.error(f"OpenAI embedding error: {str(e)}")
        raise OpenAIServiceError(f"Failed to generate embeddings: {str(e)}")


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying API call after error: {retry_state.outcome.exception()}. "
        f"Attempt {retry_state.attempt_number}/{retry_state.retry_state.stop.get_stop_after_attempt()}"
    )
)
def get_chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = None,
    max_tokens: int = None,
    model: str = None,
    stream: bool = False
) -> Union[str, Any]:
    """
    Generate a chat completion using the OpenAI API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens to generate
        model: Model to use for completion
        stream: Whether to stream the response
        
    Returns:
        Generated text or stream response object
        
    Raises:
        OpenAIServiceError: If an error occurs during the API call
        RateLimitExceededError: If the rate limit is exceeded
    """
    try:
        logger.debug(f"Generating chat completion with {len(messages)} messages")
        
        # Use config values if parameters not provided
        temperature = temperature if temperature is not None else ai_settings.temperature
        max_tokens = max_tokens if max_tokens is not None else ai_settings.max_tokens
        model = model or COMPLETION_MODEL
        
        # Check rate limit before proceeding
        if not rate_limiter.check_rate_limit("completions"):
            retry_after = rate_limiter.get_retry_after("completions")
            logger.warning(f"Rate limit exceeded for completions. Retry after {retry_after} seconds.")
            raise RateLimitExceededError(retry_after)
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            logger.debug("Returning stream response")
            return response
        else:
            completion_text = response.choices[0].message.content
            logger.debug(f"Chat completion successful, generated {len(completion_text)} chars")
            return completion_text
            
    except openai.OpenAIError as e:
        logger.error(f"OpenAI completion error: {str(e)}")
        raise OpenAIServiceError(f"Failed to generate chat completion: {str(e)}")


def moderate_content(text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if text violates OpenAI's content policy.
    
    Args:
        text: The text to moderate
        
    Returns:
        Tuple of (flagged: bool, categories: Optional[Dict])
    """
    try:
        if not ai_settings.moderation_enabled:
            return False, None
            
        logger.debug("Moderating content")
        
        # Check rate limit before proceeding
        if not rate_limiter.check_rate_limit("moderation"):
            logger.warning("Rate limit exceeded for moderation. Skipping moderation.")
            # For moderation, we'll skip rather than fail if rate limited
            return False, None
        
        response = client.moderations.create(input=text)
        result = response.results[0]
        flagged = result.flagged
        
        categories = None
        if flagged:
            categories = {
                category: score
                for category, score in result.category_scores.items()
                if getattr(result.categories, category)
            }
            logger.warning(f"Content moderation flagged text. Categories: {categories}")
            
        return flagged, categories
        
    except openai.OpenAIError as e:
        logger.error(f"OpenAI moderation error: {str(e)}")
        # Return True (flagged) to be safe if the moderation API fails
        return True, None 