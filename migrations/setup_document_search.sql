-- Setup document search infrastructure in Supabase
-- This migration creates the necessary tables, extensions, and functions for vector search

-- Enable necessary extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create documents table if it doesn't exist
CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  title text NOT NULL,
  content text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  metadata jsonb DEFAULT '{}'::jsonb
);

-- Create document_chunks table if it doesn't exist
CREATE TABLE IF NOT EXISTS document_chunks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id uuid REFERENCES documents(id) ON DELETE CASCADE,
  content text NOT NULL,
  embedding vector(1536),  -- OpenAI embeddings are 1536 dimensions
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now()
);

-- Create index for faster embedding similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create vector similarity search function
CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding vector,
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.content,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM
    document_chunks dc
  WHERE
    1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY
    dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create a simpler function that doesn't require vector input
CREATE OR REPLACE FUNCTION match_documents(
  query_text text,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  title text,
  content text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    d.content,
    similarity
  FROM
    documents d
  JOIN (
    SELECT document_id, MAX(similarity) as similarity
    FROM match_document_chunks(query_embedding => $1, match_count => $2)
    GROUP BY document_id
  ) matches ON d.id = matches.document_id
  ORDER BY
    matches.similarity DESC;
END;
$$;

-- Add RLS policies to allow public read access
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Public can read documents and chunks
CREATE POLICY "Public can read documents" ON documents
  FOR SELECT USING (true);

CREATE POLICY "Public can read document chunks" ON document_chunks
  FOR SELECT USING (true);

-- Only authenticated users can insert/update/delete
CREATE POLICY "Authenticated users can insert documents" ON documents
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can update documents" ON documents
  FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can delete documents" ON documents
  FOR DELETE USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert document chunks" ON document_chunks
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can update document chunks" ON document_chunks
  FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can delete document chunks" ON document_chunks
  FOR DELETE USING (auth.role() = 'authenticated'); 