from __future__ import annotations

from app.models.response_model import (
    CodeforcesProfileData,
    GitHubProfileData,
    LeetCodeProfileData,
    ScoreBlock,
)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(value, high))


def _github_score(github: GitHubProfileData) -> int:
    repos_score = min(github.repos, 60) / 60 * 25
    stars_score = min(github.stars, 300) / 300 * 25
    followers_score = min(github.followers, 200) / 200 * 20
    commits_score = min(github.last_30_day_commits, 120) / 120 * 20
    language_score = min(len(github.languages), 8) / 8 * 10

    return int(round(_clamp(repos_score + stars_score + followers_score + commits_score + language_score)))


def _leetcode_score(leetcode: LeetCodeProfileData) -> int:
    solved_score = min(leetcode.total_solved, 1200) / 1200 * 45
    hard_score = min(leetcode.hard, 150) / 150 * 20

    contest_rating = leetcode.contest_rating or 0
    contest_score = _clamp(((contest_rating - 1200) / 1000) * 25, 0, 25)

    streak = leetcode.streak or 0
    streak_score = min(streak, 120) / 120 * 10

    return int(round(_clamp(solved_score + hard_score + contest_score + streak_score)))


def _codeforces_score(codeforces: CodeforcesProfileData) -> int:
    if codeforces.rating is None and codeforces.max_rating is None:
        return 0

    rating = codeforces.rating or 0
    max_rating = codeforces.max_rating or rating
    contests = codeforces.contests_participated or 0

    rating_score = _clamp(((rating - 800) / 1400) * 70, 0, 70)
    max_rating_score = _clamp(((max_rating - 900) / 1500) * 15, 0, 15)
    contest_score = min(contests, 80) / 80 * 15

    return int(round(_clamp(rating_score + max_rating_score + contest_score)))


def _coding_level(overall: int) -> str:
    if overall < 35:
        return "Beginner"
    if overall < 60:
        return "Intermediate"
    if overall < 80:
        return "Strong"
    return "Excellent"


def score_profiles(
    *,
    github_score: int,
    leetcode_score: int,
    codeforces_score: int,
    consistency_score: int,
    engineering_maturity_score: int,
) -> tuple[ScoreBlock, str]:
    overall_score = int(
        round(
            (github_score * 0.40)
            + (leetcode_score * 0.35)
            + (codeforces_score * 0.15)
            + (((consistency_score + engineering_maturity_score) / 2.0) * 0.10)
        )
    )

    scores = ScoreBlock(
        github_score=github_score,
        leetcode_score=leetcode_score,
        codeforces_score=codeforces_score,
        engineering_maturity_score=engineering_maturity_score,
        overall_score=overall_score,
    )

    return scores, _coding_level(overall_score)
