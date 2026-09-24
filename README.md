# FindOne

Personal job hunt helper. Phase 0–1: API, SQLite, resume store. Phase 2: local ATS scoring. Phase 3: job table, JSON import, list/filter.

## Run backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy ..\.env.example ..\.env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Status: http://127.0.0.1:8000/api/status
- Score a JD: `POST /api/score` with `{ "title": "...", "jd_text": "..." }`
- Import jobs: `POST /api/jobs/import` with `{ "jobs": [...] }` (needs `X-FindOne-Key` and a current resume)
- List jobs: `GET /api/jobs?status=Queued`
- One job: `GET /api/jobs/{job_id}`
- Docs: http://127.0.0.1:8000/docs

`POST /api/resumes` and `POST /api/jobs/import` need header `X-FindOne-Key` (same value as `FINDONE_KEY` in `.env`).

LinkedIn URLs are stored as Skipped. Jobs that need a human read go On hold. Weak scores and out-of-family titles are Skipped. Everything else is Queued.

## Run UI

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — upload resume, import `sample-data/job_pool.example.json`, then filter the jobs table. You can still paste a single JD to score.

## Clock

`enforce_work_window` in `backend/app/profile/profile.yml` is **false** until the product is complete. Set it to `true` later for 06:00–15:30 only.

## Tests

```powershell
cd backend
pytest
```
