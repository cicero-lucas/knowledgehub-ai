# KnowledgeHub AI

**Intelligent document Q&A platform powered by RAG and Google Gemini.**

Upload your PDFs, ask questions in natural language, and get accurate answers grounded in your documents — with source citations at the page level.

---

## Problem it solves

Finding specific information in large document collections is slow and error-prone. KnowledgeHub AI turns your PDFs into a searchable, conversational knowledge base. Every answer includes references to the exact document and page number so you can verify it instantly.

---

## Features

- **Secure authentication** — JWT-based register, login, and token refresh
- **PDF upload & management** — drag-and-drop upload, processing status, deletion, reprocessing
- **Semantic search** — embeddings stored in PostgreSQL via pgvector
- **RAG-powered chat** — answers grounded exclusively in your documents
- **Source attribution** — every response cites document name and page number
- **Conversation history** — persist and revisit all past exchanges
- **Dashboard** — stats on documents, conversations, and queries
- **Dark/light theme** — system-aware CSS variables
- **Fully Dockerized** — one command to run everything

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Database | PostgreSQL 16 + pgvector |
| AI | Google Gemini API (text-embedding-004 + gemini-1.5-flash) |
| Infra | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

## RAG Flow

```
PDF Upload
    │
    ▼
Text Extraction (pypdf, page-by-page)
    │
    ▼
Chunking (RecursiveCharacterTextSplitter, 1000 chars / 200 overlap)
    │
    ▼
Embedding Generation (Google text-embedding-004, 768 dimensions)
    │
    ▼
Vector Storage (PostgreSQL + pgvector, IVFFlat index)
    │
  QUERY
    │
    ▼
Query Embedding + Semantic Search (cosine similarity)
    │
    ▼
Context Assembly (top-K chunks, filtered by user + document)
    │
    ▼
Grounded Generation (Gemini, system-prompt guards prompt injection)
    │
    ▼
Answer + Sources (document name + page number)
```

---

## Requirements

- Docker Desktop
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/knowledgehub-ai.git
cd knowledgehub-ai
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set at minimum:

```env
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
GEMINI_API_KEY=<your-google-gemini-api-key>
```

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `SECRET_KEY` | JWT signing secret (32+ chars) | — |
| `GEMINI_API_KEY` | Google AI Studio API key | — |
| `GEMINI_GENERATION_MODEL` | Gemini model for text generation | `gemini-1.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Gemini model for embeddings | `models/text-embedding-004` |
| `CHUNK_SIZE` | Characters per chunk | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `RAG_TOP_K` | Chunks retrieved per query | `5` |
| `MAX_UPLOAD_SIZE_MB` | Max PDF file size | `50` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:5173` |

---

## API Endpoints

### Auth
```
POST /api/v1/auth/register    Create account
POST /api/v1/auth/login       Login → JWT pair
POST /api/v1/auth/refresh     Refresh tokens
POST /api/v1/auth/logout      Logout
```

### Documents
```
POST   /api/v1/documents/                Upload PDF
GET    /api/v1/documents/                List documents (paginated)
GET    /api/v1/documents/{id}            Document details
GET    /api/v1/documents/{id}/status     Processing status
DELETE /api/v1/documents/{id}            Delete document
POST   /api/v1/documents/{id}/reprocess  Reprocess through RAG
```

### Conversations
```
POST   /api/v1/conversations/                      Create conversation
GET    /api/v1/conversations/                      List conversations
GET    /api/v1/conversations/{id}                  Get with messages
POST   /api/v1/conversations/{id}/messages         Ask a question (RAG)
GET    /api/v1/conversations/{id}/messages         Message history
DELETE /api/v1/conversations/{id}                  Delete conversation
```

### Dashboard
```
GET /api/v1/dashboard/stats    Usage statistics
```

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Architecture

```
backend/app/
├── core/           Config, database, security, logging
├── modules/
│   ├── auth/       JWT auth (routes → service → repo)
│   ├── users/      User management
│   ├── documents/  PDF upload + management
│   ├── conversations/  Chat + message history
│   ├── rag/        Extract → Chunk → Embed → Retrieve → Generate
│   └── dashboard/  Stats
├── integrations/
│   └── gemini/     Isolated Gemini API wrapper
└── shared/         Exceptions, pagination, storage
```

---

## Limitations

- Scanned PDFs (image-only) are not supported — text extraction requires selectable text
- Embedded tables and complex layouts may lose formatting during extraction
- Concurrent uploads are limited by Gemini API rate limits (handled with retry/backoff)
- File storage is local filesystem — for production, swap `LocalStorage` with an S3 adapter

---

## Security Notes

- Document content is treated as untrusted data and cannot override system instructions (prompt injection defense)
- All document queries are scoped by `user_id` — users can only access their own data
- Passwords are hashed with bcrypt
- JWT tokens expire and support refresh rotation
- API keys are never exposed to the frontend

---

## License

MIT
