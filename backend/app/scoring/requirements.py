"""Pull core vs nice-to-have requirement lines from a cleaned JD."""

from __future__ import annotations

import re
from dataclasses import dataclass

CORE_HEADINGS = (
    "requirements",
    "qualifications",
    "what you'll need",
    "what you will need",
    "what youll need",
    "must have",
    "must-have",
    "what we're looking for",
    "what we are looking for",
    "minimum qualifications",
    "required skills",
    "basic qualifications",
)

NICE_HEADINGS = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "bonus",
    "plus",
    "good to have",
    "preferred qualifications",
    "preferred skills",
)

SKIP_EXACT = {"requirements", "qualifications", "preferred", "bonus", "plus"}


@dataclass
class Requirement:
    text: str
    kind: str  # core | nice


def _heading_key(line: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", line.lower()).strip()


def _is_heading(line: str, headings: tuple[str, ...]) -> bool:
    key = _heading_key(line)
    return any(key == h or key.startswith(h) for h in headings)


def _usable_line(line: str) -> bool:
    stripped = line.strip(" -\t•*")
    if len(stripped) < 20:
        return False
    if _heading_key(stripped) in SKIP_EXACT:
        return False
    return True


def extract_requirements(cleaned_jd: str, fallback_n: int = 25) -> list[Requirement]:
    lines = [ln.strip() for ln in (cleaned_jd or "").splitlines()]
    found_section = False
    kind = "core"
    items: list[Requirement] = []

    for line in lines:
        if not line:
            continue
        if _is_heading(line, NICE_HEADINGS):
            found_section = True
            kind = "nice"
            continue
        if _is_heading(line, CORE_HEADINGS):
            found_section = True
            kind = "core"
            continue
        if found_section and _usable_line(line):
            items.append(Requirement(text=line.lstrip("-*• ").strip(), kind=kind))

    if items:
        return items

    fallback: list[Requirement] = []
    for line in lines:
        if _usable_line(line):
            fallback.append(Requirement(text=line.lstrip("-*• ").strip(), kind="core"))
        if len(fallback) >= fallback_n:
            break
    return fallback
