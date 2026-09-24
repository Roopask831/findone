"""Strip benefits / EEO / about-the-company blocks from a job description."""

from __future__ import annotations

import re

from app.config import load_profile

CUT_HEADINGS = (
    "benefits",
    "perks",
    "what we offer",
    "about us",
    "about the company",
    "about the team",
    "equal opportunity",
    "eeo",
    "diversity",
    "diversity equity",
    "accommodations",
    "our values",
    "who we are",
)


def _is_cut_heading(line: str) -> bool:
    stripped = re.sub(r"[^a-z0-9 ]+", "", line.lower()).strip()
    return any(stripped == heading or stripped.startswith(heading) for heading in CUT_HEADINGS)


def clean_jd(jd_text: str, char_cap: int | None = None) -> str:
    profile = load_profile()
    cap = char_cap if char_cap is not None else int(profile.get("jd_char_cap", 8000))
    kept: list[str] = []
    for raw in (jd_text or "").splitlines():
        line = raw.strip()
        if line and _is_cut_heading(line):
            break
        kept.append(raw.rstrip())
    cleaned = "\n".join(kept).strip()
    if len(cleaned) > cap:
        cleaned = cleaned[:cap].rsplit(" ", 1)[0]
    return cleaned
