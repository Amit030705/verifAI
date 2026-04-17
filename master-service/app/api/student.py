from __future__ import annotations

import logging
import json
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config import get_settings
from app.database.database import get_db
from app.database.models import RawUpload, StudentProfile
from app.dependencies.auth import get_current_student_id, get_optional_student_id
from app.schemas.student import (
    AuthTokenResponse,
    JDMatchRequest,
    JDMatchResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    StudentAnalyzeResponse,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileStoreResponse,
)
from app.services.auth_service import AuthService
from app.services.downstream import DEFAULT_HEADERS, call_jd_analyzer
from app.services.jd_file_parser import ALLOWED_JD_EXTENSIONS, extract_jd_text_from_file
from app.services.master_service import analyze_student_profile, analyze_student_profile_incremental
from app.services.matching_service import run_jd_matching
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


def _validate_resume_file(name: str) -> None:
    ext = Path(name or "").suffix.lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Resume file must be PDF or DOCX.")


def _validate_marksheet_file(name: str) -> None:
    ext = Path(name or "").suffix.lower()
    if ext not in ALLOWED_MARKSHEET_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Marksheet file must be PDF.")


def _parse_student_ids_form(raw: str | None) -> list[int] | None:
    if raw is None or not raw.strip():
        return None

    value = raw.strip()
    try:
        parsed_json = json.loads(value)
        if isinstance(parsed_json, list):
            candidate_ids = [int(item) for item in parsed_json]
        else:
            candidate_ids = [int(value)]
    except Exception:
        candidate_ids = [int(chunk.strip()) for chunk in value.split(",") if chunk.strip()]

    deduped = sorted({sid for sid in candidate_ids if sid > 0})
    return deduped or None


def _merge_jd_sources(file_text: str | None, typed_text: str | None) -> str:
    file_part = (file_text or "").strip()
    text_part = (typed_text or "").strip()

    if file_part and text_part:
        return f"{file_part}\n\nAdditional instructions:\n{text_part}"
    if file_part:
        return file_part
    if text_part:
        return text_part
    raise HTTPException(status_code=400, detail="Provide JD text and/or a JD file.")


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

    _validate_resume_file(resume_file.filename or "")
    _validate_marksheet_file(marksheet_file.filename or "")

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


@router.post("/analyze-incremental", response_model=StudentAnalyzeResponse)
async def analyze_student_incremental(
    branch: str = Form(...),
    github_username: str = Form(...),
    leetcode_username: str = Form(...),
    resume_changed: bool = Form(False),
    marksheet_changed: bool = Form(False),
    coding_changed: bool = Form(False),
    resume_file: UploadFile | None = File(None),
    marksheet_file: UploadFile | None = File(None),
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> StudentAnalyzeResponse:
    branch_clean = _require_non_empty(branch, "branch")
    github_clean = _require_non_empty(github_username, "github_username")
    leetcode_clean = _require_non_empty(leetcode_username, "leetcode_username")

    inferred_resume_changed = resume_changed or resume_file is not None
    inferred_marksheet_changed = marksheet_changed or marksheet_file is not None

    profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No existing profile found for incremental analysis. Run full analyze first with both files.",
        )

    latest_upload = (
        db.query(RawUpload)
        .filter(RawUpload.student_id == student_id)
        .order_by(RawUpload.uploaded_at.desc(), RawUpload.id.desc())
        .one_or_none()
    )

    resume_bytes: bytes | None = None
    marksheet_bytes: bytes | None = None

    if inferred_resume_changed:
        if resume_file is None:
            raise HTTPException(status_code=400, detail="Resume file is required when resume_changed is true.")
        _validate_resume_file(resume_file.filename or "")
        resume_bytes = await resume_file.read()
        if not resume_bytes:
            raise HTTPException(status_code=400, detail="Resume file is empty.")
        if len(resume_bytes) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="Resume file size exceeds 8 MB limit.")

    if inferred_marksheet_changed:
        if marksheet_file is None:
            raise HTTPException(status_code=400, detail="Marksheet file is required when marksheet_changed is true.")
        _validate_marksheet_file(marksheet_file.filename or "")
        marksheet_bytes = await marksheet_file.read()
        if not marksheet_bytes:
            raise HTTPException(status_code=400, detail="Marksheet file is empty.")
        if len(marksheet_bytes) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="Marksheet file size exceeds 8 MB limit.")

    try:
        normalized = await analyze_student_profile_incremental(
            existing_resume_data=profile.resume_data or {},
            existing_marksheet_data=profile.academic_data or {},
            existing_coding_data={
                "github": profile.github_data or {},
                "leetcode": profile.leetcode_data or {},
                "score": profile.coding_score,
                "persona": profile.coding_persona,
            },
            resume_file=resume_bytes,
            resume_filename=resume_file.filename if resume_file else None,
            resume_content_type=resume_file.content_type if resume_file else None,
            marksheet_file=marksheet_bytes,
            marksheet_filename=marksheet_file.filename if marksheet_file else None,
            marksheet_content_type=marksheet_file.content_type if marksheet_file else None,
            resume_changed=inferred_resume_changed,
            marksheet_changed=inferred_marksheet_changed,
            coding_changed=coding_changed,
            branch=branch_clean,
            github=github_clean,
            leetcode=leetcode_clean,
            existing_resume_url=latest_upload.resume_url if latest_upload else None,
        )
    except ValueError as exc:
        logger.exception("Incremental analyzer failure")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if inferred_resume_changed and resume_file is not None:
        normalized.setdefault("resume_data", {})["file_name"] = resume_file.filename
    else:
        existing_resume_name = (profile.resume_data or {}).get("file_name")
        if existing_resume_name:
            normalized.setdefault("resume_data", {})["file_name"] = existing_resume_name

    if inferred_marksheet_changed and marksheet_file is not None:
        normalized.setdefault("academic_data", {})["file_name"] = marksheet_file.filename
    else:
        existing_marksheet_name = (profile.academic_data or {}).get("file_name")
        if existing_marksheet_name:
            normalized.setdefault("academic_data", {})["file_name"] = existing_marksheet_name

    return StudentAnalyzeResponse.model_validate(normalized)


