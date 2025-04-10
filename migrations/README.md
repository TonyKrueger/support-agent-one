# Database Migrations

This directory contains SQL migrations for the Supabase database that powers the Support Agent One application.

## Fix for "match_document_chunks function not found" Error

If you encounter an error like:

```
ERROR: Supabase error searching similar chunks: {'code': 'PGRST202', 'details': 'Searched for the function public.match_document_chunks with parameters match_count, match_threshold, query_embedding or with a single unnamed json/jsonb parameter, but no matches were found in the schema cache.', 'hint': None, 'message': 'Could not find the function public.match_document_chunks(match_count, match_threshold, query_embedding) in the schema cache'}
```

This means your Supabase database is missing the required database function for vector similarity search. Follow these steps to fix it:

### Option 1: Using the Supabase Dashboard

1. Log in to your [Supabase Dashboard](https://app.supabase.com)
2. Go to your project > SQL Editor
3. Create a new query
4. Copy the contents of `setup_document_search.sql` into the SQL editor
5. Execute the query

### Option 2: Using the Migration Script

1. Make sure your `.env` file has the correct Supabase credentials:
   ```
   SUPABASE__URL=your_supabase_url
   SUPABASE__SERVICE_KEY=your_supabase_service_key
   ```

2. Run the migration script:
   ```bash
   python scripts/apply_migration.py migrations/setup_document_search.sql
   ```

## Migration Files

- `create_match_document_chunks_function.sql`: Creates only the vector search function
- `setup_document_search.sql`: Comprehensive setup of all document search infrastructure

## Troubleshooting

If you encounter permission errors when running the migrations, ensure:

1. You're using the service key (not the anon key) for Supabase
2. The user associated with the service key has permissions to create extensions and functions

## Manual SQL Execution

If the above options don't work, you can use the `pgadmin_exec_sql` function directly from your application:

```python
from app.services.supabase_service import get_supabase_client

# Read the SQL file
with open("migrations/setup_document_search.sql", "r") as f:
    sql = f.read()

# Execute the SQL
supabase = get_supabase_client()
response = supabase.rpc("pgadmin_exec_sql", {"sql": sql}).execute()
``` 