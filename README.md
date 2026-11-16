<div align="center">

# 🧠 KnowledgeHub AI

**Turn your PDFs into a conversational knowledge base.**

Ask questions in natural language and get accurate answers grounded in your documents — with citations down to the exact page.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+pgvector-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)](https://aistudio.google.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## The Problem

Searching through large document collections is slow and unreliable. Ctrl+F doesn't understand context. KnowledgeHub AI lets you *talk* to your documents — upload PDFs, ask anything, and get precise answers with source references you can verify instantly.

---

## Features

| | Feature | Description |
|---|---|---|
| 🔐 | **Secure Auth** | JWT register, login, and token refresh rotation |
| 📄 | **PDF Management** | Drag-and-drop upload, processing status, deletion, reprocessing |
| 🔍 | **Semantic Search** | 768-dim embeddings stored in PostgreSQL via pgvector |
| 🤖 | **RAG Chat** | Answers grounded exclusively in your uploaded documents |
| 📌 | **Source Attribution** | Every answer cites document name and page number |
| 💬 | **Conversation History** | Persist and revisit all past exchanges |
| 📊 | **Dashboard** | Stats on documents, conversations, and queries |
| 🌗 | **Dark / Light Theme** | System-aware, no flash |
| 🐳 | **Fully Dockerized** | One command to run everything |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Database | PostgreSQL 16 + pgvector |
| AI | Google Gemini (`text-embedding-004` + `gemini-1.5-flash`) |
| Infra | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

## How RAG Works

```
PDF Upload
    │
    ▼
Text Extraction ──── pypdf, page-by-page
    │
    ▼
Chunking ──────────── RecursiveCharacterTextSplitter (1 000 chars / 200 overlap)
    │
    ▼
Embeddings ────────── Google text-embedding-004 (768 dimensions)
    │
    ▼
Vector Storage ─────── PostgreSQL + pgvector (IVFFlat cosine index)
    │
  QUERY
    │
    ▼
Query Embedding + Semantic Search (cosine similarity, top-K)
    │
    ▼
Context Assembly ───── top-K chunks, scoped by user + document
    │
    ▼
Grounded Generation ── Gemini with system-prompt injection guard
    │
    ▼
Answer + Sources ────── document name + page number
```

---

## Quick Start

### Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Google Gemini API key](https://aistudio.google.com/app/apikey)

### 1 — Clone

```bash
git clone https://github.com/your-username/knowledgehub-ai.git
cd knowledgehub-ai
```

### 2 — Configure

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in the two required values:

```env
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your-secret-key>

GEMINI_API_KEY=<your-google-gemini-api-key>
```

### 3 — Run

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Interactive API Docs | http://localhost:8000/docs |
| Database | localhost:5432 |

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `SECRET_KEY` | JWT signing secret (32+ chars) | — |
| `GEMINI_API_KEY` | Google AI Studio API key | — |
| `GEMINI_GENERATION_MODEL` | Model for text generation | `gemini-1.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Model for embeddings | `models/text-embedding-004` |
| `CHUNK_SIZE` | Characters per chunk | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `RAG_TOP_K` | Chunks retrieved per query | `5` |
| `MAX_UPLOAD_SIZE_MB` | Max PDF file size | `50` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:5173` |

---

## API Reference

<details>
<summary><strong>Auth</strong></summary>

```
POST /api/v1/auth/register    Create account
POST /api/v1/auth/login       Login → JWT pair
POST /api/v1/auth/refresh     Refresh tokens
POST /api/v1/auth/logout      Logout
```
</details>

<details>
<summary><strong>Documents</strong></summary>

```
POST   /api/v1/documents/                Upload PDF
GET    /api/v1/documents/                List documents (paginated)
GET    /api/v1/documents/{id}            Document details
GET    /api/v1/documents/{id}/status     Processing status
DELETE /api/v1/documents/{id}            Delete document
POST   /api/v1/documents/{id}/reprocess  Reprocess through RAG
```
</details>

<details>
<summary><strong>Conversations</strong></summary>

```
POST   /api/v1/conversations/                  Create conversation
GET    /api/v1/conversations/                  List conversations
GET    /api/v1/conversations/{id}              Get with messages
POST   /api/v1/conversations/{id}/messages     Ask a question (RAG)
GET    /api/v1/conversations/{id}/messages     Message history
DELETE /api/v1/conversations/{id}              Delete conversation
```
</details>

<details>
<summary><strong>Dashboard</strong></summary>

```
GET /api/v1/dashboard/stats    Usage statistics
```
</details>

---

## Architecture

```
backend/app/
├── core/              Config, database, security, logging
├── modules/
│   ├── auth/          JWT auth (routes → service → repo)
│   ├── users/         User management
│   ├── documents/     PDF upload + management
│   ├── conversations/ Chat + message history
│   ├── rag/           Extract → Chunk → Embed → Retrieve → Generate
│   └── dashboard/     Stats
├── integrations/
│   └── gemini/        Isolated Gemini API wrapper
└── shared/            Exceptions, pagination, storage
```

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Limitations

- **Scanned PDFs** (image-only) are not supported — text extraction requires selectable text
- **Complex layouts** (tables, multi-column) may lose formatting during extraction
- **Concurrent uploads** are rate-limited by the Gemini API (retry/backoff is handled automatically)
- **File storage** is local filesystem — swap `LocalStorage` with an S3 adapter for production

---

## Security

- Prompt injection defense — document content cannot override system instructions
- All queries are scoped by `user_id` — users only access their own data
- Passwords hashed with bcrypt
- JWT tokens expire with refresh rotation
- API keys never exposed to the frontend

---

## License

[MIT](LICENSE)
