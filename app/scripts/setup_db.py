#!/usr/bin/env python
"""
Setup script for Support Agent Database
Creates necessary PostgreSQL tables, extensions and functions for vector search
"""
import os
import logging
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.client import init_supabase_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database():
    """
    Setup the Supabase database with necessary extensions, tables and functions
    for vector similarity search using pgvector
    """
    try:
        # Initialize Supabase client
        supabase = init_supabase_client()
        logger.info("Connected to Supabase")

        # Enable pgvector extension
        logger.info("Creating pgvector extension...")
        supabase.query("CREATE EXTENSION IF NOT EXISTS vector;").execute()

        # Create documents table
        logger.info("Creating documents table...")
        supabase.query("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                embedding VECTOR(1536),
                type TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            );
        """).execute()

        # Create match_documents function for vector similarity search
        logger.info("Creating match_documents function...")
        supabase.query("""
            CREATE OR REPLACE FUNCTION match_documents(
                query_embedding VECTOR(1536),
                match_threshold FLOAT,
                match_count INT
            )
            RETURNS TABLE (
                id UUID,
                content TEXT,
                type TEXT,
                metadata JSONB,
                similarity FLOAT
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    documents.id,
                    documents.content,
                    documents.type,
                    documents.metadata,
                    1 - (documents.embedding <=> query_embedding) AS similarity
                FROM documents
                WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
                ORDER BY similarity DESC
                LIMIT match_count;
            END;
            $$;
        """).execute()

        # Add row level security policies
        logger.info("Setting up Row Level Security...")
        
        # Enable RLS
        supabase.query("""
            ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
        """).execute()

        # Create policy for authenticated users
        supabase.query("""
            CREATE POLICY "Allow authenticated access" 
            ON documents FOR ALL 
            TO authenticated 
            USING (true);
        """).execute()

        logger.info("Database setup completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1) 