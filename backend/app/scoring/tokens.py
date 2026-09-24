"""Tokenize, stopwords, and synonym canonicalization."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

SYNONYM_PATH = Path(__file__).resolve().parent.parent / "profile" / "synonyms.yml"

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with", "on", "at", "by",
    "from", "as", "is", "are", "be", "been", "was", "were", "this", "that", "these",
    "those", "we", "you", "your", "our", "their", "will", "can", "must", "should",
    "able", "using", "use", "used", "including", "include", "such", "etc", "etcetera",
    "experience", "experiences", "year", "years", "plus", "minimum", "least", "required",
    "requirement", "requirements", "qualification", "qualifications", "skill", "skills",
    "knowledge", "strong", "good", "excellent", "working", "work", "role", "job",
    "candidate", "team", "ability", "across", "within", "related", "other", "both",
    "have", "has", "having", "who", "whom", "which", "into", "over", "about", "more",
    "than", "all", "any", "some", "new", "well", "also", "not", "but", "if", "then",
}

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+.#/-]*", re.I)


@lru_cache
def alias_to_canonical() -> dict[str, str]:
    raw = yaml.safe_load(SYNONYM_PATH.read_text(encoding="utf-8")) or {}
    mapping: dict[str, str] = {}
    for canonical, aliases in raw.items():
        canon = str(canonical).strip().lower()
        mapping[canon] = canon
        mapping[canon.replace(" ", "")] = canon
        for alias in aliases or []:
            key = str(alias).strip().lower()
            mapping[key] = canon
            mapping[key.replace(" ", "")] = canon
    return mapping


def canonicalize(term: str) -> str:
    key = term.strip().lower()
    mapping = alias_to_canonical()
    return mapping.get(key) or mapping.get(key.replace(" ", "")) or key


def tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in TOKEN_RE.findall(text or "")]


def content_tokens(text: str) -> list[str]:
    out: list[str] = []
    for tok in tokenize(text):
        if tok in STOPWORDS or tok.isdigit() or len(tok) < 2:
            continue
        out.append(canonicalize(tok))
    return out


def phrase_canonicals(text: str) -> set[str]:
    lowered = " " + re.sub(r"[^a-z0-9+.#/ ]+", " ", (text or "").lower()) + " "
    found: set[str] = set()
    for alias, canon in alias_to_canonical().items():
        if " " not in alias:
            continue
        if f" {alias} " in lowered:
            found.add(canon)
    return found
