from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class AnalyzeCodingProfileRequest(BaseModel):
    github_username: str | None = None
    leetcode_username: str | None = None
    codeforces_username: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one_profile(self) -> "AnalyzeCodingProfileRequest":
        if not any([self.github_username, self.leetcode_username, self.codeforces_username]):
            raise ValueError("Provide at least one platform username or profile link.")
        return self


class ActivityTrendPoint(BaseModel):
    date: str
    commits: int


class GitHubProfileData(BaseModel):
    repos: int = 0
    followers: int = 0
    following: int = 0
    stars: int = 0
    languages: list[str] = Field(default_factory=list)
    pinned_repositories: list[str] = Field(default_factory=list)
    recent_commit_activity: int = 0
    last_30_day_commits: int = 0
    activity_trend_30d: list[ActivityTrendPoint] = Field(default_factory=list)


class LeetCodeProfileData(BaseModel):
    total_solved: int = 0
    easy: int = 0
    medium: int = 0
    hard: int = 0
    contest_rating: float | None = None
    ranking: int | None = None
    streak: int | None = None


class CodeforcesProfileData(BaseModel):
    rating: int | None = None
    max_rating: int | None = None
    rank: str | None = None
    max_rank: str | None = None
    contests_participated: int | None = None


class ScoreBlock(BaseModel):
    github_score: int = 0
    leetcode_score: int = 0
    codeforces_score: int = 0
    engineering_maturity_score: int = 0
    overall_score: int = 0


class RepoAnalysisItem(BaseModel):
    name: str = ""
    description: str = ""
    stars: int = 0
    forks: int = 0
    last_updated: str = ""
    size: int = 0
    tech_stack: list[str] = Field(default_factory=list)
    quality_score: int = 0
    readme_quality_score: int = 0
    complexity_score: int = 0
    domain: str = ""


class LeetCodeIntelligence(BaseModel):
    difficulty_weighted_score: int = 0
    topic_strengths: dict[str, int] = Field(default_factory=dict)
    strongest_topics: list[str] = Field(default_factory=list)
    weakest_topics: list[str] = Field(default_factory=list)
    problem_solving_depth: int = 0
    contest_participation_count: int = 0
    best_rank: int | None = None
    contest_rating_trend: str = "Stable"
    contest_strength: str = "Low"
    consistency_score: int = 0
    average_contest_rating: float | None = None


class CodeforcesIntelligence(BaseModel):
    contest_participation_trend: str = "Low"
    rating_growth_trend: str = "Stable"
    rating_growth_velocity: float = 0.0
    problem_tags_solved: dict[str, int] = Field(default_factory=dict)
    competitive_maturity_score: int = 0
    competitive_strength: int = 0
    average_contest_rating: float | None = None


class CodingProfileAnalysisResponse(BaseModel):
    github: GitHubProfileData
    leetcode: LeetCodeProfileData
    codeforces: CodeforcesProfileData
    repo_analysis: list[RepoAnalysisItem] = Field(default_factory=list)
    leetcode_intelligence: LeetCodeIntelligence = Field(default_factory=LeetCodeIntelligence)
    codeforces_intelligence: CodeforcesIntelligence = Field(default_factory=CodeforcesIntelligence)
    inferred_strengths: list[str] = Field(default_factory=list)
    coding_persona: str = "Beginner Learner"
    consistency_score: int = 0
    engineering_maturity_score: int = 0
    repository_quality_average: int = 0
    profile_confidence: int = 0
    recruiter_summary: str = ""
    hiring_recommendation: str = "Low Fit"
    scores: ScoreBlock
    coding_level: str
    errors: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
