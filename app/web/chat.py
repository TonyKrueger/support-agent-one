from fastapi import APIRouter, Request, Depends, HTTPException, Form, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional
import json
import uuid
from pathlib import Path

from app.services.conversation_manager import ConversationManager

# Set up templates
templates = Jinja2Templates(directory=str(Path("app/templates")))

router = APIRouter()

# Store active conversation managers
active_conversations: Dict[str, ConversationManager] = {}

def get_conversation_manager(conversation_id: Optional[str] = None) -> ConversationManager:
    """Dependency for ConversationManager."""
    try:
        # Create new conversation if not provided
        if not conversation_id or conversation_id not in active_conversations:
            manager = ConversationManager()
            if not conversation_id:
                conversation_id = manager.create_conversation()
            active_conversations[conversation_id] = manager
        
        return active_conversations[conversation_id]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation manager unavailable: {str(e)}")

@router.get("/", response_class=HTMLResponse)
async def chat_home(request: Request):
    """Chat interface home page."""
    conversation_id = str(uuid.uuid4())
    return templates.TemplateResponse(
        "chat/index.html", 
        {"request": request, "conversation_id": conversation_id}
    )

@router.post("/send")
async def send_message(
    conversation_id: str = Form(...),
    message: str = Form(...),
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """Handle sending a message via traditional HTTP request."""
    try:
        # Add user message to conversation
        conversation_manager.add_message(conversation_id, "user", message)
        
        # Get relevant context
        context = conversation_manager.retrieve_relevant_context(conversation_id, message)
        
        # Get full context for chat completion
        chat_context = conversation_manager.get_chat_context(conversation_id)
        
        # TODO: Call AI model for response
        # For now, use a placeholder response
        ai_response = f"I received your message: '{message}'. This is a placeholder response."
        
        # Add assistant response to conversation
        conversation_manager.add_message(conversation_id, "assistant", ai_response)
        
        # Get conversation history for display
        history = conversation_manager.get_conversation_history(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "message": ai_response,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """Handle WebSocket connection for real-time chat."""
    try:
        await websocket.accept()
        
        # Get or create conversation manager
        if conversation_id not in active_conversations:
            manager = ConversationManager()
            if conversation_id == "new":
                conversation_id = manager.create_conversation()
            active_conversations[conversation_id] = manager
        
        conversation_manager = active_conversations[conversation_id]
        
        # Send initial conversation data
        await websocket.send_json({
            "type": "connection_established",
            "conversation_id": conversation_id
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process user message
            user_message = message_data.get("message", "")
            
            # Add user message to conversation
            conversation_manager.add_message(conversation_id, "user", user_message)
            
            # Get relevant context
            context = conversation_manager.retrieve_relevant_context(conversation_id, user_message)
            
            # TODO: Call AI model for response
            # For now, use a placeholder response
            ai_response = f"I received your message: '{user_message}'. This is a placeholder response."
            
            # Add assistant response to conversation
            conversation_manager.add_message(conversation_id, "assistant", ai_response)
            
            # Send response to client
            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": ai_response,
                "conversation_id": conversation_id
            })
            
    except WebSocketDisconnect:
        # Handle client disconnect
        pass
    except Exception as e:
        # Handle other errors
        if websocket.client_state.CONNECTED:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })

@router.get("/history/{conversation_id}", response_class=HTMLResponse)
async def conversation_history(
    request: Request,
    conversation_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """View conversation history."""
    try:
        history = conversation_manager.get_conversation_history(conversation_id)
        
        return templates.TemplateResponse(
            "chat/history.html", 
            {"request": request, "history": history, "conversation_id": conversation_id}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {str(e)}")

@router.post("/end/{conversation_id}")
async def end_conversation(
    conversation_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """End a conversation and archive it."""
    try:
        result = conversation_manager.end_conversation(conversation_id)
        
        # Remove from active conversations
        if conversation_id in active_conversations:
            del active_conversations[conversation_id]
            
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error ending conversation: {str(e)}") 