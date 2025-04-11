---
title: Document Processing Pipeline
description: Documentation for the document processing pipeline in the Support Agent project
date_created: 2025-04-09
last_updated: 2025-04-15
tags:
  - documents
  - embeddings
  - chunking
  - vector-search
sidebar_position: 3
---

# Document Processing Pipeline

## Overview

The Document Processing Pipeline handles the ingestion, transformation, and storage of knowledge documents for the Support Agent. This pipeline transforms raw text content into searchable vector embeddings that enable semantic retrieval.

The pipeline consists of four main stages:
1. **Text Extraction**: Extracting plain text from various document formats
2. **Text Chunking**: Breaking text into optimally sized chunks
3. **Embedding Generation**: Converting text chunks to vector embeddings
4. **Vector Storage**: Storing embeddings in a vector database for similarity search

> **Note:** Our system now uses the Application Layer Chunking implementation, which provides enhanced chunking capabilities and better integration with OpenAI. See [Application Layer Chunking](ApplicationLayerChunking.md) for details on this implementation.

## Architecture

The document processing system is implemented as a modular service that coordinates between OpenAI and Supabase:

```
app/
  services/
    document_processor.py  # Core document processing functions
    openai_service.py      # Embedding generation (via OpenAI)
    supabase_service.py    # Vector storage (via Supabase)
  utils/
    text_chunker.py        # Centralized chunking logic (new)
    embedding_pipeline.py  # Document → chunks → embeddings pipeline (new)
```

## Pipeline Stages

### 1. Text Extraction

The text extraction stage handles various document formats and converts them to plain text:

```python
from app.services.document_processor import extract_text_from_file

# Extract text from a PDF file
text = extract_text_from_file("document.pdf")

# Extract from other formats
from app.services.document_processor import extract_text_from_string
html_text = extract_text_from_string(html_content, content_type='html')
```

Supported formats include:
- Plain text (`.txt`)
- Markdown (`.md`)
- PDF (`.pdf`) - requires PyPDF2
- Word documents (`.docx`, `.doc`) - requires python-docx
- HTML (`.html`, `.htm`) - requires BeautifulSoup4

The extraction process removes non-text elements like scripts, styles, and formatting to produce clean, indexable text.

### 2. Text Chunking

The chunking stage splits documents into smaller, semantically meaningful segments:

```python
from app.services.document_processor import chunk_text

# Split text into chunks with overlap
chunks = chunk_text(
    text,
    chunk_size=1000,    # Maximum size of each chunk in characters
    chunk_overlap=200,  # Size of overlap between chunks
    separator='\n'      # Preferred boundary between chunks
)
```

Key features of the chunking system:
- **Configurable Size**: Customizable chunk size to optimize for vector embedding
- **Chunk Overlap**: Overlapping content helps maintain context across chunks
- **Semantic Boundaries**: Tries to split at natural paragraph boundaries
- **Context Preservation**: Ensures important context isn't lost during splitting

The chunk size is optimized for:
- Vector embedding token limits (typically 1536 tokens for OpenAI models)
- Retrieval granularity (smaller chunks are more precise but may lack context)
- Processing efficiency (larger chunks reduce the number of API calls)

### 3. Embedding Generation

The embedding stage converts text chunks into high-dimensional vector embeddings using OpenAI's embedding models:

```python
from app.services.openai_service import get_embeddings

# Generate embeddings for multiple chunks
embeddings = get_embeddings(chunks)
```

The embedding process:
- Uses OpenAI's `text-embedding-3-small` model (configurable)
- Produces 1536-dimensional vectors for each text chunk
- Handles API rate limiting and batch processing
- Includes automatic retries for transient failures

Embeddings capture the semantic meaning of text, enabling similarity-based retrieval that goes beyond simple keyword matching.

### 4. Vector Storage

The storage stage persists both the original document and its chunked embeddings in Supabase:

```python
from app.services.supabase_service import store_document, store_document_chunks

# Store document and get its ID
document = store_document(title, content, metadata)
document_id = document["id"]

# Store chunks with their embeddings
stored_chunks = store_document_chunks(document_id, chunks, embeddings, chunk_metadata)
```

The storage system:
- Maintains a link between chunks and their parent document
- Stores metadata with each chunk for filtering and context
- Uses pgvector's capabilities for efficient vector similarity search
- Structures data for easy retrieval and reconstruction

## Integrated Processing

For convenience, the pipeline provides integrated processing functions:

```python
from app.services.document_processor import process_document, process_file

# Process a document string
document, chunks = process_document(
    title="User Manual",
    content=html_content,
    content_type='html',
    metadata={"category": "manual", "version": "1.0"}
)

# Process a file
document, chunks = process_file(
    file_path="documentation.pdf",
    metadata={"department": "support"}
)
```

These functions handle the entire pipeline from extraction to storage, returning the created records for confirmation.

## Error Handling

The pipeline includes comprehensive error handling:
- Custom `DocumentProcessingError` exceptions with context
- Detailed logging at each processing stage
- Graceful degradation when optional dependencies are missing
- Input validation to prevent processing invalid content

## Performance Considerations

For optimal performance:
- Process documents in batches rather than individually
- Use appropriate chunk sizes (generally 500-1500 characters)
- Consider document preprocessing to remove irrelevant content
- Monitor embedding API usage for cost management

## Handling Different Document Types

### Knowledge Base Articles

For knowledge base articles, the default chunking strategy works well:

```python
document, chunks = process_document(
    title="Troubleshooting Guide",
    content=kb_article,
    metadata={"category": "troubleshooting", "product": "ProductX"}
)
```

### Long Technical Documents

For longer technical documents, consider:
- Smaller chunk sizes to improve specificity
- Include document structure in metadata
- Process hierarchically (sections, subsections)

```python
document, chunks = process_document(
    title="Technical Reference",
    content=technical_doc,
    chunk_size=800,
    chunk_overlap=150,
    metadata={"type": "technical", "audience": "developers"}
)
```

### Product Manuals

For product manuals with diverse content types:
- Process sections separately
- Add detailed metadata for filtering
- Adjust chunking by section type

## Next Steps

Future improvements to the document processing pipeline:
1. Automatic document type detection
2. Improved hierarchical chunking
3. Advanced preprocessing for noisy documents
4. Parallel processing for large document batches
5. Incremental updates to existing documents 