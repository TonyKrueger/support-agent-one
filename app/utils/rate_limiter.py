"""
Rate Limiter Utility

This module provides rate limiting functionality to prevent excessive API usage.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

from app.utils.logger import get_logger
from app.config.ai_settings import ai_settings

logger = get_logger(__name__)


class RateLimiter:
    """
    A simple rate limiter to prevent excessive API calls.
    Uses a sliding window approach.
    """
    
    def __init__(self, max_requests: int = None, window_seconds: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests or ai_settings.rate_limit_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        logger.info(f"Rate limiter initialized with {self.max_requests} requests per {self.window_seconds}s")
    
    def check_rate_limit(self, key: str = "default") -> bool:
        """
        Check if a request should be rate limited.
        
        Args:
            key: Identifier for the rate limit bucket (e.g., user ID)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        with self.lock:
            current_time = time.time()
            
            # Initialize if key doesn't exist
            if key not in self.requests:
                self.requests[key] = []
                
            # Remove timestamps older than the window
            self.requests[key] = [
                ts for ts in self.requests[key] 
                if current_time - ts < self.window_seconds
            ]
            
            # Check if under the limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(current_time)
                return True
            
            # Rate limited
            logger.warning(f"Rate limit exceeded for {key}: {len(self.requests[key])} requests in {self.window_seconds}s")
            return False
    
    def get_remaining_requests(self, key: str = "default") -> int:
        """
        Get the number of remaining requests in the current window.
        
        Args:
            key: Identifier for the rate limit bucket
            
        Returns:
            Number of remaining requests
        """
        with self.lock:
            current_time = time.time()
            
            # Initialize if key doesn't exist
            if key not in self.requests:
                return self.max_requests
                
            # Remove timestamps older than the window
            self.requests[key] = [
                ts for ts in self.requests[key] 
                if current_time - ts < self.window_seconds
            ]
            
            return max(0, self.max_requests - len(self.requests[key]))
    
    def get_retry_after(self, key: str = "default") -> float:
        """
        Get the time in seconds until the next request is allowed.
        
        Args:
            key: Identifier for the rate limit bucket
            
        Returns:
            Time in seconds until next request is allowed, or 0 if not rate limited
        """
        with self.lock:
            current_time = time.time()
            
            # Initialize if key doesn't exist
            if key not in self.requests:
                return 0
                
            # If under the limit, no need to wait
            if len(self.requests[key]) < self.max_requests:
                return 0
                
            # Find the oldest timestamp
            if self.requests[key]:
                oldest = min(self.requests[key])
                # Calculate when it will expire from the window
                return max(0, oldest + self.window_seconds - current_time)
                
            return 0


# Create a global rate limiter instance
rate_limiter = RateLimiter() 