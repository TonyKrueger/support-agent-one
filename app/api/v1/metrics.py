"""
Metrics API endpoints for retrieving observability data.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.utils.observability import get_metrics, reset_metrics

# Configure router
router = APIRouter()

# Response models
class MetricsResponse(BaseModel):
    counters: Dict[str, int]
    gauges: Dict[str, float]
    histograms: Dict[str, Dict[str, Any]]
    timestamp: str

@router.get("/", response_model=MetricsResponse)
async def get_system_metrics():
    """
    Get all current metrics for the system.
    
    Returns metrics for:
    - Document chunking operations
    - Embedding generation
    - Search operations
    - Pipeline performance
    """
    try:
        # Retrieve metrics from the observability system
        metrics_data = get_metrics()
        return metrics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.delete("/", response_model=Dict[str, str])
async def reset_system_metrics():
    """
    Reset all metrics counters to zero.
    
    Use with caution as this will clear all collected metrics data.
    """
    try:
        reset_metrics()
        return {"status": "success", "message": "All metrics have been reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting metrics: {str(e)}")

@router.get("/chunking", response_model=Dict[str, Any])
async def get_chunking_metrics():
    """
    Get metrics specifically related to document chunking operations.
    """
    try:
        # Get all metrics and filter for chunking-related ones
        all_metrics = get_metrics()
        
        chunking_metrics = {
            "counters": {k: v for k, v in all_metrics["counters"].items() if k.startswith("chunking.")},
            "histograms": {k: v for k, v in all_metrics["histograms"].items() if k.startswith("chunking.")},
            "timestamp": all_metrics["timestamp"]
        }
        
        return chunking_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chunking metrics: {str(e)}")

@router.get("/embedding", response_model=Dict[str, Any])
async def get_embedding_metrics():
    """
    Get metrics specifically related to embedding generation.
    """
    try:
        # Get all metrics and filter for embedding-related ones
        all_metrics = get_metrics()
        
        embedding_metrics = {
            "counters": {k: v for k, v in all_metrics["counters"].items() if k.startswith("embedding.")},
            "histograms": {k: v for k, v in all_metrics["histograms"].items() if k.startswith("embedding.")},
            "timestamp": all_metrics["timestamp"]
        }
        
        return embedding_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving embedding metrics: {str(e)}")

@router.get("/search", response_model=Dict[str, Any])
async def get_search_metrics():
    """
    Get metrics specifically related to search operations.
    """
    try:
        # Get all metrics and filter for search-related ones
        all_metrics = get_metrics()
        
        search_metrics = {
            "counters": {k: v for k, v in all_metrics["counters"].items() if k.startswith("search.")},
            "histograms": {k: v for k, v in all_metrics["histograms"].items() if k.startswith("search.")},
            "timestamp": all_metrics["timestamp"]
        }
        
        return search_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving search metrics: {str(e)}")

@router.get("/pipeline", response_model=Dict[str, Any])
async def get_pipeline_metrics():
    """
    Get metrics specifically related to pipeline operations.
    """
    try:
        # Get all metrics and filter for pipeline-related ones
        all_metrics = get_metrics()
        
        pipeline_metrics = {
            "counters": {k: v for k, v in all_metrics["counters"].items() if k.startswith("pipeline.")},
            "histograms": {k: v for k, v in all_metrics["histograms"].items() if k.startswith("pipeline.")},
            "timestamp": all_metrics["timestamp"]
        }
        
        return pipeline_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving pipeline metrics: {str(e)}") 