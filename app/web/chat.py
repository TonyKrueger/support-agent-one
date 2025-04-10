from fastapi import APIRouter, Request, Depends, HTTPException, Form, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional
import json
import uuid
import logfire
from pathlib import Path

from app.services.conversation_manager import ConversationManager
from app.services.openai_service import get_chat_completion, moderate_content, OpenAIServiceError, RateLimitExceededError
from app.config.ai_settings import ai_settings

# Set up templates
templates = Jinja2Templates(directory=str(Path("app/templates")))

router = APIRouter()

# Store active conversation managers
active_conversations: Dict[str, ConversationManager] = {}

def get_conversation_manager(conversation_id: Optional[str] = None) -> ConversationManager:
    """Dependency for ConversationManager."""
    try:
        # Log conversation ID for debugging
        logfire.debug("get_conversation_manager called", 
                     conversation_id=conversation_id, 
                     active_conversations_count=len(active_conversations),
                     active_conversation_ids=list(active_conversations.keys()))
        
        # Create new conversation if not provided
        if not conversation_id or conversation_id not in active_conversations:
            manager = ConversationManager(max_conversation_length=ai_settings.max_conversation_messages)
            if not conversation_id:
                conversation_id = manager.create_conversation()
                logfire.info("Created new conversation", new_conversation_id=conversation_id)
            else:
                logfire.info("Initializing manager for existing conversation ID", conversation_id=conversation_id)
            active_conversations[conversation_id] = manager
        
        return active_conversations[conversation_id]
    except Exception as e:
        logfire.error("Error in get_conversation_manager", 
                     error=str(e), 
                     conversation_id=conversation_id,
                     active_conversations=list(active_conversations.keys()))
        raise HTTPException(status_code=500, detail=f"Conversation manager unavailable: {str(e)}")

