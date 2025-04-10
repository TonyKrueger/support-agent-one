"""
Logger Utility

This module provides a standardized logging configuration for the application,
using Pydantic Logfire for structured logging.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any

import logfire
from logfire.pydantic import LogfireBaseModel

from app.config.settings import settings

# Configure Logfire if API key is available
if settings.LOG.LOGFIRE_API_KEY:
    logfire.configure(
        write_key=settings.LOG.LOGFIRE_API_KEY,
        service_name=settings.APP_NAME,
        service_version=os.environ.get("SERVICE_VERSION", "unknown"),
        environment=settings.ENVIRONMENT,
    )


class LogContext(LogfireBaseModel):
    """Base model for structured log context."""
    component: str
    operation: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured based on application settings.
    
    Args:
        name: The logger name, typically __name__
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level based on configuration
    log_level = getattr(logging, settings.LOG.LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Configure handler if not already set up
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        # Use JSON formatter for structured logs if configured
        if settings.LOG.FORMAT.lower() == "json":
            try:
                import json_log_formatter
                formatter = json_log_formatter.JSONFormatter()
                handler.setFormatter(formatter)
            except ImportError:
                # Fall back to standard formatting if json_log_formatter not available
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
        else:
            # Use standard formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
        logger.addHandler(handler)
    
    return logger


def log_with_context(
    level: str, 
    msg: str, 
    context: LogContext,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log a message with structured context using Logfire if available.
    
    Args:
        level: Log level (debug, info, warning, error, critical)
        msg: Log message
        context: Structured context for the log
        logger: Optional logger instance, uses root logger if not provided
    """
    if not logger:
        logger = logging.getLogger()
    
    # Use logfire for structured logging if configured
    if settings.LOG.LOGFIRE_API_KEY:
        log_func = getattr(logfire, level.lower(), logfire.info)
        log_func(msg, **context.model_dump(exclude_none=True))
    else:
        # Standard logging if logfire not configured
        log_func = getattr(logger, level.lower(), logger.info)
        
        # Add context to log message
        context_str = " ".join([f"{k}={v}" for k, v in context.model_dump(exclude_none=True).items()])
        log_func(f"{msg} - {context_str}") 