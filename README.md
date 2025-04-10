# Support Agent One

A customer support agent that can have chat conversations with users, reference documentation, and access product and customer information.

## Features

- Chat-based support interface
- Document search and retrieval
- Product information lookup via serial number
- Customer information access
- Conversation history tracking
- Solution identification and storage

## Tech Stack

- **Python** with Poetry for dependency management
- **Pydantic AI** for AI model integration
- **Pydantic Logfire** for structured logging
- **FastAPI** for building the API
- **OpenAI** for natural language processing
- **Supabase** for database and vector search
- Document processing with various libraries

## Development Setup

1. Clone the repository
```bash
git clone <repository-url>
cd support-agent-one
```

2. Install dependencies with Poetry
```bash
poetry install
```

3. Set up environment variables
```bash
# Copy the example .env file
cp .env.example .env

# Edit the .env file with your credentials
```

4. Run the development server
```bash
poetry run python -m app.main
```

## Project Structure

- `app/api` - API routes and endpoints
- `app/models` - Data models and Pydantic schemas
- `app/services` - Business logic and service layers
- `app/core` - Core application components
- `app/utils` - Utility functions and helpers
- `app/config` - Application configuration
- `app/data` - Data storage and document files 