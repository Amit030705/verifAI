from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.models.response_model import JDAnalyzeRequest, JDAnalyzeResponse
from app.services.jd_analyzer_service import JDAnalyzerService, JDAnalyzerServiceError

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"request": request})


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze-jd", response_model=JDAnalyzeResponse)
async def analyze_jd(payload: JDAnalyzeRequest) -> JDAnalyzeResponse:
    try:
        service = JDAnalyzerService(settings=get_settings())
        return await service.parse_jd(payload.jd_text)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except JDAnalyzerServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"JD analysis failed: {exc}") from exc
