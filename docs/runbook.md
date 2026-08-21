# Tradly Platform Operations Runbook

**Environment:** Local Development, Docker, & Production Deployments  
**Author:** 11-Agent Swarm

---

## 1. Quickstart (Local Development)

### Backend API:
```bash
cd apps/api
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Gateway & Swagger UI will be available at `http://localhost:8000/docs`.

### Frontend Web Terminal:
```bash
cd apps/web
npm install
npm run dev
```
Web terminal will be available at `http://localhost:3000`.

---

## 2. Running Test Suites

Run the complete test suite (unit, domain math, integration, strategy engine):
```bash
cd apps/api
python -m pytest
```

---

## 3. Docker Compose Stack

Start PostgreSQL with pgvector, Redis, FastAPI Gateway, and Next.js Web:
```bash
cd infra/docker
docker compose up -d --build
```

---

## 4. Environment Variables Configuration

Create `.env` in `apps/api/` with:
```env
APP_ENV=production
DATABASE_URL=postgresql://tradly:tradlypass@localhost:5432/tradly
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=generate-a-secure-random-32-character-secret-key

# Optional external SaaS providers:
OANDA_API_KEY=
OANDA_ACCOUNT_ID=
GROQ_API_KEY=
OPENAI_API_KEY=
RESEND_API_KEY=
```
