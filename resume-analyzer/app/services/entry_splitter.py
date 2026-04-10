from __future__ import annotations

import re

from app.utils.text import clean_line

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
TECH_STACK_HINT_RE = re.compile(r"\b(tech stack|technologies|stack|built with|tools)\b", re.IGNORECASE)


def _lines(section_text: str) -> list[str]:
    return [clean_line(line) for line in section_text.splitlines() if clean_line(line)]


def _has_date(line: str) -> bool:
    return bool(YEAR_RANGE_RE.search(line) or MONTH_RANGE_RE.search(line))


def split_education_entries(section_text: str) -> list[list[str]]:
    lines = _lines(section_text)
    entries: list[list[str]] = []
    current: list[str] = []
    current_has_institution = False
    current_has_degree = False
    current_has_date = False

    for line in lines:
        has_institution = bool(EDU_INSTITUTION_RE.search(line))
        has_degree = bool(DEGREE_RE.search(line))
        has_date = _has_date(line)

        should_split = bool(
            current
            and (
                (has_date and current_has_date)
                or (has_institution and (current_has_institution or current_has_degree))
                or (has_degree and current_has_degree and current_has_institution)
            )
        )
        if should_split:
            entries.append(current)
            current = []
            current_has_institution = False
            current_has_degree = False
            current_has_date = False

        current.append(line)
        current_has_institution = current_has_institution or has_institution
        current_has_degree = current_has_degree or has_degree
        current_has_date = current_has_date or has_date

    if current:
        entries.append(current)
    return entries


def split_experience_entries(section_text: str) -> list[list[str]]:
    lines = _lines(section_text)
    entries: list[list[str]] = []
    current: list[str] = []
    current_has_company = False
    current_has_date = False

    for line in lines:
        is_bullet = line.startswith(("-", "*", "•"))
        has_company = bool(COMPANY_RE.search(line))
        has_role = bool(ROLE_RE.search(line))
        has_date = _has_date(line)

        should_split = bool(
            current
            and not is_bullet
            and (
                (has_company and current_has_company)
                or (has_date and current_has_date)
                or (has_role and current_has_company and any(s.startswith(("-", "*", "•")) for s in current))
            )
        )
        if should_split:
            entries.append(current)
            current = []
            current_has_company = False
            current_has_date = False

        current.append(line)
        current_has_company = current_has_company or has_company
        current_has_date = current_has_date or has_date

    if current:
        entries.append(current)
    return entries


def split_project_entries(section_text: str) -> list[list[str]]:
    lines = _lines(section_text)
    entries: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        looks_like_title = bool(
            (":" in line or "|" in line or " - " in line)
            and len(line.split()) <= 14
            and not line.startswith(("-", "*", "•"))
        )
        if looks_like_title and current:
            entries.append(current)
            current = []
        elif TECH_STACK_HINT_RE.search(line) and current and any(TECH_STACK_HINT_RE.search(s) for s in current):
            entries.append(current)
            current = []

        current.append(line)

    if current:
        entries.append(current)
    return entries
