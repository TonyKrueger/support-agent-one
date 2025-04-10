from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import json
import os
from pathlib import Path

from app.services.document_service import DocumentService

# Set up templates
templates = Jinja2Templates(directory=str(Path("app/templates")))

router = APIRouter()

def get_document_service():
    """Dependency for DocumentService."""
    try:
        return DocumentService()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Document service unavailable")

@router.get("/", response_class=HTMLResponse)
async def documents_home(
    request: Request,
    document_service: DocumentService = Depends(get_document_service)
):
    """Document management home page."""
    documents = document_service.get_all_documents(limit=100)
    return templates.TemplateResponse(
        "documents/index.html", 
        {"request": request, "documents": documents}
    )

@router.get("/search", response_class=HTMLResponse)
async def search_documents_page(
    request: Request,
    query: Optional[str] = None,
    document_service: DocumentService = Depends(get_document_service)
):
    """Document search page."""
    results = []
    if query:
        results = document_service.search_documents(query)
    
    return templates.TemplateResponse(
        "documents/search.html", 
        {"request": request, "results": results, "query": query or ""}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_document_page(request: Request):
    """Create document page."""
    return templates.TemplateResponse(
        "documents/create.html", 
        {"request": request}
    )

@router.post("/create")
async def create_document(
    title: str = Form(...),
    content: str = Form(...),
    metadata: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """Handle document creation form submission."""
    metadata_dict = {}
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            # If not valid JSON, treat as plain text
            metadata_dict = {"notes": metadata}
    
    document_id = document_service.store_document(
        title=title,
        content=content,
        metadata=metadata_dict
    )
    
    if not document_id:
        raise HTTPException(status_code=500, detail="Failed to store document")
        
    return RedirectResponse(url=f"/documents/{document_id}", status_code=303)

@router.get("/upload", response_class=HTMLResponse)
async def upload_document_page(request: Request):
    """Upload document page."""
    return templates.TemplateResponse(
        "documents/upload.html", 
        {"request": request}
    )

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """Handle document upload form submission."""
    content = await file.read()
    
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a text document")
    
    # Use filename as title if not provided
    if not title:
        title = file.filename
    
    # Create metadata with file info
    metadata = {
        "filename": file.filename,
        "content_type": file.content_type
    }
    
    document_id = document_service.store_document(
        title=title,
        content=content_str,
        metadata=metadata
    )
    
    if not document_id:
        raise HTTPException(status_code=500, detail="Failed to store document")
        
    return RedirectResponse(url=f"/documents/{document_id}", status_code=303)

@router.get("/{document_id}", response_class=HTMLResponse)
async def view_document(
    request: Request,
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """View a single document."""
    document = document_service.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return templates.TemplateResponse(
        "documents/view.html", 
        {"request": request, "document": document}
    )

@router.get("/{document_id}/edit", response_class=HTMLResponse)
async def edit_document_page(
    request: Request,
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Edit document page."""
    document = document_service.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return templates.TemplateResponse(
        "documents/edit.html", 
        {"request": request, "document": document}
    )

@router.post("/{document_id}/edit")
async def update_document(
    document_id: str,
    title: str = Form(...),
    content: str = Form(...),
    metadata: Optional[str] = Form(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """Handle document edit form submission."""
    metadata_dict = None
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            # If not valid JSON, treat as plain text
            metadata_dict = {"notes": metadata}
    
    success = document_service.update_document(
        doc_id=document_id,
        title=title,
        content=content,
        metadata=metadata_dict
    )
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail="Document not found or update failed"
        )
        
    return RedirectResponse(url=f"/documents/{document_id}", status_code=303)

@router.post("/{document_id}/delete")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Handle document deletion."""
    success = document_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail="Document not found or delete failed"
        )
        
    return RedirectResponse(url="/documents", status_code=303) 