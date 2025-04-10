import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

from app.utils.search_utils import store_document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_text_file(file_path: Union[str, Path], doc_type: str = "document") -> Dict[str, Any]:
    """
    Process a text file and store it in the vector database
    
    Args:
        file_path: Path to the text file
        doc_type: Type of document
        
    Returns:
        The stored document record
    """
    try:
        file_path = Path(file_path)
        
        # Extract metadata
        metadata = {
            "title": file_path.stem,
            "source": str(file_path),
            "file_type": "text"
        }
        
        # Read content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Store document with embedding
        return store_document(content, doc_type, metadata)
    
    except Exception as e:
        logger.error(f"Error processing text file {file_path}: {str(e)}")
        raise

def process_json_file(
    file_path: Union[str, Path], 
    content_key: str = "content",
    title_key: Optional[str] = "title",
    doc_type: str = "document"
) -> List[Dict[str, Any]]:
    """
    Process a JSON file containing documents and store them in the vector database
    
    Args:
        file_path: Path to the JSON file
        content_key: Key for the document content in each JSON object
        title_key: Optional key for the document title in each JSON object
        doc_type: Type of document
        
    Returns:
        List of stored document records
    """
    try:
        file_path = Path(file_path)
        
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process each document in the JSON
        stored_docs = []
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            docs = data
        else:
            docs = [data]
        
        for i, doc in enumerate(docs):
            if content_key not in doc:
                logger.warning(f"Skipping document {i} - missing content key: {content_key}")
                continue
            
            content = doc[content_key]
            
            # Extract metadata
            metadata = {k: v for k, v in doc.items() if k != content_key}
            
            # Add file source info
            metadata.update({
                "source": str(file_path),
                "file_type": "json"
            })
            
            # Set title if not in original metadata
            if title_key and title_key in doc:
                metadata["title"] = doc[title_key]
            elif "title" not in metadata:
                metadata["title"] = f"{file_path.stem}_{i+1}"
            
            # Store document with embedding
            stored_doc = store_document(content, doc_type, metadata)
            stored_docs.append(stored_doc)
        
        return stored_docs
    
    except Exception as e:
        logger.error(f"Error processing JSON file {file_path}: {str(e)}")
        raise

def process_markdown_file(file_path: Union[str, Path], doc_type: str = "document") -> Dict[str, Any]:
    """
    Process a markdown file and store it in the vector database
    
    Args:
        file_path: Path to the markdown file
        doc_type: Type of document
        
    Returns:
        The stored document record
    """
    try:
        file_path = Path(file_path)
        
        # Read content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first heading if possible
        title = file_path.stem
        content_lines = content.split('\n')
        
        for line in content_lines:
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break
        
        # Extract metadata
        metadata = {
            "title": title,
            "source": str(file_path),
            "file_type": "markdown"
        }
        
        # Store document with embedding
        return store_document(content, doc_type, metadata)
    
    except Exception as e:
        logger.error(f"Error processing markdown file {file_path}: {str(e)}")
        raise

def process_directory(
    directory_path: Union[str, Path],
    doc_type: str = "document",
    recursive: bool = True,
    file_extensions: List[str] = ['.txt', '.md', '.json'],
    file_processor_map: Optional[Dict[str, Callable]] = None
) -> List[Dict[str, Any]]:
    """
    Process all supported files in a directory
    
    Args:
        directory_path: Path to the directory
        doc_type: Type of document
        recursive: Whether to recursively process subdirectories
        file_extensions: List of file extensions to process
        file_processor_map: Optional map of file extensions to processor functions
        
    Returns:
        List of stored document records
    """
    try:
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Default processor map
        if file_processor_map is None:
            file_processor_map = {
                '.txt': process_text_file,
                '.md': process_markdown_file,
                '.json': process_json_file
            }
        
        # Get files to process
        if recursive:
            files = list(directory_path.glob('**/*'))
        else:
            files = list(directory_path.glob('*'))
        
        # Filter to only supported files
        files = [f for f in files if f.is_file() and f.suffix.lower() in file_extensions]
        
        # Process each file
        all_docs = []
        for file_path in files:
            try:
                processor = file_processor_map.get(file_path.suffix.lower())
                if processor:
                    logger.info(f"Processing file: {file_path}")
                    result = processor(file_path, doc_type)
                    
                    # Handle both single doc and lists of docs
                    if isinstance(result, list):
                        all_docs.extend(result)
                    else:
                        all_docs.append(result)
                else:
                    logger.warning(f"No processor found for file: {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
        
        return all_docs
    
    except Exception as e:
        logger.error(f"Error processing directory {directory_path}: {str(e)}")
        raise 