from __future__ import annotations

from app.models.response_model import (
    CodeforcesProfileData,
    GitHubProfileData,
    LeetCodeProfileData,
)


def normalize_github(data: dict | None) -> GitHubProfileData:
    data = data or {}
    return GitHubProfileData(
        repos=int(data.get("repos", 0) or 0),
        followers=int(data.get("followers", 0) or 0),
        following=int(data.get("following", 0) or 0),
        stars=int(data.get("stars", 0) or 0),
        languages=list(data.get("languages", []) or []),
        pinned_repositories=list(data.get("pinned_repositories", []) or []),
        recent_commit_activity=int(data.get("recent_commit_activity", 0) or 0),
        last_30_day_commits=int(data.get("last_30_day_commits", 0) or 0),
        activity_trend_30d=list(data.get("activity_trend_30d", []) or []),
    )


def normalize_leetcode(data: dict | None) -> LeetCodeProfileData:
    data = data or {}
    return LeetCodeProfileData(
        total_solved=int(data.get("total_solved", 0) or 0),
        easy=int(data.get("easy", 0) or 0),
        medium=int(data.get("medium", 0) or 0),
        hard=int(data.get("hard", 0) or 0),
        contest_rating=float(data["contest_rating"]) if data.get("contest_rating") is not None else None,
        ranking=int(data["ranking"]) if data.get("ranking") is not None else None,
        streak=int(data["streak"]) if data.get("streak") is not None else None,
    )


def normalize_codeforces(data: dict | None) -> CodeforcesProfileData:
    data = data or {}
    return CodeforcesProfileData(
        rating=int(data["rating"]) if data.get("rating") is not None else None,
        max_rating=int(data["max_rating"]) if data.get("max_rating") is not None else None,
        rank=data.get("rank"),
        max_rank=data.get("max_rank"),
        contests_participated=int(data["contests_participated"]) if data.get("contests_participated") is not None else None,
    )
