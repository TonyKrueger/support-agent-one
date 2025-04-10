from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.conversation_manager import ConversationManager
from app.services.chat_service import ChatService

router = APIRouter()

# Models for chat requests and responses
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    customer_id: Optional[str] = None
    product_serial: Optional[str] = None

class ChatResponse(BaseModel):
    message: ChatMessage
    sources: Optional[List[str]] = None
    conversation_id: str

# Get dependencies
def get_conversation_manager():
    return ConversationManager()

def get_chat_service():
    return ChatService()

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat with the support agent.
    """
    try:
        # Create a new conversation if one doesn't exist
        conversation_id = conversation_manager.create_conversation(
            customer_id=request.customer_id,
            product_id=request.product_serial
        )
        
        # Add previous messages to conversation if any
        for msg in request.messages[:-1]:  # Add all messages except the last one
            conversation_manager.add_message(
                conversation_id=conversation_id,
                role=msg.role,
                content=msg.content
            )
        
        # Get the last message (current query)
        current_message = request.messages[-1].content
        
        # Add user message to conversation
        conversation_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=current_message
        )
        
        # Retrieve relevant context for the query
        relevant_context = conversation_manager.retrieve_relevant_context(
            conversation_id=conversation_id,
            query=current_message
        )
        
        # Get formatted context for chat completion
        formatted_messages = conversation_manager.get_chat_context(conversation_id)
        
        # Process message with chat service
        raw_messages = [{"role": msg["role"], "content": msg["content"]} for msg in formatted_messages]
        response = await chat_service.process_message(
            messages=raw_messages,
            customer_id=request.customer_id,
            product_serial=request.product_serial
        )
        
        # Add assistant response to conversation
        conversation_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response["message"]["content"]
        )
        
        # Return formatted response
        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=response["message"]["content"]
            ),
            sources=response.get("suggested_documents", []),
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{customer_id}", response_model=List[ChatMessage])
async def get_chat_history(
    customer_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get the chat history for a specific customer.
    """
    try:
        history = await chat_service.get_conversation_history(customer_id)
        return [ChatMessage(role=msg["role"], content=msg["content"]) for msg in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 