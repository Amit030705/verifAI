from __future__ import annotations

import asyncio
import base64
from datetime import UTC, datetime
from typing import Any

import httpx

from app.utils.http import request_with_retry

GITHUB_API_BASE = "https://api.github.com"

DOMAIN_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("AI Project", ("ai", "ml", "llm", "nlp", "pytorch", "tensorflow")),
    ("Backend System", ("api", "backend", "fastapi", "django", "flask", "microservice")),
    ("Web App", ("react", "next", "frontend", "webapp", "javascript")),
    ("Mobile App", ("android", "ios", "react-native", "flutter", "mobile")),
    ("SaaS Product", ("saas", "multi-tenant", "billing", "dashboard")),
    ("Dev Tool", ("cli", "devtool", "tooling", "plugin", "automation")),
]

TECH_KEYWORDS = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "react": "React",
    "next": "Next.js",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "docker": "Docker",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "python": "Python",
    "node": "Node.js",
    "redis": "Redis",
}


def _to_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _repo_relevance(repo: dict[str, Any]) -> float:
    stars = float(repo.get("stargazers_count") or 0)
    size = float(repo.get("size") or 0)
    updated_at = _to_dt(repo.get("updated_at"))
    recency_days = 365.0
    if updated_at:
        recency_days = max((datetime.now(UTC) - updated_at).days, 0)
    recency_score = max(0.0, 1.0 - min(recency_days / 365.0, 1.0))
    originality_boost = 1.0 if not repo.get("fork") else 0.0
    return (stars * 1.8) + (min(size, 50000) / 2000.0) + (recency_score * 30.0) + (originality_boost * 25.0)


def _documentation_score(readme_text: str) -> int:
    lower = readme_text.lower()
    score = 20
    for token in ("install", "setup", "run", "usage"):
        if token in lower:
            score += 12
    for token in ("architecture", "design", "system", "api"):
        if token in lower:
            score += 8
    if len(readme_text) > 1200:
        score += 20
    elif len(readme_text) > 600:
        score += 10
    return max(0, min(score, 100))


def _infer_domain(repo: dict[str, Any], tech_stack: list[str], readme_text: str) -> str:
    hay = " ".join(
        [
            str(repo.get("name") or ""),
            str(repo.get("description") or ""),
            " ".join(tech_stack),
            readme_text[:1000],
        ]
    ).lower()
    matched: list[str] = []
    for label, tokens in DOMAIN_RULES:
        if any(token in hay for token in tokens):
            matched.append(label)
    if not matched:
        return "General Software Project"
    if len(matched) >= 2:
        return f"{matched[0]} + {matched[1]}"
    return matched[0]


async def _fetch_readme(client: httpx.AsyncClient, owner: str, repo: str) -> str:
    response = await request_with_retry(
        client,
        method="GET",
        url=f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme",
        platform="github",
    )
    if response.status_code >= 400:
        return ""
    payload = response.json()
    encoded = payload.get("content")
    if not encoded:
        return ""
    try:
        return base64.b64decode(encoded).decode("utf-8", errors="ignore")
    except Exception:
        return ""


async def _fetch_root_listing(client: httpx.AsyncClient, owner: str, repo: str) -> list[dict[str, Any]]:
    response = await request_with_retry(
        client,
        method="GET",
        url=f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents",
        platform="github",
    )
    if response.status_code >= 400:
        return []
    payload = response.json()
    return payload if isinstance(payload, list) else []


def _extract_tech_stack(repo: dict[str, Any], readme_text: str, root_items: list[dict[str, Any]]) -> list[str]:
    tokens = {
        str(repo.get("language") or "").lower(),
        str(repo.get("description") or "").lower(),
        readme_text.lower(),
        " ".join(item.get("name", "").lower() for item in root_items),
    }
    blob = " ".join(tokens)
    detected = {label for token, label in TECH_KEYWORDS.items() if token in blob}
    return sorted(detected)


def _complexity_score(repo: dict[str, Any], root_items: list[dict[str, Any]], readme_text: str) -> int:
    size = float(repo.get("size") or 0)
    file_count = len([item for item in root_items if item.get("type") == "file"])
    dir_count = len([item for item in root_items if item.get("type") == "dir"])
    dep_markers = sum(
        1
        for item in root_items
        if item.get("name", "").lower() in {"package.json", "requirements.txt", "pyproject.toml", "dockerfile"}
    )
    score = (min(size, 50000) / 700.0) + (file_count * 1.2) + (dir_count * 2.0) + (dep_markers * 8.0)
    if len(readme_text) > 1000:
        score += 8
    return int(max(0, min(round(score), 100)))


def _quality_score(repo: dict[str, Any], readme_score: int, complexity_score: int) -> int:
    stars = min(float(repo.get("stargazers_count") or 0), 200) / 200.0 * 35.0
    forks = min(float(repo.get("forks_count") or 0), 100) / 100.0 * 15.0
    pushed_at = _to_dt(repo.get("pushed_at"))
    freshness = 0.0
    if pushed_at:
        freshness = max(0.0, 1.0 - min((datetime.now(UTC) - pushed_at).days / 365.0, 1.0)) * 20.0
    return int(max(0, min(round(stars + forks + freshness + (readme_score * 0.2) + (complexity_score * 0.1)), 100)))


async def _analyze_single_repo(client: httpx.AsyncClient, owner: str, repo: dict[str, Any], sem: asyncio.Semaphore) -> dict[str, Any]:
    name = str(repo.get("name") or "")
    async with sem:
        readme_text, root_items = await asyncio.gather(
            _fetch_readme(client, owner, name),
            _fetch_root_listing(client, owner, name),
            return_exceptions=True,
        )

    readme_text = "" if isinstance(readme_text, Exception) else readme_text
    root_items = [] if isinstance(root_items, Exception) else root_items
    tech_stack = _extract_tech_stack(repo, readme_text, root_items)
    readme_score = _documentation_score(readme_text)
    complexity = _complexity_score(repo, root_items, readme_text)
    quality = _quality_score(repo, readme_score, complexity)
    domain = _infer_domain(repo, tech_stack, readme_text)

    return {
        "name": name,
        "description": repo.get("description") or "",
        "stars": int(repo.get("stargazers_count") or 0),
        "forks": int(repo.get("forks_count") or 0),
        "last_updated": repo.get("updated_at") or "",
        "size": int(repo.get("size") or 0),
        "tech_stack": tech_stack,
        "quality_score": quality,
        "readme_quality_score": readme_score,
        "complexity_score": complexity,
        "domain": domain,
    }


async def analyze_github_repositories(client: httpx.AsyncClient, username: str, repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = [
        repo
        for repo in repositories
        if not repo.get("fork") and not repo.get("archived") and int(repo.get("size") or 0) > 0
    ]
    ranked = sorted(filtered, key=_repo_relevance, reverse=True)[:12]
    sem = asyncio.Semaphore(5)
    analyzed = await asyncio.gather(
        *[_analyze_single_repo(client, username, repo, sem) for repo in ranked],
        return_exceptions=True,
    )
    return [item for item in analyzed if not isinstance(item, Exception)]
