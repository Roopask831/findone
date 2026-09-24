"""POST /api/score — score a JD against the current stored resume."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Resume
from app.schemas import ScoreIn, ScoreOut
from app.scoring.ats import score_job

router = APIRouter(prefix="/api", tags=["scoring"])


@router.post("/score", response_model=ScoreOut)
def score_current_resume(body: ScoreIn, db: Session = Depends(get_db)) -> ScoreOut:
    if not (body.jd_text or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="jd_text is required")
    row = db.query(Resume).filter(Resume.is_current.is_(True)).order_by(Resume.id.desc()).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current resume")
    result = score_job(
        resume=json.loads(row.resume_json),
        jd_text=body.jd_text,
        job_title=body.title,
        resume_text=row.resume_text,
    )
    return ScoreOut(
        title=body.title,
        score=result["score"],
        tier=result["tier"],
        scoring_status=result["scoring_status"],
        matched_requirements=result["matched_requirements"],
        gaps=result["gaps"],
        reasoning=result["reasoning"],
        title_in_family=result["title_in_family"],
    )
