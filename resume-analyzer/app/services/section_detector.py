from __future__ import annotations

import re

CANONICAL_SECTIONS = ("education", "experience", "projects", "skills", "certifications")

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "education": (
        "education",
        "academic",
        "academics",
        "academic background",
        "education background",
        "qualification",
        "qualifications",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "internship",
        "internships",
    ),
    "projects": (
        "projects",
        "project",
        "project experience",
        "academic projects",
    ),
    "skills": (
        "skills",
        "technical skills",
        "tech stack",
        "core competencies",
    ),
    "certifications": (
        "certifications",
        "certification",
        "certificates",
        "licenses",
        "achievements",
    ),
}

HEADING_SANITIZE_RE = re.compile(r"[^a-z0-9\s]")
MULTISPACE_RE = re.compile(r"\s+")


def normalize_heading(value: str) -> str:
    lowered = value.lower().strip()
    lowered = lowered.rstrip(":|-")
    lowered = HEADING_SANITIZE_RE.sub(" ", lowered)
    return MULTISPACE_RE.sub(" ", lowered).strip()


class SectionDetector:
    def __init__(self) -> None:
        self._heading_lookup: dict[str, str] = {}
        for section, aliases in SECTION_ALIASES.items():
            for alias in aliases:
                self._heading_lookup[normalize_heading(alias)] = section

    def detect_heading(self, line: str) -> str | None:
        normalized = normalize_heading(line)
        if not normalized:
            return None
        return self._heading_lookup.get(normalized)
