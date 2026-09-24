"""POST /api/resumes and GET /api/resumes/current."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import config
from app.auth import require_api_key
from app.db import get_db
from app.models import Resume
from app.pdf_text import extract_pdf_text, resume_dict_from_pdf_text
from app.resume_normalize import canonical_resume
from app.resume_text import flatten_resume
from app.schemas import MasterResume, ResumeOut

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_TEXT_BYTES = 1 * 1024 * 1024


def _to_out(row: Resume) -> ResumeOut:
    return ResumeOut(
        id=row.id,
        label=row.label,
        is_current=row.is_current,
        resume_json=json.loads(row.resume_json),
        resume_text=row.resume_text,
        master_pdf_path=row.master_pdf_path,
        cover_letter_template=row.cover_letter_template,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _read_resume_json(raw: str) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"resume_json is not valid JSON: {exc.msg}",
        ) from exc
    parsed = MasterResume.model_validate(canonical_resume(payload))
    return parsed.model_dump()


async def _read_optional_text(upload: UploadFile | None) -> str:
    if upload is None or not upload.filename:
        return ""
    raw = await upload.read()
    if len(raw) > MAX_TEXT_BYTES:
        raise HTTPException(status_code=400, detail="Text file is larger than 1MB")
    return raw.decode("utf-8-sig", errors="replace").strip()


@router.get("/current", response_model=ResumeOut)
def get_current_resume(db: Session = Depends(get_db)) -> ResumeOut:
    row = db.query(Resume).filter(Resume.is_current.is_(True)).order_by(Resume.id.desc()).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current resume")
    return _to_out(row)


@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
    pdf: UploadFile = File(..., description="Master resume PDF"),
    resume_json: str | None = Form(default=None),
    cover_letter_template: str | None = Form(default=None),
    resume_json_file: UploadFile | None = File(default=None),
    cover_letter_file: UploadFile | None = File(default=None),
    label: str = Form(default="master"),
) -> ResumeOut:
    contents = await pdf.read()
    if len(contents) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="PDF is larger than 10MB")
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Resume file must be a PDF")

    json_from_file = await _read_optional_text(resume_json_file)
    json_raw = json_from_file or (resume_json or "").strip()
    if json_raw:
        data = _read_resume_json(json_raw)
        text = flatten_resume(data)
    else:
        extracted = extract_pdf_text(contents)
        if len(extracted) < 40:
            raise HTTPException(
                status_code=400,
                detail="Could not read enough text from the PDF. Upload a resume JSON file too.",
            )
        data = MasterResume.model_validate(resume_dict_from_pdf_text(extracted)).model_dump()
        text = extracted if len(extracted) > len(flatten_resume(data)) else flatten_resume(data)

    letter_from_file = await _read_optional_text(cover_letter_file)
    template = letter_from_file or (cover_letter_template or "").strip()
    if not template:
        raise HTTPException(
            status_code=400,
            detail="Upload a cover letter .txt file or paste the cover letter template.",
        )

    now = datetime.now()
    db.query(Resume).filter(Resume.is_current.is_(True)).update(
        {"is_current": False, "updated_at": now}
    )

    row = Resume(
        label=label.strip() or "master",
        is_current=True,
        resume_json=json.dumps(data, ensure_ascii=False, indent=2),
        resume_text=text,
        master_pdf_path="",
        cover_letter_template=template,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()

    settings = config.get_settings()
    version_dir = settings.data_dir / "resumes" / str(row.id)
    version_dir.mkdir(parents=True, exist_ok=True)
    version_pdf = version_dir / "master.pdf"
    current_pdf = settings.data_dir / "resumes" / "master.pdf"
    version_pdf.write_bytes(contents)
    shutil.copyfile(version_pdf, current_pdf)
    (version_dir / "cover_letter.txt").write_text(template, encoding="utf-8")
    (settings.data_dir / "resumes" / "cover_letter.txt").write_text(template, encoding="utf-8")

    rel = Path("data") / "resumes" / str(row.id) / "master.pdf"
    row.master_pdf_path = rel.as_posix()
    db.commit()
    db.refresh(row)
    return _to_out(row)
