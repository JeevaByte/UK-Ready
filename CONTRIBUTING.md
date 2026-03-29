# Contributing to UKReady

Thank you for your interest in contributing. UKReady exists to help real people — skilled migrants making high-stakes decisions about their immigration status. That means accuracy and quality are non-negotiable.

---

## Who we especially welcome

- **Skilled migrants in the UK** — you understand the problems firsthand. Your lived experience is the most valuable contribution.
- **Immigration lawyers and advisors** — for accuracy improvements, edge cases, and flagging where our answers could mislead.
- **Platform / DevOps engineers** — for infrastructure, deployment, and reliability improvements.
- **Frontend developers** — for accessibility (WCAG compliance), UX, and internationalisation.
- **Data contributors** — for adding new gov.uk document sources or improving the RAG retrieval quality.

---

## Types of contributions needed

### High priority
- [ ] **Accuracy fixes** — if you find a wrong answer, open an issue with the correct gov.uk citation
- [ ] **New gov.uk document sources** — add URLs to `backend/app/ingestion/scraper.py`
- [ ] **New visa types** — Global Talent, BN(O) Overseas, Innovator Founder, Family visa

### Medium priority
- [ ] **Translations** — translate the UI to other languages (Polish, Urdu, Mandarin, Malayalam...)
- [ ] **Regional guides** — Scotland, Wales, Northern Ireland have different systems in some areas
- [ ] **Accessibility** — ensure the app meets WCAG 2.1 AA

### Infrastructure / Developer Experience
- [ ] **Production deployment** — help configure the Terraform modules and CI/CD
- [ ] **Performance** — improve RAG retrieval quality or reduce latency
- [ ] **Observability** — structured logging, metrics, tracing

---

## Code of conduct

This project serves vulnerable people making life-changing decisions. Please keep this in mind:

1. **Accuracy first.** If you're not sure an answer is correct, open an issue rather than submitting a PR. Wrong answers about visa rules can harm real people.
2. **Be respectful.** Contributors come from all backgrounds and immigration statuses.
3. **Cite your sources.** Any claim about visa rules must be backed by a gov.uk URL.
4. **No personal data.** Do not commit any personal information, API keys, or credentials.

---

## How to contribute

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/uk-ready.git
cd uk-ready
```

### 2. Create a branch

```bash
git checkout -b feature/your-improvement
# or
git checkout -b fix/inaccurate-graduate-visa-answer
```

Use descriptive branch names. Prefix with `feature/`, `fix/`, `docs/`, or `infra/`.

### 3. Set up local development

Follow [docs/local-setup.md](docs/local-setup.md). The short version:

```bash
cp .env.example .env.local
# Add your ANTHROPIC_API_KEY to .env.local
docker compose up
```

### 4. Make your changes

- For backend changes, the server auto-reloads on save
- For frontend changes, the dev server hot-reloads
- Write tests for any new functionality

### 5. Run tests

```bash
# Backend tests
docker compose run --rm backend pytest tests/ -v

# Frontend type check + lint
cd frontend && npm run type-check && npm run lint
```

All tests must pass before submitting a PR.

### 6. Submit a pull request

Push your branch and open a PR against `main`. Include:
- A clear description of what changed and why
- For accuracy fixes: the incorrect answer, the correct answer, and the gov.uk URL proving it
- For new features: a brief demo (screenshot or example Q&A)

---

## Development guidelines

### Python (backend)

- Python 3.11+ only
- Type hints on all public functions — `mypy --strict` must pass
- Linting: `ruff check app/ tests/` — zero warnings
- Every public function/class needs a docstring
- Error handling: use structured logging (`logger.error(..., exc_info=exc)`)
- No secrets in code — all config via environment variables in `app/config.py`

### TypeScript (frontend)

- Strict TypeScript — `tsc --noEmit` must pass
- ESLint — `npx eslint src/` with zero warnings
- No `any` types without a comment explaining why
- Components should be accessible (use semantic HTML, ARIA labels where needed)

### Visa accuracy

- Every answer about visa rules must be traceable to a gov.uk page
- Use the `VISA_CONTEXT` dict in `backend/app/models/visa.py` to add/correct visa-specific facts
- If adding a new visa type, add it to:
  - `VisaType` enum in `backend/app/models/visa.py`
  - `VISA_CONTEXT` dict in the same file
  - `VISA_DISPLAY_NAMES` and `VISA_DESCRIPTIONS` in `frontend/src/lib/api.ts`
  - `frontend/src/components/VisaSelector.tsx`
  - `docs/visa-types.md`

### Adding new gov.uk document sources

1. Add the URL to `GOV_UK_URLS` in `backend/app/ingestion/scraper.py`
2. Test scraping works: `docker compose run --rm ingest python -c "from app.ingestion.scraper import scrape_page; p = scrape_page('YOUR_URL'); print(p.title, len(p.content))"`
3. Re-ingest: `docker compose run --rm ingest python -m app.ingestion.embedder --force`
4. Test a relevant question in the chat interface

---

## Reporting accuracy issues

If you find an answer that is **factually wrong** about UK visa rules:

1. [Open a GitHub issue](https://github.com/jeevabyte/uk-ready/issues/new) with the label `accuracy`
2. Include:
   - The visa type selected
   - The question asked
   - The incorrect answer given
   - The correct answer with a gov.uk URL

Accuracy issues are the highest priority for this project. We aim to fix them within 48 hours.

---

## Questions?

Open a [GitHub Discussion](https://github.com/jeevabyte/uk-ready/discussions) for questions about the project, contributing, or UK visa rules.
