from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core_engine.utils import clamp, round_score, safe_float


ROLE_WEIGHTS: dict[str, dict[str, int]] = {
    "backend": {
        "resume": 35,
        "github": 30,
        "leetcode": 20,
        "academics": 15,
    },
    "frontend": {
        "resume": 40,
        "github": 30,
        "leetcode": 10,
        "academics": 20,
    },
    "fullstack": {
        "resume": 35,
        "github": 30,
        "leetcode": 15,
        "academics": 20,
    },
    "sde_dsa": {
        "resume": 30,
        "github": 15,
        "leetcode": 40,
        "academics": 15,
    },
    "ml_engineer": {
        "resume": 35,
        "github": 25,
        "leetcode": 15,
        "academics": 25,
    },
    "generic": {
        "resume": 40,
        "github": 20,
        "leetcode": 20,
        "academics": 20,
    },
}

COMPONENT_MAX_SCORES: dict[str, float] = {
    "resume": 40.0,
    "github": 20.0,
    "leetcode": 20.0,
    "academics": 20.0,
}

COMPONENT_SCORE_KEYS: dict[str, str] = {
    "resume": "resume_score",
    "github": "github_score",
    "leetcode": "leetcode_score",
    "academics": "academic_score",
}


def get_role_weights(role: str | None) -> dict[str, int]:
    normalized_role = str(role or "").strip().lower()
    return dict(ROLE_WEIGHTS.get(normalized_role, ROLE_WEIGHTS["generic"]))


def _score_to_percent(score: Any, max_score: float) -> float:
    numeric_score = safe_float(score)
    if numeric_score is None or max_score <= 0:
        return 0.0
    return round_score(clamp((numeric_score / max_score) * 100.0))


def normalize_component_scores(component_scores: Mapping[str, Any] | None) -> dict[str, float]:
    scores = component_scores or {}
    return {
        component: _score_to_percent(scores.get(score_key), COMPONENT_MAX_SCORES[component])
        for component, score_key in COMPONENT_SCORE_KEYS.items()
    }


def calculate_weighted_final_score(
    component_scores: Mapping[str, Any] | None,
    role: str | None,
) -> dict[str, Any]:
    weights = get_role_weights(role)
    normalized_scores = normalize_component_scores(component_scores)

    total_weight = sum(weights.values())
    if total_weight <= 0:
        weights = get_role_weights("generic")
        total_weight = sum(weights.values())

    weighted_score = sum(
        normalized_scores[component] * weights.get(component, 0)
        for component in COMPONENT_MAX_SCORES
    ) / total_weight

    return {
        "weights_used": weights,
        "component_percentages": normalized_scores,
        "final_score": round_score(clamp(weighted_score)),
    }
