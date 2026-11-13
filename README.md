# PromptLab

A platform for versioning prompts and evaluating them rigorously — think **GitHub + RAGAS in one tool**.

Built with FastAPI + React, featuring git-like prompt versioning, LLM-as-judge evaluation metrics, A/B testing with statistical significance, and async Celery pipelines.

---

## Features

### Prompt Registry

- Create prompts with name, description, and tags
- Every save auto-creates a new version with a short hash + commit message
- Diff view between any two versions
- Tag versions as `dev`, `staging`, `production` — only one `production` per prompt
- Rollback: promote any older version back to production
- Variable support: auto-extract `{{variable}}` placeholders
- Fork prompts from any version

### Dataset Manager

- Upload evaluation datasets as CSV/JSON (`question`, `context`, `expected_answer`)
- Preview datasets in a table with filtering
- Generate synthetic Q&A pairs from any document via LLM
- Tag datasets by domain (`medical`, `legal`, `cs`)

### Model Registry

- Register any OpenAI-compatible LLM endpoint (OpenAI, Anthropic, local Ollama, etc.)
- Store metadata: context window, cost per 1k tokens, provider
- Mark models as **target** or **judge**

### Eval Engine

**LLM-as-judge metrics:**

- **Faithfulness** — does the answer stay within the context, or hallucinate?
- **Answer Relevance** — does the answer address the question?
- **Context Precision** — how much of the retrieved context was useful?
- **Context Recall** — did retrieval capture everything needed?

**Non-LLM metrics:**

- Latency (total time)
- Token count (input + output)
- Estimated cost per query (from model pricing)

**Run config:**

- Pick prompt version, model, dataset, judge model
- Set sample size (full or random N)
- Retry logic with exponential backoff
- Async execution via Celery + Redis

### A/B Testing Engine

- Compare two distinct completed eval runs you own on the same dataset
- Statistical significance via paired t-test
- Head-to-head metric table with 95% confidence intervals
- Pair by dataset row ID; retain unmatched rows and expose missing results and judge scores
- Compare human-overridden quality scores alongside lower-is-better latency, cost, and token counts
- Preserve raw A-minus-B deltas and confidence intervals; orient winners to each known metric's direction
- Declare an overall quality preference only with complete known coverage and unanimous quality metrics

The comparison is descriptive, not an automatic release recommendation. No primary metric or multiple-comparison correction is configured. Unknown metric directions never receive an assumed winner. Missing run totals leave coverage unverified. Cost and speed metrics do not vote against quality metrics; individually significant metric results should not be read as family-wise significance. Existing saved comparisons retain their historical results until recomputed.

Result-row coverage is separate from metric coverage. A single pair retains its observed difference but has no confidence interval or significance claim. New evaluation runs record the exact rows eligible for each metric; reference-answer metrics are inapplicable when no reference exists. Comparisons use eligibility only when both evaluation-time manifests match. Historical runs without manifests report conditional metric coverage as unknown rather than guessing from today's editable dataset. Retrying a partially recorded run with a changed manifest requires a new run.

New runs also fingerprint sampled row IDs, questions, contexts, reference answers and extras using canonical JSON. Different snapshots/samples are rejected even when the dataset ID is the same. A changed snapshot during a partially recorded retry requires a new run. Historical runs without fingerprints remain inspectable but cannot declare an overall preference. The fingerprint identifies exact serialized inputs, not semantic equivalence, annotation correctness, or an immutable backup of the dataset.

### Analytics

- Trend charts: track any metric over prompt versions (Recharts)
- Run comparison: side-by-side delta view
- Export eval runs as JSON or CSV

---

## Tech Stack

