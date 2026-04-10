from __future__ import annotations

import json

import httpx

from app.utils.errors import PlatformServiceError
from app.utils.http import request_with_retry

LEETCODE_GRAPHQL_ENDPOINT = "https://leetcode.com/graphql"

PROFILE_QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
        submissions
      }
    }
    profile {
      ranking
    }
  }
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
    topPercentage
  }
}
"""

STREAK_QUERY = """
query userProfileCalendar($username: String!) {
  userProfileCalendar(username: $username) {
    streak
    totalActiveDays
    submissionCalendar
  }
}
"""


def _extract_submission_counts(payload: dict) -> tuple[int, int, int, int]:
    solved_map = {"All": 0, "Easy": 0, "Medium": 0, "Hard": 0}
    buckets = (
        payload.get("matchedUser", {})
        .get("submitStatsGlobal", {})
        .get("acSubmissionNum", [])
    )

    for row in buckets:
        difficulty = row.get("difficulty")
        count = int(row.get("count", 0) or 0)
        if difficulty in solved_map:
            solved_map[difficulty] = count

    return solved_map["All"], solved_map["Easy"], solved_map["Medium"], solved_map["Hard"]


async def _graphql_request(client: httpx.AsyncClient, query: str, username: str) -> dict:
    response = await request_with_retry(
        client,
        method="POST",
        url=LEETCODE_GRAPHQL_ENDPOINT,
        platform="leetcode",
        json={"query": query, "variables": {"username": username}},
        headers={"Referer": f"https://leetcode.com/{username}/", "Content-Type": "application/json"},
    )

    if response.status_code >= 400:
        raise PlatformServiceError("leetcode", "Unable to fetch LeetCode profile.", response.status_code)

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise PlatformServiceError("leetcode", "LeetCode returned invalid response.", 502) from exc


async def analyze_leetcode_profile(client: httpx.AsyncClient, username: str) -> dict:
    payload = await _graphql_request(client, PROFILE_QUERY, username)

    if payload.get("errors"):
        raise PlatformServiceError("leetcode", f"LeetCode query failed for '{username}'.", 404)

    matched_user = payload.get("data", {}).get("matchedUser")
    if not matched_user:
        raise PlatformServiceError("leetcode", f"LeetCode user '{username}' not found.", 404)

    contest = payload.get("data", {}).get("userContestRanking") or {}
    total, easy, medium, hard = _extract_submission_counts(payload.get("data", {}))

    ranking = matched_user.get("profile", {}).get("ranking")
    contest_rating = contest.get("rating")

    streak_value: int | None = None
    try:
        streak_payload = await _graphql_request(client, STREAK_QUERY, username)
        calendar = streak_payload.get("data", {}).get("userProfileCalendar") or {}
        if calendar.get("streak") is not None:
            streak_value = int(calendar.get("streak"))
    except PlatformServiceError:
        streak_value = None

    return {
        "total_solved": int(total),
        "easy": int(easy),
        "medium": int(medium),
        "hard": int(hard),
        "contest_rating": float(contest_rating) if contest_rating is not None else None,
        "ranking": int(ranking) if ranking is not None else None,
        "streak": streak_value,
    }
