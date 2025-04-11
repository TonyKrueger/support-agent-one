---
title: Search Similarity Thresholds
description: Understanding and configuring similarity thresholds for vector search
date_created: 2025-04-11
last_updated: 2025-04-11
tags:
  - search
  - similarity
  - thresholds
  - vector-search
  - relevance
sidebar_position: 3.6
---

# Search Similarity Thresholds

## Overview

This document explains how similarity thresholds work in vector search, why they're critical for search quality, and how to properly configure them. It addresses common issues with similarity thresholds and provides guidance on improving search quality.

## Understanding Similarity Thresholds

Similarity thresholds are scalar values (typically between 0 and 1) that determine the minimum relevance score required for a document to be included in search results. 

- A threshold of **1.0** means only exact matches are returned (usually resulting in no matches)
- A threshold of **0.0** means all documents are returned regardless of relevance
- A practical threshold is usually between **0.7** and **0.8**

The threshold is applied after calculating the cosine similarity between the query embedding and document embeddings:

```python
# Example threshold check
similarity_score = 1 - (query_embedding <=> document_embedding)
if similarity_score > SIMILARITY_THRESHOLD:
    # Include in results
```

## Impact of Threshold Settings

### Low Thresholds (e.g., 0.1)

With a very low threshold like 0.1 (10% similarity):

- Documents with minimal relevance appear in results
- Short queries produce many false positives
- Similar documents repeatedly appear across unrelated searches
- User trust in search results diminishes

### High Thresholds (e.g., 0.9)

With a very high threshold like 0.9 (90% similarity):

- Only highly relevant results are shown
- Many legitimate matches may be excluded
- Searches may return zero results
- Less effective for exploratory searches

### Optimal Thresholds (e.g., 0.7-0.8)

With an optimal threshold range (70-80% similarity):

- Results maintain high relevance to the query
- Most legitimate matches are included
- Irrelevant documents are filtered out
- Better user experience and trust

## Case Study: Irrelevant Search Results

### The Issue

Our support agent system was returning document ID `d2cf7cb1-d17e-4b65-b47a-501a6ae63b7a` when searching for unrelated terms like "37" or "bella" due to a misconfigured similarity threshold of 0.1 (10%).

### Root Cause Analysis

1. **Low threshold setting**: The system was configured to accept documents with as little as 10% similarity to the search query.

2. **Semantic vector quirks**: In vector space, even unrelated terms like "37" and "bella" have some minimal semantic relationship.

3. **Limited document corpus**: With few documents in the system, the same document becomes the "closest match" for many queries, even if not truly relevant.

4. **Short query embedding behavior**: Single-word queries produce less discriminative embedding vectors than longer queries.

### Resolution

Increasing the similarity threshold from 0.1 to 0.7 immediately improved search quality:

```python
# Before
self.SIMILARITY_THRESHOLD = 0.1  # Accept documents with 10% similarity

# After
self.SIMILARITY_THRESHOLD = 0.7  # Require documents to have 70% similarity
```

## Improving Search Quality

### Beyond Similarity Thresholds

While proper threshold settings are essential, other techniques can further improve search quality:

#### 1. Metadata-Based Filtering

Combining vector search with metadata filters:

```python
# Example: Filter by document category in addition to similarity
results = search.search(
    query="password reset",
    metadata_filter={"category": "authentication"}
)
```

#### 2. Hybrid Search Approaches

Combining semantic search with keyword search:

```python
# Placeholder for hybrid search implementation
results = search.hybrid_search(
    query="reset password",
    keyword_weight=0.3,  # 30% weight to exact keyword matching
    semantic_weight=0.7  # 70% weight to semantic similarity
)
```

#### 3. Query Expansion

Enhancing short queries with related terms:

```python
# Example of query expansion
expanded_query = search.expand_query("37")  # Might expand to "37 number integer"
```

#### 4. Document Indexing Options

Several indexing approaches can improve search quality:

- **Keyword indexing**: Adding explicit keywords to document metadata
- **Custom document vectors**: Creating custom domain-specific embedding models
- **Category-based indexing**: Organizing documents by category for filtered search
- **Hierarchical indexing**: Creating document hierarchies for easier navigation

#### 5. Faceted Search

Implementing faceted search allows users to refine results by metadata:

```python
# Initial search
results = search.search("configuration")

# Extract facets from results
facets = search.extract_facets(results)
# Returns: {"category": ["setup", "admin", "security"], "difficulty": ["beginner", "advanced"]}

# Refined search with facet
refined_results = search.search(
    query="configuration", 
    facet_filters={"category": "security"}
)
```

## Configuration Recommendations

### Basic Configuration

```python
# Recommended defaults
self.SIMILARITY_THRESHOLD = 0.75  # 75% similarity required
self.MAX_RESULTS = 10            # Return up to 10 results
```

### Advanced Configuration

```python
# Tiered thresholds based on query length
def get_dynamic_threshold(query_length):
    if query_length <= 3:        # Very short queries
        return 0.8               # Require higher similarity
    elif query_length <= 10:     # Medium queries
        return 0.75              # Standard threshold
    else:                        # Long queries
        return 0.7               # Slightly lower threshold
```

## Best Practices

- **Start conservative**: Begin with a threshold around 0.75-0.8
- **Analyze zero-result searches**: Identify queries that return no results
- **Monitor false positives**: Check for irrelevant documents in results
- **A/B test thresholds**: Compare user satisfaction with different settings
- **Consider query-specific thresholds**: Adjust based on query characteristics
- **Always prefer quality over quantity**: Better to return fewer, more relevant results

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No results for legitimate queries | Lower threshold slightly (e.g., 0.7 → 0.65) |
| Irrelevant results appearing | Raise threshold (e.g., 0.7 → 0.8) |
| Same document appearing for different queries | Increase document collection size or raise threshold |
| Short queries perform poorly | Implement query expansion or use higher thresholds for short queries |

## Related Documentation

- [Vector Search](./VectorSearch.md)
- [Document Processing](./DocumentProcessing.md)
- [Application Layer Chunking](./ApplicationLayerChunking.md)

## Next Steps

- Implement hybrid search combining semantic and keyword search
- Create dashboards to monitor search quality and zero-result rates
- Add a metadata enrichment pipeline to improve document findability
- Consider fine-tuning embedding models for your specific domain 