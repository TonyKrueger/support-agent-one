from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.products import router as products_router
from app.api.v1.customers import router as customers_router
from app.api.v1.documents import router as documents_router
from app.api.v1.metrics import router as metrics_router

# Create the main API router
router = APIRouter()

# Include all API routes
router.include_router(chat_router, prefix="/v1/chat", tags=["Chat"])
router.include_router(products_router, prefix="/v1/products", tags=["Products"])
router.include_router(customers_router, prefix="/v1/customers", tags=["Customers"])
router.include_router(documents_router, prefix="/v1/documents", tags=["Documents"])
router.include_router(metrics_router, prefix="/v1/metrics", tags=["Metrics"]) 