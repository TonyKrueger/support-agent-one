from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging

from app.services.document_service import DocumentService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Models for document requests and responses
class DocumentSearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity: float

class DocumentSearchResponse(BaseModel):
    results: List[DocumentSearchResult]

class DocumentMetadata(BaseModel):
    metadata: Dict[str, Any] = {}

class DocumentCreate(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]

class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

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

@router.get("/search", response_model=DocumentSearchResponse)
async def search_documents(
    query: str, 
    limit: Optional[int] = 5,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Search support documents using vector similarity.
    """
    try:
        results = document_service.search_documents(query, limit)
        
        # Format results for response
        search_results = [
            DocumentSearchResult(
                id=doc.get("id", ""),
                title=doc.get("title", ""),
                content=doc.get("content", ""),
                similarity=doc.get("similarity", 0.0)
            ) for doc in results
        ]
        
        return DocumentSearchResponse(results=search_results)
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@router.post("/", response_model=Dict[str, str])
async def create_document(
    document: DocumentCreate,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Create a new document with content and optional metadata.
    """
    try:
        document_id = document_service.store_document(
            title=document.title,
            content=document.content,
            metadata=document.metadata
        )
        
        if not document_id:
            raise HTTPException(status_code=500, detail="Failed to store document")
            
        return {"id": document_id}
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")

@router.post("/upload", response_model=Dict[str, str])
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    metadata_json: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document file and store it.
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
        
        # Store document
        document_id = document_service.store_document(
            title=title,
            content=content_str,
            metadata=metadata
        )
        
        if not document_id:
            raise HTTPException(status_code=500, detail="Failed to store document")
            
        return {"id": document_id}
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get a document by ID.
    """
    try:
        document = document_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
            
        return DocumentResponse(
            id=document.get("id", ""),
            title=document.get("title", ""),
            content=document.get("content", ""),
            metadata=document.get("metadata", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")

@router.put("/{document_id}", response_model=Dict[str, str])
async def update_document(
    document_id: str,
    update_data: DocumentUpdateRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Update an existing document.
    """
    try:
        success = document_service.update_document(
            doc_id=document_id,
            title=update_data.title,
            content=update_data.content,
            metadata=update_data.metadata
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found or update failed")
            
        return {"status": "success", "message": f"Document {document_id} updated successfully"}
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