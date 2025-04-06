from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

# Models for product requests and responses
class Product(BaseModel):
    id: str
    serial_number: str
    name: str
    description: str
    specifications: Dict[str, Any]

@router.get("/{serial_number}", response_model=Product)
async def get_product_by_serial(serial_number: str):
    """
    Get product information by serial number.
    """
    # TODO: Implement product lookup by serial number
    # For now, return placeholder data
    return Product(
        id="prod-123",
        serial_number=serial_number,
        name="Example Product",
        description="This is a placeholder product.",
        specifications={
            "weight": "1.2kg",
            "dimensions": "10x20x30cm",
            "color": "black"
        }
    ) 