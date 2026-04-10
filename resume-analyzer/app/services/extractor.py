from __future__ import annotations

import re
from dataclasses import dataclass

import spacy
from spacy.language import Language

from app.services.entity_extractor import EntityExtractor
from app.services.entry_splitter import (
    split_education_entries,
    split_experience_entries,
    split_project_entries,
)
from app.services.section_chunker import SectionChunker
from app.services.section_detector import SectionDetector
from app.services.skill_matcher import SkillMatcher
from app.services.summarizer import generate_summary
from app.utils.text import clean_line, dedupe_preserve_order, normalize_inline_text

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,5}[\s-]?\d{4,6}")
GPA_RE = re.compile(r"\b(?:cgpa|gpa)\s*[:\-]?\s*(\d(?:\.\d{1,2})?\s*(?:/\s*\d{1,2}(?:\.\d{1,2})?)?)\b", re.IGNORECASE)

def _load_best_spacy_model() -> Language:
    candidates = [
        "en_core_web_trf",
        "en_core_web_lg",
        "en_core_web_md",
        "en_core_web_sm",
    ]
    for model in candidates:
        try:
            return spacy.load(model)
        except OSError:
            continue
    return spacy.blank("en")


@dataclass
class ResumeExtractionResult:
    data: dict
    completeness_score: float
    section_map: dict[str, str]


class ResumeExtractor:
    def __init__(self) -> None:
        self.nlp = _load_best_spacy_model()
        self.section_detector = SectionDetector()
        self.section_chunker = SectionChunker(self.section_detector)
        self.entity_extractor = EntityExtractor(self.nlp)
        self.skill_matcher = SkillMatcher(self.nlp)

    def _extract_name(self, text: str) -> str:
        lines = [clean_line(line) for line in text.splitlines() if clean_line(line)]
        top_lines = lines[:8]

        for line in top_lines:
            if EMAIL_RE.search(line) or PHONE_RE.search(line):
                continue
            if len(line.split()) in {2, 3, 4} and all(token.replace(".", "").isalpha() for token in line.split()):
                return line.title()

        doc = self.nlp("\n".join(top_lines))
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return normalize_inline_text(ent.text.title())

        return ""

    def _extract_phone(self, text: str) -> str:
        for match in PHONE_RE.findall(text):
            digits = re.sub(r"\D", "", match)
            if 10 <= len(digits) <= 15:
                return normalize_inline_text(match)
        return ""

    def _extract_simple_list(self, section_text: str) -> list[str]:
        if not section_text.strip():
            return []
        lines = [clean_line(line) for line in section_text.splitlines()]
        lines = [line for line in lines if line and len(line) > 2]
        return dedupe_preserve_order(lines)

    def _extract_gpa(self, text: str) -> str:
        match = GPA_RE.search(text)
        return match.group(1).replace(" ", "") if match else ""

    def _extract_email(self, text: str) -> str:
        match = EMAIL_RE.search(text)
        return match.group(0) if match else ""

    def _calculate_completeness(self, data: dict) -> float:
        critical_fields = [
            bool(data.get("name")),
            bool(data.get("email")),
            bool(data.get("phone")),
            bool(data.get("education")),
            bool(data.get("skills")),
            bool(data.get("experience")),
        ]
        return round(sum(critical_fields) / len(critical_fields), 2)

    def extract(self, text: str) -> ResumeExtractionResult:
        section_map = self.section_chunker.chunk(text)

        skills = self.skill_matcher.extract(text, section_map.get("skills", ""))
        education_entries = split_education_entries(section_map.get("education", ""))
        experience_entries = split_experience_entries(section_map.get("experience", ""))
        project_entries = split_project_entries(section_map.get("projects", ""))

        education = self.entity_extractor.extract_education(education_entries)
        experience = self.entity_extractor.extract_experience(experience_entries)
        projects = self.entity_extractor.extract_projects(project_entries)
        certifications = self._extract_simple_list(section_map.get("certifications", ""))

        education_summary = [
            " ".join(part for part in [item.get("degree", ""), item.get("institution", "")] if part).strip()
            for item in education
            if any(item.values())
        ]
        experience_summary = [
            " at ".join(part for part in [item.get("role", ""), item.get("company", "")] if part).strip()
            for item in experience
            if item.get("role") or item.get("company")
        ]
        project_summary = [item.get("title", "") for item in projects if item.get("title")]

        data = {
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "education": education,
            "cgpa": self._extract_gpa(text),
            "skills": skills,
            "projects": projects,
            "experience": experience,
            "certifications": certifications,
            "summary": "",
        }

        data["summary"] = generate_summary(
            education=education_summary,
            skills=data["skills"],
            experience=experience_summary,
            projects=project_summary,
        )

        completeness_score = self._calculate_completeness(data)

        return ResumeExtractionResult(
            data=data,
            completeness_score=completeness_score,
            section_map=section_map,
        )
