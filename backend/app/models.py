"""SQLAlchemy tables for Phase 0–3."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Resume(Base):
    __tablename__ = "resume"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(200), default="master")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    resume_json: Mapped[str] = mapped_column(Text)
    resume_text: Mapped[str] = mapped_column(Text)
    master_pdf_path: Mapped[str] = mapped_column(String(500))
    cover_letter_template: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Job(Base):
    __tablename__ = "job"

    job_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="import")
    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(200), default="", index=True)
    location: Mapped[str] = mapped_column(String(200), default="")
    apply_url: Mapped[str] = mapped_column(String(1000), default="")
    jd_text: Mapped[str] = mapped_column(Text, default="")
    jd_text_clean: Mapped[str] = mapped_column(Text, default="")
    jd_hash: Mapped[str] = mapped_column(String(64), default="")
    posted_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    score_master: Mapped[int] = mapped_column(Integer, default=0)
    tier_master: Mapped[str] = mapped_column(String(20), default="weak")
    matched_requirements: Mapped[str] = mapped_column(Text, default="[]")
    gaps: Mapped[str] = mapped_column(Text, default="[]")
    reasoning: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="New", index=True)
    hold_reason: Mapped[str | None] = mapped_column(String(80), nullable=True)
    scoring_status: Mapped[str] = mapped_column(String(40), default="scored")
    is_new_for_ui: Mapped[bool] = mapped_column(Boolean, default=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
