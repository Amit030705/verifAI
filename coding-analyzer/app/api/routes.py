from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.response_model import AnalyzeCodingProfileRequest, CodingProfileAnalysisResponse
from app.services.codeforces_behavior_analyzer import analyze_codeforces_behavior
from app.services.codeforces_service import analyze_codeforces_profile, empty_codeforces_payload
from app.services.github_repo_analyzer import analyze_github_repositories
from app.services.github_service import analyze_github_profile
from app.services.leetcode_behavior_analyzer import analyze_leetcode_behavior
from app.services.leetcode_service import analyze_leetcode_profile
from app.services.normalizer import normalize_codeforces, normalize_github, normalize_leetcode
from app.services.profile_synthesizer import synthesize_profile
from app.services.recruiter_summary_generator import generate_recruiter_summary
from app.services.scoring_engine import score_profiles
from app.utils.cache import TTLCache
from app.utils.errors import PlatformServiceError
from app.utils.identifiers import extract_username

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

HTTP_TIMEOUT = httpx.Timeout(12.0, connect=8.0)
DEFAULT_HEADERS = {
    "User-Agent": "VeriAI-Coding-Analyzer/1.0",
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
}
RESPONSE_CACHE = TTLCache(ttl_seconds=300)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "index.html", {"request": request})


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze-coding-profile", response_model=CodingProfileAnalysisResponse)
async def analyze_coding_profile(payload: AnalyzeCodingProfileRequest) -> CodingProfileAnalysisResponse:
    github_username = extract_username(payload.github_username, "github")
    leetcode_username = extract_username(payload.leetcode_username, "leetcode")
    codeforces_username = extract_username(payload.codeforces_username, "codeforces")
    cache_key = f"{github_username or ''}|{leetcode_username or ''}|{codeforces_username or ''}"
    cached = RESPONSE_CACHE.get(cache_key)
    if cached:
        return CodingProfileAnalysisResponse(**cached)

    tasks: dict[str, asyncio.Task] = {}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
        if github_username:
            tasks["github"] = asyncio.create_task(analyze_github_profile(client, github_username))

        if leetcode_username:
            tasks["leetcode"] = asyncio.create_task(analyze_leetcode_profile(client, leetcode_username))

        if codeforces_username:
            tasks["codeforces"] = asyncio.create_task(analyze_codeforces_profile(client, codeforces_username))

        platform_results: dict[str, dict | None] = {
            "github": None,
            "leetcode": None,
            "codeforces": empty_codeforces_payload(),
        }
        errors: dict[str, str] = {}

        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for platform, result in zip(tasks.keys(), results, strict=False):
                if isinstance(result, PlatformServiceError):
                    errors[platform] = result.message
                    continue

                if isinstance(result, Exception):
                    errors[platform] = f"Unexpected {platform} processing error."
                    continue

                platform_results[platform] = result

    github = normalize_github(platform_results.get("github"))
    leetcode = normalize_leetcode(platform_results.get("leetcode"))
    codeforces = normalize_codeforces(platform_results.get("codeforces"))
    repo_analysis: list[dict] = []
    leetcode_intelligence: dict = {}
    codeforces_intelligence: dict = {}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=True) as deep_client:
        deep_tasks: dict[str, asyncio.Task] = {}
        if github_username and platform_results.get("github"):
            deep_tasks["github_repo_analysis"] = asyncio.create_task(
                analyze_github_repositories(
                    deep_client,
                    github_username,
                    list((platform_results.get("github") or {}).get("repositories", []) or []),
                )
            )
        if leetcode_username and platform_results.get("leetcode"):
            deep_tasks["leetcode_intelligence"] = asyncio.create_task(
                analyze_leetcode_behavior(deep_client, leetcode_username, platform_results.get("leetcode") or {})
            )
        if codeforces_username and platform_results.get("codeforces"):
            deep_tasks["codeforces_intelligence"] = asyncio.create_task(
                analyze_codeforces_behavior(deep_client, codeforces_username, platform_results.get("codeforces") or {})
            )

        if deep_tasks:
            deep_results = await asyncio.gather(*deep_tasks.values(), return_exceptions=True)
            for key, value in zip(deep_tasks.keys(), deep_results, strict=False):
                if isinstance(value, Exception):
                    errors[key] = "Deep analysis unavailable for this platform."
                    continue
                if key == "github_repo_analysis":
                    repo_analysis = value
                elif key == "leetcode_intelligence":
                    leetcode_intelligence = value
                elif key == "codeforces_intelligence":
                    codeforces_intelligence = value

    github_deep_score = 0
    if repo_analysis:
        github_deep_score = int(round(sum(item.get("quality_score", 0) for item in repo_analysis) / len(repo_analysis)))
    else:
        github_deep_score = min(100, int((github.stars / 5) + (github.last_30_day_commits / 2)))

    leetcode_deep_score = int(leetcode_intelligence.get("problem_solving_depth", 0))
    if not leetcode_deep_score:
        leetcode_deep_score = min(100, int((leetcode.total_solved / 12) + (leetcode.hard / 3)))

    codeforces_deep_score = int(codeforces_intelligence.get("competitive_strength", 0))
    if not codeforces_deep_score:
        codeforces_deep_score = min(100, int(((codeforces.rating or 0) - 800) / 12))

    synthesis = synthesize_profile(
        github=github.model_dump(),
        leetcode=leetcode.model_dump(),
        codeforces=codeforces.model_dump(),
        repo_analysis=repo_analysis,
        leetcode_intelligence=leetcode_intelligence,
        codeforces_intelligence=codeforces_intelligence,
    )

    scores, coding_level = score_profiles(
        github_score=max(0, min(github_deep_score, 100)),
        leetcode_score=max(0, min(leetcode_deep_score, 100)),
        codeforces_score=max(0, min(codeforces_deep_score, 100)),
        consistency_score=int(synthesis.get("consistency_score", 0)),
        engineering_maturity_score=int(synthesis.get("engineering_maturity_score", 0)),
    )

    recruiter_summary, hiring_recommendation = generate_recruiter_summary(
        coding_persona=str(synthesis.get("coding_persona", "Beginner Learner")),
        inferred_strengths=list(synthesis.get("inferred_strengths", [])),
        engineering_maturity_score=int(synthesis.get("engineering_maturity_score", 0)),
        consistency_score=int(synthesis.get("consistency_score", 0)),
        leetcode_depth=leetcode_deep_score,
        codeforces_strength=codeforces_deep_score,
    )

    metadata = {
        "requested_profiles": {
            "github": github_username,
            "leetcode": leetcode_username,
            "codeforces": codeforces_username,
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }

    response_payload = CodingProfileAnalysisResponse(
        github=github,
        leetcode=leetcode,
        codeforces=codeforces,
        repo_analysis=repo_analysis,
        leetcode_intelligence=leetcode_intelligence,
        codeforces_intelligence=codeforces_intelligence,
        inferred_strengths=list(synthesis.get("inferred_strengths", [])),
        coding_persona=str(synthesis.get("coding_persona", "Beginner Learner")),
        consistency_score=int(synthesis.get("consistency_score", 0)),
        engineering_maturity_score=int(synthesis.get("engineering_maturity_score", 0)),
        repository_quality_average=int(synthesis.get("repository_quality_average", 0)),
        profile_confidence=int(synthesis.get("profile_confidence", 0)),
        recruiter_summary=recruiter_summary,
        hiring_recommendation=hiring_recommendation,
        scores=scores,
        coding_level=coding_level,
        errors=errors,
        metadata=metadata,
    )
    RESPONSE_CACHE.set(cache_key, response_payload.model_dump())
    return response_payload
