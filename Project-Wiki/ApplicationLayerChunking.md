---
title: Application Layer Chunking
description: Documentation for the application-layer document chunking implementation
date_created: 2025-04-15
last_updated: 2025-04-17
tags:
  - documents
  - embeddings
  - chunking
  - vector-search
  - openai
sidebar_position: 3.1
---

# Application Layer Chunking

## Overview

The application layer chunking system handles document chunking entirely within the application layer, eliminating the need for database triggers and functions. This approach provides greater control, flexibility, and observability while streamlining the document processing pipeline.

## Architecture

The application layer chunking system consists of several main components:

```
app/
  utils/
    text_chunker.py        # Centralized chunking logic
    embedding_pipeline.py  # Document → chunks → embeddings pipeline
    observability.py       # Performance tracking and metrics
  services/
    document_storage.py    # Transactional storage management
    search_service.py      # Advanced search capabilities
  api/v1/
    documents.py           # Document API endpoints
    metrics.py             # Metrics API endpoints
```

## Core Components

### Text Chunker

The `text_chunker.py` module provides centralized chunking logic with multiple strategies:

```python
from app.utils.text_chunker import chunk_text, ChunkingStrategy

# Simple line-based chunking
chunks = chunk_text(
    text,
    chunk_size=1000,
    chunk_overlap=200,
    strategy=ChunkingStrategy.SIMPLE
)

# Sentence-based chunking
sentence_chunks = chunk_text(
    text,
    chunk_size=1000,
    chunk_overlap=200,
    strategy=ChunkingStrategy.SENTENCE
)

# Markdown-aware chunking
markdown_chunks = chunk_text(
    markdown_text,
    chunk_size=1000,
    chunk_overlap=200,
    strategy=ChunkingStrategy.MARKDOWN,
    content_type="markdown"
)
```

The chunker automatically selects appropriate strategies based on content type and provides specialized algorithms for different document formats:

| Strategy | Description | Best For |
|----------|-------------|----------|
| `SIMPLE` | Line-based chunking | Plain text, log files |
| `SENTENCE` | Sentence-aware chunking | Articles, prose |
| `PARAGRAPH` | Paragraph-based chunking | Web content, documentation |
| `MARKDOWN` | Markdown-aware chunking | Markdown files, preserving headers |
| `SEMANTIC` | Chunking by semantic units | Complex documents (future enhancement) |

### Embedding Pipeline

The `embedding_pipeline.py` module provides a seamless pipeline from document to chunks to embeddings:

```python
from app.utils.embedding_pipeline import process_text, process_document

# Full pipeline: chunking and embedding generation
chunks, embeddings = process_text(
    text=content,
    content_type="markdown",
    chunk_size=800,
    chunk_overlap=150
)

# Process document with metadata
chunks, embeddings, chunk_metadata = process_document(
    document_id="doc-123",
    title="User Guide",
    content=content,
    content_type="text",
    metadata={"category": "manual"}
)
```

Key features:
- **Efficient Batching**: Processes embeddings in optimized batches for API efficiency
- **Caching Layer**: Caches embeddings to avoid redundant API calls
- **Content-Type Awareness**: Tailors chunking based on content type
- **Configurable Parameters**: Allows customization of chunk size and overlap

### Document Storage

The `document_storage.py` service handles atomic storage of documents and chunks:

```python
from app.services.document_storage import DocumentStorage

storage = DocumentStorage()

# Store document with chunks atomically
document, chunks = storage.store_document_with_chunks(
    title="API Documentation",
    content=content,
    chunks=chunks,
    embeddings=embeddings,
    metadata={"category": "technical"}
)

# Update document with new chunks
updated_doc, updated_chunks = storage.update_document_with_chunks(
    doc_id="doc-123",
    content=new_content,
    chunks=new_chunks,
    embeddings=new_embeddings,
    replace_chunks=True
)

# Search using vector similarity
results = storage.search_documents(
    query_embedding=query_embedding,
    limit=5,
    similarity_threshold=0.7
)
```

Key features:
- **Transaction-like Operations**: Ensures atomicity when storing documents and chunks
- **Version Tracking**: Tracks document versions for change management
- **Bulk Operations**: Efficiently handles batch operations
- **Error Recovery**: Implements rollback on partial failures

### Search Service

The `search_service.py` module provides advanced search capabilities with relevance ranking and context retrieval:

```python
from app.services.search_service import SearchService

search = SearchService()

# Basic semantic search
results = search.search(
    query="How to configure API keys?",
    limit=5
)

# Search with surrounding context
context_results = search.search(
    query="Authentication methods",
    include_context=True
)

# Search with metadata filtering
filtered_results = search.search(
    query="Deploy to production",
    metadata_filter={"category": "deployment", "version": "1.0"}
)

# Search with different strategies
strategy_results = search.search_by_strategy(
    query="Database migration",
    strategy="semantic_with_context"
)
```

Key features:
- **Context Retrieval**: Includes surrounding document chunks for better understanding
- **Relevance Ranking**: Sorts results by their similarity to the query
- **Metadata Filtering**: Filters results based on document metadata
- **Multiple Search Strategies**: Supports semantic, context-aware, and hybrid search approaches

