"""
Tests for the conversation management functionality
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging

# Set up path for importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.conversation_manager import ConversationManager, Message


class TestConversationManager(unittest.TestCase):
    """Tests for the conversation manager"""
    
    def setUp(self):
        """Set up for each test"""
        self.manager = ConversationManager(max_conversation_length=5)
        
    def test_create_conversation(self):
        """Test creating a new conversation"""
        # Create conversation with basic info
        conversation_id = self.manager.create_conversation(
            customer_id="cust123",
            product_id="prod456"
        )
        
        # Verify it's in active conversations
        self.assertIn(conversation_id, self.manager.active_conversations)
        
        # Check conversation data
        context = self.manager.active_conversations[conversation_id]
        self.assertEqual(context.conversation_id, conversation_id)
        self.assertEqual(context.customer_id, "cust123")
        self.assertEqual(context.product_id, "prod456")
        
    def test_add_message(self):
        """Test adding messages to a conversation"""
        # Create conversation
        conversation_id = self.manager.create_conversation()
        
        # Add a user message
        self.manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content="How do I reset my password?"
        )
        
        # Add an assistant message
        self.manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content="You can reset your password by clicking the 'Forgot Password' link."
        )
        
        # Check conversation history
        context = self.manager.active_conversations[conversation_id]
        self.assertEqual(len(context.messages), 2)
        self.assertEqual(context.messages[0].role, "user")
        self.assertEqual(context.messages[0].content, "How do I reset my password?")
        self.assertEqual(context.messages[1].role, "assistant")
        
        # Test invalid role
        with self.assertRaises(ValueError):
            self.manager.add_message(
                conversation_id=conversation_id,
                role="invalid_role",
                content="This should fail"
            )
            
        # Test invalid conversation ID
        with self.assertRaises(ValueError):
            self.manager.add_message(
                conversation_id="invalid_id",
                role="user",
                content="This should fail"
            )
    
    def test_get_conversation_history(self):
        """Test retrieving conversation history"""
        # Create conversation with messages
        conversation_id = self.manager.create_conversation()
        
        # Add several messages
        for i in range(10):
            role = "user" if i % 2 == 0 else "assistant"
            self.manager.add_message(
                conversation_id=conversation_id,
                role=role,
                content=f"Message {i}"
            )
        
        # Get full history
        history = self.manager.get_conversation_history(conversation_id)
        self.assertEqual(len(history), 10)
        
        # Get limited history
        limited_history = self.manager.get_conversation_history(conversation_id, limit=3)
        self.assertEqual(len(limited_history), 3)
        self.assertEqual(limited_history[0]["content"], "Message 7")
        self.assertEqual(limited_history[2]["content"], "Message 9")
        
        # Check dictionary format
        self.assertIn("role", limited_history[0])
        self.assertIn("content", limited_history[0])
        self.assertIn("timestamp", limited_history[0])
        self.assertIn("metadata", limited_history[0])
    
    @patch('app.services.conversation_manager.search_and_format_query')
    def test_retrieve_relevant_context(self, mock_search):
        """Test retrieving relevant context for a query"""
        # Mock search result
        mock_search.return_value = "Mocked relevant document context"
        
        # Create conversation
        conversation_id = self.manager.create_conversation(product_id="prod123")
        
        # Retrieve context
        result = self.manager.retrieve_relevant_context(
            conversation_id=conversation_id,
            query="How do I reset my password?"
        )
        
        # Check result
        self.assertEqual(result, "Mocked relevant document context")
        
        # Verify search was called with correct parameters
        mock_search.assert_called_once()
        args, kwargs = mock_search.call_args
        self.assertEqual(kwargs["query"], "How do I reset my password?")
        self.assertEqual(kwargs["filters"], {"product_id": "prod123"})
        
        # Check conversation context was updated
        context = self.manager.active_conversations[conversation_id]
        self.assertEqual(context.relevant_docs, "Mocked relevant document context")
    
    def test_get_chat_context(self):
        """Test getting formatted chat context"""
        # Create conversation
        conversation_id = self.manager.create_conversation(
            customer_id="cust123",
            product_id="prod456"
        )
        
        # Add messages to conversation
        self.manager.add_message(conversation_id, "user", "Hello")
        self.manager.add_message(conversation_id, "assistant", "Hi there, how can I help?")
        self.manager.add_message(conversation_id, "user", "I need help with my account")
        
        # Update context with relevant docs
        with patch('app.services.conversation_manager.search_and_format_query') as mock_search:
            mock_search.return_value = "Relevant info about account management"
            self.manager.retrieve_relevant_context(
                conversation_id=conversation_id,
                query="I need help with my account"
            )
        
        # Get chat context
        chat_context = self.manager.get_chat_context(conversation_id)
        
        # Check format
        self.assertEqual(len(chat_context), 4)  # system + 3 messages
        self.assertEqual(chat_context[0]["role"], "system")
        self.assertEqual(chat_context[1]["role"], "user")
        self.assertEqual(chat_context[1]["content"], "Hello")
        
        # Check system message contains relevant docs
        self.assertIn("Relevant info about account management", chat_context[0]["content"])
        self.assertIn("customer ID: cust123", chat_context[0]["content"])
        self.assertIn("product: prod456", chat_context[0]["content"])
    
    @patch('app.services.conversation_manager.store_document')
    def test_end_conversation(self, mock_store):
        """Test ending and archiving a conversation"""
        # Mock store_document
        mock_store.return_value = {"id": "doc123"}
        
        # Create conversation with messages
        conversation_id = self.manager.create_conversation(
            customer_id="cust123",
            product_id="prod456"
        )
        
        self.manager.add_message(conversation_id, "user", "Hello")
        self.manager.add_message(conversation_id, "assistant", "Hi there!")
        
        # End conversation
        result = self.manager.end_conversation(conversation_id)
        
        # Check result
        self.assertEqual(result["conversation_id"], conversation_id)
        self.assertEqual(result["message_count"], 2)
        self.assertEqual(result["archived_id"], "doc123")
        self.assertEqual(result["metadata"]["customer_id"], "cust123")
        
        # Check conversation was removed from active conversations
        self.assertNotIn(conversation_id, self.manager.active_conversations)
        
        # Check store_document was called
        mock_store.assert_called_once()
        args, kwargs = mock_store.call_args
        self.assertIn("USER: Hello", kwargs["content"])
        self.assertIn("ASSISTANT: Hi there!", kwargs["content"])
    
    @patch('app.services.conversation_manager.store_document')
    def test_end_conversation_error(self, mock_store):
        """Test handling errors when ending a conversation"""
        # Mock store_document to raise an exception
        mock_store.side_effect = Exception("Database error")
        
        # Create conversation
        conversation_id = self.manager.create_conversation()
        self.manager.add_message(conversation_id, "user", "Test message")
        
        # End conversation
        result = self.manager.end_conversation(conversation_id)
        
        # Check result
        self.assertEqual(result["conversation_id"], conversation_id)
        self.assertEqual(result["archived"], False)
        self.assertIn("Database error", result["error"])
        
        # Check conversation was still removed from active conversations
        self.assertNotIn(conversation_id, self.manager.active_conversations)


if __name__ == "__main__":
    unittest.main() 