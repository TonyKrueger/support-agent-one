#!/usr/bin/env python
"""
Environment Setup Script

This script creates a .env file from .env.example, prompting the user
for required API keys.
"""

import os
import sys
from typing import Dict, Any

# Check if .env already exists
if os.path.exists('.env'):
    overwrite = input('.env file already exists. Overwrite? (y/N): ')
    if overwrite.lower() != 'y':
        print('Setup cancelled.')
        sys.exit(0)

# Read .env.example
try:
    with open('.env.example', 'r') as f:
        env_template = f.read()
except FileNotFoundError:
    print('.env.example file not found. Please make sure the file exists.')
    sys.exit(1)

# Define required keys that we'll prompt for
required_keys = {
    'OPENAI__API_KEY': 'Enter your OpenAI API key: ',
    'SUPABASE__SERVICE_KEY': 'Enter your Supabase service key (if needed, or leave empty): ',
    'LOG__LOGFIRE_API_KEY': 'Enter your Logfire API key (if needed, or leave empty): '
}

# Collect values from user
values: Dict[str, Any] = {}
print('Setting up environment variables for the Support Agent')
print('------------------------------------------------------')

for key, prompt in required_keys.items():
    value = input(prompt)
    values[key] = value

# Replace values in the template
env_content = env_template
for key, value in values.items():
    if value:  # Only replace if the user entered a value
        env_content = env_content.replace(f'{key}=your_openai_api_key' if 'OPENAI' in key 
                                        else f'{key}=your_supabase_service_key' if 'SUPABASE' in key
                                        else f'{key}=your_logfire_api_key',
                                     f'{key}={value}')

# Write to .env file
with open('.env', 'w') as f:
    f.write(env_content)

print('\nEnvironment setup complete! .env file created.')
print('You can now run the application or tests.') 