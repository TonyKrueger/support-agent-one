-- Create vector similarity search function for document chunks
-- This function is used for semantic search on document embeddings

-- Create the match_document_chunks function
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