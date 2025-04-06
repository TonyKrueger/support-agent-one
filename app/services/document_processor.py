import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import logfire
from openai import OpenAI
from PyPDF2 import PdfReader
from supabase import create_client

from app.config.settings import settings


class DocumentProcessor:
    """
    Service for processing and storing documents in the vector database.
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.supabase = create_client(settings.supabase_url, settings.supabase_key)
        logfire.info("Document processor initialized")
    
    async def process_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a document and store it in the vector database.
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata for the document
            
        Returns:
            The document ID
        """
        if metadata is None:
            metadata = {}
        
        # Extract text from the document
        document_text = self._extract_text(file_path)
        
        # Create document record in the database
        doc_id = await self._create_document_record(file_path.name, metadata)
        
        # Split text into chunks
        chunks = self._split_text(document_text)
        
        # Generate embeddings and store chunks
        await self._process_chunks(doc_id, chunks)
        
        return doc_id
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from a document file."""
        # Get file extension
        extension = file_path.suffix.lower()
        
        # Extract text based on file type
        if extension == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif extension in ['.txt', '.md']:
            return file_path.read_text(encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF file."""
        text = ""
        with open(file_path, 'rb') as f:
            pdf = PdfReader(f)
            for page in pdf.pages:
                text += page.extract_text() + "\n\n"
        return text
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        if len(text) <= chunk_size:
            chunks.append(text)
        else:
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                chunks.append(chunk)
        return chunks
    
    async def _create_document_record(self, filename: str, metadata: Dict[str, Any]) -> str:
        """Create a document record in the database."""
        # TODO: Implement actual database insertion
        logfire.info("Creating document record", filename=filename, metadata=metadata)
        return "doc-" + os.urandom(4).hex()
    
    async def _process_chunks(self, doc_id: str, chunks: List[str]) -> None:
        """Process text chunks, generate embeddings, and store in the database."""
        for i, chunk in enumerate(chunks):
            # Generate embedding
            response = self.openai_client.embeddings.create(
                input=chunk,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            
            # Store chunk with embedding
            await self._store_chunk(doc_id, chunk, embedding, {"chunk_index": i})
    
    async def _store_chunk(self, doc_id: str, chunk: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        """Store a text chunk with its embedding in the vector database."""
        # TODO: Implement actual vector database insertion
        logfire.info("Storing document chunk", doc_id=doc_id, chunk_length=len(chunk), metadata=metadata) 