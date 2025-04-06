"""Tests for Logfire logging."""

import pytest
import logfire
import time


@pytest.mark.asyncio
async def test_logfire_configuration(configure_logfire):
    """Test that Logfire is properly configured."""
    # Simply test that we can log without errors
    logfire.info("Logfire configuration test", test_value=True)
    
    # We can't easily assert on external logging, so this test just verifies
    # that the logging call doesn't raise an exception
    assert True


@pytest.mark.asyncio
async def test_logfire_levels():
    """Test that different log levels work."""
    # Log at different levels
    logfire.debug("Debug test message", level="debug")
    logfire.info("Info test message", level="info")
    logfire.warning("Warning test message", level="warning")
    logfire.error("Error test message", level="error")
    
    # Again, we're just checking that no exceptions occur
    assert True


@pytest.mark.asyncio
async def test_logfire_structured_data():
    """Test that structured data is logged correctly."""
    # Log with structured data
    logfire.info(
        "Structured data test",
        str_value="test",
        int_value=123,
        float_value=3.14,
        bool_value=True,
        list_value=[1, 2, 3],
        dict_value={"key": "value"},
        timestamp=time.time()
    )
    
    # Just checking that no exceptions occur
    assert True 