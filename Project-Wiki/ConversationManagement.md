---
title: Conversation Context Management
description: Documentation for the conversation context management system
date_created: 2023-05-16
last_updated: 2023-05-16
tags:
  - context
  - conversation
  - vector-search
  - history
sidebar_position: 5
---

# Conversation Context Management

## Overview

The Conversation Context Management system handles user conversations with the support agent, managing conversation history, retrieving relevant document context, and maintaining conversation state. This system provides the intelligence behind the chat interface, enabling contextually relevant responses and persistent conversation history.

## Key Features

- Conversation state management and tracking
- Context-aware document retrieval for relevant information
- Conversation history storage and retrieval
- Integration with vector search for semantic relevance
- System prompt construction with contextual information
- Conversation archiving and persistence

## Implementation Details

### Context Manager Utility

The ContextManager utility class provides core functionality for managing conversation context:

```python
class ConversationContext:
    def __init__(self, max_history: int = 10, max_tokens: int = 4000):
        self.history = []
        self.relevant_docs = []
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.conversation_embedding = None
    
    def add_message(self, role: str, content: str) -> None:
        # Add a message to the conversation history and update embedding
    
    def _update_conversation_embedding(self) -> None:
        # Update the embedding for the entire conversation for semantic search
    
    def get_relevant_documents(self, query: str, doc_type: Optional[str] = None, limit: int = 3):
        # Retrieve documents relevant to the current query
    
    def build_context_for_llm(self, system_prompt: str = None):
        # Build context for the LLM, including history and relevant documents
    
    def save_context(self, filepath: str) -> bool:
        # Save the conversation context to a file
    
    def load_context(self, filepath: str) -> bool:
        # Load the conversation context from a file
    
    def clear_context(self) -> None:
        # Clear the conversation context
```

### Conversation Manager Service

The Conversation Manager service manages conversation state, history, and context retrieval:

```python
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
    def __init__(self, max_conversation_length: int = 10):
        self.max_conversation_length = max_conversation_length
        self.active_conversations = {}
        
    def create_conversation(self, customer_id=None, product_id=None, metadata=None):
        # Create a new conversation and return the ID
        
    def add_message(self, conversation_id, role, content, metadata=None):
        # Add a message to a conversation
        
    def get_conversation_history(self, conversation_id, limit=None):
        # Get the conversation history
        
    def retrieve_relevant_context(self, conversation_id, query, limit=5, threshold=0.7):
        # Retrieve relevant context for a query
        
    def get_chat_context(self, conversation_id):
        # Get formatted context for chat completion
        
    def _get_system_prompt(self, context):
        # Construct the system prompt for a conversation
        
    def end_conversation(self, conversation_id):
        # End a conversation and archive it
```

### System Prompt Construction

The system prompt is dynamically constructed based on the conversation context:

```python
def _get_system_prompt(self, context: ConversationContext) -> str:
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
```

### Document Retrieval Integration

The conversation context integrates with the document retrieval system:

```python
def retrieve_relevant_context(self, conversation_id, query, limit=5, threshold=0.7):
    # Get the conversation context
    context = self.active_conversations[conversation_id]
    
    # Apply product filter if available
    filters = {}
    if context.product_id:
        filters["product_id"] = context.product_id
        
    # Retrieve relevant documents using vector search
    relevant_docs = search_and_format_query(
        query=query,
        limit=limit,
        threshold=threshold,
        filters=filters
    )
    
    # Update conversation context with relevant documents
    context.relevant_docs = relevant_docs
    
    return relevant_docs
```

## Database Schema

Conversations are stored in Supabase with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| customer_id | text | Optional customer identifier |
| messages | jsonb | Array of message objects with role, content, timestamp |
| metadata | jsonb | Additional metadata |
| created_at | timestamp | Creation timestamp |

## Configuration

Configuration parameters for the conversation context system:

```
# Conversation manager settings
MAX_CONVERSATION_LENGTH=10  # Maximum number of messages in context
MAX_TOKENS=4000  # Maximum number of tokens in context
CONTEXT_THRESHOLD=0.7  # Similarity threshold for document retrieval
```

## Best Practices

- Keep conversation context concise to maintain focus
- Include relevant document context but avoid overwhelming the AI model
- Incorporate customer and product context when available
- Balance context relevance with token limits for optimal performance
- Archive completed conversations for future reference
- Use conversation embeddings for more relevant document retrieval

## Troubleshooting

Common issues and their solutions:

| Issue | Solution |
|-------|----------|
| Context too large | Reduce max_conversation_length or limit document context |
| Irrelevant document retrieval | Adjust similarity threshold or fine-tune vector embeddings |
| Missing conversation history | Verify conversation ID is consistent across requests |
| System prompt not working | Check prompt construction and ensure formatting is correct |
| Conversations not being saved | Check database connection and schema configuration |

## Related Documentation

- [Chat Interface](./ChatInterface.md)
- [Document Management](./DocumentManagement.md)
- [Vector Search](./VectorSearch.md)
- [OpenAI Integration](./OpenAI.md)

## Next Steps

- Implement multi-turn reasoning for complex queries
- Add conversation summarization for long conversations
- Develop analytics for conversation quality and efficiency
- Implement customer preference tracking based on conversation history
- Create a feedback system for improving context relevance
- Integrate with CRM systems for enhanced customer context 