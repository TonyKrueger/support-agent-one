from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

# Agent dependency types
@dataclass
class AgentDependencies:
    """Dependencies for the support agent."""
    customer_id: Optional[str] = None
    product_serial: Optional[str] = None
    conversation_history: List[dict] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []

# Agent result types
class SupportResult(BaseModel):
    """Structured result from the support agent."""
    support_response: str = Field(description="Response to the customer's query")
    needs_followup: bool = Field(description="Whether the query needs human followup", default=False)
    suggested_documents: List[str] = Field(description="IDs of relevant support documents", default_factory=list)
    
# Create the support agent
support_agent = Agent(
    'openai:gpt-4o',  # Using OpenAI's most capable model
    deps_type=AgentDependencies,
    result_type=SupportResult,
    system_prompt=(
        "You are a helpful support agent for our company's products. "
        "Answer customer questions accurately and concisely based on the available information. "
        "If you don't know the answer, admit it and suggest escalating to human support."
    )
)

# Document search tool
@support_agent.tool
async def search_documents(ctx: RunContext[AgentDependencies], query: str) -> List[dict]:
    """
    Search the knowledge base for relevant documents.
    
    Args:
        query: The search query string
        
    Returns:
        A list of relevant document snippets
    """
    # TODO: Implement actual vector search against Supabase
    # This is a placeholder implementation
    return [
        {
            "id": "doc-123",
            "title": "Example Document",
            "content": f"This is a placeholder document that would match the query: {query}",
            "relevance": 0.95
        }
    ]

# Product info lookup tool
@support_agent.tool
async def get_product_info(ctx: RunContext[AgentDependencies], serial_number: Optional[str] = None) -> dict:
    """
    Get product information by serial number.
    
    Args:
        serial_number: The product serial number to look up (if None, uses the one from context)
        
    Returns:
        Product information as a dictionary
    """
    # Use provided serial or the one from context
    serial = serial_number or ctx.deps.product_serial
    if not serial:
        return {"error": "No serial number provided"}
    
    # TODO: Implement actual product lookup from database
    # This is a placeholder implementation
    return {
        "serial": serial,
        "name": "Example Product",
        "description": "This is a placeholder product description",
        "specs": {
            "weight": "1.2kg",
            "dimensions": "10x20x30cm"
        }
    }

# Customer info lookup tool
@support_agent.tool
async def get_customer_info(ctx: RunContext[AgentDependencies], customer_id: Optional[str] = None) -> dict:
    """
    Get customer information by ID.
    
    Args:
        customer_id: The customer ID to look up (if None, uses the one from context)
        
    Returns:
        Customer information as a dictionary
    """
    # Use provided ID or the one from context
    cust_id = customer_id or ctx.deps.customer_id
    if not cust_id:
        return {"error": "No customer ID provided"}
    
    # TODO: Implement actual customer lookup from database
    # This is a placeholder implementation
    return {
        "id": cust_id,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-1234",
        "preferences": {
            "contact_method": "email",
            "notification_frequency": "weekly"
        }
    } 