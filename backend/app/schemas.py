"""Request and response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Role(BaseModel):
    title: str
    company: str
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    school: str = ""
    degree: str = ""
    field: str = ""
    end_date: str = ""


class MasterResume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    summary: str | None = None
    roles: list[Role]
    skills: list[str] = Field(default_factory=list)
    education: list[EducationItem | str | dict[str, Any]] = Field(default_factory=list)
    certifications: list[str | dict[str, Any]] = Field(default_factory=list)


class ResumeOut(BaseModel):
    id: int
    label: str
    is_current: bool
    resume_json: dict[str, Any]
    resume_text: str
    master_pdf_path: str
    cover_letter_template: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StatusOut(BaseModel):
    product: str = "FindOne"
    in_window: bool
    running: bool
    work_start: str
    work_end: str
    poll_minutes: int
    timezone: str
    has_current_resume: bool
    enforce_work_window: bool = False
    clock_in_window: bool = False
    next_poll: str | None = None
    database_ready: bool = False
    counts: dict[str, int]


class ScoreIn(BaseModel):
    title: str = ""
    jd_text: str


class ScoreOut(BaseModel):
    title: str = ""
    score: int
    tier: str
    scoring_status: str
    matched_requirements: list[str]
    gaps: list[str]
    reasoning: str
    title_in_family: bool


class JobIn(BaseModel):
    job_id: str | None = None
    id: str | None = None
    title: str = ""
    company: str = ""
    location: str = ""
    jd_text: str = ""
    description: str | None = None
    apply_url: str = ""
    url: str | None = None
    source_portal: str | None = None
    source: str | None = None
    posted_date: str | None = None


class JobImportIn(BaseModel):
    jobs: list[JobIn]


class JobOut(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    apply_url: str
    source: str
    posted_date: str | None = None
    first_seen_at: datetime | None = None
    score: int
    tier: str
    status: str
    hold_reason: str | None = None
    scoring_status: str
    matched_requirements: list[str]
    gaps: list[str]
    reasoning: str
    title_in_family: bool | None = None
    jd_text: str | None = None


class JobImportOut(BaseModel):
    seen: int
    created: int
    updated: int
    queued: int
    skipped: int
    on_hold: int

