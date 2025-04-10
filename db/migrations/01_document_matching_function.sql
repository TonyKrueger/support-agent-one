-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the match_documents function for vector similarity search
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  metadata JSONB,
  embedding vector(1536),
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.title,
    documents.content,
    documents.metadata,
    documents.embedding,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM
    documents
  WHERE
    1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY
    documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$; 