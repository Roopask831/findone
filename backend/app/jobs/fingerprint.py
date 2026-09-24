"""Stable job fingerprint for dedup across sources."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

DROP_QUERY = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gh_src", "lever-source"}


def norm_name(value: str) -> str:
    text = (value or "").lower()
    text = re.sub(r"\b(inc|llc|ltd|corp|co)\b\.?", "", text)
    text = re.sub(r"[^a-z0-9+.# ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    host = parsed.netloc.lower().removeprefix("www.")
    query = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in DROP_QUERY
    ]
    cleaned = parsed._replace(
        scheme=parsed.scheme.lower() or "https",
        netloc=host,
        query=urlencode(query),
        fragment="",
    )
    return urlunparse(cleaned).rstrip("/")


def is_linkedin(url: str) -> bool:
    host = urlparse((url or "").lower()).netloc
    return "linkedin.com" in host


def fingerprint(title: str, company: str, location: str, apply_url: str) -> str:
    url = canonical_url(apply_url)
    if url:
        return "url:" + hashlib.sha256(url.encode()).hexdigest()[:32]
    key = "|".join([norm_name(company), norm_name(title), norm_name(location)])
    return "ctl:" + hashlib.sha256(key.encode()).hexdigest()[:32]


def jd_hash(jd_text: str) -> str:
    return hashlib.sha256((jd_text or "").encode("utf-8")).hexdigest()[:32]


def make_job_id(raw_id: str | None, fp: str) -> str:
    if raw_id and raw_id.strip():
        return raw_id.strip()[:80]
    return fp.replace(":", "-")[:80]
