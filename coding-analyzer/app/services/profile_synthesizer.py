from __future__ import annotations

from typing import Any


def synthesize_profile(
    *,
    github: dict[str, Any],
    leetcode: dict[str, Any],
    codeforces: dict[str, Any],
    repo_analysis: list[dict[str, Any]],
    leetcode_intelligence: dict[str, Any],
    codeforces_intelligence: dict[str, Any],
) -> dict[str, Any]:
    strengths: list[str] = []
    if any("Backend" in (repo.get("domain") or "") for repo in repo_analysis):
        strengths.append("Backend Development")
    if any("AI" in (repo.get("domain") or "") for repo in repo_analysis):
        strengths.append("AI Engineering")
    if (leetcode_intelligence.get("problem_solving_depth") or 0) >= 60 or (
        codeforces_intelligence.get("competitive_strength") or 0
    ) >= 60:
        strengths.append("Problem Solving")
    if github.get("last_30_day_commits", 0) >= 30:
        strengths.append("Execution Consistency")
    if not strengths:
        strengths.append("General Engineering Foundations")

    repo_quality_avg = 0
    if repo_analysis:
        repo_quality_avg = round(sum(repo.get("quality_score", 0) for repo in repo_analysis) / len(repo_analysis))

    github_signal = min(100, int((repo_quality_avg * 0.7) + (min(github.get("last_30_day_commits", 0), 120) / 120 * 30)))
    leetcode_signal = int(leetcode_intelligence.get("problem_solving_depth") or 0)
    codeforces_signal = int(codeforces_intelligence.get("competitive_strength") or 0)

    if github_signal >= 70 and max(leetcode_signal, codeforces_signal) < 55:
        persona = "Project Builder"
    elif max(leetcode_signal, codeforces_signal) >= 75 and github_signal < 60:
        persona = "Competitive Programmer"
    elif github_signal >= 60 and max(leetcode_signal, codeforces_signal) >= 60:
        persona = "Balanced Engineer"
    elif github.get("last_30_day_commits", 0) >= 20 and (leetcode.get("streak") or 0) >= 30:
        persona = "Consistent Developer"
    else:
        persona = "Beginner Learner"

    consistency_score = int(
        min(
            round(
                (min(github.get("last_30_day_commits", 0), 120) / 120 * 40)
                + (leetcode_intelligence.get("consistency_score", 0) * 0.4)
                + (30 if codeforces_intelligence.get("contest_participation_trend") == "Active" else 15)
            ),
            100,
        )
    )
    maturity = int(
        min(
            round(
                (github_signal * 0.45)
                + (leetcode_signal * 0.35)
                + (codeforces_signal * 0.20)
            ),
            100,
        )
    )

    provided_platforms = sum(
        1
        for present in (
            bool(github.get("repos") or github.get("followers")),
            bool(leetcode.get("total_solved")),
            bool(codeforces.get("rating") or codeforces.get("max_rating")),
        )
        if present
    )
    confidence = min(100, int((provided_platforms / 3 * 60) + (min(len(repo_analysis), 10) / 10 * 20) + 20))

    return {
        "inferred_strengths": strengths,
        "coding_persona": persona,
        "engineering_maturity_score": maturity,
        "consistency_score": consistency_score,
        "repository_quality_average": repo_quality_avg,
        "profile_confidence": confidence,
    }
