---
title: Vector Search
description: Documentation for the vector search implementation in the Support Agent project
date_created: 2025-04-16
last_updated: 2025-04-16
tags:
  - search
  - embeddings
  - vector-search
  - relevance
  - context
sidebar_position: 3.5
---

# Vector Search

## Overview

The Vector Search system provides semantic search capabilities over chunked documents. Unlike traditional keyword search, vector search uses embeddings to find content that is semantically similar to the query, even if it doesn't contain the exact keywords.

The Search Service builds on our application layer chunking infrastructure to offer advanced features like relevance ranking, context retrieval, and multiple search strategies.

## Architecture

The search system is built on three main components:

```
app/
  services/
    search_service.py      # Advanced search capabilities and context retrieval
    document_service.py    # Document and chunk management
    document_storage.py    # Low-level vector similarity search
```

## Search Service

The `SearchService` class in `search_service.py` provides high-level search functionality:

```python
from app.services.search_service import SearchService

search = SearchService()

# Basic search
results = search.search(
    query="How to reset my password?",
    limit=5
)
```

### Key Features

The search service includes several advanced features:

#### 1. Context Retrieval

When `include_context=True`, the search service will return not only the matching chunks but also surrounding chunks from the same document for better context understanding:

```python
# Search with context
results = search.search(
    query="Authentication methods",
    include_context=True
)

# Results include surrounding chunks marked with:
# - is_context: True
# - context_for: The chunk index it provides context for
# - context_position: "before" or "after"
```

#### 2. Metadata Filtering

You can filter search results based on document metadata:

```python
# Search only in a specific category
results = search.search(
    query="Database migration",
    metadata_filter={"category": "technical", "version": "2.0"}
)
```

#### 3. Multiple Search Strategies

Different search strategies can be used for different scenarios:

```python
# Default semantic search
results = search.search_by_strategy(
    query="API rate limits",
    strategy="semantic"
)

# Semantic search with context
results = search.search_by_strategy(
    query="API rate limits",
    strategy="semantic_with_context"
)

# Other strategies (placeholders for future implementation)
# - "exact": Exact text matching
# - "hybrid": Combination of semantic and exact matching
```

## Implementation Details

### Search Process

1. **Query Embedding**: The search query is converted to an embedding vector
2. **Vector Similarity**: The query embedding is compared to stored document chunks
3. **Relevance Ranking**: Results are ranked by similarity score
4. **Context Addition**: If requested, surrounding chunks are added for context
5. **Result Enhancement**: Document metadata is added to each result

### Relevance Ranking

Search results are ranked by cosine similarity between the query embedding and chunk embeddings:

```python
# Results are sorted by similarity score (highest first)
context_results.sort(
    key=lambda x: x.get("similarity", 0) if not x.get("is_context", False) else 0,
    reverse=True
)
```

Context chunks are given lower priority in the ranking to ensure the most relevant chunks appear first.

### Context Retrieval Algorithm

The context retrieval algorithm:

1. Groups results by document ID
2. Fetches all chunks for each document
3. For each matching chunk, adds surrounding chunks as context
4. Marks context chunks with metadata to indicate their relationship

```python
# Add preceding chunks as context
for i in range(1, self.CONTEXT_WINDOW_SIZE + 1):
    prev_index = chunk_index - i
    if prev_index in chunk_map and prev_index not in chunks:
        prev_chunk = chunk_map[prev_index]
        prev_chunk["is_context"] = True
        prev_chunk["context_for"] = chunk_index
        prev_chunk["context_position"] = "before"
        context_results.append(prev_chunk)
```

## Usage Examples

### Basic Search

```python
from app.services.search_service import SearchService

search = SearchService()

# Perform a basic search
results = search.search(
    query="How to configure authentication",
    limit=5
)

# Process results
for result in results:
    print(f"Document: {result['document_title']}")
    print(f"Content: {result['content']}")
    print(f"Similarity: {result['similarity']}")
```

### Search with Context

```python
# Search with context
results = search.search(
    query="User authentication",
    include_context=True
)

# Extract primary results and their context
primary_results = [r for r in results if not r.get('is_context')]
for result in primary_results:
    print(f"Document: {result['document_title']}")
    print(f"Content: {result['content']}")
    print(f"Similarity: {result['similarity']}")
    
    # Get context for this result
    context = [r for r in results if r.get('context_for') == result.get('chunk_index')]
    before = [c for c in context if c.get('context_position') == 'before']
    after = [c for c in context if c.get('context_position') == 'after']
    
    if before:
        print("Previous context:")
        for ctx in before:
            print(f"- {ctx['content'][:100]}...")
    
    if after:
        print("Following context:")
        for ctx in after:
            print(f"- {ctx['content'][:100]}...")
```

### Filtered Search

```python
# Search with metadata filtering
results = search.search(
    query="Deploy to production",
    metadata_filter={"category": "deployment"}
)

# Count results by document
doc_counts = {}
for result in results:
    doc_title = result.get('document_title', 'Unknown')
    doc_counts[doc_title] = doc_counts.get(doc_title, 0) + 1

print("Results by document:")
for doc, count in doc_counts.items():
    print(f"- {doc}: {count} chunks")
```

## Integration with Document Processing

The search service integrates with the document processing pipeline:

1. Documents are processed and chunked (see [Application Layer Chunking](ApplicationLayerChunking.md))
2. Chunks are stored with embeddings in the vector database
3. The search service retrieves these chunks based on query similarity

This integration ensures that all documents are automatically searchable after processing.

## Related Documentation

- [Application Layer Chunking](ApplicationLayerChunking.md) - Details on document chunking
- [Document Processing](DocumentProcessing.md) - Document processing pipeline
- [OpenAI Integration](OpenAI.md) - Embedding generation via OpenAI
- [Supabase Integration](Supabase.md) - Vector database implementation

## Future Enhancements

Planned improvements to the search service:

1. **Exact Text Search**: Implement non-semantic search for exact matches
2. **Hybrid Search**: Combine semantic and exact matching for improved results
3. **Enhanced Filtering**: More advanced metadata filtering options
4. **Faceted Search**: Group search results by categories and attributes
5. **Search Caching**: Cache frequent search queries to improve performance
6. **Search Analytics**: Track search patterns to improve relevance
7. **Custom Ranking**: Allow customization of the ranking algorithm 