# Support Agent Technical Stack

## Core Technologies

### Backend
- **Python** - Primary development language
- **FastAPI** - API framework for building the backend service
- **Pydantic AI** - For AI model integration and structure
  - [Documentation](https://ai.pydantic.dev/)
- **Pydantic Logfire** - Structured logging for application monitoring
  - [Documentation](https://logfire.pydantic.dev/docs/)
- **OpenAI API** - For natural language processing and generation
  - GPT-4/GPT-3.5 for conversation handling
  - Embeddings API for document vectorization

### Database
- **Supabase** - PostgreSQL database with extensions
  - pgvector for vector search capabilities
  - User authentication and authorization
  - Real-time subscription capabilities
  - [Documentation](https://supabase.com/docs)

### Document Processing
- **LangChain/LlamaIndex** - For document processing pipelines
- **PyPDF2/PDFMiner** - For handling PDF documents
- **BeautifulSoup/Scrapy** - For web document extraction if needed
- **NLTK/spaCy** - For additional NLP processing

### Frontend (Optional)
- **Next.js/React** - For building the UI
- **Shadcn/Ui,Tailwind CSS** - For styling
- **Supabase Auth UI** - For authentication components

## Infrastructure
- **Docker** - For containerization and deployment
- **GitHub Actions** - For CI/CD pipeline
- **Poetry/pip** - For dependency management
- **pytest** - For testing framework

## Data Flow

1. **Document Processing**
   ```
   Raw Documents → Text Extraction → Chunking → Embedding Generation → Vector Storage (Supabase)
   ```

2. **Chat Flow**
   ```
   User Query → Context Building → OpenAI API → Vector Search → Response Generation → Conversation Storage
   ```

3. **Information Lookup**
   ```
   Serial Number → Database Query → Information Retrieval → Response Formatting
   ```

## Environment Variables
```
# OpenAI
OPENAI_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=

# Application
LOG_LEVEL=
ENVIRONMENT=development|production
```

## Development Setup
1. Clone repository
2. Install dependencies with Poetry/pip
3. Set up Supabase local or cloud instance
4. Configure environment variables
5. Run development server

## Database Schema (High-Level)

### customers
- id (primary key)
- name
- email
- phone
- preferences (jsonb)
- created_at
- updated_at

### products
- id (primary key)
- serial_number
- name
- description
- specifications (jsonb)
- created_at
- updated_at

### conversations
- id (primary key)
- customer_id (foreign key)
- started_at
- ended_at
- summary
- satisfaction_score

### messages
- id (primary key)
- conversation_id (foreign key)
- role (user/assistant)
- content
- timestamp
- metadata (jsonb)

### documents
- id (primary key)
- title
- content
- metadata (jsonb)
- created_at
- updated_at

### document_chunks
- id (primary key)
- document_id (foreign key)
- content
- embedding (vector)
- metadata (jsonb)

### solutions
- id (primary key)
- problem_description
- solution_content
- related_products (array)
- effectiveness_score
- created_at
- updated_at 