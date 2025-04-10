import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from app.utils.vector_search import search_documents, generate_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationContext:
    """Manages conversation context, including history and relevant documents."""
    
    def __init__(self, max_history: int = 10, max_tokens: int = 4000):
        """Initialize the conversation context manager.
        
        Args:
            max_history (int): Maximum number of messages to keep in history
            max_tokens (int): Maximum number of tokens to include in context
        """
        self.history: List[Dict[str, Any]] = []
        self.relevant_docs: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.conversation_embedding = None
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history.
        
        Args:
            role (str): The role of the message sender (user, assistant, system)
            content (str): The message content
        """
        # Create message object
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to history
        self.history.append(message)
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Update conversation embedding
        self._update_conversation_embedding()
    
    def _update_conversation_embedding(self) -> None:
        """Update the embedding for the entire conversation."""
        try:
            # Combine all messages into a single text
            conversation_text = " ".join([
                f"{msg['role']}: {msg['content']}" for msg in self.history[-3:]
            ])
            
            # Generate embedding
            self.conversation_embedding = generate_embedding(conversation_text)
        except Exception as e:
            logger.error(f"Error updating conversation embedding: {str(e)}")
    
    def get_relevant_documents(self, query: str, doc_type: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Get documents relevant to the current query and conversation context.
        
        Args:
            query (str): The current user query
            doc_type (Optional[str]): Filter by document type
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of relevant documents
        """
        try:
            # Search for documents based on the query
            self.relevant_docs = search_documents(
                query=query,
                doc_type=doc_type,
                limit=limit
            )
            
            return self.relevant_docs
        except Exception as e:
            logger.error(f"Error getting relevant documents: {str(e)}")
            return []
    
    def build_context_for_llm(self, system_prompt: str = None) -> List[Dict[str, str]]:
        """Build the context for the LLM, including history and relevant documents.
        
        Args:
            system_prompt (str, optional): System prompt to use
            
        Returns:
            List[Dict[str, str]]: Formatted messages for the LLM
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add relevant documents as context in the system message
        if self.relevant_docs:
            docs_context = "Here are some relevant documents that might help answer the query:\n\n"
            
            for i, doc in enumerate(self.relevant_docs):
                docs_context += f"Document {i+1} - {doc.get('title', 'Untitled')}:\n"
                docs_context += f"{doc.get('content', '')}\n\n"
            
            messages.append({"role": "system", "content": docs_context})
        
        # Add conversation history
        for msg in self.history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages
    
    def save_context(self, filepath: str) -> bool:
        """Save the conversation context to a file.
        
        Args:
            filepath (str): Path to save the context
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a serializable dictionary
            context_data = {
                "history": self.history,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(context_data, f, indent=2)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving conversation context: {str(e)}")
            return False
    
    def load_context(self, filepath: str) -> bool:
        """Load the conversation context from a file.
        
        Args:
            filepath (str): Path to load the context from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load from file
            with open(filepath, 'r') as f:
                context_data = json.load(f)
            
            # Update history
            self.history = context_data.get("history", [])
            
            # Update conversation embedding
            self._update_conversation_embedding()
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading conversation context: {str(e)}")
            return False
    
    def clear_context(self) -> None:
        """Clear the conversation context."""
        self.history = []
        self.relevant_docs = []
        self.conversation_embedding = None 