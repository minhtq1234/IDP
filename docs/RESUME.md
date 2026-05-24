# Resume — pick up the IDP project in a new session

Hand this file to the new Claude Code session and say:
**"Read `docs/RESUME.md` and bring the project back up."**

The container is ephemeral, so nothing from the previous session's filesystem
carries over except what's committed in this repo. Postgres, backend deps,
the `.env` file, and the running servers all need to be re-established.

---

## 1. Bring up Postgres

```bash
sudo pg_ctlcluster 16 main start
sudo -u postgres psql -c "CREATE USER idp WITH PASSWORD 'idp' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE idp OWNER idp;"
```

If the user already exists from a prior session, the `CREATE USER` line will
error — that's fine, just continue.

## 2. Backend: install + migrate

```bash
cd /home/user/IDP/backend
python3 -m venv .venv
.venv/bin/pip install -q \
  "fastapi>=0.115" "uvicorn[standard]>=0.30" "sqlalchemy>=2.0" \
  "alembic>=1.13" "psycopg[binary]>=3.2" "pydantic>=2.7" \
  "pydantic-settings>=2.4" "httpx>=0.27" "python-multipart>=0.0.9" \
  pytest
```

Create `backend/.env` (gitignored). Ask the user for the Gemma API key
— don't fabricate one. The other values are fixed:

```env
DATABASE_URL=postgresql+psycopg://idp:idp@localhost:5432/idp

LLM_PROVIDER=gemma

GEMMA_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn
GEMMA_MODEL=google/gemma-4-31b-it
GEMMA_API_KEY=<ask the user>

OPENAI_API_KEY=
OPENAI_MODEL=gpt-5
```

Run migrations (seeds CCCD, Payslip, Bank Statement, Retail Personal Loan):

```bash
cd /home/user/IDP/backend
.venv/bin/alembic upgrade head
```

Smoke-test:

```bash
.venv/bin/python -m pytest tests/ -q   # expect 8 passed
```

## 3. Start backend

```bash
cd /home/user/IDP/backend
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
disown
sleep 3
curl -s http://localhost:8000/health     # {"status":"ok"}
```

## 4. Frontend: install + start

```bash
cd /home/user/IDP/frontend
npm install --no-audit --no-fund
nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/frontend.log 2>&1 &
disown
sleep 4
curl -sI http://localhost:5173/ | head -1   # HTTP/1.1 200 OK
```

## 5. Verify the Gemma wiring

The previous session was blocked by `403 Host not in allowlist`. That host
is `maas-llm-aiplatform-hcm.api.vngcloud.vn` and should now be in the
environment's Custom **Allowed domains**. Confirm with a direct call:

```bash
curl -sS -m 30 -w "\nHTTP %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GEMMA_KEY" \
  'https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1/chat/completions' \
  --data '{"model":"google/gemma-4-31b-it","messages":[{"role":"user","content":"Say hi in one word."}],"max_tokens":20}'
```

Expect `HTTP 200` and a JSON body with `choices[0].message.content`.
If still `403 Host not in allowlist`, the allowlist change didn't take
— ask the user to start a fresh session after saving the policy.

Now exercise the app's authoring LLM path:

```bash
curl -sS -X POST -H "Content-Type: application/json" \
  http://localhost:8000/suggest \
  --data '{
    "document_type_name":"Salary Certificate",
    "description":"Employer-issued income verification for loan applications",
    "sample_text":"Cong ty ABC xac nhan nhan vien Nguyen Van A, chuc danh Senior Engineer, thu nhap hang thang 25,000,000 VND. Ngay cap: 01/05/2026."
  }'
```

Expect a JSON object like `{"fields":[...],"provider":"gemma"}` where each
field has `name`, `data_type`, `required`, `hint`. Confirm the `name`s are
snake_case and `data_type` is one of `string|number|date|currency|list|object`.

## 6. Drive the UI (optional)

The frontend lives at http://localhost:5173/. The "LLM Field Suggestion"
card on any template editor calls `POST /suggest`. Click **Suggest fields**
with sample text pasted in — it should populate the field grid with
Gemma's proposals.

## Project state recap

- Active branch: `claude/project-setup-ThtY9`
- Epic E0 Option C is implemented (US-E0-01 through US-E0-06).
- Tech: FastAPI + SQLAlchemy 2 + Alembic + Postgres 16; React 18 + Vite + TS.
- Authoring LLM: `LLM_PROVIDER=gemma|openai`, single provider per deploy.
- Open follow-ups: auth/admin login, E1 pipeline wiring (real VLM extraction),
  full template versioning (US-E0-08), test runner (US-E0-07).

## Things NOT to do

- Don't commit `backend/.env` — it's gitignored on purpose.
- Don't `git push` to anything other than `claude/project-setup-ThtY9`
  unless the user says otherwise.
- Don't change the schema generator or prompt template without checking
  with the user — those are centralised on purpose (US-E0-06 AC#4).
