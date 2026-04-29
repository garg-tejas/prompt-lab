# End-to-End Setup & Walkthrough

This guide gets PromptLab running locally and walks through a complete user flow.

---

## Prerequisites

- Python 3.11+ with [uv](https://docs.astral.sh/uv/) installed
- Node.js 20+ with [pnpm](https://pnpm.io/) installed
- Docker + Docker Compose
- A [Clerk](https://clerk.com) account (free tier works)
- An OpenAI API key (or any OpenAI-compatible endpoint)

---

## Step 1: Environment Files

### 1.1 Copy templates

```bash
cd promptLab

cp .env.example .env
cp frontend/.env.example frontend/.env
```

### 1.2 Get Clerk keys

Go to [Clerk Dashboard → API Keys](https://dashboard.clerk.com/last-active?path=api-keys) and copy:

1. **Publishable key** (starts with `pk_test_...` or `pk_live_...`)
2. **Secret key** (starts with `sk_test_...` or `sk_live_...`)
3. **Frontend API URL** (looks like `https://useful-pegasus-7.clerk.accounts.dev`)

### 1.3 Fill in `.env` (project root)

```bash
# Already correct — only change these 3:
CLERK_JWT_ISSUER=https://useful-pegasus-7.clerk.accounts.dev
CLERK_SECRET_KEY=sk_test_YOUR_ACTUAL_SECRET_KEY

# Add your LLM key
OPENAI_API_KEY=sk-...
```

### 1.4 Fill in `frontend/.env`

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_PUBLISHABLE_KEY
VITE_API_URL=/api
```

---

## Step 2: Start Infrastructure

```bash
docker-compose up -d postgres redis
```

Verify:
```bash
docker-compose ps
# Both postgres and redis should show "running"
```

---

## Step 3: Start Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**

Test it:
```bash
curl http://localhost:8000/health
# → {"status":"ok","environment":"development"}
```

---

## Step 4: Start Celery Worker

Open a **new terminal**:

```bash
cd backend
uv run celery -A app.tasks.celery_app worker --loglevel=info
```

> Keep this running. It processes eval runs and A/B tests in the background.

---

## Step 5: Start Frontend

Open a **new terminal**:

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend runs at **http://localhost:5173**

---

## Step 6: First-Time Walkthrough

### 6.1 Sign up

Open http://localhost:5173 → you should see a Clerk sign-in page.

- Click "Sign up" → create an account with email + password
- Clerk will auto-create your user in the local PostgreSQL database on first API call

### 6.2 Register a Judge Model

Before you can run evaluations, you need at least one LLM endpoint registered.

1. Click **Models** in the top nav
2. Click **Add Model**
3. Fill in:
   - **Name**: `GPT-4 Judge`
   - **Model Name**: `gpt-4`
   - **Provider**: `openai`
   - **Base URL**: `https://api.openai.com/v1`
   - **API Key**: your OpenAI key
   - **Context Window**: `8192`
   - **Cost / 1k Input**: `0.03`
   - **Cost / 1k Output**: `0.06`
   - Check **Use as judge model**
4. Click **Add Model**

### 6.3 Create a Prompt

1. Click **Prompts** in the top nav
2. Click **New Prompt**
3. Fill in:
   - **Name**: `RAG Q&A`
   - **Content**:
     ```
     You are a helpful assistant. Answer the question based on the provided context.

     Context: {{context}}
     Question: {{question}}
     ```
   - **Commit Message**: `Initial version`
4. Click **Save Prompt**

### 6.4 Create a Dataset

You have two options:

**Option A: Upload CSV**

1. Click **Datasets** → **Upload**
2. Use the provided `demo-dataset.csv`:
   - **Name**: `Demo QA`
   - Select the file
3. Click **Upload Dataset**

**Option B: Synthetic Generation**

1. Click **Datasets** → **Synthetic**
2. Paste a document into the **Context** field
3. Set **Number of Q&A pairs**: `5`
4. Click **Generate**

### 6.5 Run an Evaluation

1. Click **Runs** → **New Eval**
2. **Step 1**: Select your `RAG Q&A` prompt → pick the `production` version
3. **Step 2**: Select your `Demo QA` dataset
4. **Step 3**: Select your `GPT-4 Judge` model as both **Target Model** and **Judge Model**
5. **Step 4**: Give it a name like `Baseline eval`
6. Click **Start Evaluation**

The run will show as **pending** → **running** → refresh the page after ~30-60 seconds to see **completed** with scores.

### 6.6 View Results

Click on the run name to see:
- **Metrics summary** (faithfulness, answer_relevance, etc.)
- **Per-sample results** table with latency, tokens, cost, and individual scores
- **Export** buttons (JSON / CSV) in the top-right

### 6.7 Create a New Prompt Version

1. Go back to **Prompts** → click your `RAG Q&A` prompt
2. Click **New Version**
3. Update the content (e.g., add "Think step by step." to the prompt)
4. **Commit Message**: `Added CoT`
5. Click **Save Version**

### 6.8 A/B Test

1. Click **A/B Tests** → **New A/B Test**
2. **Run A**: select your first (baseline) eval run
3. **Run B**: select the eval run from your new version
   - You may need to run a second eval first on the new version
4. Click **Run Comparison**

After ~10 seconds, refresh to see:
- Head-to-head metric table with **mean diff**, **95% CI**, **significance**
- Overall winner banner
- Per-sample breakdown

### 6.9 View Trends

1. Go to **Prompts**
2. Click **Trends** on any prompt card
3. Switch between metrics (faithfulness, answer_relevance, etc.)
4. See your prompt improving (or regressing) over versions as a line chart

---

## Troubleshooting

### "Not authenticated" error
- Make sure both `.env` files are filled in correctly
- Check that `CLERK_JWT_ISSUER` has **no trailing slash**
- Verify your Clerk publishable key matches your account's domain

### Eval run stays "pending"
- Make sure Celery worker is running (`uv run celery -A app.tasks.celery_app worker`)
- Check Redis is running: `docker-compose ps`

### "No judge model available"
- Register at least one model with **Use as judge model** checked
- The synthetic dataset generator and eval engine both require a judge model

### Backend can't find `.env`
- Make sure `.env` is at the **project root** (same level as `docker-compose.yml`)
- Backend looks for `../../.env` relative to `backend/app/config.py`

### Frontend can't reach backend
- Backend must be running on port 8000
- Frontend proxy is configured in `vite.config.ts` — no manual CORS setup needed for dev

---

## File Reference

| File | Purpose |
|------|---------|
| `.env` | Backend env (Clerk secret, DB, Redis, LLM keys) |
| `frontend/.env` | Frontend env (Clerk publishable key) |
| `demo-dataset.csv` | Sample dataset for testing |
| `docker-compose.yml` | Postgres + Redis + Celery worker |
| `backend/app/config.py` | Settings loader (reads `../../.env`) |
| `frontend/vite.config.ts` | Dev proxy to backend (:8000) |

---

## All Services Summary

| Service | Terminal Command | URL |
|---------|-----------------|-----|
| PostgreSQL | `docker-compose up -d postgres` | localhost:5432 |
| Redis | `docker-compose up -d redis` | localhost:6379 |
| Backend | `uv run uvicorn app.main:app --reload` | http://localhost:8000 |
| Celery | `uv run celery -A app.tasks.celery_app worker --loglevel=info` | — |
| Frontend | `pnpm dev` | http://localhost:5173 |
