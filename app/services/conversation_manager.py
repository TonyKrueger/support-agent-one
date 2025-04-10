"""
Conversation Manager Service

This module manages conversation history, context, and state for the support agent.
"""

import time
import uuid
import logging
import logfire
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from app.services.document_retrieval import search_and_format_query
from app.services.supabase_service import store_document
from app.utils.logger import get_logger

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Represents the context for a conversation."""
    conversation_id: str
    customer_id: Optional[str] = None
    product_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevant_docs: str = ""  # Relevant document context for the current query


class ConversationManager:
    """
    Manages conversation state, history, and context retrieval.
    """
    
    def __init__(self, max_conversation_length: int = 10):
        """
        Initialize the conversation manager.
        
        Args:
            max_conversation_length: Maximum number of messages to include in context
        """
        self.max_conversation_length = max_conversation_length
        self.active_conversations: Dict[str, ConversationContext] = {}
        logfire.info("ConversationManager initialized", 
                    max_conversation_length=max_conversation_length)
        
    def create_conversation(
        self,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            customer_id: Optional customer identifier
            product_id: Optional product identifier
            metadata: Optional conversation metadata
            conversation_id: Optional existing conversation ID to register
            
        Returns:
            The new conversation ID
        """
        # Use provided ID or generate a new one
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Check if this ID is already in use
        if conversation_id in self.active_conversations:
            logfire.warning("Conversation ID already exists", 
                           conversation_id=conversation_id,
                           action="returning_existing")
            return conversation_id
        
        context = ConversationContext(
            conversation_id=conversation_id,
            customer_id=customer_id,
            product_id=product_id,
            metadata=metadata or {}
        )
        
        self.active_conversations[conversation_id] = context
        logger.info(f"Created new conversation: {conversation_id}")
        logfire.info("New conversation created", 
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    product_id=product_id,
                    active_conversations_count=len(self.active_conversations))
        
        return conversation_id
        
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: The conversation identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata
            
        Raises:
            ValueError: If the conversation ID is invalid or role is invalid
        """
        logfire.debug("Adding message to conversation", 
                     conversation_id=conversation_id,
                     role=role,
                     content_length=len(content),
                     active_conversations=list(self.active_conversations.keys()))
                     
        if conversation_id not in self.active_conversations:
            logfire.error("Invalid conversation ID in add_message", 
                         conversation_id=conversation_id,
                         active_conversations=list(self.active_conversations.keys()))
            raise ValueError(f"Invalid conversation ID: {conversation_id}")
            
        if role not in ["user", "assistant"]:
            logfire.error("Invalid message role", 
                         conversation_id=conversation_id,
                         role=role)
            raise ValueError(f"Invalid message role: {role}")
            
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.active_conversations[conversation_id].messages.append(message)
        logger.debug(f"Added {role} message to conversation {conversation_id}")
        logfire.debug(f"Added {role} message to conversation", 
                     conversation_id=conversation_id,
                     message_count=len(self.active_conversations[conversation_id].messages))
        
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            conversation_id: The conversation identifier
            limit: Optional limit on number of messages to return (most recent)
            
        Returns:
            List of messages in the conversation
            
        Raises:
            ValueError: If the conversation ID is invalid
        """
        logfire.debug("Getting conversation history", 
                     conversation_id=conversation_id,
                     limit=limit,
                     active_conversations=list(self.active_conversations.keys()))
                     
        if conversation_id not in self.active_conversations:
            logfire.error("Invalid conversation ID in get_conversation_history", 
                         conversation_id=conversation_id,
                         active_conversations=list(self.active_conversations.keys()))
            raise ValueError(f"Invalid conversation ID: {conversation_id}")
            
        messages = self.active_conversations[conversation_id].messages
        
        if limit is not None:
            messages = messages[-limit:]
            
        # Convert to dictionaries for serialization
        history = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata
            }
            for msg in messages
        ]
        
        logfire.debug("Retrieved conversation history", 
                     conversation_id=conversation_id,
                     message_count=len(history))
        
        return history
        
    def retrieve_relevant_context(
        self,
        conversation_id: str,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> str:
        """
        Retrieve relevant context for a query and update the conversation.
        
        Args:
            conversation_id: The conversation identifier
            query: The user's query
            limit: Maximum number of document chunks to retrieve
            threshold: Similarity threshold for retrieval
            
        Returns:
            Context string with relevant information
            
        Raises:
            ValueError: If the conversation ID is invalid
        """
        logfire.debug("Retrieving relevant context", 
                     conversation_id=conversation_id,
                     query_length=len(query),
                     limit=limit,
                     threshold=threshold)
                     
        if conversation_id not in self.active_conversations:
            logfire.error("Invalid conversation ID in retrieve_relevant_context", 
                         conversation_id=conversation_id,
                         active_conversations=list(self.active_conversations.keys()))
            raise ValueError(f"Invalid conversation ID: {conversation_id}")
            
        context = self.active_conversations[conversation_id]
        
        # Apply product filter if available
        filters = {}
        if context.product_id:
            filters["product_id"] = context.product_id
            
        # Retrieve relevant documents
        try:
            relevant_docs = search_and_format_query(
                query=query,
                limit=limit,
                threshold=threshold,
                filters=filters
            )
            
            # Update conversation context with relevant documents
            context.relevant_docs = relevant_docs
            
            logfire.info("Retrieved relevant context", 
                        conversation_id=conversation_id,
                        context_length=len(relevant_docs))
                        
            return relevant_docs
        except Exception as e:
            logfire.error("Error retrieving relevant context", 
                         conversation_id=conversation_id,
                         error=str(e))
            raise
        
    def get_chat_context(
        self,
        conversation_id: str
    ) -> List[Dict[str, str]]:
        """
        Get formatted context for chat completion.
        
        Args:
            conversation_id: The conversation identifier
            
        Returns:
            Formatted context for chat completion API
            
        Raises:
            ValueError: If the conversation ID is invalid
        """
        logfire.debug("Getting chat context", 
                     conversation_id=conversation_id,
                     active_conversations=list(self.active_conversations.keys()))
                     
        if conversation_id not in self.active_conversations:
            logfire.error("Invalid conversation ID in get_chat_context", 
                         conversation_id=conversation_id,
                         active_conversations=list(self.active_conversations.keys()))
            raise ValueError(f"Invalid conversation ID: {conversation_id}")
            
        context = self.active_conversations[conversation_id]
        
        # Start with system message
        chat_messages = [{
            "role": "system",
            "content": self._get_system_prompt(context)
        }]
        
        # Add conversation history, limited by max length
        for message in context.messages[-self.max_conversation_length:]:
            chat_messages.append({
                "role": message.role,
                "content": message.content
            })
            
        logfire.debug("Chat context prepared", 
                     conversation_id=conversation_id,
                     message_count=len(chat_messages))
            
        return chat_messages
        
    def _get_system_prompt(self, context: ConversationContext) -> str:
        """
        Construct the system prompt for a conversation.
        
        Args:
            context: The conversation context
            
        Returns:
            System prompt string
        """
        # Start with base prompt
        prompt = """You are a helpful support agent. Answer the user's questions based on the context provided.
If you don't know the answer or can't find relevant information in the context, say so clearly.
Be concise, accurate, and helpful. Do not make up information."""
        
        # Add relevant document context if available
        if context.relevant_docs:
            prompt += "\n\n### Relevant Information:\n" + context.relevant_docs
            
        # Add customer context if available
        if context.customer_id:
            prompt += f"\n\nYou are speaking with customer ID: {context.customer_id}."
            
        # Add product context if available
        if context.product_id:
            prompt += f"\n\nThe customer is asking about product: {context.product_id}."
            
        return prompt
        
    def end_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        End a conversation and archive it.
        
        Args:
            conversation_id: The conversation identifier
            
        Returns:
            Summary of the archived conversation
            
        Raises:
            ValueError: If the conversation ID is invalid
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Invalid conversation ID: {conversation_id}")
            
        context = self.active_conversations[conversation_id]
        
        # Create conversation summary
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in context.messages
        ]
        
        metadata = {
            "customer_id": context.customer_id,
            "product_id": context.product_id,
            **context.metadata
        }
        
        # Store conversation in database
        conversation_content = "\n\n".join([
            f"{msg.role.upper()}: {msg.content}"
            for msg in context.messages
        ])
        
        title = f"Conversation {conversation_id}"
        
        try:
            stored_conversation = store_document(
                title=title,
                content=conversation_content,
                metadata=metadata
            )
            
            logger.info(f"Archived conversation {conversation_id}")
            
            # Remove from active conversations
            del self.active_conversations[conversation_id]
            
            return {
                "conversation_id": conversation_id,
                "message_count": len(context.messages),
                "archived_id": stored_conversation["id"],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to archive conversation {conversation_id}: {str(e)}")
            # Still remove from active conversations
            del self.active_conversations[conversation_id]
            
            return {
                "conversation_id": conversation_id,
                "message_count": len(context.messages),
                "archived": False,
                "error": str(e)
            } 