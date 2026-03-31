# FB Support Bot

RAG-based customer support bot for Facebook Messenger, with a web dashboard for support agents. The project uses a FastAPI backend, PostgreSQL/Supabase for storage, and a lightweight HTML/CSS/JavaScript frontend.

## Overview

This repository contains:

- A webhook/API backend to ingest customer messages, store conversations, and power admin actions
- A knowledge-base ingestion pipeline for Retrieval-Augmented Generation (RAG)
- A browser-based support dashboard with Supabase-authenticated admin actions
- Realtime updates via Postgres Realtime (frontend) and an in-memory SSE broker (backend)

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Uvicorn
- Database: PostgreSQL (Supabase-compatible), pgvector
- AI: Groq API (`llama-3.3-70b-versatile`), sentence-transformers (`all-MiniLM-L6-v2`)
- Frontend: Vanilla HTML/CSS/JavaScript + Supabase JS SDK
- Integrations: Meta Graph API (Facebook Messenger)

## Repository Structure

```text
fb-support-bot/
  backend/
    app/
      api/routes/           # health, chat, admin, messenger webhook
      core/                 # settings + Supabase JWT verification
      db/                   # SQLAlchemy models/session/base
      rag/                  # embedding + retrieval helper
      realtime/             # in-memory event broker (SSE)
      services/             # Meta send APIs, Groq responder, FB profile lookup
    scripts/                # KB ingestion/chunking/loaders/db writes
    worker.py               # async bot worker (currently commented/outdated)
    requirements.txt
  frontend/
    dashboard.html
    login.html
    css/main.css
    js/config.js
    js/login.js
    js/dashboard.js
```

## Current Feature Status

Implemented:

- Messenger webhook verification + inbound message persistence
- Conversation and message browsing APIs
- Admin APIs for status updates and manual replies (Supabase JWT protected)
- Dashboard login and inbox/chat workflow
- KB ingestion for PDF/DOCX/MD/TXT and vector storage in pgvector

In progress / important caveats:

- `worker.py` is largely commented legacy code, so queued `bot_jobs` are not auto-processed right now
- RAG retrieval utilities exist, but the live webhook path currently enqueues jobs instead of generating immediate AI replies
- No migration tooling (Alembic) is included; schema setup is manual
- SSE endpoint exists in backend (`/api/events/conversations/{id}`), while frontend currently uses Supabase Postgres Realtime
- WhatsApp route files exist in the codebase, but WhatsApp functionality is currently not included in this project README scope

## API Endpoints

### Health

- `GET /` - Basic app check
- `GET /health` - Service health metadata
- `GET /health/db` - Database connectivity check

### Chat and Realtime

- `GET /api/conversations` - List conversations (latest first)
- `GET /api/conversations/{conversation_id}/messages` - Get message history
- `GET /api/events/conversations/{conversation_id}` - SSE stream for conversation messages
- `POST /api/debug/inbound` - Simulate inbound message (debug)
- `POST /api/debug/outbound` - Simulate outbound message (debug)

### Admin (requires Supabase Bearer JWT)

- `POST /api/admin/conversations/{conversation_id}/status?status=BOT_ACTIVE|NEEDS_HUMAN|RESOLVED`
- `POST /api/admin/conversations/{conversation_id}/reply?content=...`

### Channel Webhooks and Tests

- `GET /webhook`, `POST /webhook` - Facebook Messenger verification/events

## Database Model (Core Tables)

- `customers`: platform identity field (currently used for Facebook in active flow), user id, optional name
- `conversations`: one active thread per customer with status lifecycle
- `messages`: inbound/outbound/admin/bot messages
- `bot_jobs`: queued jobs intended for async bot processing
- `kb_documents`, `kb_chunks`: knowledge base source docs and embedded chunks

## Environment Variables

Create `backend/.env` and configure at least:

- App: `APP_NAME`, `ENV`
- Database: `DATABASE_URL`
- Groq: `GROQ_API_KEY`, `GROQ_MODEL`
- Messenger: `FB_VERIFY_TOKEN`, `FB_PAGE_ACCESS_TOKEN`, `FB_APP_SECRET`
- Supabase auth: `SUPABASE_URL`, `SUPABASE_JWT_AUD`, `SUPABASE_ANON_KEY`

Also update frontend config:

- `frontend/js/config.js` with your `API_BASE`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY`

## Setup and Run

### 1) Backend install

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Initialize database

This project does not include migrations. Create required tables manually (based on `backend/app/db/models.py`) and ensure pgvector is enabled:

```sql
create extension if not exists vector;
```

RAG retrieval expects a SQL function named `match_kb_chunks(vector(384), int)`.

### 3) Ingest knowledge base files

```bash
cd backend
python -m scripts.ingest_kb --path kb_sources --source company_docs --reindex
```

Supported file types: `.pdf`, `.docx`, `.md`, `.txt`

### 4) Start API

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- OpenAPI docs: `http://127.0.0.1:8000/docs`

### 5) Run frontend

Serve `frontend/` with any static server (recommended), then open `login.html`:

```bash
npx http-server frontend
```

## Security Notes

- Do not commit real API keys, tokens, or DB passwords.
- Rotate any credentials that were accidentally exposed.
- Restrict CORS and webhook signature policies for production.
- Consider auth protection for non-admin conversation list/message endpoints if dashboard is public-facing.

## Suggested Next Improvements

- Re-enable/fix `worker.py` and connect `bot_jobs` to the Groq + RAG pipeline
- Add Alembic migrations and SQL bootstrap scripts
- Move frontend hardcoded config to environment-driven build or server-side injection
- Replace in-memory broker with Redis/pub-sub for multi-instance scalability
- Add tests for webhook idempotency, auth verification, and admin flows

## License

Add a license file (`LICENSE`) before publishing publicly on GitHub.
