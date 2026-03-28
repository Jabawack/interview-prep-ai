# InterviewPrepAI

AI-powered interview preparation assistant. Ask about jobs, companies, and interview prep — the system runs specialized agents in parallel to research and compose answers in real time.

## Stack

- **Frontend**: Next.js 15, React 19, TailwindCSS v4
- **Backend**: FastAPI, LangGraph, LangChain
- **LLM**: OpenAI (via LangChain-OpenAI)
- **Database**: Neon (Postgres + pgvector)
- **Streaming**: SSE via sse-starlette
- **Job Data**: python-jobspy

## Architecture

```
User Message
  → Intent Classification
  → Parallel Subagents (Job Search, Company Research)
  → Response Composer
  → SSE Stream to Client
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Neon](https://neon.tech) database
- An [OpenAI](https://platform.openai.com) API key

### Environment

Copy the example env file and fill in your values:

```bash
cp .env.example .env.local
```

Required variables:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `NEON_DATABASE_URL` | Neon Postgres connection string |

Optional:

| Variable | Description |
|---|---|
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing (`true`/`false`) |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `NEXT_PUBLIC_API_URL` | Backend URL (defaults to `http://localhost:8000`) |

### Database

Run the migrations against your Neon database in order:

```bash
psql $NEON_DATABASE_URL -f migrations/001_initial_schema.sql
psql $NEON_DATABASE_URL -f migrations/002_job_postings.sql
psql $NEON_DATABASE_URL -f migrations/003_company_profiles.sql
psql $NEON_DATABASE_URL -f migrations/004_interview_prep.sql
```

### Backend

```bash
cd src/backend
pip install -e .
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev
```

The app will be running at [http://localhost:3000](http://localhost:3000).

## Testing

```bash
cd src/backend
pytest
```
