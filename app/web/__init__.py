from fastapi import APIRouter

from app.web.documents import router as documents_router

# Create the main web router
router = APIRouter()

# Include all web routes
router.include_router(documents_router, prefix="/documents") 