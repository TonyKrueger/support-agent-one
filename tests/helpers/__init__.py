"""
Helper module for tests that sets environment variables before any other imports
This module must be imported before any app modules in test files.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load test environment variables from .env.test
test_env_path = Path(__file__).parent.parent.parent / '.env.test'
load_dotenv(test_env_path)

# These settings override any from .env.test if needed
os.environ['TEST_MOCK_OPENAI'] = 'true'
os.environ['TEST_MOCK_SUPABASE'] = 'true'
os.environ['ENVIRONMENT'] = 'test'

# Set test environment variables
os.environ['OPENAI_API_KEY'] = 'sk-test-key'
os.environ['SUPABASE_URL'] = 'https://example.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtYmNxcWFndW5mbm10Y3h6Y3F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2MTYxMDM1MzgsImV4cCI6MTkzMTY3OTUzOH0.r4M9LAU4NX0e4e6JhNmOyjTL0zGgTiKf1QpBnfF25U0' 