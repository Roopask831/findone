"""POST /api/jobs/import, GET /api/jobs, GET /api/jobs/{job_id}, HTML job pages."""

from __future__ import annotations

import html
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.jobs.ingest import ingest_jobs
from app.models import Job
from app.schemas import JobImportIn, JobImportOut, JobOut
from app.scoring.titles import title_in_family

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
pages = APIRouter(tags=["jobs"])


def _job_page(row: Job) -> str:
    title = html.escape(row.title or "Untitled job")
    company = html.escape(row.company or "—")
    location = html.escape(row.location or "—")
    apply_url = html.escape(row.apply_url or "")
    jd = html.escape(row.jd_text or "(no job description stored)")
    reasoning = html.escape(row.reasoning or "")
    status_line = html.escape(row.status or "")
    reason = html.escape(row.hold_reason or "")
    extra = f" ({reason})" if reason else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{title} — FindOne</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; background: #f4f1ea; color: #1b1b1b; margin: 0; }}
    main {{ max-width: 800px; margin: 0 auto; padding: 24px 16px 48px; }}
    a {{ color: #3d348b; }}
    .card {{ background: #fff; border: 1px solid #ddd4c4; border-radius: 12px; padding: 16px; }}
    pre {{ white-space: pre-wrap; }}
  </style>
</head>
<body>
  <main>
    <p><a href="http://127.0.0.1:5173/">← Back to FindOne</a></p>
    <h1>{title}</h1>
    <p>{company} · {location}</p>
    <p><strong>{row.score_master}</strong> / 100 · {html.escape(row.tier_master or "")} · {status_line}{extra}</p>
    <div class="card">
      <h2>Job description</h2>
      <pre>{jd}</pre>
      <h2>Why this score</h2>
      <pre>{reasoning or "(none)"}</pre>
      <h2>Stored apply URL</h2>
      <p>{apply_url or "—"}</p>
      <p>Sample and skipped listings are kept inside FindOne. The apply URL is stored for later; it is not opened from the jobs table.</p>
    </div>
  </main>
</body>
</html>
"""


def _to_out(row: Job, include_jd: bool = False) -> JobOut:
    try:
        matched = json.loads(row.matched_requirements or "[]")
    except json.JSONDecodeError:
        matched = []
    try:
        gaps = json.loads(row.gaps or "[]")
    except json.JSONDecodeError:
        gaps = []
    return JobOut(
        job_id=row.job_id,
        title=row.title,
        company=row.company,
        location=row.location,
        apply_url=row.apply_url,
        source=row.source,
        posted_date=row.posted_date,
        first_seen_at=row.first_seen_at,
        score=row.score_master,
        tier=row.tier_master,
        status=row.status,
        hold_reason=row.hold_reason,
        scoring_status=row.scoring_status,
        matched_requirements=matched,
        gaps=gaps,
        reasoning=row.reasoning,
        title_in_family=title_in_family(row.title),
        jd_text=row.jd_text if include_jd else None,
    )


@router.post("/import", response_model=JobImportOut)
def import_jobs(
    body: JobImportIn,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
) -> JobImportOut:
    listings = [item.model_dump() for item in body.jobs]
    try:
        stats = ingest_jobs(db, listings)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JobImportOut(**stats)


@router.get("", response_model=list[JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    tier: str | None = None,
    q: str | None = None,
) -> list[JobOut]:
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    if tier:
        query = query.filter(Job.tier_master == tier)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Job.title.ilike(like)) | (Job.company.ilike(like)) | (Job.location.ilike(like))
        )
    rows = query.order_by(Job.score_master.desc(), Job.first_seen_at.desc()).all()
    return [_to_out(row) for row in rows]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    row = db.query(Job).filter(Job.job_id == job_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _to_out(row, include_jd=True)


@pages.get("/jobs/{job_id}", response_class=HTMLResponse)
def view_job(job_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    row = db.query(Job).filter(Job.job_id == job_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return HTMLResponse(_job_page(row))
