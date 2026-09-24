"""Import listings, score against the current resume, persist jobs."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.jobs.fingerprint import fingerprint, is_linkedin, jd_hash, make_job_id
from app.models import Job, Resume
from app.scoring.ats import score_job

STATUS_QUEUED = "Queued"
STATUS_SKIPPED = "Skipped"
STATUS_ON_HOLD = "On hold"


def _current_resume(db: Session) -> Resume | None:
    return db.query(Resume).filter(Resume.is_current.is_(True)).order_by(Resume.id.desc()).first()


def _classify(apply_url: str, result: dict[str, Any]) -> tuple[str, str | None]:
    if is_linkedin(apply_url):
        return STATUS_SKIPPED, "linkedin"
    if result.get("scoring_status") == "needs_manual":
        return STATUS_ON_HOLD, "needs_manual"
    if not result.get("title_in_family", True):
        return STATUS_SKIPPED, "title_cap"
    if int(result.get("score") or 0) < 50:
        return STATUS_SKIPPED, "weak"
    return STATUS_QUEUED, None


def _apply_score(row: Job, result: dict[str, Any], apply_url: str, now: datetime) -> None:
    status, reason = _classify(apply_url, result)
    row.score_master = int(result.get("score") or 0)
    row.tier_master = str(result.get("tier") or "weak")
    row.matched_requirements = json.dumps(result.get("matched_requirements") or [], ensure_ascii=False)
    row.gaps = json.dumps(result.get("gaps") or [], ensure_ascii=False)
    row.reasoning = str(result.get("reasoning") or "")
    row.jd_text_clean = str(result.get("jd_text_clean") or "")
    row.scoring_status = str(result.get("scoring_status") or "scored")
    row.status = status
    row.hold_reason = reason
    row.scored_at = now


def ingest_jobs(db: Session, listings: list[dict[str, Any]]) -> dict[str, int]:
    resume = _current_resume(db)
    if resume is None:
        raise ValueError("No current resume")
    resume_data = json.loads(resume.resume_json)
    stats = {"seen": 0, "created": 0, "updated": 0, "queued": 0, "skipped": 0, "on_hold": 0}
    now = datetime.now()

    for raw in listings:
        stats["seen"] += 1
        title = str(raw.get("title") or "").strip()
        company = str(raw.get("company") or "").strip()
        location = str(raw.get("location") or "").strip()
        apply_url = str(raw.get("apply_url") or raw.get("url") or "").strip()
        jd_text = str(raw.get("jd_text") or raw.get("description") or "").strip()
        if not title and not jd_text:
            continue
        fp = fingerprint(title, company, location, apply_url)
        digest = jd_hash(jd_text)
        existing = db.query(Job).filter(Job.fingerprint == fp).first()
        if existing:
            existing.last_seen_at = now
            stats["updated"] += 1
            if digest != existing.jd_hash:
                existing.jd_text = jd_text
                existing.jd_hash = digest
                existing.title = title or existing.title
                existing.company = company or existing.company
                existing.location = location or existing.location
                existing.apply_url = apply_url or existing.apply_url
                result = score_job(resume_data, jd_text, title, resume.resume_text)
                _apply_score(existing, result, apply_url or existing.apply_url, now)
            continue

        job_id = make_job_id(raw.get("job_id") or raw.get("id"), fp)
        if db.query(Job).filter(Job.job_id == job_id).first():
            job_id = fp.replace(":", "-")[:80]
        row = Job(
            job_id=job_id,
            fingerprint=fp,
            external_id=str(raw.get("job_id") or raw.get("id") or "") or None,
            source=str(raw.get("source_portal") or raw.get("source") or "import"),
            title=title,
            company=company,
            location=location,
            apply_url=apply_url,
            jd_text=jd_text,
            jd_hash=digest,
            posted_date=str(raw.get("posted_date") or "") or None,
            first_seen_at=now,
            last_seen_at=now,
            is_new_for_ui=True,
        )
        result = score_job(resume_data, jd_text, title, resume.resume_text)
        _apply_score(row, result, apply_url, now)
        db.add(row)
        stats["created"] += 1

    db.commit()
    stats["queued"] = db.query(Job).filter(Job.status == STATUS_QUEUED).count()
    stats["skipped"] = db.query(Job).filter(Job.status == STATUS_SKIPPED).count()
    stats["on_hold"] = db.query(Job).filter(Job.status == STATUS_ON_HOLD).count()
    return stats
