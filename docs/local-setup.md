# Local Development Setup

This guide walks you through running UKReady entirely on your local machine using Docker Compose. No AWS account required.

---

## Prerequisites

- **Docker Desktop** (v4.x+) — [install](https://www.docker.com/products/docker-desktop/)
- **Git**
- **An Anthropic API key** — [get one free](https://console.anthropic.com/) (required for AI responses)
- 4GB+ free RAM (sentence-transformer model + all services)

---

## Step 1: Clone the repository

```bash
git clone https://github.com/jeevabyte/uk-ready.git
cd uk-ready
```

---

## Step 2: Configure environment variables

```bash
cp .env.example .env.local
```

Open `.env.local` and set your Anthropic API key:

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-real-key-here
```

All other values in `.env.example` work as-is for local development.

> **Note:** `.env.local` is gitignored. Never commit it.

---

## Step 3: Start all services

```bash
docker compose up
```

This starts five services:

| Service | Port | What it does |
|---------|------|-------------|
| `postgres` | 5432 | PostgreSQL 15 database |
| `chroma` | 8001 | ChromaDB vector store |
| `ingest` | — | Scrapes + embeds gov.uk docs (runs once, then exits) |
| `backend` | 8000 | FastAPI API server (auto-reloads on file changes) |
| `frontend` | 3000 | Next.js dev server (hot module replacement) |

**First run note:** The `ingest` service downloads a ~90MB sentence-transformer model and scrapes 10 gov.uk pages. This takes 3–5 minutes on the first run. Subsequent starts skip ingestion (marker file detected).

Watch for this log line to know ingestion is complete:
```
ukready_ingest  | INFO: Ingestion complete {"documents_indexed": 47}
ukready_ingest exited with code 0
```

---

## Step 4: Open the app

Visit [http://localhost:3000](http://localhost:3000)

1. Select your visa type
2. Click through to the chat interface
3. Ask a question like: *"Can I switch employers?"*

---

## Step 5: Check the API

The FastAPI backend has interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs) (development mode only).

Health check:
```bash
curl http://localhost:8000/health
```

Expected response when fully ready:
```json
{
  "status": "ok",
  "vector_store": "ok",
  "ai_provider": "anthropic",
  "documents_indexed": 47
}
```

---

## Running Tests

```bash
# Run backend tests inside Docker (matches CI environment)
docker compose run --rm backend pytest tests/ -v

# Or run locally (requires Python 3.11 + uv installed)
cd backend
uv pip install -e ".[dev]"
pytest tests/ -v
```

---

## Re-ingesting Documents

If you want to re-scrape gov.uk documents (e.g. after adding new URLs):

```bash
# Force re-ingestion — deletes the marker file first
docker compose run --rm ingest python -m app.ingestion.embedder --force
```

Or to add new URLs, edit `backend/app/ingestion/scraper.py` and update the `GOV_UK_URLS` list.

---

## Development Workflow

### Backend changes (Python/FastAPI)
The backend container mounts `./backend` as a volume and runs with `--reload`. Changes to `.py` files are picked up automatically — no restart needed.

### Frontend changes (Next.js/TypeScript)
The frontend container also mounts source with hot module replacement. Changes to `.tsx`/`.ts` files refresh the browser automatically.

### Adding a new API endpoint
1. Create a new router in `backend/app/routers/`
2. Register it in `backend/main.py`: `app.include_router(your_router.router)`
3. Add types to `frontend/src/lib/api.ts`

### Adding a new gov.uk document
1. Add the URL to `GOV_UK_URLS` in `backend/app/ingestion/scraper.py`
2. Re-run ingestion: `docker compose run --rm ingest python -m app.ingestion.embedder --force`

---

## Troubleshooting

### `ingest` exits with code 1
- Check logs: `docker compose logs ingest`
- Usually caused by gov.uk being unreachable or rate-limited. Wait 60 seconds and retry.

### Backend returns 503
- Check `ANTHROPIC_API_KEY` is set correctly in `.env.local`
- Verify with: `docker compose exec backend env | grep ANTHROPIC`

### ChromaDB `degraded` in health check
- Wait for ChromaDB to be ready: `docker compose logs chroma`
- The ChromaDB container can take 15–20 seconds to start on first run.

### Port already in use
- Stop any running services: `docker compose down`
- Check for conflicting processes: `lsof -i :3000` or `lsof -i :8000`

### Reset everything and start fresh
```bash
docker compose down -v   # Removes containers + volumes (wipes data)
docker compose up        # Fresh start
```

---

## Using AWS Bedrock Instead of Anthropic

To test the production AI provider locally:

1. Ensure your AWS account has Bedrock model access enabled for `claude-sonnet-4-5-20251001` in `eu-west-2`
2. Update `.env.local`:
```env
AI_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=eu-west-2
```
3. Restart the backend: `docker compose restart backend`
