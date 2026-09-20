"""SQLAlchemy tables for Phase 0–1."""

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
