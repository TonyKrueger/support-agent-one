from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, Body, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging

from app.services.document_service import DocumentService
from app.services.search_service import SearchService
from app.utils.text_chunker import ChunkingStrategy
from app.utils.embedding_pipeline import process_text

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Models for document requests and responses
class DocumentSearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity: float
    document_title: Optional[str] = None
    is_context: Optional[bool] = None
    context_position: Optional[str] = None
    context_for: Optional[int] = None

class DocumentSearchResponse(BaseModel):
    results: List[DocumentSearchResult]

class DocumentMetadata(BaseModel):
    metadata: Dict[str, Any] = {}

class DocumentCreate(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunking_strategy: Optional[str] = None
    content_type: Optional[str] = "text"

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    chunks_count: Optional[int] = 0

class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunking_strategy: Optional[str] = None
    replace_chunks: Optional[bool] = True

class DocumentChunk(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: Dict[str, Any]

class DocumentChunksResponse(BaseModel):
    chunks: List[DocumentChunk]
    total: int

class DocumentListResponse(BaseModel):
    documents: List[Dict[str, Any]]
    total: int

def get_document_service():
    """Dependency for DocumentService."""
    try:
        return DocumentService()
    except Exception as e:
        logger.error(f"Failed to initialize DocumentService: {str(e)}")
        raise HTTPException(status_code=500, detail="Document service unavailable")

def get_search_service():
    """Dependency for SearchService."""
    try:
        return SearchService()
    except Exception as e:
        logger.error(f"Failed to initialize SearchService: {str(e)}")
        raise HTTPException(status_code=500, detail="Search service unavailable")

@router.get("/search", response_model=DocumentSearchResponse)
async def search_documents(
    query: str,
    limit: Optional[int] = 5,
    include_context: Optional[bool] = False,
    strategy: Optional[str] = "semantic",
    metadata_filter: Optional[str] = None,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search support documents using vector similarity with advanced features.
    
    - **query**: The search query text
    - **limit**: Maximum number of results to return
    - **include_context**: Whether to include surrounding chunks for context
    - **strategy**: Search strategy (semantic, semantic_with_context, exact, hybrid)
    - **metadata_filter**: JSON string of metadata filters (e.g. {"category": "technical"})
    """
    try:
        # Parse metadata filter if provided
        filter_dict = None
        if metadata_filter:
            try:
                filter_dict = json.loads(metadata_filter)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata filter JSON format")
        
        # Use the appropriate search method based on strategy
        if strategy == "semantic_with_context" or include_context:
            results = search_service.search(
                query=query,
                limit=limit,
                include_context=True,
                metadata_filter=filter_dict
            )
        elif strategy in ["exact", "hybrid"]:
            results = search_service.search_by_strategy(
                query=query,
                strategy=strategy,
                limit=limit,
                metadata_filter=filter_dict
            )
        else:
            # Default semantic search
            results = search_service.search(
                query=query,
                limit=limit,
                include_context=False,
                metadata_filter=filter_dict
            )
        
        # Format results for response
        search_results = [
            DocumentSearchResult(
                id=doc.get("id", ""),
                title=doc.get("title", ""),
                content=doc.get("content", ""),
                similarity=doc.get("similarity", 0.0),
                document_title=doc.get("document_title", ""),
                is_context=doc.get("is_context", False),
                context_position=doc.get("context_position"),
                context_for=doc.get("context_for")
            ) for doc in results
        ]
        
        return DocumentSearchResponse(results=search_results)
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@router.post("/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Create a new document with content and optional metadata.
    
    Now uses the enhanced chunking pipeline with configurable parameters:
    - **chunk_size**: Size of text chunks (default is 1000)
    - **chunk_overlap**: Overlap between chunks (default is 200)
    - **chunking_strategy**: Strategy for chunking (simple, sentence, paragraph, markdown)
    - **content_type**: Type of content (text, html, markdown, etc.)
    """
    try:
        # Prepare chunking strategy from string if provided
        chunking_strategy = None
        if document.chunking_strategy:
            if hasattr(ChunkingStrategy, document.chunking_strategy.upper()):
                chunking_strategy = getattr(ChunkingStrategy, document.chunking_strategy.upper())
        
        # Add content type to metadata if not present
        metadata = document.metadata or {}
        if document.content_type and "content_type" not in metadata:
            metadata["content_type"] = document.content_type
        
        # Store document with our enhanced chunking pipeline
        stored_doc = document_service.store_document(
            title=document.title,
            content=document.content,
            metadata=metadata,
            chunk_size=document.chunk_size,
            chunk_overlap=document.chunk_overlap,
            chunking_strategy=chunking_strategy
        )
        
        if not stored_doc:
            raise HTTPException(status_code=500, detail="Failed to store document")
        
        # Get chunks count
        chunks = document_service.get_document_chunks(stored_doc["id"])
        chunks_count = len(chunks)
            
        # Format response
        return DocumentResponse(
            id=stored_doc["id"],
            title=stored_doc["title"],
            content=stored_doc["content"],
            metadata=stored_doc["metadata"],
            chunks_count=chunks_count
        )
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    metadata_json: Optional[str] = Form(None),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
    chunking_strategy: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document file and store it with chunking options.
    
    Uses the enhanced chunking pipeline with configurable parameters:
    - **chunk_size**: Size of text chunks
    - **chunk_overlap**: Overlap between chunks
    - **chunking_strategy**: Strategy for chunking (simple, sentence, paragraph, markdown)
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode("utf-8")
        
        # Parse metadata if provided
        metadata = {}
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
        
        # Add file info to metadata
        metadata["filename"] = file.filename
        metadata["content_type"] = file.content_type
        
        # Use filename as title if not provided
        if not title and file.filename:
            title = file.filename
        
        # Determine content type based on file extension
        content_type = "text"
        if file.filename:
            ext = file.filename.lower().split('.')[-1]
            if ext in ["md", "markdown"]:
                content_type = "markdown"
            elif ext in ["html", "htm"]:
                content_type = "html"
            
        metadata["content_type"] = content_type
        
        # Prepare chunking strategy from string if provided
        chunking_strategy_enum = None
        if chunking_strategy:
            if hasattr(ChunkingStrategy, chunking_strategy.upper()):
                chunking_strategy_enum = getattr(ChunkingStrategy, chunking_strategy.upper())
        
        # Store document with our enhanced chunking pipeline
        stored_doc = document_service.store_document(
            title=title,
            content=content_str,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy_enum
        )
        
        if not stored_doc:
            raise HTTPException(status_code=500, detail="Failed to store document")
        
        # Get chunks count
        chunks = document_service.get_document_chunks(stored_doc["id"])
        chunks_count = len(chunks)
            
        # Format response
        return DocumentResponse(
            id=stored_doc["id"],
            title=stored_doc["title"],
            content=stored_doc["content"],
            metadata=stored_doc["metadata"],
            chunks_count=chunks_count
        )
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    include_chunks_count: bool = False,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get a document by ID.
    
    - **include_chunks_count**: Whether to include the count of chunks
    """
    try:
        document = document_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        chunks_count = 0
        if include_chunks_count:
            chunks = document_service.get_document_chunks(document_id)
            chunks_count = len(chunks)
            
        return DocumentResponse(
            id=document.get("id", ""),
            title=document.get("title", ""),
            content=document.get("content", ""),
            metadata=document.get("metadata", {}),
            chunks_count=chunks_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")

@router.put("/{document_id}", response_model=Dict[str, Any])
async def update_document(
    document_id: str,
    update_data: DocumentUpdateRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Update an existing document.
    
    Now uses the enhanced chunking pipeline with configurable parameters:
    - **title**: New document title (optional)
    - **content**: New document content (optional)
    - **metadata**: New document metadata (optional)
    - **chunk_size**: Size of text chunks
    - **chunk_overlap**: Overlap between chunks
    - **chunking_strategy**: Strategy for chunking (simple, sentence, paragraph, markdown)
    - **replace_chunks**: Whether to replace existing chunks
    """
    try:
        # Verify document exists
        existing_doc = document_service.get_document_by_id(document_id)
        if not existing_doc:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Prepare chunking strategy from string if provided
        chunking_strategy = None
        if update_data.chunking_strategy:
            if hasattr(ChunkingStrategy, update_data.chunking_strategy.upper()):
                chunking_strategy = getattr(ChunkingStrategy, update_data.chunking_strategy.upper())
        
        # Update document with our enhanced pipeline
        success = document_service.update_document(
            doc_id=document_id,
            title=update_data.title,
            content=update_data.content,
            metadata=update_data.metadata,
            chunk_size=update_data.chunk_size,
            chunk_overlap=update_data.chunk_overlap,
            chunking_strategy=chunking_strategy,
            replace_chunks=update_data.replace_chunks
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update document")
        
        # Get updated document
        updated_doc = document_service.get_document_by_id(document_id)
        
        # Get chunks count
        chunks = document_service.get_document_chunks(document_id)
        updated_doc["chunks_count"] = len(chunks)
        
        return updated_doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@router.delete("/{document_id}", response_model=Dict[str, str])
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete a document by ID.
    """
    try:
        success = document_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found or delete failed")
            
        return {"status": "success", "message": f"Document {document_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    List all documents with pagination.
    """
    try:
        documents = document_service.get_all_documents(limit=limit, offset=offset)
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)  # In a real implementation, get actual total count
        )
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.get("/{document_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get all chunks for a document.
    """
    try:
        chunks = document_service.get_document_chunks(document_id)
        
        if not chunks and not document_service.get_document_by_id(document_id):
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Format chunks for response
        formatted_chunks = [
            DocumentChunk(
                id=chunk.get("id", ""),
                document_id=chunk.get("document_id", ""),
                chunk_index=chunk.get("chunk_index", 0),
                content=chunk.get("content", ""),
                metadata=chunk.get("metadata", {})
            ) for chunk in chunks
        ]
        
        return DocumentChunksResponse(
            chunks=formatted_chunks,
            total=len(chunks)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document chunks: {str(e)}")

@router.post("/{document_id}/chunks", response_model=Dict[str, Any])
async def create_document_chunks(
    document_id: str,
    chunk_size: int = Query(None, description="Size of chunks in characters"),
    chunk_overlap: int = Query(None, description="Overlap between chunks in characters"),
    chunking_strategy: str = Query(None, description="Chunking strategy to use"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Create chunks for an existing document using the enhanced chunking pipeline.
    
    - **chunk_size**: Size of chunks in characters (optional)
    - **chunk_overlap**: Overlap between chunks in characters (optional)
    - **chunking_strategy**: Strategy for chunking (simple, sentence, paragraph, markdown)
    """
    try:
        # Verify document exists
        document = document_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Check if document already has chunks
        existing_chunks = document_service.get_document_chunks(document_id)
        if existing_chunks:
            # Delete existing chunks first
            document_service.delete_document_chunks(document_id)
        
        # Prepare chunking strategy from string if provided
        chunking_strategy_enum = None
        if chunking_strategy:
            if hasattr(ChunkingStrategy, chunking_strategy.upper()):
                chunking_strategy_enum = getattr(ChunkingStrategy, chunking_strategy.upper())
        
        # Determine content type from metadata
        content_type = document.get("metadata", {}).get("content_type", "text")
        
        # Create chunks using the advanced chunking pipeline
        chunks = document_service.create_document_chunks(
            document_id=document_id,
            text=document.get("content", ""),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy_enum,
            content_type=content_type
        )
        
        if not chunks:
            raise HTTPException(status_code=500, detail="Failed to create document chunks")
        
        return {
            "document_id": document_id,
            "chunks_count": len(chunks),
            "message": f"Successfully created {len(chunks)} chunks for document"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating document chunks: {str(e)}")

@router.delete("/{document_id}/chunks", response_model=Dict[str, str])
async def delete_document_chunks(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete all chunks for a document.
    """
    try:
        # Check if document exists
        document = document_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Delete chunks
        success = document_service.delete_document_chunks(document_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to delete chunks for document {document_id}")
        
        return {
            "status": "success",
            "message": f"All chunks for document {document_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document chunks: {str(e)}") 