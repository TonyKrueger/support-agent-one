from typing import List, Dict, Any, Optional
import time

import logfire
from supabase import create_client

from app.config.settings import settings
from app.models.agent import support_agent, AgentDependencies, SupportResult


class ChatService:
    """
    Service for handling chat interactions with the AI agent.
    """
    
    def __init__(self):
        self.supabase = create_client(settings.supabase_url, settings.supabase_key)
        logfire.info("Chat service initialized")
    
    async def process_message(
        self, 
        messages: List[Dict[str, str]], 
        customer_id: Optional[str] = None,
        product_serial: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and get a response from the AI agent.
        
        Args:
            messages: List of conversation messages (role, content)
            customer_id: Optional customer ID for context
            product_serial: Optional product serial number for context
            
        Returns:
            A dictionary with the AI response and metadata
        """
        logfire.info("Processing message", 
                   customer_id=customer_id, 
                   product_serial=product_serial,
                   message_count=len(messages))
        
        # Create agent dependencies with conversation context
        deps = AgentDependencies(
            customer_id=customer_id,
            product_serial=product_serial,
            conversation_history=messages[:-1]  # All messages except the latest
        )
        
        # Get the latest user message
        user_message = messages[-1]["content"]
        
        # Run the agent to get a response
        result = await support_agent.run(user_message, deps=deps)
        
        # Store the conversation in the database
        await self._store_conversation(messages, result.data, customer_id, product_serial)
        
        # Prepare the response
        response = {
            "message": {
                "role": "assistant",
                "content": result.data.support_response
            },
            "needs_followup": result.data.needs_followup,
            "suggested_documents": result.data.suggested_documents
        }
        
        return response
    
    async def get_conversation_history(self, customer_id: str) -> List[Dict[str, str]]:
        """
        Get the conversation history for a specific customer.
        
        Args:
            customer_id: The customer ID
            
        Returns:
            A list of conversation messages
        """
        try:
            # Retrieve conversations from Supabase
            result = self.supabase.table("conversations")\
                .select("id, messages, created_at")\
                .eq("customer_id", customer_id)\
                .order("created_at", desc=True)\
                .execute()
            
            if result.data and len(result.data) > 0:
                # Return the messages from the most recent conversation
                return result.data[0].get("messages", [])
            
            return []
            
        except Exception as e:
            logfire.error("Error retrieving conversation history", 
                        customer_id=customer_id,
                        error=str(e))
            # Return empty list on error
            return []
    
    async def _store_conversation(
        self, 
        messages: List[Dict[str, str]], 
        result: SupportResult,
        customer_id: Optional[str],
        product_serial: Optional[str]
    ) -> None:
        """
        Store the conversation in the database.
        
        Args:
            messages: The conversation messages
            result: The AI agent result
            customer_id: Optional customer ID
            product_serial: Optional product serial number
        """
        try:
            # Format messages for storage
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.get("role", "unknown"),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp", time.time())
                })
            
            # Add the latest assistant response
            formatted_messages.append({
                "role": "assistant",
                "content": result.support_response,
                "timestamp": time.time()
            })
            
            # Create metadata
            metadata = {
                "needs_followup": result.needs_followup,
                "suggested_documents": result.suggested_documents,
                "product_serial": product_serial
            }
            
            # Store in Supabase
            conversation_data = {
                "customer_id": customer_id,
                "messages": formatted_messages,
                "metadata": metadata
            }
            
            self.supabase.table("conversations").insert(conversation_data).execute()
            
            logfire.info("Stored conversation", 
                       message_count=len(formatted_messages), 
                       customer_id=customer_id,
                       product_serial=product_serial)
                       
        except Exception as e:
            logfire.error("Failed to store conversation", 
                        error=str(e),
                        customer_id=customer_id,
                        product_serial=product_serial) 