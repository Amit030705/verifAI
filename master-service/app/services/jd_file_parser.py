from __future__ import annotations

import io
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


ALLOWED_JD_EXTENSIONS = {".pdf", ".docx"}


def normalize_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    compact = [line for line in lines if line]
    return "\n".join(compact).strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text)
    return normalize_text("\n".join(pages))


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(io.BytesIO(file_bytes))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return normalize_text("\n".join(paragraphs))


def extract_jd_text_from_file(file_bytes: bytes, filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_JD_EXTENSIONS:
        raise ValueError("JD file must be PDF or DOCX.")

    if suffix == ".pdf":
        parsed = extract_text_from_pdf(file_bytes)
    else:
        parsed = extract_text_from_docx(file_bytes)

    if len(parsed) < 20:
        raise ValueError("Could not extract enough JD content from file (minimum 20 characters required).")
    return parsed

