from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.student import StudentAnalyzeResponse, StudentProfileCreate, StudentProfileResponse, StudentProfileStoreResponse
from app.services.master_service import analyze_student_profile
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/student", tags=["student"])

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MARKSHEET_EXTENSIONS = {".pdf"}
MAX_FILE_BYTES = 8 * 1024 * 1024


def _require_non_empty(value: str, field_name: str) -> str:
    v = value.strip()
    if not v:
        raise HTTPException(status_code=400, detail=f"{field_name} is required.")
    return v


@router.post("/analyze", response_model=StudentAnalyzeResponse)
async def analyze_student(
    resume_file: UploadFile = File(...),
    marksheet_file: UploadFile = File(...),
    branch: str = Form(...),
    github_username: str = Form(...),
    leetcode_username: str = Form(...),
) -> StudentAnalyzeResponse:
    branch_clean = _require_non_empty(branch, "branch")
    github_clean = _require_non_empty(github_username, "github_username")
    leetcode_clean = _require_non_empty(leetcode_username, "leetcode_username")

    resume_ext = Path(resume_file.filename or "").suffix.lower()
    marksheet_ext = Path(marksheet_file.filename or "").suffix.lower()
    if resume_ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Resume file must be PDF or DOCX.")
    if marksheet_ext not in ALLOWED_MARKSHEET_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Marksheet file must be PDF.")

    resume_bytes = await resume_file.read()
    marksheet_bytes = await marksheet_file.read()
    if not resume_bytes:
        raise HTTPException(status_code=400, detail="Resume file is empty.")
    if not marksheet_bytes:
        raise HTTPException(status_code=400, detail="Marksheet file is empty.")
    if len(resume_bytes) > MAX_FILE_BYTES or len(marksheet_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 8 MB limit.")

    try:
        normalized = await analyze_student_profile(
            resume_file=resume_bytes,
            resume_filename=resume_file.filename or "resume.bin",
            resume_content_type=resume_file.content_type,
            marksheet_file=marksheet_bytes,
            marksheet_filename=marksheet_file.filename or "marksheet.pdf",
            marksheet_content_type=marksheet_file.content_type,
            branch=branch_clean,
            github=github_clean,
            leetcode=leetcode_clean,
        )
    except ValueError as exc:
        logger.exception("Analyzer failure")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return StudentAnalyzeResponse.model_validate(normalized)


@router.post("/profile", response_model=StudentProfileStoreResponse)
def create_student_profile(payload: StudentProfileCreate, db: Session = Depends(get_db)) -> StudentProfileStoreResponse:
    service = ProfileService(db)
    return service.save_profile(payload)


@router.get("/profile/{id}", response_model=StudentProfileResponse)
def get_student_profile(id: int, db: Session = Depends(get_db)) -> StudentProfileResponse:
    service = ProfileService(db)
    return service.get_profile(id)