@router.get("/", response_class=HTMLResponse)
async def chat_home(request: Request):
    """Chat interface home page."""
    conversation_id = str(uuid.uuid4())
    logfire.info("Generating chat home page with new conversation", 
                conversation_id=conversation_id,
                client_ip=request.client.host)
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
        logfire.info("Message received", 
                    conversation_id=conversation_id, 
                    message_length=len(message))
        
        # Check for harmful content if moderation is enabled
        if ai_settings.moderation_enabled:
            is_harmful, categories = moderate_content(message)
            if is_harmful:
                logfire.warning("Message moderated", 
                               conversation_id=conversation_id,
                               categories=categories)
                return {
                    "conversation_id": conversation_id,
                    "message": "I'm sorry, but I cannot respond to this message as it may contain harmful content.",
                    "moderated": True
                }
            
        # Add user message to conversation
        try:
            conversation_manager.add_message(conversation_id, "user", message)
            logfire.debug("User message added to conversation", conversation_id=conversation_id)
        except ValueError as e:
            logfire.error("Failed to add message to conversation", 
                         error=str(e), 
                         conversation_id=conversation_id,
                         active_conversation_ids=list(active_conversations.keys()))
            raise HTTPException(status_code=400, detail=str(e))
        
        # Get relevant context
        context = conversation_manager.retrieve_relevant_context(
            conversation_id, 
            message,
            limit=5,  # Could be configurable
            threshold=0.7  # Could be configurable
        )
        
        # Get full context for chat completion
        chat_context = conversation_manager.get_chat_context(conversation_id)
        
        # Call AI model for response using OpenAI service with settings
        logfire.info("Requesting chat completion", 
                    conversation_id=conversation_id,
                    model=ai_settings.model,
                    temperature=ai_settings.temperature)
        
        ai_response = get_chat_completion(
            messages=chat_context,
            temperature=ai_settings.temperature,
            max_tokens=ai_settings.max_tokens,
            model=ai_settings.model
        )
        
        # Add assistant response to conversation
        conversation_manager.add_message(conversation_id, "assistant", ai_response)
        
        # Get conversation history for display
        history = conversation_manager.get_conversation_history(conversation_id)
        
        logfire.info("Response generated successfully", 
                    conversation_id=conversation_id,
                    response_length=len(ai_response),
                    history_messages_count=len(history))
        
        return {
            "conversation_id": conversation_id,
            "message": ai_response,
            "history": history
        }
    except RateLimitExceededError as e:
        # Handle rate limit errors specifically
        logfire.warning("Rate limit exceeded", 
                       conversation_id=conversation_id,
                       retry_after=e.retry_after)
        return {
            "conversation_id": conversation_id,
            "message": "The system is currently experiencing high demand. Please try again in a moment.",
            "error": True,
            "retry_after": e.retry_after
        }
    except OpenAIServiceError as e:
        # Handle OpenAI service errors
        logfire.error("OpenAI service error", 
                     conversation_id=conversation_id,
                     error=str(e))
        error_message = f"The AI service is currently unavailable: {str(e)}"
        return {
            "conversation_id": conversation_id,
            "message": error_message,
            "error": True
        }
    except Exception as e:
        logfire.error("Unexpected error in send_message", 
                     conversation_id=conversation_id,
                     error=str(e),
                     error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """Handle WebSocket connection for real-time chat."""
    try:
        await websocket.accept()
        
        logfire.info("WebSocket connection established", 
                    conversation_id=conversation_id,
                    client=websocket.client.host)
        
        # Get or create conversation manager
        if conversation_id not in active_conversations:
            logfire.debug("Creating new conversation manager for websocket", 
                         conversation_id=conversation_id)
            manager = ConversationManager(max_conversation_length=ai_settings.max_conversation_messages)
            
            if conversation_id == "new":
                # Generate a new ID when "new" is specified
                conversation_id = manager.create_conversation()
                logfire.info("Created new conversation via websocket", 
                            new_conversation_id=conversation_id)
            else:
                # Register the existing ID in the conversation manager
                logfire.info("Registering existing conversation ID in manager", 
                            conversation_id=conversation_id)
                # This creates an entry in the manager's internal dictionary
                manager.create_conversation(conversation_id=conversation_id)
                
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
            
            # Check for harmful content if moderation is enabled
            if ai_settings.moderation_enabled:
                is_harmful, categories = moderate_content(user_message)
                if is_harmful:
                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": "I'm sorry, but I cannot respond to this message as it may contain harmful content.",
                        "conversation_id": conversation_id,
                        "moderated": True
                    })
                    continue
            
            # Add user message to conversation
            conversation_manager.add_message(conversation_id, "user", user_message)
            
            # Get relevant context
            context = conversation_manager.retrieve_relevant_context(
                conversation_id, 
                user_message,
                limit=5,  # Could be configurable
                threshold=0.7  # Could be configurable
            )
            
            # Get chat context for completion
            chat_context = conversation_manager.get_chat_context(conversation_id)
            
            try:
                # Check if streaming is requested and enabled
                stream = message_data.get("stream", False) and ai_settings.stream_enabled
                
                if stream:
                    # Send a "thinking" status to the client
                    await websocket.send_json({
                        "type": "status",
                        "status": "thinking",
                        "conversation_id": conversation_id
                    })
                    
                    # Get streaming response
                    response_stream = get_chat_completion(
                        messages=chat_context,
                        temperature=ai_settings.temperature,
                        max_tokens=ai_settings.max_tokens,
                        model=ai_settings.model,
                        stream=True
                    )
                    
                    # Initialize variables for collecting the response
                    full_response = ""
                    
                    # Stream the response chunks to the client
                    for chunk in response_stream:
                        if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                            content = chunk.choices[0].delta.content
                            if content:
                                full_response += content
                                await websocket.send_json({
                                    "type": "stream",
                                    "content": content,
                                    "conversation_id": conversation_id
                                })
                    
                    # Add the complete response to the conversation history
                    conversation_manager.add_message(conversation_id, "assistant", full_response)
                    
                    # Send completion notification
                    await websocket.send_json({
                        "type": "stream_end",
                        "conversation_id": conversation_id
                    })
                else:
                    # Get complete response (non-streaming)
                    ai_response = get_chat_completion(
                        messages=chat_context,
                        temperature=ai_settings.temperature,
                        max_tokens=ai_settings.max_tokens,
                        model=ai_settings.model
                    )
                    
                    # Add assistant response to conversation
                    conversation_manager.add_message(conversation_id, "assistant", ai_response)
                    
                    # Send response to client
                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": ai_response,
                        "conversation_id": conversation_id
                    })
            
            except RateLimitExceededError as e:
                # Handle rate limit errors specifically
                await websocket.send_json({
                    "type": "error",
                    "message": "The system is currently experiencing high demand. Please try again in a moment.",
                    "conversation_id": conversation_id,
                    "retry_after": e.retry_after
                })
            except OpenAIServiceError as e:
                # Handle OpenAI service errors
                error_message = f"The AI service is currently unavailable: {str(e)}"
                
                await websocket.send_json({
                    "type": "error",
                    "message": error_message,
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