#!/usr/bin/env python3
"""
Apply Supabase Migrations

This script applies SQL migrations to the Supabase database.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Get a configured Supabase client."""
    supabase_url = os.getenv("SUPABASE__URL")
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_URL")
    
    supabase_key = os.getenv("SUPABASE__SERVICE_KEY")
    if not supabase_key:
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and service key must be set in environment variables")
    
    return create_client(supabase_url, supabase_key)

def apply_migration(migration_file: str) -> bool:
    """
    Apply a SQL migration file to the Supabase database.
    
    Args:
        migration_file: Path to the SQL migration file
        
    Returns:
        True if successful
    """
    # Read the migration file
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
    except Exception as e:
        logger.error(f"Failed to read migration file: {str(e)}")
        return False
    
    # Get Supabase client
    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return False
    
    # Apply the migration
    try:
        logger.info(f"Applying migration: {migration_file}")
        
        # Execute the raw SQL
        response = supabase.rpc("pgadmin_exec_sql", {"sql": sql}).execute()
        
        logger.info(f"Migration applied successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to apply migration: {str(e)}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Apply Supabase migrations")
    parser.add_argument("file", help="SQL migration file to apply")
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"Migration file not found: {args.file}")
        sys.exit(1)
    
    success = apply_migration(args.file)
    
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 