import argparse
import logging
import os
from pathlib import Path

from app.utils.document_processor import (
    process_text_file,
    process_json_file, 
    process_markdown_file,
    process_directory
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Command-line utility for importing documents into the vector database"""
    
    parser = argparse.ArgumentParser(description="Import documents into the vector database")
    
    # Required arguments
    parser.add_argument("path", help="Path to file or directory to import")
    
    # Optional arguments
    parser.add_argument("--doc-type", default="document", 
                        help="Document type (default: document)")
    parser.add_argument("--recursive", action="store_true", 
                        help="Recursively process directories")
    parser.add_argument("--content-key", default="content", 
                        help="Key for content in JSON documents (default: content)")
    parser.add_argument("--title-key", default="title", 
                        help="Key for title in JSON documents (default: title)")
    parser.add_argument("--extensions", default=".txt,.md,.json", 
                        help="Comma-separated list of file extensions to process (default: .txt,.md,.json)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    path = Path(args.path)
    
    try:
        # Process directory
        if path.is_dir():
            extensions = args.extensions.split(",")
            logger.info(f"Processing directory: {path}")
            logger.info(f"File extensions: {extensions}")
            logger.info(f"Recursive: {args.recursive}")
            
            docs = process_directory(
                path,
                doc_type=args.doc_type,
                recursive=args.recursive,
                file_extensions=extensions
            )
            
            logger.info(f"Successfully processed {len(docs)} documents")
        
        # Process single file
        elif path.is_file():
            logger.info(f"Processing file: {path}")
            
            if path.suffix.lower() == '.txt':
                result = process_text_file(path, doc_type=args.doc_type)
                logger.info(f"Successfully processed text file: {result.get('id')}")
                
            elif path.suffix.lower() == '.md':
                result = process_markdown_file(path, doc_type=args.doc_type)
                logger.info(f"Successfully processed markdown file: {result.get('id')}")
                
            elif path.suffix.lower() == '.json':
                results = process_json_file(
                    path, 
                    content_key=args.content_key,
                    title_key=args.title_key,
                    doc_type=args.doc_type
                )
                logger.info(f"Successfully processed JSON file with {len(results)} documents")
            
            else:
                logger.error(f"Unsupported file type: {path.suffix}")
                return 1
        
        else:
            logger.error(f"Path not found: {path}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}", exc_info=args.verbose)
        return 1

if __name__ == "__main__":
    exit(main()) 