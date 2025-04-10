# Document Management with Vector Similarity Search

## Overview
This module provides document management capabilities with vector similarity search using OpenAI embeddings and Supabase's pgvector extension.

## Features

- **Vector Similarity Search**: Search documents based on semantic similarity rather than keyword matching
- **Document Management**: Create, read, update, and delete documents through both API and web UI
- **Embedding Generation**: Automatically generate embeddings for documents using OpenAI's embedding models
- **File Upload**: Upload text files and automatically extract content and generate embeddings
- **Metadata Support**: Add and update custom metadata for each document

## Architecture

The document management system consists of:

1. **Database Schema**: 
   - `documents` table in Supabase with pgvector support
   - `match_documents` SQL function for similarity search
   
2. **Backend Services**:
   - `DocumentService`: Core service for document operations and vector search
   - FastAPI routes for API endpoints at `/api/v1/documents/*`
   - Web UI routes at `/documents/*`
   
3. **Frontend Templates**:
   - Document listing and search UI
   - Create/edit/view document forms
   - File upload interface

## Database Setup

The system requires the pgvector extension in Supabase for vector similarity search. The database setup includes:

1. Enable the pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
2. Create the documents table with vector column
3. Create the match_documents function for similarity search
4. Set up appropriate indexes for efficient vector queries

## API Endpoints

### Document Management

- `GET /api/v1/documents/`: List all documents
- `POST /api/v1/documents/`: Create a new document
- `GET /api/v1/documents/{document_id}`: Get a specific document
- `PUT /api/v1/documents/{document_id}`: Update a document
- `DELETE /api/v1/documents/{document_id}`: Delete a document

### Search

- `GET /api/v1/documents/search?query={query}&limit={limit}`: Search documents by similarity

### File Upload

- `POST /api/v1/documents/upload`: Upload a file to create a document

## Web UI

The system includes a web UI for document management:

- `/documents/`: Document listing page
- `/documents/search`: Search interface
- `/documents/create`: Create new document form
- `/documents/upload`: File upload form
- `/documents/{document_id}`: View document details
- `/documents/{document_id}/edit`: Edit document form

## How Vector Search Works

1. When a document is created or updated, its text content is sent to OpenAI's embedding model (text-embedding-3-small).
2. The resulting embedding vector (1536 dimensions) is stored in Supabase alongside the document content.
3. When searching, the user's query is converted to an embedding vector.
4. pgvector compares the query embedding to all document embeddings using cosine similarity.
5. Documents are returned ranked by similarity score, with a threshold to filter irrelevant results.

## Usage Examples

### Creating a Document via API

```python
import requests

data = {
    "title": "Network Troubleshooting Guide",
    "content": "Step 1: Check your internet connection...",
    "metadata": {
        "category": "troubleshooting",
        "tags": ["network", "connectivity"]
    }
}

response = requests.post("http://localhost:8000/api/v1/documents/", json=data)
document_id = response.json()["id"]
```

### Searching Documents via API

```python
import requests

query = "How do I fix my internet connection?"
response = requests.get(f"http://localhost:8000/api/v1/documents/search?query={query}")
results = response.json()["results"]

for doc in results:
    print(f"Document: {doc['title']} (Score: {doc['similarity']})")
    print(doc['content'][:100] + "...\n")
```

## Environment Variables

The document system requires the following environment variables:

```
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
OPENAI_API_KEY=your-openai-api-key
```

## Related Components

- [Document Processing](DocumentProcessing.md): Handles document extraction and chunking
- [Supabase Setup](Supabase.md): Database configuration and vector search setup
- [OpenAI Integration](OpenAI.md): Embedding model configuration 