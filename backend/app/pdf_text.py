"""Read text out of an uploaded resume PDF."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(contents: bytes) -> str:
    reader = PdfReader(BytesIO(contents))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def resume_dict_from_pdf_text(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets = lines[:40]
    return {
        "name": lines[0] if lines else None,
        "summary": text[:2000] if text else None,
        "roles": [
            {
                "title": "From uploaded PDF",
                "company": "",
                "start_date": "",
                "end_date": "",
                "bullets": bullets or [text[:500]],
            }
        ],
        "skills": [],
        "education": [],
        "certifications": [],
    }
