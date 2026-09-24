"""Local ATS: match JD requirements to resume evidence. No LLM."""

from __future__ import annotations

from typing import Any

from app.config import load_profile
from app.resume_normalize import canonical_resume
from app.resume_text import flatten_resume
from app.scoring.jd_clean import clean_jd
from app.scoring.requirements import extract_requirements
from app.scoring.titles import title_in_family
from app.scoring.tokens import alias_to_canonical, content_tokens, phrase_canonicals

TECH_HINTS = {
    "java",
    "spring",
    "spring boot",
    "hibernate",
    "jpa",
    "kafka",
    "docker",
    "aws",
    "kubernetes",
    "sql",
    "mysql",
    "mongodb",
    "rest",
    "microservices",
    "junit",
    "react",
    "python",
    "git",
    "maven",
    "linux",
}


def _evidence_from_resume(resume: dict[str, Any], resume_text: str | None = None) -> set[str]:
    data = canonical_resume(resume)
    bag: set[str] = set()
    texts = [flatten_resume(data)]
    if resume_text:
        texts.append(resume_text)
    for skill in data.get("skills") or []:
        texts.append(str(skill))
    for blob in texts:
        bag.update(content_tokens(blob))
        bag.update(phrase_canonicals(blob))
    bag.discard("")
    return bag


def _is_tech(token: str) -> bool:
    return token in TECH_HINTS or token in set(alias_to_canonical().values())


def line_matches(requirement_text: str, evidence: set[str]) -> bool:
    tokens = list(dict.fromkeys(content_tokens(requirement_text)))
    for extra in phrase_canonicals(requirement_text):
        if extra not in tokens:
            tokens.append(extra)
    if not tokens:
        return False
    hits = [tok for tok in tokens if tok in evidence]
    tech = [tok for tok in tokens if _is_tech(tok)]
    if tech:
        return all(tok in evidence for tok in tech)
    return (len(hits) / len(tokens)) >= 0.5


def _tier(score: int, good: int, strong: int) -> str:
    if score >= strong:
        return "strong"
    if score >= good:
        return "good"
    return "weak"


def score_job(
    resume: dict[str, Any],
    jd_text: str,
    job_title: str = "",
    resume_text: str | None = None,
    profile: dict | None = None,
) -> dict[str, Any]:
    profile = profile if profile is not None else load_profile()
    core_w = float(profile.get("core_weight", 2.0))
    nice_w = float(profile.get("nice_weight", 0.7))
    good = int(profile.get("good", 50))
    strong = int(profile.get("strong", 75))

    cleaned = clean_jd(jd_text)
    reqs = extract_requirements(cleaned)
    if not reqs:
        return {
            "score": 0,
            "tier": "weak",
            "scoring_status": "needs_manual",
            "matched_requirements": [],
            "gaps": [],
            "reasoning": "No extractable requirements; needs_manual.",
            "title_in_family": title_in_family(job_title, profile) if job_title else True,
            "jd_text_clean": cleaned,
        }

    evidence = _evidence_from_resume(resume, resume_text)
    matched: list[str] = []
    gaps: list[str] = []
    matched_weight = 0.0
    total_weight = 0.0
    core_matched = 0
    core_total = 0

    for req in reqs:
        weight = core_w if req.kind == "core" else nice_w
        total_weight += weight
        if req.kind == "core":
            core_total += 1
        if line_matches(req.text, evidence):
            matched.append(req.text)
            matched_weight += weight
            if req.kind == "core":
                core_matched += 1
        else:
            gaps.append(req.text)

    if total_weight <= 0:
        score = 0
        status = "needs_manual"
    else:
        score = max(0, min(100, int(round(100 * matched_weight / total_weight))))
        status = "scored"

    in_family = title_in_family(job_title, profile) if job_title else True
    if job_title and not in_family:
        score = min(score, 49)

    gap_preview = "; ".join(gaps[:3]) if gaps else "none"
    reasoning = (
        f"{len(matched)} of {len(reqs)} requirements matched "
        f"({core_matched}/{core_total} core). Gaps: {gap_preview}."
    )
    if job_title and not in_family:
        reasoning += " Title is outside the target family so score is capped at 49."

    return {
        "score": score,
        "tier": _tier(score, good, strong),
        "scoring_status": status,
        "matched_requirements": matched,
        "gaps": gaps,
        "reasoning": reasoning,
        "title_in_family": in_family,
        "jd_text_clean": cleaned,
    }
