from __future__ import annotations

import json
from statistics import mean
from typing import Any

import httpx

from app.utils.http import request_with_retry

LEETCODE_GRAPHQL_ENDPOINT = "https://leetcode.com/graphql"

TOPIC_QUERY = """
query userProfileUserQuestionProgressV2($userSlug: String!) {
  userProfileUserQuestionProgressV2(userSlug: $userSlug) {
    numAcceptedQuestions {
      count
      difficulty
    }
    userSessionBeatsPercentage {
      difficulty
      percentage
    }
  }
  matchedUser(username: $userSlug) {
    tagProblemCounts {
      advanced { tagName problemsSolved }
      intermediate { tagName problemsSolved }
      fundamental { tagName problemsSolved }
    }
  }
  userContestRankingHistory(username: $userSlug) {
    attended
    trendDirection
    problemsSolved
    totalProblems
    rating
    ranking
    contest {
      startTime
    }
  }
}
"""


async def _graphql_request(client: httpx.AsyncClient, query: str, username: str) -> dict[str, Any]:
    response = await request_with_retry(
        client,
        method="POST",
        url=LEETCODE_GRAPHQL_ENDPOINT,
        platform="leetcode",
        json={"query": query, "variables": {"userSlug": username}},
        headers={"Referer": f"https://leetcode.com/{username}/", "Content-Type": "application/json"},
    )
    if response.status_code >= 400:
        return {}
    try:
        return response.json()
    except json.JSONDecodeError:
        return {}


def _difficulty_weighted_score(easy: int, medium: int, hard: int) -> int:
    weighted = (easy * 1.0) + (medium * 3.0) + (hard * 5.0)
    return int(min(round((weighted / 1200.0) * 100), 100))


def _contest_strength(rating: float | None) -> str:
    if rating is None:
        return "Low"
    if rating < 1600:
        return "Moderate"
    if rating < 1900:
        return "Strong"
    return "Elite"


def _consistency_score(streak: int | None, contest_count: int, attended_ratio: float) -> int:
    streak_component = min((streak or 0), 180) / 180.0 * 45.0
    contest_component = min(contest_count, 40) / 40.0 * 30.0
    ratio_component = max(0.0, min(attended_ratio, 1.0)) * 25.0
    return int(min(round(streak_component + contest_component + ratio_component), 100))


async def analyze_leetcode_behavior(
    client: httpx.AsyncClient,
    username: str,
    leetcode_profile: dict[str, Any],
) -> dict[str, Any]:
    payload = await _graphql_request(client, TOPIC_QUERY, username)
    data = payload.get("data", {}) if isinstance(payload, dict) else {}

    tags_payload = ((data.get("matchedUser") or {}).get("tagProblemCounts") or {})
    tag_counts: dict[str, int] = {}
    for bucket in ("advanced", "intermediate", "fundamental"):
        for item in tags_payload.get(bucket, []) or []:
            tag_name = str(item.get("tagName") or "").strip()
            solved = int(item.get("problemsSolved") or 0)
            if tag_name and solved > 0:
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + solved

    sorted_topics = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    strongest_topics = [topic for topic, _ in sorted_topics[:5]]
    weakest_topics = [topic for topic, count in sorted(tag_counts.items(), key=lambda x: x[1])[:3] if count > 0]

    history = data.get("userContestRankingHistory") or []
    attended = [row for row in history if row.get("attended")]
    contest_count = len(attended)
    best_rank = min((int(row.get("ranking")) for row in attended if row.get("ranking")), default=None)
    ratings = [float(row.get("rating")) for row in attended if row.get("rating") is not None]
    rating_trend = "Stable"
    if len(ratings) >= 2:
        delta = ratings[-1] - ratings[0]
        if delta > 50:
            rating_trend = "Improving"
        elif delta < -50:
            rating_trend = "Declining"

    easy = int(leetcode_profile.get("easy", 0) or 0)
    medium = int(leetcode_profile.get("medium", 0) or 0)
    hard = int(leetcode_profile.get("hard", 0) or 0)
    weighted = _difficulty_weighted_score(easy, medium, hard)

    attended_ratio = 0.0
    if history:
        attended_ratio = contest_count / len(history)

    depth = int(min(round((weighted * 0.6) + (min(hard, 200) / 200 * 30) + (min(contest_count, 50) / 50 * 10)), 100))
    consistency = _consistency_score(leetcode_profile.get("streak"), contest_count, attended_ratio)

    return {
        "difficulty_weighted_score": weighted,
        "topic_strengths": {topic: solved for topic, solved in sorted_topics[:10]},
        "strongest_topics": strongest_topics,
        "weakest_topics": weakest_topics,
        "problem_solving_depth": depth,
        "contest_participation_count": contest_count,
        "best_rank": best_rank,
        "contest_rating_trend": rating_trend,
        "contest_strength": _contest_strength(leetcode_profile.get("contest_rating")),
        "consistency_score": consistency,
        "average_contest_rating": round(mean(ratings), 2) if ratings else None,
    }
