"""GET /api/status — clock config and whether a master resume exists."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import clock_in_work_window, load_profile, operations_allowed
from app.db import get_db, get_engine
from app.models import Resume
from app.scheduler import next_poll_at
from app.schemas import StatusOut

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status", response_model=StatusOut)
def get_status(db: Session = Depends(get_db)) -> StatusOut:
    profile = load_profile()
    running = operations_allowed(profile=profile)
    has_resume = (
        db.query(Resume).filter(Resume.is_current.is_(True)).first() is not None
    )
    tz = datetime.now().astimezone().tzname() or "local"
    db_file = get_engine().url.database
    return StatusOut(
        product="FindOne",
        in_window=running,
        running=running,
        work_start=profile.get("work_start", "06:00"),
        work_end=profile.get("work_end", "15:30"),
        poll_minutes=int(profile.get("poll_minutes", 20)),
        timezone=tz,
        has_current_resume=has_resume,
        enforce_work_window=bool(profile.get("enforce_work_window", False)),
        clock_in_window=clock_in_work_window(profile=profile),
        next_poll=next_poll_at(profile=profile).isoformat(),
        database_ready=bool(db_file and Path(db_file).is_file()),
        counts={
            "applied_today": 0,
            "on_hold": 0,
            "skipped": 0,
            "queue": 0,
        },
    )
