from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()

# Models for customer requests and responses
class CustomerPreference(BaseModel):
    key: str
    value: Any

class Customer(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    preferences: Optional[List[CustomerPreference]] = None

@router.get("/{customer_id}", response_model=Customer)
async def get_customer_by_id(customer_id: str):
    """
    Get customer information by ID.
    """
    # TODO: Implement customer lookup by ID
    # For now, return placeholder data
    return Customer(
        id=customer_id,
        name="John Doe",
        email="john.doe@example.com",
        phone="555-1234",
        preferences=[
            CustomerPreference(key="contact_method", value="email"),
            CustomerPreference(key="notification_frequency", value="weekly")
        ]
    )

@router.get("/by-product/{serial_number}", response_model=Customer)
async def get_customer_by_product_serial(serial_number: str):
    """
    Get customer information by product serial number.
    """
    # TODO: Implement customer lookup by product serial number
    # For now, return placeholder data
    return Customer(
        id="cust-456",
        name="Jane Smith",
        email="jane.smith@example.com",
        phone="555-5678",
        preferences=[
            CustomerPreference(key="contact_method", value="phone"),
            CustomerPreference(key="notification_frequency", value="daily")
        ]
    ) 