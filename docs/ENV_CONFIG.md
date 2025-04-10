# Environment Configuration

## OpenAI API Key Configuration Issue

This document addresses an inconsistency in how the application accesses the OpenAI API key from environment variables.

### Problem

The application code has two different approaches to accessing the OpenAI API key:

1. Through Pydantic settings with double-underscore delimiter:
   - Uses `OPENAI__API_KEY` (with double underscores)
   - Defined in `app/config/settings.py`

2. Direct environment variable access in utility modules:
   - Uses `OPENAI_API_KEY` (with single underscore)
   - Accessed via `os.environ.get()` or `os.getenv()`

This inconsistency causes errors when running the application.

### Applied Fixes

The following files have been updated to use a consistent approach to API key access:

1. `app/utils/openai_client.py`
2. `app/services/search_utils.py`
3. `app/utils/vector_search.py`
4. `app/utils/search_utils.py`

Each file now follows this pattern:

```python
try:
    openai_api_key = settings.OPENAI_API_KEY  # First try settings from Pydantic
except (AttributeError, ImportError):
    # Fall back to direct environment variables with both formats
    openai_api_key = os.environ.get("OPENAI__API_KEY") or os.environ.get("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OpenAI API key not found. Please set OPENAI__API_KEY in your .env file")
```

### Recommended Solution for Deployment

For a permanent fix, update the application to use a single consistent approach:

#### Option 1: Environment Variables Initialization Module

Create a dedicated module to initialize all environment variables:

```python
# app/config/init_env.py
import os
from dotenv import load_dotenv

def initialize_environment():
    """Initialize environment variables for the application."""
    # Load .env file
    load_dotenv()
    
    # Set OpenAI API key in both formats for compatibility
    if "OPENAI__API_KEY" in os.environ and "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = os.environ["OPENAI__API_KEY"]
    elif "OPENAI_API_KEY" in os.environ and "OPENAI__API_KEY" not in os.environ:
        os.environ["OPENAI__API_KEY"] = os.environ["OPENAI_API_KEY"]
        
    # Add other environment variable initializations as needed
```

Then import this module in `app/main.py` before any other imports:

```python
# At the top of app/main.py
from app.config.init_env import initialize_environment
initialize_environment()

# Rest of the imports
import uvicorn
from fastapi import FastAPI
# ...
```

#### Option 2: Modify setup_env.py Script

Update the `setup_env.py` script to create both formats in the `.env` file:

```python
# Modified section of setup_env.py
# Replace values in the template
env_content = env_template
for key, value in values.items():
    if value:  # Only replace if the user entered a value
        # For OpenAI API key, add both formats
        if key == 'OPENAI__API_KEY':
            # Replace double underscore format
            env_content = env_content.replace(
                f'{key}=your_openai_api_key',
                f'{key}={value}'
            )
            # Also add single underscore format if not already present
            if 'OPENAI_API_KEY=' not in env_content:
                env_content += f'\nOPENAI_API_KEY={value}'
        # For other keys, just replace normally
        else:
            env_content = env_content.replace(
                f'{key}=your_supabase_service_key' if 'SUPABASE' in key
                else f'{key}=your_logfire_api_key',
                f'{key}={value}'
            )
```

### Current Workaround

Until a permanent solution is implemented, the following approach works:

1. Add both formats to your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI__API_KEY=your_openai_api_key
   ```

2. Or export the API key before running the application:
   ```bash
   export OPENAI_API_KEY="$(grep OPENAI_API_KEY .env | cut -d'=' -f2)"
   poetry run python -m app.main
   ```

This solution has been documented in the README.md file. 