### API Endpoints

The document API endpoints have been updated to leverage the enhanced chunking pipeline:

```python
# Create a document with chunking options
POST /api/v1/documents/
{
  "title": "API Documentation",
  "content": "Document content...",
  "metadata": {"category": "technical"},
  "chunk_size": 800,
  "chunk_overlap": 150,
  "chunking_strategy": "markdown",
  "content_type": "markdown"
}

# Upload a document file with chunking options
POST /api/v1/documents/upload
FormData:
  - file: <file upload>
  - title: "User Guide"
  - metadata_json: {"category": "manual"}
  - chunk_size: 800
  - chunk_overlap: 150
  - chunking_strategy: "markdown"

# Update a document with chunking options
PUT /api/v1/documents/{document_id}
{
  "content": "Updated content...",
  "chunk_size": 800,
  "chunk_overlap": 150,
  "chunking_strategy": "markdown",
  "replace_chunks": true
}

# Create chunks for an existing document
POST /api/v1/documents/{document_id}/chunks?chunk_size=800&chunk_overlap=150&chunking_strategy=markdown
```

These endpoints provide full access to:
- Configurable chunking parameters
- Different chunking strategies
- Content type detection
- Chunk management operations
- Advanced search options

### Observability

The system includes comprehensive observability features for monitoring and optimizing performance. See the [Observability](./Observability.md) documentation for details on:

- Performance tracking for chunking operations
- Metrics collection for embedding generation
- Pipeline stage monitoring
- Detailed logging throughout the process
- API endpoints for accessing metrics

## Advantages Over Database Triggers

The application layer approach offers several advantages over database triggers:

1. **Greater Control**: Full control over chunking algorithms and embedding generation
2. **Better Observability**: Comprehensive logging and metrics throughout the pipeline
3. **Testing Simplicity**: Easier to test and mock components
4. **Enhanced Flexibility**: Simpler to modify and extend without database changes
5. **Language-Specific Features**: Leverages Python's natural language processing capabilities
6. **Error Handling**: More robust error handling and recovery strategies
7. **Caching**: Efficient resource usage through caching

## Implementation Benefits

Benefits of the current implementation:

1. **Modular Architecture**: Clear separation of concerns between components
2. **Content-Aware Chunking**: Specialized strategies based on content type
3. **Optimized Performance**: Batching and caching for efficiency
4. **Transaction Safety**: Pseudo-transactions for data integrity
5. **Versioning**: Built-in versioning for change tracking
6. **Context-Aware Search**: Improved search results with surrounding context
7. **Multiple Search Strategies**: Flexibility in how documents are retrieved
8. **Comprehensive Metrics**: Detailed performance tracking and monitoring
9. **API-First Design**: Full access to chunking capabilities through REST endpoints

## Usage Examples

### Processing a New Document

```python
from app.utils.embedding_pipeline import process_text
from app.services.document_storage import DocumentStorage

# Initialize storage
storage = DocumentStorage()

# Process document content
chunks, embeddings = process_text(
    text=document_content,
    content_type="markdown"
)

# Store document and chunks
document, stored_chunks = storage.store_document_with_chunks(
    title="Getting Started Guide",
    content=document_content,
    chunks=chunks,
    embeddings=embeddings,
    metadata={"category": "tutorial"}
)
```

### Performing Vector Search with Context

```python
from app.services.search_service import SearchService

# Initialize search service
search = SearchService()

# Search with context retrieval
results = search.search(
    query="How to configure authentication?",
    include_context=True,
    limit=3
)

# Process and display results
for result in results:
    print(f"Document: {result['document_title']}")
    print(f"Relevance: {result['similarity']:.2f}")
    print(f"Content: {result['content'][:100]}...")
    print(f"Is Context: {result.get('is_context', False)}")
    print("-" * 40)
```

### Using the API Endpoints

```python
import requests
import json

# Create a document with chunking
response = requests.post(
    "http://api.example.com/api/v1/documents/",
    json={
        "title": "Configuration Guide",
        "content": "Long document content...",
        "chunking_strategy": "paragraph",
        "chunk_size": 800,
        "metadata": {"type": "guide", "version": "1.0"}
    }
)
document = response.json()
document_id = document["id"]

# Search documents
response = requests.get(
    "http://api.example.com/api/v1/documents/search",
    params={
        "query": "How to configure?",
        "limit": 5,
        "include_context": "true",
        "strategy": "semantic_with_context",
        "metadata_filter": json.dumps({"type": "guide"})
    }
)
results = response.json()["results"]
```

## Related Documentation

- [Document Processing](./DocumentProcessing.md)
- [Vector Search](./VectorSearch.md)
- [Observability](./Observability.md)

## Next Steps

Upcoming enhancements to the application layer chunking system:

1. **Semantic Chunking**: Implement advanced semantic-based chunking
2. **Parallel Processing**: Add support for parallel chunk processing
3. **Compression**: Implement storage compression for large documents
4. **Custom Embedding Models**: Support for custom or local embedding models
5. **Incremental Updates**: Optimize partial document updates
6. **Caching Enhancements**: Distributed cache for embedding results
7. **Advanced Search Features**: Implement exact and hybrid search strategies 