@router.post("/profile", response_model=StudentProfileStoreResponse)
def create_student_profile(
    payload: StudentProfileCreate,
    db: Session = Depends(get_db),
    requesting_student_id: int | None = Depends(get_optional_student_id),
) -> StudentProfileStoreResponse:
    service = ProfileService(db)
    return service.save_profile(payload, requesting_student_id=requesting_student_id)


@router.get("/profile/me", response_model=StudentProfileResponse)
def get_my_profile(
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    service = ProfileService(db)
    return service.get_profile(student_id)


@router.post("/register", response_model=RegisterResponse)
def register_student(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    auth_service = AuthService(get_settings())
    service = ProfileService(db, auth_service=auth_service)
    student = service.register_student(payload)
    return RegisterResponse(
        student_id=student.id,
        message="Registration successful.",
    )


@router.post("/login", response_model=AuthTokenResponse)
def login_student(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    auth_service = AuthService(get_settings())
    service = ProfileService(db, auth_service=auth_service)
    return service.login_student(payload)


@router.get("/profile/{id}", response_model=StudentProfileResponse)
def get_student_profile(id: int, db: Session = Depends(get_db)) -> StudentProfileResponse:
    service = ProfileService(db)
    return service.get_profile(id)


@router.post("/match-jd", response_model=JDMatchResponse)
async def match_students_with_jd(request: Request, db: Session = Depends(get_db)) -> JDMatchResponse:
    content_type = request.headers.get("content-type", "").lower()
    merged_jd_text: str
    student_ids: list[int] | None = None
    top_k: int | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        jd_text = str(form.get("jd_text") or "").strip() or None

        jd_file = form.get("jd_file")
        file_text: str | None = None
        if isinstance(jd_file, (UploadFile, StarletteUploadFile)):
            suffix = Path(jd_file.filename or "").suffix.lower()
            if suffix not in ALLOWED_JD_EXTENSIONS:
                raise HTTPException(status_code=400, detail="JD file must be PDF or DOCX.")
            raw_file = await jd_file.read()
            if not raw_file:
                raise HTTPException(status_code=400, detail="JD file is empty.")
            if len(raw_file) > MAX_FILE_BYTES:
                raise HTTPException(status_code=413, detail="JD file size exceeds 8 MB limit.")
            try:
                file_text = extract_jd_text_from_file(raw_file, jd_file.filename or "jd_file")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        merged_jd_text = _merge_jd_sources(file_text, jd_text)
        if len(merged_jd_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Merged JD content must be at least 20 characters.")

        try:
            student_ids = _parse_student_ids_form(form.get("student_ids"))  # type: ignore[arg-type]
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid student_ids format.") from exc

        raw_top_k = form.get("top_k")
        if raw_top_k not in (None, ""):
            try:
                top_k = int(str(raw_top_k))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="top_k must be an integer.") from exc
            if top_k < 1 or top_k > 500:
                raise HTTPException(status_code=400, detail="top_k must be between 1 and 500.")
    else:
        try:
            payload = JDMatchRequest.model_validate(await request.json())
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON payload for JD matching.") from exc
        merged_jd_text = payload.jd_text
        student_ids = payload.student_ids
        top_k = payload.top_k

    settings = get_settings()
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
        jd_data, jd_error = await call_jd_analyzer(
            settings=settings,
            client=client,
            jd_text=merged_jd_text,
        )
    if jd_error or jd_data is None:
        raise HTTPException(status_code=502, detail=f"JD analyzer failed: {jd_error or 'unknown error'}")

    constraints, filters, candidates = run_jd_matching(
        db=db,
        jd_data=jd_data,
        student_ids=student_ids,
        top_k=top_k,
    )
    return JDMatchResponse(jd=constraints, filters=filters, candidates=candidates)
