# UKReady — System Architecture

## Overview

UKReady is a monorepo containing a Next.js frontend, FastAPI backend, and supporting infrastructure. The core feature is a RAG (Retrieval-Augmented Generation) pipeline that produces visa-type-aware answers sourced from official gov.uk guidance.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Next.js Frontend (localhost:3000 / Vercel)              │   │
│  │                                                           │   │
│  │  VisaSelector → localStorage → ChatInterface             │   │
│  │         ↓                           ↓                    │   │
│  │  Visa type persisted        POST /api/chat               │   │
│  └─────────────────────────────────────────────────────────-┘   │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ Next.js rewrite: /api/* → backend
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (localhost:8000 / Lambda)       │
│                                                                  │
│  POST /chat                                                      │
│       ↓                                                          │
│  RagPipeline.answer()                                            │
│       │                                                          │
│       ├─1─ Embed query (sentence-transformers)                   │
│       ├─2─ Retrieve top-5 chunks ──→ ChromaDB / OpenSearch       │
│       ├─3─ Build prompt (visa context + retrieved docs)          │
│       ├─4─ Call AI provider ──────→ Anthropic / Bedrock          │
│       └─5─ Parse response (confidence + sources)                 │
│                                                                  │
│  GET /health → checks ChromaDB + document count                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### Frontend (`frontend/`)

**Technology:** Next.js 14 (App Router) + TypeScript + Tailwind CSS

**Key design decisions:**
- **App Router** over Pages Router — better for future RSC usage and layouts
- **localStorage for visa state** — no backend session needed in MVP; simple and private
- **Next.js rewrites** proxy `/api/*` to the FastAPI backend — avoids CORS in development and production alike
- **No auth** in MVP — visa type is a non-sensitive preference, not personal data

**Component tree:**
```
layout.tsx (header + footer)
├── page.tsx (landing — visa selector)
│   └── VisaSelector.tsx
│       └── useVisaContext.ts (localStorage hook)
└── chat/page.tsx (Q&A interface)
    └── ChatInterface.tsx
        ├── MessageBubble.tsx
        │   └── SourceCitation.tsx
        └── lib/api.ts (typed fetch wrapper)
```

---

### Backend (`backend/`)

**Technology:** Python 3.11 + FastAPI + Pydantic v2

**Key design decisions:**

#### AI Provider Abstraction
The `AIProvider` ABC decouples the RAG pipeline from any specific model provider:

```
AIProvider (abstract)
├── AnthropicProvider  — direct API (local dev, AI_PROVIDER=anthropic)
├── BedrockProvider    — AWS Bedrock (production, AI_PROVIDER=bedrock)
└── OpenAIProvider     — fallback (AI_PROVIDER=openai)
```

Switching providers is a single env var change (`AI_PROVIDER=bedrock`). No code changes.

#### Vector Store Abstraction
Same pattern for the vector database:

```
VectorStore (abstract)
├── ChromaDBVectorStore  — local Docker (default)
└── OpenSearchVectorStore — AWS production (future)
```

#### RAG Pipeline Flow
1. **Query embedding**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, runs locally, no API key)
2. **Retrieval**: Top-5 chunks by cosine similarity from ChromaDB
3. **Prompt assembly**: Visa context string + retrieved chunk text + user question
4. **Inference**: AI provider returns text with embedded `CONFIDENCE: HIGH/MEDIUM/LOW` marker
5. **Response parsing**: Extract confidence marker, deduplicate source URLs, return `ChatResponse`

#### Visa Context Injection
Every prompt includes a detailed, visa-specific context string from `app/models/visa.py`. This prevents the LLM from giving generic or wrong-visa answers. Example for Graduate visa:

```
SYSTEM: The user is on a GRADUATE VISA.
Key facts:
- Duration: 2 years (3 if PhD)
- Work rights: Any job, any employer, no sponsorship required
- Cannot extend...
[+ retrieved gov.uk document chunks]
```

---

### Document Ingestion (`backend/app/ingestion/`)

**Run once** (via `docker compose up` → `ingest` service), then idempotent (marker file).

Pipeline:
```
scraper.py           embedder.py              vector_store.py
    │                     │                        │
gov.uk URLs ──→ ScrapedPage ──→ DocumentChunks ──→ ChromaDB
(10 pages)     (title, text,    (512 tokens,        (upsert,
               last_scraped)    50 overlap,          idempotent)
                                embeddings)
```

**Chunking rationale:** 512 tokens with 50-token overlap. This is:
- Large enough to include full policy paragraphs with context
- Small enough to remain semantically focused for retrieval
- Standard for RAG pipelines targeting 4k context models

---

### Vector Store — Local vs Production

| | Local (dev) | Production |
|---|---|---|
| Technology | ChromaDB | AWS OpenSearch Serverless |
| Setup | Docker Compose (zero config) | Terraform module (not yet deployed) |
| Embedding | all-MiniLM-L6-v2 (local) | Amazon Titan Embed v2 |
| Switch | `CHROMA_HOST=chroma` | `VECTOR_STORE=opensearch` (future) |

---

### Infrastructure (`infrastructure/terraform/`)

All resources are defined with feature flags (default: `false`) so nothing is deployed until explicitly enabled. The skeleton is ready for production deployment.

```
infrastructure/terraform/
├── main.tf                          # Root module — wires everything together
├── variables.tf                     # deploy_lambda / deploy_opensearch / deploy_rds flags
├── outputs.tf                       # ARNs + endpoints when deployed
├── modules/
│   ├── bedrock/    — Model invocation logging
│   ├── opensearch/ — Vector store (replaces ChromaDB)
│   ├── lambda/     — FastAPI backend + API Gateway v2
│   └── rds/        — Aurora Serverless v2 (PostgreSQL)
└── environments/dev/terraform.tfvars
```

**Region: `eu-west-2` (London)** — all resources are in London for UK data residency. This is important for GDPR compliance and for the Global Talent visa application evidence.

---

## Data Flow Diagram

```
User selects "Graduate visa"
         │
         ▼
localStorage.setItem("ukready_visa_type", "GRADUATE")
         │
         ▼ (navigate to /chat)
User types: "Can I switch employers?"
         │
         ▼
POST /api/chat
{
  "visa_type": "GRADUATE",
  "message": "Can I switch employers?",
  "conversation_id": null
}
         │ (Next.js rewrites to http://backend:8000/chat)
         ▼
FastAPI: RagPipeline.answer()
         │
         ├─ embed("Can I switch employers?")  → [0.12, -0.04, ...]  (384-dim)
         │
         ├─ ChromaDB.query(embedding, top_k=5)
         │    → ["Graduate visa holders can work... (gov.uk/graduate-visa)",
         │        "You can change employers... (gov.uk/graduate-visa/what-you-can-do)",
         │        ...]
         │
         ├─ Build system prompt:
         │    SYSTEM: User is on GRADUATE VISA. [visa context]. [retrieved docs]
         │    USER: Can I switch employers?
         │
         ├─ AnthropicProvider.complete(system, user)
         │    → "Yes, you can switch employers freely... CONFIDENCE: HIGH"
         │
         └─ Parse → ChatResponse{
                answer: "Yes, you can switch employers...",
                confidence: "HIGH",
                sources: [{url: "gov.uk/graduate-visa", ...}],
                conversation_id: "uuid",
                disclaimer: "This is information, not legal advice..."
              }
         │
         ▼
Frontend renders MessageBubble + SourceCitation
```

---

## Local Development Environment

See [local-setup.md](./local-setup.md) for full setup instructions.

```
docker compose up
    │
    ├── postgres  (port 5432) — PostgreSQL 15
    ├── chroma    (port 8001) — ChromaDB vector store
    ├── ingest    (exits)     — scrapes + embeds gov.uk docs
    ├── backend   (port 8000) — FastAPI + uvicorn --reload
    └── frontend  (port 3000) — Next.js dev server
```

---

## Security Considerations

- **No secrets in code** — all credentials via env vars, validated at startup
- **API key never sent to frontend** — all AI calls are server-side in FastAPI
- **CORS restricted** — only localhost:3000 and the production domain in production
- **Non-root Docker user** — backend runs as `appuser`, not root
- **S3 public access blocked** — documents bucket has all public access blocked
- **RDS encrypted** — storage encryption enabled on RDS Aurora
- **OpenSearch private** — network policy blocks public access

---

## Future Architecture (Post-MVP)

| Phase | Change |
|-------|--------|
| Auth (Week 5-6) | Add NextAuth.js + Cognito; move visa preference to DB |
| Tax calculator | New FastAPI router + HMRC tax band data ingestion |
| Salary benchmarker | ONS ASHE data ingestion + percentile calculation |
| Production deploy | Enable Terraform flags; point frontend to Lambda URL |
| Conversation memory | Store messages in PostgreSQL by conversation_id |
| OpenSearch migration | Implement OpenSearchVectorStore, point VECTOR_STORE env var |