| Layer                | Tech                                                    |
| -------------------- | ------------------------------------------------------- |
| **Backend**          | FastAPI + SQLAlchemy async + PostgreSQL + Alembic       |
| **Job Queue**        | Redis + Celery                                          |
| **Frontend**         | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| **Auth**             | Clerk (JWT + OAuth)                                     |
| **LLM SDK**          | OpenAI Python SDK (any OpenAI-compatible endpoint)      |
| **Charts**           | Recharts                                                |
| **Package Managers** | `uv` (backend), `pnpm` (frontend)                       |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose (for PostgreSQL & Redis)
- [uv](https://docs.astral.sh/uv/) and [pnpm](https://pnpm.io/)

### 1. Clone & setup environment

```bash
git clone https://github.com/garg-tejas/prompt-lab
cd prompt-lab

# Copy env templates
cp .env.example .env
cp frontend/.env.example frontend/.env

# Fill in your Clerk keys in both files
# Get them from: https://dashboard.clerk.com/last-active?path=api-keys
```

### 2. Start infrastructure

```bash
docker-compose up -d postgres redis
```

### 3. Run backend

```bash
cd backend
uv sync                    # install deps
uv run alembic upgrade head # run migrations
uv run uvicorn app.main:app --reload
```

### 4. Run Celery worker (separate terminal)

```bash
cd backend
uv run celery -A app.tasks.celery_app worker --loglevel=info
```

### 5. Run frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Environment Variables

### Root `.env` (backend)

| Variable           | Description                                                                      |
| ------------------ | -------------------------------------------------------------------------------- |
| `DATABASE_URL`     | PostgreSQL async connection string                                               |
| `REDIS_URL`        | Redis broker URL                                                                 |
| `CLERK_JWT_ISSUER` | Your Clerk frontend API URL (e.g. `https://useful-pegasus-7.clerk.accounts.dev`) |
| `CLERK_SECRET_KEY` | Clerk secret key (`sk_test_...`)                                                 |
| `SECRET_KEY`       | App secret for session/signing                                                   |
| `ALLOWED_ORIGINS`  | CORS origins (comma-separated)                                                   |
| `OPENAI_API_KEY`   | Default LLM API key                                                              |
| `OPENAI_BASE_URL`  | Default LLM base URL                                                             |

### `frontend/.env`

| Variable                     | Description                           |
| ---------------------------- | ------------------------------------- |
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key (`pk_test_...`) |
| `VITE_API_URL`               | Backend API prefix (default: `/api`)  |

---

## Project Structure

```
prompt-lab/
├── .env.example               # Backend env template
├── docker-compose.yml         # Postgres + Redis + backend services
├── backend/
│   ├── pyproject.toml         # uv project config
│   ├── alembic/               # Database migrations
│   └── app/
│       ├── main.py            # FastAPI app entry
│       ├── config.py          # Pydantic settings
│       ├── database.py        # Async SQLAlchemy setup
│       ├── api/v1/            # API routes
│       │   ├── auth.py
│       │   ├── prompts.py
│       │   ├── datasets.py
│       │   ├── models.py
│       │   ├── eval_runs.py
│       │   ├── ab_tests.py
│       │   └── analytics.py
│       ├── models/            # SQLAlchemy models
│       ├── schemas/           # Pydantic schemas
│       ├── services/          # Business logic
│       └── tasks/             # Celery tasks
├── frontend/
│   ├── .env.example           # Frontend env template
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx           # React entry with ClerkProvider
│       ├── App.tsx            # Router setup
│       ├── components/        # Shared UI components
│       ├── pages/
│       │   ├── prompts/       # List, detail, form
│       │   ├── eval/          # Wizard, history, detail
│       │   ├── ab-tests/      # List, create, detail
│       │   ├── datasets/      # List, detail, upload, synthetic
│       │   ├── models/        # List, create
│       │   ├── analytics/     # Trends, compare
│       │   └── sign-in.tsx
│       └── types/             # TypeScript type definitions
```

---

## API Overview

| Endpoint                                           | Description              |
| -------------------------------------------------- | ------------------------ |
| `POST /api/v1/prompts`                             | Create prompt            |
| `POST /api/v1/prompts/{id}/versions`               | New version              |
| `POST /api/v1/prompts/{id}/versions/{vid}/promote` | Promote to production    |
| `GET /api/v1/prompts/{id}/versions/{a}/diff/{b}`   | Diff two versions        |
| `POST /api/v1/eval-runs`                           | Trigger eval run (async) |
| `GET /api/v1/eval-runs/{id}`                       | Get run results          |
| `GET /api/v1/eval-runs/{id}/export/json`           | Export as JSON           |
| `GET /api/v1/eval-runs/{id}/export/csv`            | Export as CSV            |
| `POST /api/v1/ab-tests`                            | Create A/B test (async)  |
| `GET /api/v1/analytics/prompts/{id}/trends`        | Metric trends over time  |
| `GET /api/v1/analytics/runs/{a}/compare/{b}`       | Compare two runs         |

---

## Build for Production

### Frontend

```bash
cd frontend
pnpm run build
# Output in dist/
```

### Backend (Docker)

```bash
docker-compose up --build
```

---

## Roadmap

- [x] Phase 1: Core (Prompt registry + Eval engine)
- [x] Phase 2: A/B Testing engine
- [x] Phase 3: Dataset manager + Model registry + Trends
- [x] Phase 4: CI gate (`.github/actions/promptlab-eval`), webhooks, badges
- [x] Phase 4: Live ingest (`POST /api/v1/ingest`, `sdk/promptlab.py`)
- [x] Phase 4: Regression check against the previous run on the same prompt, dataset, and model

### Connect a pipeline

Create a token on the Connect page. It is shown once and sent as `Authorization: Bearer pl_...`.

```python
from promptlab import PromptLab

lab = PromptLab("http://localhost:8000", "pl_...")
lab.ingest(
    prompt_id="<uuid>",
    inputs={"question": "...", "context": "...", "expected_answer": "..."},
    output="the model's answer",
)
```

Omit `output` and pass `model_id` to have PromptLab run the prompt. A completed eval that drops a metric by 0.1 or more against the previous matching run is marked `anomaly` and fires the `eval.anomaly` webhook.

Badge (no auth, latest completed run):

`GET /api/v1/badges/{prompt_id}.svg?metric=answer_correctness`

GitHub Action: `.github/actions/promptlab-eval`. It creates a run, polls until it finishes, and fails the job when the metric mean is under `min_score`.

---

## License

MIT
