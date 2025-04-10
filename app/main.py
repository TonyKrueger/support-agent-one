import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from pathlib import Path

from app.config.settings import settings
from app.api.routes import router as api_router
from app.web import router as web_router

# Create templates directory if it doesn't exist
TEMPLATES_DIR = Path("app/templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

# Create static directory if it doesn't exist
STATIC_DIR = Path("app/static")
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Support Agent One",
    description="API for customer support agent with document search and customer history",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Set up templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API routes
app.include_router(api_router, prefix="/api")

# Include web routes
app.include_router(web_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.get("/api-status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "online",
        "environment": settings.environment,
        "version": "0.1.0"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 