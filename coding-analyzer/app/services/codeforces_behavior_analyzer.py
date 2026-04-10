from __future__ import annotations

from statistics import mean
from typing import Any

import httpx

from app.services.codeforces_service import CODEFORCES_API_BASE
from app.utils.http import request_with_retry


def _rating_trend(ratings: list[float]) -> str:
    if len(ratings) < 2:
        return "Stable"
    delta = ratings[-1] - ratings[0]
    if delta > 80:
        return "Improving"
    if delta < -80:
        return "Declining"
    return "Stable"


def _competitive_strength(current: int | None, max_rating: int | None, contests: int) -> int:
    current_score = min(max((current or 0) - 800, 0), 1600) / 1600.0 * 60.0
    peak_score = min(max((max_rating or 0) - 800, 0), 1800) / 1800.0 * 25.0
    contest_score = min(contests, 120) / 120.0 * 15.0
    return int(min(round(current_score + peak_score + contest_score), 100))


async def analyze_codeforces_behavior(
    client: httpx.AsyncClient,
    username: str,
    codeforces_profile: dict[str, Any],
) -> dict[str, Any]:
    rating_resp = await request_with_retry(
        client,
        method="GET",
        url=f"{CODEFORCES_API_BASE}/user.rating",
        platform="codeforces",
        params={"handle": username},
    )
    status_resp = await request_with_retry(
        client,
        method="GET",
        url=f"{CODEFORCES_API_BASE}/user.status",
        platform="codeforces",
        params={"handle": username, "from": 1, "count": 300},
    )

    rating_history = []
    if rating_resp.status_code < 400:
        payload = rating_resp.json()
        if payload.get("status") == "OK":
            rating_history = payload.get("result", []) or []

    ratings = [float(item.get("newRating")) for item in rating_history if item.get("newRating") is not None]
    contests = len(rating_history)

    tag_counter: dict[str, int] = {}
    solved_count = 0
    if status_resp.status_code < 400:
        payload = status_resp.json()
        if payload.get("status") == "OK":
            for sub in payload.get("result", []) or []:
                if sub.get("verdict") != "OK":
                    continue
                solved_count += 1
                for tag in (sub.get("problem") or {}).get("tags", []) or []:
                    tag_counter[tag] = tag_counter.get(tag, 0) + 1

    sorted_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)
    maturity = int(
        min(
            round(
                (min(solved_count, 500) / 500.0 * 45)
                + (min(contests, 100) / 100.0 * 30)
                + (min(len(sorted_tags), 20) / 20.0 * 25)
            ),
            100,
        )
    )

    current_rating = codeforces_profile.get("rating")
    max_rating = codeforces_profile.get("max_rating")
    return {
        "contest_participation_trend": "Active" if contests >= 15 else "Moderate" if contests >= 5 else "Low",
        "rating_growth_trend": _rating_trend(ratings),
        "rating_growth_velocity": round((ratings[-1] - ratings[0]) / max(len(ratings), 1), 2) if len(ratings) >= 2 else 0.0,
        "problem_tags_solved": {tag: count for tag, count in sorted_tags[:12]},
        "competitive_maturity_score": maturity,
        "competitive_strength": _competitive_strength(current_rating, max_rating, contests),
        "average_contest_rating": round(mean(ratings), 2) if ratings else None,
    }
