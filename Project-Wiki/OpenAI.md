---
title: OpenAI Integration
description: Documentation for the OpenAI API integration in the Support Agent project
date_created: 2025-04-09
last_updated: 2025-04-09
tags:
  - openai
  - ai
  - embeddings
  - completions
sidebar_position: 2
---

# OpenAI Integration

## Overview

The Support Agent uses OpenAI's API for two primary functions:

1. **Text Embeddings**: Converting text chunks into vector embeddings for similarity search
2. **Chat Completions**: Generating responses to user queries based on context

Our implementation provides robust wrappers around the OpenAI API with error handling, retries, and rate limit management to ensure reliable operation in production.

## Architecture

The OpenAI integration is structured as a service layer that abstracts the API details from the rest of the application:

```
app/
  services/
    openai_service.py  # Core OpenAI API wrapper functions
  config/
    settings.py        # Configuration for API keys and model settings
```

## Key Features

- **Robust Error Handling**: Comprehensive error management for API failures
- **Automatic Retries**: Exponential backoff for transient errors like rate limits
- **Batched Requests**: Smart batching for embedding generation to optimize API usage
- **Content Moderation**: Integration with OpenAI's moderation API to filter inappropriate content
- **Configurable Models**: Easy configuration of models via environment variables

## OpenAI Services

### Embedding Generation

The system uses OpenAI's text embedding models to convert text into high-dimensional vectors. These embeddings enable semantic search capabilities by finding similar content based on meaning rather than exact text matching.

```python
from app.services.openai_service import get_embeddings

# Generate embeddings for text chunks
chunks = ["This is a sample text", "Another example chunk"]
embeddings = get_embeddings(chunks)

# Each embedding is a vector of floating-point numbers
# embeddings[0] = [0.123, 0.456, ...] (1536-dimensional vector)
```

Key implementation details:
- Uses the `text-embedding-3-small` model (configurable)
- Automatically batches requests to stay within API limits
- Applies progressive backoff for rate limit errors
- Returns 1536-dimensional embeddings suitable for vector search

### Chat Completions

The chat completion service generates natural language responses based on conversation history and context. It leverages OpenAI's conversation models to power the support agent's ability to understand and respond to user queries.

```python
from app.services.openai_service import get_chat_completion

# Define conversation messages
messages = [
    {"role": "system", "content": "You are a helpful support assistant."},
    {"role": "user", "content": "How do I reset my password?"}
]

# Generate a completion
response = get_chat_completion(
    messages=messages,
    temperature=0.7,
    max_tokens=500
)

# response = "To reset your password, please follow these steps..."
```

Key implementation details:
- Uses the `gpt-4-turbo` model by default (configurable)
- Supports streaming responses for real-time interaction
- Configurable temperature for controlling response randomness
- Includes optional token limits to control response length

### Content Moderation

For safety, the service includes a content moderation function that checks user inputs against OpenAI's content policy:

```python
from app.services.openai_service import moderate_content

# Check if content violates policy
flagged, categories = moderate_content("User input text here")

if flagged:
    # Handle flagged content
    print(f"Content was flagged in categories: {categories}")
```

## Configuration

OpenAI integration is configured through environment variables, using nested settings for organization:

```
# .env file
OPENAI__API_KEY=your_openai_api_key
OPENAI__EMBEDDING_MODEL=text-embedding-3-small
OPENAI__COMPLETION_MODEL=gpt-4-turbo
OPENAI__TEMPERATURE=0.7
```

These settings are managed through the Pydantic settings system in `app/config/settings.py`.

## Error Handling

The OpenAI service includes a custom exception class `OpenAIServiceError` that wraps OpenAI-specific errors with contextual information. The service automatically retries on transient errors using the `tenacity` library:

```python
@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5)
)
def get_embeddings(texts):
    # Implementation with retry logic
```

## Integration with Supabase

The OpenAI embeddings are designed to work with Supabase's pgvector extension:

1. Text is processed and chunked
2. OpenAI generates embeddings for each chunk
3. Embeddings are stored in Supabase with the `VECTOR(1536)` data type
4. Vector similarity search is performed using the `<=>` operator

See the [Supabase documentation](./Supabase.md) for details on vector storage and search.

## Testing

The integration includes test code to verify the connection and functionality:

```python
# From app/tests/test_integration.py
def test_openai_connection():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'OpenAI connection successful' if you can see this message."}
    ]
    
    response = get_chat_completion(messages, temperature=0)
    assert "OpenAI connection successful" in response
```

## Best Practices

When working with the OpenAI integration:

1. **Use Batching**: Process documents in reasonably sized chunks
2. **Handle Rate Limits**: The service handles retries, but design your application to work within API limits
3. **Monitor Token Usage**: Track API usage to control costs
4. **Prompt Engineering**: Design effective system prompts for the chat completions
5. **Cache Results**: Consider caching embeddings for frequently accessed content

## Future Enhancements

Planned improvements to the OpenAI integration:

1. Fine-tuning support for domain-specific models
2. Streaming response handler for real-time UI updates
3. Function calling capabilities for tool use
4. Cost tracking and usage analytics
5. Model switching based on query complexity 