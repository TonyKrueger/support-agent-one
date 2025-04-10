from fastapi import APIRouter

from app.web.documents import router as documents_router
from app.web.chat import router as chat_router

# Create the main web router
router = APIRouter()

# Include all web routes
router.include_router(documents_router, prefix="/documents")
router.include_router(chat_router, prefix="/chat") 