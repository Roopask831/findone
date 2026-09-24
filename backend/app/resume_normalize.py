"""Map several resume JSON shapes into the scorer's roles/skills form."""

from __future__ import annotations

from typing import Any


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def flatten_skill_list(skills: Any) -> list[str]:
    if not skills:
        return []
    if isinstance(skills, list):
        out: list[str] = []
        for item in skills:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                out.extend(flatten_skill_list(list(item.values())))
        return out
    if isinstance(skills, dict):
        out: list[str] = []
        for value in skills.values():
            out.extend(flatten_skill_list(value))
        return out
    if isinstance(skills, str) and skills.strip():
        return [skills.strip()]
    return []


def canonical_resume(data: dict[str, Any]) -> dict[str, Any]:
    """Accept Phase-1 shape or the richer personal JSON (work_experience, nested skills)."""
    personal = data.get("personal_information") if isinstance(data.get("personal_information"), dict) else {}
    roles = data.get("roles")
    if not roles:
        roles = []
        for job in _as_list(data.get("work_experience")):
            if not isinstance(job, dict):
                continue
            bullets = job.get("bullets") or job.get("responsibilities_and_achievements") or []
            roles.append(
                {
                    "title": job.get("title") or job.get("job_title") or "",
                    "company": job.get("company") or "",
                    "start_date": job.get("start_date") or "",
                    "end_date": job.get("end_date") or "",
                    "bullets": [str(b).strip() for b in _as_list(bullets) if str(b).strip()],
                }
            )
        for project in _as_list(data.get("projects")):
            if not isinstance(project, dict):
                continue
            tech = project.get("technologies") or []
            desc = project.get("description") or []
            bullets = [str(b).strip() for b in _as_list(desc) if str(b).strip()]
            if tech:
                bullets.append("Technologies: " + ", ".join(str(t) for t in tech))
            roles.append(
                {
                    "title": project.get("name") or "Project",
                    "company": project.get("type") or "Project",
                    "start_date": "",
                    "end_date": "",
                    "bullets": bullets,
                }
            )

    skills = flatten_skill_list(data.get("skills"))
    skills.extend(flatten_skill_list(data.get("core_technical_strengths")))

    education = data.get("education") or []
    normalized_edu = []
    for item in _as_list(education):
        if isinstance(item, dict):
            normalized_edu.append(
                {
                    "school": item.get("school") or item.get("institution") or "",
                    "degree": item.get("degree") or "",
                    "field": item.get("field") or "",
                    "end_date": item.get("end_date") or item.get("graduation_date") or "",
                }
            )
        else:
            normalized_edu.append(item)

    return {
        "name": data.get("name") or personal.get("name"),
        "email": data.get("email") or personal.get("email"),
        "phone": data.get("phone") or personal.get("phone"),
        "location": data.get("location") or personal.get("location"),
        "linkedin": data.get("linkedin") or personal.get("linkedin"),
        "github": data.get("github") or personal.get("github"),
        "summary": data.get("summary") or data.get("professional_summary"),
        "roles": roles or [],
        "skills": skills,
        "education": normalized_edu,
        "certifications": data.get("certifications") or [],
    }
