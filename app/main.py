# Initialize environment variables first
from app.config.init_env import initialize_environment
initialize_environment()

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
import logfire
from pathlib import Path

from app.config.settings import settings
from app.api.routes import router as api_router
from app.web import router as web_router

# Add Logfire startup logging
logfire.info("Application starting up", 
    app_name=settings.APP_NAME, 
    environment=settings.ENVIRONMENT,
    logfire_token_available=bool(os.environ.get("LOGFIRE_TOKEN")),
    python_version=os.environ.get("PYTHON_VERSION", "unknown")
)

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

# Add more Logfire logs
logfire.info("FastAPI app initialized", routes_count=len(app.routes))

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

logfire.info("All routes registered", 
    api_routes_count=len(api_router.routes),
    web_routes_count=len(web_router.routes)
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    logfire.info("Home page accessed", client_host=request.client.host)
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.get("/api-status")
async def api_status():
    """API status endpoint."""
    status_info = {
        "status": "online",
        "environment": settings.environment,
        "version": "0.1.0"
    }
    logfire.info("API status checked", **status_info)
    return status_info

@app.get("/debug/log-test")
async def test_logging():
    """Debug endpoint to test Logfire logging."""
    # Log at different levels
    logfire.debug("This is a debug message", source="log-test")
    logfire.info("This is an info message", source="log-test")
    logfire.warning("This is a warning message", source="log-test")
    logfire.error("This is an error message", source="log-test")
    
    # Log with structured data
    logfire.info(
        "Testing structured logging",
        source="log-test",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        random_value=123,
        nested_data={
            "key1": "value1",
            "key2": "value2"
        }
    )
    
    return JSONResponse({
        "status": "success",
        "message": "Log messages sent to Logfire",
        "logfire_token_available": bool(os.environ.get("LOGFIRE_TOKEN")),
        "logfire_project_url": os.environ.get("LOGFIRE_PROJECT_URL", "https://logfire-us.pydantic.dev/")
    })

if __name__ == "__main__":
    logfire.info("Starting uvicorn server", host="0.0.0.0", port=8000)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 