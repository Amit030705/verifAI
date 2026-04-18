from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from core_engine.utils import as_dict


PARSED_JD_FIELDS = (
    "job_title",
    "required_skills",
    "preferred_skills",
    "tools_and_technologies",
    "domain",
)

RAW_JD_FIELDS = (
    "jd_text",
    "raw_jd",
    "raw_text",
    "description",
    "job_description",
    "responsibilities",
    "requirements",
)

ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "backend": (
        "node",
        "express",
        "api",
        "backend",
        "django",
        "flask",
        "fastapi",
        "sql",
        "mongodb",
        "redis",
        "microservices",
    ),
    "frontend": (
        "react",
        "next",
        "angular",
        "vue",
        "css",
        "tailwind",
        "ui",
        "ux",
        "frontend",
    ),
    "fullstack": (
        "full stack",
        "frontend + backend",
        "react + node",
        "mern",
        "mean",
    ),
    "sde_dsa": (
        "algorithms",
        "data structures",
        "coding rounds",
        "problem solving",
        "competitive programming",
    ),
    "ml_engineer": (
        "python",
        "machine learning",
        "tensorflow",
        "pytorch",
        "ai",
        "nlp",
        "deep learning",
    ),
}


def _iter_text_values(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, Mapping):
        for nested_value in value.values():
            yield from _iter_text_values(nested_value)
        return
    if isinstance(value, Iterable) and not isinstance(value, bytes):
        for nested_value in value:
            yield from _iter_text_values(nested_value)
        return
    yield str(value)


def _collect_field_text(data: Mapping[str, Any], fields: tuple[str, ...]) -> str:
    return " ".join(
        text
        for field in fields
        for text in _iter_text_values(data.get(field))
    )


def _collect_jd_texts(jd: Mapping[str, Any] | str | None) -> tuple[str, str]:
    if jd is None:
        return "", ""
    if isinstance(jd, str):
        return jd, ""

    data = as_dict(jd)
    return _collect_field_text(data, PARSED_JD_FIELDS), _collect_field_text(data, RAW_JD_FIELDS)


def _normalize_text(text: str) -> str:
    lowered = text.lower().replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9+#.\s/-]", " ", lowered)
    lowered = lowered.replace("/", " ").replace("-", " ")
    return re.sub(r"\s+", " ", lowered).strip()


def _contains_keyword(text: str, keyword: str) -> bool:
    if "+" in keyword:
        return all(_contains_keyword(text, part.strip()) for part in keyword.split("+"))

    keyword = keyword.strip().lower()
    if keyword == "node":
        return bool(re.search(r"\bnode(?:\.js|js)?\b", text))
    if keyword == "next":
        return bool(re.search(r"\bnext(?:\.js|js)?\b", text))
    if keyword == "full stack":
        return bool(re.search(r"\bfull\s*-?\s*stack\b|\bfullstack\b", text))
    if keyword == "api":
        return bool(re.search(r"\bapis?\b", text))
    if keyword == "backend":
        return bool(re.search(r"\bback\s*end\b|\bbackend\b", text))
    if keyword == "frontend":
        return bool(re.search(r"\bfront\s*end\b|\bfrontend\b", text))

    pattern = r"\b" + r"\s+".join(re.escape(part) for part in keyword.split()) + r"\b"
    return bool(re.search(pattern, text))


def _score_roles_from_text(text: str) -> dict[str, int]:
    text = _normalize_text(text)
    if not text:
        return {role: 0 for role in ROLE_KEYWORDS}

    return {
        role: sum(1 for keyword in keywords if _contains_keyword(text, keyword))
        for role, keywords in ROLE_KEYWORDS.items()
    }


def score_roles_from_jd(jd: Mapping[str, Any] | str | None) -> dict[str, int]:
    parsed_text, raw_text = _collect_jd_texts(jd)
    parsed_scores = _score_roles_from_text(parsed_text)
    if any(parsed_scores.values()):
        return parsed_scores
    return _score_roles_from_text(raw_text)


def detect_role_from_jd(jd: Mapping[str, Any] | str | None) -> str:
    role_scores = score_roles_from_jd(jd)
    matched_roles = {role: score for role, score in role_scores.items() if score > 0}
    if not matched_roles:
        return "generic"

    if matched_roles.get("fullstack", 0) > 0:
        return "fullstack"

    highest_score = max(matched_roles.values())
    highest_roles = sorted(role for role, score in matched_roles.items() if score == highest_score)
    if len(highest_roles) == 1:
        return highest_roles[0]

    return "fullstack"
