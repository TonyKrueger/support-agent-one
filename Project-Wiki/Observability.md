---
title: Observability System
description: Documentation for the system observability, metrics collection, and performance tracking
date_created: 2025-04-17
last_updated: 2025-04-17
tags:
  - observability
  - metrics
  - performance
  - logging
  - monitoring
sidebar_position: 3.5
---

# Observability System

## Overview

The observability system provides comprehensive monitoring, metrics collection, and performance tracking for document processing operations. It enables detailed insights into chunking operations, embedding generation, search performance, and pipeline stages to optimize system performance and diagnose issues.

## Key Features

- **Metrics Collection**: Counters, gauges, and histograms for all key operations
- **Performance Tracking**: Decorators to measure function performance
- **Pipeline Stage Monitoring**: Track multi-stage pipeline execution
- **Structured Logging**: Contextual logging for all operations
- **API Endpoints**: REST endpoints to access metrics

## Implementation Details

### Observability Components

The observability system is built around four main components:

```
app/
  utils/
    observability.py       # Core metrics and tracking utilities
    logger.py              # Enhanced structured logging
  api/v1/
    metrics.py             # API endpoints for metrics access
```

### Metrics Classes

The system provides specialized classes for different types of operations:

```python
from app.utils.observability import ChunkingMetrics, EmbeddingMetrics, SearchMetrics

# Track chunking operation
ChunkingMetrics.track_chunking_operation(
    operation="create",
    document_id="doc-123",
    start_time=start,
    end_time=end,
    chunks_count=5,
    tokens_count=2500,
    strategy="markdown"
)

# Track embedding generation
EmbeddingMetrics.track_embedding_generation(
    document_id="doc-123",
    start_time=start,
    end_time=end,
    chunks_count=5,
    tokens_count=2500,
    model="text-embedding-3-small"
)

# Track search operation
SearchMetrics.track_search_operation(
    query_text="How to configure API?",
    start_time=start,
    end_time=end,
    results_count=3,
    strategy="semantic"
)
```

### Performance Tracking Decorator

The `track_performance` decorator makes it easy to monitor function performance:

```python
from app.utils.observability import track_performance

@track_performance(component="document", operation="store")
def store_document(self, title, content, metadata=None):
    # Function implementation
    # Performance is automatically tracked
    return stored_document
```

This decorator:
- Records execution time
- Tracks success/failure rates
- Logs context-rich information
- Updates metrics counters and histograms

### Pipeline Tracking

For multi-stage operations, the `PipelineTracker` provides step-by-step monitoring:

```python
from app.utils.observability import PipelineTracker

# Start tracking a pipeline
context = PipelineTracker.start_pipeline(
    document_id="doc-123",
    pipeline_name="document_processing"
)

# Track each stage
PipelineTracker.start_stage(context, "extraction")
# Extraction logic here
PipelineTracker.end_stage(context, success=True)

PipelineTracker.start_stage(context, "chunking")
# Chunking logic here
PipelineTracker.end_stage(context, success=True, metrics={"chunks_count": 5})

PipelineTracker.start_stage(context, "embedding_generation")
# Embedding logic here
PipelineTracker.end_stage(context, success=True, metrics={"embeddings_count": 5})

# End pipeline tracking
PipelineTracker.end_pipeline(context, success=True)
```

### Metrics Storage

The system stores metrics in three categories:

- **Counters**: Monotonically increasing values (operations count, error count)
- **Gauges**: Current point-in-time values
- **Histograms**: Distribution of values with statistics (min, max, avg)

```python
from app.utils.observability import increment_counter, set_gauge, add_to_histogram

# Increment operation counter
increment_counter("document.creation.count")

# Track error rate
increment_counter("document.creation.error_count")

# Record operation duration
add_to_histogram("document.creation.duration", duration_seconds)

# Set current queue size
set_gauge("document.processing_queue.size", 5)
```

## API Access

Metrics are accessible through REST API endpoints:

```
GET /api/v1/metrics/            # All system metrics
GET /api/v1/metrics/chunking    # Chunking-related metrics
GET /api/v1/metrics/embedding   # Embedding-related metrics
GET /api/v1/metrics/search      # Search-related metrics 
GET /api/v1/metrics/pipeline    # Pipeline-related metrics
DELETE /api/v1/metrics/         # Reset all metrics
```

Example response:

```json
{
  "counters": {
    "chunking.create.count": 25,
    "chunking.update.count": 12,
    "embedding.generation.count": 37,
    "search.semantic.count": 150
  },
  "gauges": {
    "system.active_tasks": 3
  },
  "histograms": {
    "chunking.create.duration": {
      "count": 25,
      "min": 0.12,
      "max": 1.45,
      "avg": 0.35,
      "latest": 0.28
    },
    "search.semantic.duration": {
      "count": 150,
      "min": 0.05,
      "max": 0.75,
      "avg": 0.22,
      "latest": 0.18
    }
  },
  "timestamp": "2025-04-17T14:30:45.123456"
}
```

## Integration with Document Processing

The observability system is integrated with the document processing pipeline:

1. **Chunking**: Tracks performance of chunking operations
2. **Embedding Generation**: Monitors token usage and API performance 
3. **Storage Operations**: Measures database write performance
4. **Search Operations**: Analyzes search latency and result quality

## Best Practices

- **Use Standard Metric Names**: Follow the `component.operation.metric_type` naming convention
- **Track Business Metrics**: Monitor user-focused metrics like search success rates
- **Set Alerts**: Configure alerts for critical thresholds
- **Periodic Analysis**: Regularly analyze performance trends
- **Include Context**: Always include relevant context in logging calls

## Troubleshooting

Common issues and their solutions:

| Issue | Solution |
|-------|----------|
| Missing metrics | Check the component is properly instrumented with tracking calls |
| High latency in operations | Use pipeline tracking to identify slow stages |
| Increased error rates | Check error metrics and detailed logs for specific error types |
| Memory growth | Periodically reset histograms if storing many values |

## Related Documentation

- [Application Layer Chunking](./ApplicationLayerChunking.md)
- [Document Processing](./DocumentProcessing.md)
- [Vector Search](./VectorSearch.md)

## Next Steps

- Configure alerts based on metrics thresholds
- Set up a monitoring dashboard
- Implement periodic reports on system performance 