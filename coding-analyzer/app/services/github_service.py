from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

import httpx
from bs4 import BeautifulSoup

from app.utils.errors import PlatformServiceError
from app.utils.http import request_with_retry

GITHUB_API_BASE = "https://api.github.com"


async def _fetch_user(client: httpx.AsyncClient, username: str) -> dict:
    url = f"{GITHUB_API_BASE}/users/{username}"
    response = await request_with_retry(client, method="GET", url=url, platform="github")

    if response.status_code == 404:
        raise PlatformServiceError("github", f"GitHub user '{username}' not found.", 404)

    if response.status_code == 403:
        raise PlatformServiceError("github", "GitHub API rate limited. Try again later.", 429)

    if response.status_code >= 400:
        raise PlatformServiceError("github", "Unable to fetch GitHub profile data.", response.status_code)

    return response.json()


async def _fetch_repositories(client: httpx.AsyncClient, username: str) -> list[dict]:
    repos: list[dict] = []

    for page in range(1, 5):
        url = f"{GITHUB_API_BASE}/users/{username}/repos"
        response = await request_with_retry(
            client,
            method="GET",
            url=url,
            platform="github",
            params={"per_page": 100, "page": page, "sort": "updated", "direction": "desc"},
        )

        if response.status_code == 404:
            break

        if response.status_code >= 400:
            raise PlatformServiceError("github", "Unable to fetch GitHub repositories.", response.status_code)

        batch = response.json()
        if not isinstance(batch, list) or not batch:
            break

        repos.extend(batch)
        if len(batch) < 100:
            break

    return repos


async def _fetch_pinned_repositories(client: httpx.AsyncClient, username: str) -> list[str]:
    url = f"https://github.com/{username}"
    response = await request_with_retry(client, method="GET", url=url, platform="github")

    if response.status_code >= 400:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    pinned: list[str] = []

    selectors = [
        "div.pinned-item-list-item-content span.repo",
        "div.js-pinned-items-reorder-container span.repo",
        "ol.pinned-items-list span.repo",
    ]

    for selector in selectors:
        nodes = soup.select(selector)
        for node in nodes:
            name = node.get_text(strip=True)
            if name and name not in pinned:
                pinned.append(name)

    return pinned[:6]


async def _fetch_commit_activity(client: httpx.AsyncClient, username: str) -> tuple[int, list[dict[str, int | str]]]:
    since = datetime.now(UTC) - timedelta(days=30)
    commit_by_day: defaultdict[str, int] = defaultdict(int)

    for page in range(1, 4):
        url = f"{GITHUB_API_BASE}/users/{username}/events/public"
        response = await request_with_retry(
            client,
            method="GET",
            url=url,
            platform="github",
            params={"per_page": 100, "page": page},
        )

        if response.status_code == 404:
            break

        if response.status_code >= 400:
            break

        events = response.json()
        if not isinstance(events, list) or not events:
            break

        has_recent_events = False
        for event in events:
            created_at = event.get("created_at")
            if not created_at:
                continue

            event_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if event_dt < since:
                continue

            has_recent_events = True

            if event.get("type") == "PushEvent":
                payload = event.get("payload", {})
                commits = payload.get("size") or len(payload.get("commits", [])) or 1
                date_key = event_dt.date().isoformat()
                commit_by_day[date_key] += int(commits)

        if not has_recent_events:
            break

    total = sum(commit_by_day.values())
    trend = [{"date": day, "commits": commit_by_day[day]} for day in sorted(commit_by_day.keys())]
    return total, trend


async def analyze_github_profile(client: httpx.AsyncClient, username: str) -> dict:
    user_data = await _fetch_user(client, username)
    repos = await _fetch_repositories(client, username)

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    language_counter: Counter[str] = Counter()
    for repo in repos:
        language = repo.get("language")
        if language:
            language_counter[language] += 1

    top_languages = [lang for lang, _ in language_counter.most_common(6)]

    pinned = await _fetch_pinned_repositories(client, username)
    last_30_day_commits, trend = await _fetch_commit_activity(client, username)

    return {
        "repos": int(user_data.get("public_repos", 0)),
        "followers": int(user_data.get("followers", 0)),
        "following": int(user_data.get("following", 0)),
        "stars": int(stars),
        "languages": top_languages,
        "pinned_repositories": pinned,
        "recent_commit_activity": int(last_30_day_commits),
        "last_30_day_commits": int(last_30_day_commits),
        "activity_trend_30d": trend,
        "repositories": repos,
    }
