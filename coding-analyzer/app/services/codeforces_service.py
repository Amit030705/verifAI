from __future__ import annotations

import httpx

from app.utils.errors import PlatformServiceError
from app.utils.http import request_with_retry

CODEFORCES_API_BASE = "https://codeforces.com/api"


def empty_codeforces_payload() -> dict:
    return {
        "rating": None,
        "max_rating": None,
        "rank": None,
        "max_rank": None,
        "contests_participated": None,
    }


async def analyze_codeforces_profile(client: httpx.AsyncClient, username: str) -> dict:
    info_resp = await request_with_retry(
        client,
        method="GET",
        url=f"{CODEFORCES_API_BASE}/user.info",
        platform="codeforces",
        params={"handles": username},
    )

    if info_resp.status_code >= 400:
        raise PlatformServiceError("codeforces", "Unable to fetch Codeforces profile.", info_resp.status_code)

    info_payload = info_resp.json()
    if info_payload.get("status") != "OK" or not info_payload.get("result"):
        raise PlatformServiceError("codeforces", f"Codeforces user '{username}' not found.", 404)

    user = info_payload["result"][0]

    rating_resp = await request_with_retry(
        client,
        method="GET",
        url=f"{CODEFORCES_API_BASE}/user.rating",
        platform="codeforces",
        params={"handle": username},
    )

    contests_participated: int | None = None
    if rating_resp.status_code < 400:
        rating_payload = rating_resp.json()
        if rating_payload.get("status") == "OK":
            contests_participated = len(rating_payload.get("result", []))

    return {
        "rating": int(user["rating"]) if user.get("rating") is not None else None,
        "max_rating": int(user["maxRating"]) if user.get("maxRating") is not None else None,
        "rank": user.get("rank"),
        "max_rank": user.get("maxRank"),
        "contests_participated": contests_participated,
    }
