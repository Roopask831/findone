"""Decide whether a job title is in the user's target family."""

from __future__ import annotations

import re

from app.config import load_profile

BLOCKED_PHRASES = (
    "intern",
    "internship",
    "principal",
    "staff software",
    "staff engineer",
    "distinguished",
    "director",
    "vice president",
    "data scientist",
    "machine learning engineer",
    "android",
    "ios developer",
    "ios engineer",
    "mobile engineer",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+.# ]+", " ", (text or "").lower())).strip()


def title_in_family(job_title: str, profile: dict | None = None) -> bool:
    profile = profile if profile is not None else load_profile()
    title = _norm(job_title)
    if re.search(r"\b(vp|cto)\b", title):
        return False
    if any(phrase in title for phrase in BLOCKED_PHRASES):
        return False

    for alias, canonical in (profile.get("title_aliases") or {}).items():
        title = title.replace(_norm(str(alias)), _norm(str(canonical)))

    for target in profile.get("target_titles") or []:
        nt = _norm(str(target))
        if nt and (nt in title or title in nt):
            return True
    return False
