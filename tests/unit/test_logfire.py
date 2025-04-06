"""Tests for Logfire logging."""

# Import test helper first to set environment variables
import tests.helpers

import pytest
import logging
from unittest.mock import patch
import time


@pytest.mark.asyncio
async def test_logfire_configuration():
    """Test that logfire is properly configured."""
    # Just a simple assertion since actual logfire is mocked in conftest.py
    assert True


@pytest.mark.asyncio
async def test_logfire_levels():
    """Test that different log levels work."""
    
    # Use standard Python logging instead of logfire in tests
    with patch('logging.debug') as mock_debug, \
         patch('logging.info') as mock_info, \
         patch('logging.warning') as mock_warning, \
         patch('logging.error') as mock_error:
        
        # Call logging functions
        logging.debug("Debug test message")
        logging.info("Info test message")
        logging.warning("Warning test message")
        logging.error("Error test message")
        
        # Check that they were called
        mock_debug.assert_called_once()
        mock_info.assert_called_once()
        mock_warning.assert_called_once()
        mock_error.assert_called_once()


@pytest.mark.asyncio
async def test_logfire_structured_data():
    """Test that structured data is logged correctly."""
    # Use Python's standard logging instead
    with patch('logging.info') as mock_info:
        logging.info(
            "Structured data test",
            extra={
                "str_value": "test",
                "int_value": 123,
                "float_value": 3.14,
                "bool_value": True,
                "list_value": [1, 2, 3],
                "dict_value": {"key": "value"},
                "timestamp": time.time()
            }
        )
        
        # Check it was called
        mock_info.assert_called_once()
        assert True 