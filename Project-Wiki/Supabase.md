---
title: Supabase Setup and Configuration
description: Documentation for the Supabase database infrastructure used in the Support Agent project
date_created: 2025-04-09
last_updated: 2025-04-09
tags:
  - database
  - supabase
  - vector-search
sidebar_position: 1
---

# Supabase Setup and Configuration

## Overview

Supabase serves as the primary database infrastructure for the Support Agent project. We chose Supabase for several key reasons:

1. **PostgreSQL Foundation**: Built on PostgreSQL, providing a robust and reliable database system with advanced features
2. **Vector Search Capabilities**: Native support for pgvector extension, enabling similarity search for document embeddings
3. **Ease of Setup**: Quick provisioning with minimal configuration
4. **Built-in Auth**: Authentication system that can be leveraged for admin access
5. **RESTful API**: Automatic API generation for database tables
6. **Realtime Capabilities**: Support for real-time subscriptions if needed for chat functionality

## Project Setup

### Project Details

- **Project Name**: support-agent-db
- **Region**: us-east-2
- **Project URL**: https://qffbdxyquoyjdmkbgvxo.supabase.co
- **Project ID**: qffbdxyquoyjdmkbgvxo

### Extensions

The following PostgreSQL extensions were enabled for the project:

- **pgvector (vector)**: Enabled for vector similarity search, critical for finding relevant documents based on embedding similarity
- **uuid-ossp**: Used for UUID generation in database tables

## Database Schema

The database schema was designed to support the core functionality of the Support Agent, including customer information storage, product data, conversation history, and document retrieval.

### Customers Table

```sql
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  phone TEXT,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

This table stores customer information, using:
- UUID primary keys for security and distribution
- JSONB for flexible preference storage
- Timestamp tracking for record management

### Products Table

```sql
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  serial_number TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  specifications JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

The products table allows support agents to:
- Look up product details via serial number
- Access technical specifications stored in a flexible JSONB format
- Track product data changes over time

### Conversations Table

```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  customer_id UUID REFERENCES customers(id),
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ended_at TIMESTAMP WITH TIME ZONE,
  summary TEXT,
  satisfaction_score INTEGER
);
```

Used to track support conversations:
- Links to customers with foreign key references
- Records conversation duration
- Stores satisfaction score for analytics
- Includes a summary field for quick reference

### Messages Table

```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('user', 'assistant')),
  content TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);
```

Stores individual messages within conversations:
- CASCADE deletion ensures messages are removed with their parent conversation
- Role constraint ensures messages are properly identified as user or assistant
- Metadata field allows for additional message attributes (e.g., attachments, reactions)

### Documents Table

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  content TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

The primary storage for knowledge base documents:
- Stores complete document content
- Includes metadata for categorization and filtering
- Timestamps for version tracking

### Document Chunks Table

```sql
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  metadata JSONB DEFAULT '{}'
);
```

Critical for semantic search functionality:
- Chunks store smaller segments of documents for precise retrieval
- The embedding field (VECTOR type) stores 1536-dimensional OpenAI embeddings
- CASCADE deletion ensures chunks are removed with their parent document
- Direct relationship to original document for context retrieval

### Solutions Table

```sql
CREATE TABLE solutions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  problem_description TEXT NOT NULL,
  solution_content TEXT NOT NULL,
  related_products TEXT[],
  effectiveness_score FLOAT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

Repository for known solutions:
- Tracks effectiveness for solution ranking
- Array of related product identifiers enables product-specific solutions
- Timestamps for freshness evaluation

## Security Configuration

### Row Level Security (RLS)

Row Level Security policies have been enabled for all tables to ensure data security. The default policy allows authenticated access only, with specific policies to be refined based on user roles as the project develops.

Basic RLS policies include:
- Read-only access to documents and solutions for all authenticated users
- Write access to conversations and messages only for the user who created them
- Admin-only access for document management

## Connection Information

To connect to the Supabase instance from the application:

### Environment Variables

```
SUPABASE_URL=https://qffbdxyquoyjdmkbgvxo.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFmZmJkeHlxdW95amRta2JndnhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyNDYxODgsImV4cCI6MjA1OTgyMjE4OH0.ibMBFYiA145noyr3HpcmGs4zWmSN5lIIBM-MfW7ECic
```

### Python Client Example

```python
from supabase import create_client

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

# Example: Query customers
response = supabase.table('customers').select('*').execute()
```

## Vector Search Implementation

The document_chunks table includes a VECTOR(1536) field designed to store OpenAI embeddings. Vector similarity search can be performed using:

```sql
SELECT
  dc.content,
  d.title,
  d.id,
  (dc.embedding <=> query_embedding) as distance
FROM
  document_chunks dc
JOIN
  documents d ON d.id = dc.document_id
ORDER BY
  distance
LIMIT 5;
```

Where `query_embedding` is the vector representation of the user's query.

## Next Steps

1. **Testing Supabase Connection**: Implement and test the database connection from the application
2. **RLS Policy Refinement**: Define detailed access policies for different user roles
3. **Index Creation**: Optimize query performance with appropriate indexes
4. **Vector Search Testing**: Validate embedding storage and similarity search functionality

## Maintenance Considerations

- **Backups**: Supabase automatically creates daily backups; additional manual backups recommended
- **Monitoring**: Set up alerts for database performance and storage usage
- **Schema Migration**: Use migration files for all future schema changes to maintain version control 