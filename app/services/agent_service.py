import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.document_service import DocumentService
from app.utils.openai_client import get_openai_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupportAgent:
    """Support agent that processes queries using document search and LLM responses."""
    
    def __init__(self, doc_service: DocumentService):
        """
        Initialize the support agent.
        
        Args:
            doc_service: The document service for retrieval
        """
        self.doc_service = doc_service
        self.openai_client = get_openai_client()
        self.conversation_history = []
        
    def process_query(self, query: str, doc_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user query and return a response.
        
        Args:
            query: The user's question
            doc_type: Optional document type to filter the search
            
        Returns:
            Dict containing the answer and source documents
        """
        try:
            # Search for relevant documents
            relevant_docs = self.doc_service.search_documents(query, doc_type=doc_type, limit=5)
            
            # Format documents for context
            context = self._format_documents_for_context(relevant_docs)
            
            # Prepare conversation history for context
            history_context = self._format_history_for_context()
            
            # Get answer from OpenAI
            answer = self._get_answer_from_openai(query, context, history_context)
            
            # Add to conversation history
            self._add_to_history(query, answer, relevant_docs)
            
            return {
                "answer": answer,
                "sources": [doc["metadata"] for doc in relevant_docs]
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise e
    
    def _format_documents_for_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format documents for inclusion in the prompt context.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant documents found."
        
        context = "Here are some relevant documents that might help answer the question:\n\n"
        
        for i, doc in enumerate(documents, 1):
            context += f"Document {i}:\n"
            context += f"Title: {doc['metadata'].get('title', 'Untitled')}\n"
            context += f"Source: {doc['metadata'].get('source', 'Unknown')}\n"
            context += f"Content: {doc['content']}\n\n"
            
        return context
    
    def _format_history_for_context(self) -> str:
        """
        Format conversation history for inclusion in the prompt context.
        
        Returns:
            Formatted history string
        """
        if not self.conversation_history:
            return "No previous conversation history."
        
        # Only include the last 5 exchanges to avoid context length issues
        recent_history = self.conversation_history[-5:]
        
        context = "Here is the recent conversation history:\n\n"
        
        for i, exchange in enumerate(recent_history, 1):
            context += f"User: {exchange['query']}\n"
            context += f"Assistant: {exchange['answer']}\n\n"
            
        return context
    
    def _get_answer_from_openai(self, query: str, doc_context: str, history_context: str) -> str:
        """
        Get an answer from OpenAI based on the query and context.
        
        Args:
            query: The user query
            doc_context: Context from relevant documents
            history_context: Context from conversation history
            
        Returns:
            Generated answer
        """
        system_prompt = """
        You are a helpful support agent with specific knowledge about our products and services.
        Use the provided document information to answer the user's question accurately.
        If you don't know the answer or can't find it in the documents, say so honestly.
        Be concise, professional, and helpful in your responses.
        """
        
        user_prompt = f"""
        {history_context}
        
        {doc_context}
        
        User question: {query}
        
        Please provide a helpful response based on the information above.
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",  # Can be configured based on requirements
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
    
    def _add_to_history(self, query: str, answer: str, sources: List[Dict[str, Any]]) -> None:
        """
        Add an exchange to the conversation history.
        
        Args:
            query: The user query
            answer: The agent's response
            sources: The source documents used
        """
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer,
            "sources": [doc["metadata"] for doc in sources]
        })
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the full conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history
    
    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    def save_conversation(self, filepath: str) -> bool:
        """
        Save the conversation history to a file.
        
        Args:
            filepath: Path where to save the conversation
            
        Returns:
            Success status
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "history": self.conversation_history
                }, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            return False
    
    def load_conversation(self, filepath: str) -> bool:
        """
        Load conversation history from a file.
        
        Args:
            filepath: Path of the saved conversation
            
        Returns:
            Success status
        """
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                self.conversation_history = data.get("history", [])
            
            return True
        except Exception as e:
            logger.error(f"Error loading conversation: {str(e)}")
            return False 