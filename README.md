# IDP — Phase 1 (Epic E0)

Configuration-driven document extraction platform. This scaffold covers
**Epic E0 (Option C)**: application type and template configuration with
auto-generated JSON schema and VLM prompt. Test runner (E0-07) and full
version history (E0-08) are deferred to Phase 2.

## Stack

- **Backend:** Python 3.11 + FastAPI + SQLAlchemy 2 + Alembic
- **DB:** Postgres 16
- **Frontend:** React 18 + Vite + TypeScript
- **Authoring LLM:** pluggable provider, env-selected
  - `LLM_PROVIDER=gemma` → self-hosted HTTP endpoint (e.g. vLLM / Ollama)
  - `LLM_PROVIDER=openai` → GPT-5 via OpenAI API
- **In-house VLM:** consumes prompt text generated here; not wired in E0

## Decisions captured for v1

| Area | Decision |
|---|---|
| Scope | Option C: E0-01 through E0-06 |
| Tenancy | Single-tenant |
| Admin | Internal ops only |
| UI language | English only |
| Field types | string, number, date, currency, list, object, regex validation |
| Authoring LLM | Single provider per deploy, switched by env var |

Open spec items deferred: E0-07 test runner, E0-08 immutable versioning,
multi-tenant template scoping, i18n.

## Layout

```
backend/   FastAPI app, models, migrations, LLM clients, generators
frontend/  Vite + React admin UI
docker-compose.yml   Postgres for local dev
```

## Quick start

```bash
docker compose up -d db
cd backend && cp .env.example .env && uv sync && uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# in another shell
cd frontend && npm install && npm run dev
```

Backend: http://localhost:8000 — OpenAPI at `/docs`
Frontend: http://localhost:5173

## Branch

Active dev branch: `claude/project-setup-ThtY9`.
