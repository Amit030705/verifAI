from __future__ import annotations

import re

from spacy.language import Language

from app.services.skill_matcher import SKILL_ONTOLOGY

YEAR_RANGE_RE = re.compile(r"\b(?:19|20)\d{2}\s*[-–]\s*(?:present|current|(?:19|20)\d{2})\b", re.IGNORECASE)
MONTH_RANGE_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}\s*[-–]\s*"
    r"(?:present|current|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4})\b",
    re.IGNORECASE,
)
EDU_INSTITUTION_RE = re.compile(r"\b(university|college|institute|school|academy)\b", re.IGNORECASE)
DEGREE_RE = re.compile(r"\b(b\.?\s?tech|b\.?\s?e|bachelor|master|m\.?\s?tech|mca|mba|bca|bsc|msc|ph\.?d)\b", re.IGNORECASE)
COMPANY_RE = re.compile(r"\b(pvt\.?\s*ltd|ltd|inc|llc|corp|company|technologies|solutions|labs|systems)\b", re.IGNORECASE)
ROLE_RE = re.compile(
    r"\b(intern|engineer|developer|manager|analyst|consultant|designer|architect|lead|specialist)\b",
    re.IGNORECASE,
)
BULLET_PREFIX_RE = re.compile(r"^[-*•]\s*")

KNOWN_TECH = {term.lower() for group in SKILL_ONTOLOGY.values() for term in group}


def _extract_duration(text: str) -> str:
    month_match = MONTH_RANGE_RE.search(text)
    if month_match:
        return month_match.group(0)
    year_match = YEAR_RANGE_RE.search(text)
    if year_match:
        return year_match.group(0)
    return ""


def _cleanup_description(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        normalized = BULLET_PREFIX_RE.sub("", line).strip()
        if normalized:
            cleaned.append(normalized)
    return cleaned


class EntityExtractor:
    def __init__(self, nlp: Language) -> None:
        self.nlp = nlp

    def _extract_org_with_spacy(self, text: str) -> str:
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                return ent.text.strip()
        return ""

    def extract_education(self, entries: list[list[str]]) -> list[dict[str, str]]:
        structured: list[dict[str, str]] = []
        for lines in entries:
            blob = "\n".join(lines)
            duration = _extract_duration(blob)

            institution = ""
            degree = ""
            for line in lines:
                if not institution and EDU_INSTITUTION_RE.search(line):
                    institution = line
                if not degree and DEGREE_RE.search(line):
                    degree = line

            if not institution:
                institution = self._extract_org_with_spacy(blob)
            if not institution and lines:
                institution = lines[0]
            if not degree:
                for line in lines:
                    if line != institution and line != duration:
                        degree = line
                        break

            structured.append(
                {
                    "institution": institution,
                    "duration": duration,
                    "degree": degree,
                }
            )
        return structured

    def extract_experience(self, entries: list[list[str]]) -> list[dict[str, object]]:
        structured: list[dict[str, object]] = []
        for lines in entries:
            blob = "\n".join(lines)
            duration = _extract_duration(blob)
            company = ""
            role = ""

            for line in lines:
                if not company and COMPANY_RE.search(line):
                    company = line
                if not role and ROLE_RE.search(line):
                    role = line

            if not company:
                company = self._extract_org_with_spacy(blob)
            if not company and lines:
                company = lines[0]

            if not role:
                for line in lines:
                    if line != company and line != duration:
                        role = line
                        break

            description_source = [line for line in lines if line not in {company, role, duration}]
            structured.append(
                {
                    "company": company,
                    "duration": duration,
                    "role": role,
                    "description": _cleanup_description(description_source),
                }
            )
        return structured

    def extract_projects(self, entries: list[list[str]]) -> list[dict[str, object]]:
        structured: list[dict[str, object]] = []
        for lines in entries:
            if not lines:
                continue

            head = lines[0]
            title = re.split(r"[:|\-]\s*", head, maxsplit=1)[0].strip() or head

            tech_stack: list[str] = []
            for line in lines:
                for token in re.split(r"[,|/()]+", line):
                    candidate = token.strip().lower()
                    if candidate in KNOWN_TECH:
                        tech_stack.append(candidate)

            description = _cleanup_description(lines[1:] if len(lines) > 1 else [])
            structured.append(
                {
                    "title": title,
                    "tech_stack": sorted({item.title() for item in tech_stack}),
                    "description": description,
                }
            )
        return structured
