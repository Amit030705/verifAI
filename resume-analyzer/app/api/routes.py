from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.response_model import ResumeAnalysisResponse
from app.services.extractor import ResumeExtractor
from app.services.parser import ResumeParsingError, extract_resume_text

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR.parent / "uploads"
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024

extractor = ResumeExtractor()


@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "index.html", {"request": request})


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze-resume", response_model=ResumeAnalysisResponse)
async def analyze_resume(response: Response, file: UploadFile = File(...)) -> ResumeAnalysisResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF or DOCX.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / safe_name

    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Uploaded file is too large. Please upload a file smaller than 8 MB.",
            )
        file_path.write_bytes(contents)

        text = extract_resume_text(file_path)
        extraction_result = extractor.extract(text)
        response.headers["X-Resume-Completeness-Score"] = str(extraction_result.completeness_score)

        return ResumeAnalysisResponse(**extraction_result.data)

    except ResumeParsingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {exc}") from exc
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
