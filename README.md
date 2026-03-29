# UKReady — AI navigator for skilled migrants in the UK

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-red)](https://github.com/jeevabyte/uk-ready)
[![Built with Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black)](https://nextjs.org)
[![Built with FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![AI: Claude on AWS Bedrock](https://img.shields.io/badge/AI-Claude%20%7C%20AWS%20Bedrock-orange)](https://aws.amazon.com/bedrock/)
[![CI](https://github.com/jeevabyte/uk-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/jeevabyte/uk-ready/actions/workflows/ci.yml)

---

## What is this?

UKReady is a free AI assistant that helps skilled migrants navigate UK visa rules, work rights, and government systems — with answers that are **specific to your visa type**.

The problem: when a Graduate visa holder asks a generic AI "Can I switch employers?", they get a generic answer. When a Skilled Worker visa holder asks the same question, they should get a completely different answer — because the rules are completely different. Generic AI tools don't know which visa you're on.

UKReady fixes this. You tell it your visa once. Every answer after that is specific to your situation, sourced from official gov.uk guidance, with a confidence score and citation links.

**Who it's for:** The 400,000+ skilled migrants working in UK tech, finance, and healthcare who make high-stakes decisions about their immigration status every day.

---

## Who built this and why?

This project was built by a Senior Platform Engineer currently on a Graduate visa in the UK.

I built this because I kept getting wrong or incomplete answers from generic AI tools — answers that didn't account for my specific visa type. I found myself cross-referencing multiple gov.uk pages, Reddit threads, and immigration forums just to answer basic questions like "can I freelance on the side?" or "what happens if I take a pay cut?"

UKReady exists to make those answers clear, accurate, and visa-specific. It's not a side project — it's built for a real community of people making real life decisions.

This project is also being submitted as evidence for a [UK Global Talent visa](https://www.gov.uk/global-talent) endorsement application, demonstrating technical leadership and open source contribution to the UK tech ecosystem.

---

## Features — MVP (Week 1–2)

- **Visa-aware Q&A** — select your visa type once, get tailored answers every time
  - Graduate Visa
  - Skilled Worker Visa
  - Student Visa
  - Indefinite Leave to Remain (ILR)
- **Sourced from gov.uk** — answers backed by official UK government guidance via RAG
- **Confidence scoring** — every answer rated HIGH / MEDIUM / LOW
- **Source citations** — direct links to the gov.uk pages used to generate the answer
- **Legal disclaimer** — always present, because these are life decisions
- **Works locally** — `docker compose up` and you're running, no cloud account needed

### Coming soon
- [ ] UK tax calculator — visa-aware take-home pay (Week 3–4)
- [ ] Salary benchmarker — how does your offer compare to ONS data? (Week 3–4)
- [ ] User accounts — save your visa type and conversation history (Week 5–6)
- [ ] Job worth-it scorer — is this offer worth switching employers for? (Month 3–4)
- [ ] Community knowledge base — verified Q&A from the migrant community (Month 5+)
- [ ] Global Talent, BN(O), Innovator Founder visa support

---

## Quick Start (Local)

**Requirements:** Docker Desktop, Git, Anthropic API key ([get one free](https://console.anthropic.com/))

```bash
# 1. Clone
git clone https://github.com/jeevabyte/uk-ready.git
cd uk-ready

# 2. Configure environment
cp .env.example .env.local
# Edit .env.local — set ANTHROPIC_API_KEY=sk-ant-your-key-here

# 3. Start everything
docker compose up

# 4. Wait for ingestion to complete (~3-5 mins on first run)
# Watch for: "Ingestion complete {"documents_indexed": 47}"

# 5. Open the app
open http://localhost:3000
```

That's it. Select your visa type, ask a question, get a sourced answer.

For detailed setup and troubleshooting, see [docs/local-setup.md](docs/local-setup.md).

---

## Architecture

UKReady is a monorepo with a Next.js frontend, FastAPI backend, and a RAG pipeline backed by ChromaDB locally and AWS OpenSearch Serverless in production.

```
User browser → Next.js (Vercel) → FastAPI (AWS Lambda)
                                        │
                    ┌───────────────────┤
                    │                   │
              ChromaDB              AI Provider
          (vector search)       (Anthropic / Bedrock)
                    │
            gov.uk documents
          (scraped + embedded)
```

Key design decisions:
- **AI provider is swappable** — `AI_PROVIDER=anthropic|bedrock|openai` env var
- **Vector store is swappable** — ChromaDB locally, OpenSearch in production
- **Visa context injected into every prompt** — model cannot give generic answers
- **All answers include confidence + source citations** — no black-box responses

Full architecture documentation: [docs/architecture.md](docs/architecture.md)

---

## Project Structure

```
ukready-ai/
├── frontend/          Next.js 14 + TypeScript + Tailwind CSS
├── backend/           FastAPI + Python 3.11 + RAG pipeline
├── infrastructure/    Terraform IaC (AWS Bedrock, Lambda, OpenSearch, RDS)
├── docs/              Architecture, setup, and visa type reference
└── .github/workflows/ CI (lint + test) and deploy (placeholder)
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 14, TypeScript, Tailwind CSS | SSR, SEO, future community features |
| Backend | Python 3.11, FastAPI, Pydantic v2 | Async, type-safe, ML ecosystem |
| AI (local dev) | Anthropic Claude via direct API | Fast iteration, no AWS setup needed |
| AI (production) | Claude on AWS Bedrock | UK data residency, AWS-native logging |
| Vector store (local) | ChromaDB | Zero-config Docker, perfect for dev |
| Vector store (prod) | AWS OpenSearch Serverless | Scalable, AWS-native, no infra to manage |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Fast, local, no API key needed |
| Database | PostgreSQL 15 (local) / RDS Aurora Serverless v2 (prod) | Standard, reliable |
| IaC | Terraform | Everything defined as code, reproducible |
| CI/CD | GitHub Actions | Standard, integrates with GitHub |

---

## Contributing

Contributions are welcome — especially from people who have lived the problem.

**We especially want contributions from:**
- Skilled migrants in the UK who've experienced immigration confusion firsthand
- Immigration lawyers and advisors (for accuracy improvements and edge cases)
- Platform / DevOps engineers (for infrastructure and deployment improvements)
- Frontend developers (for accessibility and UX improvements)

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

**Quick contribution guide:**
```bash
git checkout -b feature/your-improvement
# Make changes, write tests
docker compose run --rm backend pytest tests/
git push origin feature/your-improvement
# Open a pull request
```

---

## Roadmap

| Phase | Features | Status |
|-------|---------|--------|
| Week 1–2 | Visa Q&A MVP (Graduate, Skilled Worker, Student, ILR) | ✅ In progress |
| Week 3–4 | UK tax calculator + salary benchmarker | Planned |
| Week 5–6 | User accounts + conversation history | Planned |
| Month 3–4 | Job worth-it scorer | Planned |
| Month 5+ | Community knowledge base | Planned |
| Ongoing | Additional visa types (Global Talent, BN(O), Innovator) | Planned |

---

## Accuracy & Limitations

UKReady sources answers from official gov.uk guidance via RAG retrieval. However:

- **Visa rules change.** The knowledge base is scraped periodically but may not reflect same-day changes to gov.uk.
- **This is not legal advice.** Every response includes a disclaimer. For actual visa decisions, consult a [registered immigration solicitor](https://www.gov.uk/find-an-immigration-adviser).
- **Confidence is self-reported.** HIGH confidence means the retrieved documents directly state the answer. LOW confidence means you should verify independently.

If you find an inaccurate answer, please [open a GitHub issue](https://github.com/jeevabyte/uk-ready/issues) with the question, the incorrect answer, and the correct gov.uk citation.

---

## License

MIT — free forever for anyone who needs it.

See [LICENSE](LICENSE).

---

## Acknowledgements

Built on official [gov.uk](https://www.gov.uk) guidance, which is published under the [Open Government Licence](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
