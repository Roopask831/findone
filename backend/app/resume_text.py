"""Turn structured resume JSON into plain text for scoring and Applied snapshots."""

from __future__ import annotations

from typing import Any


def _as_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        parts = [
            str(value.get(key) or "").strip()
            for key in ("school", "degree", "field", "name", "issuer", "end_date", "year")
        ]
        joined = ", ".join(part for part in parts if part)
        return [joined] if joined else []
    return [str(value).strip()] if str(value).strip() else []


def flatten_resume(data: dict[str, Any]) -> str:
    lines: list[str] = []

    header = [
        data.get("name"),
        data.get("email"),
        data.get("phone"),
        data.get("location"),
        data.get("linkedin"),
        data.get("github"),
    ]
    header_line = " | ".join(str(part).strip() for part in header if part)
    if header_line:
        lines.append(header_line)

    summary = (data.get("summary") or "").strip()
    if summary:
        lines.append("")
        lines.append(summary)

    roles = data.get("roles") or []
    if roles:
        lines.append("")
        lines.append("Experience")
        for role in roles:
            title = (role.get("title") or "").strip()
            company = (role.get("company") or "").strip()
            start = (role.get("start_date") or "").strip()
            end = (role.get("end_date") or "").strip()
            dates = " – ".join(part for part in (start, end) if part)
            heading = " | ".join(part for part in (title, company, dates) if part)
            if heading:
                lines.append(heading)
            for bullet in role.get("bullets") or []:
                text = str(bullet).strip()
                if text:
                    lines.append(f"- {text}")

    skills = [str(skill).strip() for skill in (data.get("skills") or []) if str(skill).strip()]
    if skills:
        lines.append("")
        lines.append("Skills")
        lines.append(", ".join(skills))

    education_lines: list[str] = []
    for item in data.get("education") or []:
        education_lines.extend(_as_lines(item))
    if education_lines:
        lines.append("")
        lines.append("Education")
        lines.extend(education_lines)

    cert_lines: list[str] = []
    for item in data.get("certifications") or []:
        cert_lines.extend(_as_lines(item))
    if cert_lines:
        lines.append("")
        lines.append("Certifications")
        lines.extend(cert_lines)

    return "\n".join(lines).strip() + "\n"
