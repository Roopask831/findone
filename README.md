# FindOne

Personal job hunt helper. Phase 0: FastAPI + Vite + SQLite + `/api/status`. Phase 1: resume store.

## Run backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy ..\.env.example ..\.env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Hello: http://127.0.0.1:8000/
- Status: http://127.0.0.1:8000/api/status
- Docs: http://127.0.0.1:8000/docs
- SQLite file: `data/findone.db` (created on first API start)

`POST /api/resumes` needs header `X-FindOne-Key` (same value as `FINDONE_KEY` in `.env`).

## Run UI

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — upload JSON + PDF + cover letter template.

## Clock

`enforce_work_window` in `backend/app/profile/profile.yml` is **false** until the product is complete. Hunt/apply will run any time. Set it to `true` later for 06:00–15:30 only.


```powershell
cd backend
pytest
```
