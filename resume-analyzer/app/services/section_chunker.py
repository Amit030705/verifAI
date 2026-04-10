from __future__ import annotations

from app.services.section_detector import CANONICAL_SECTIONS, SectionDetector
from app.utils.text import clean_line


class SectionChunker:
    def __init__(self, detector: SectionDetector) -> None:
        self.detector = detector

    def chunk(self, text: str) -> dict[str, str]:
        section_lines: dict[str, list[str]] = {name: [] for name in CANONICAL_SECTIONS}
        current_section: str | None = None

        for raw_line in text.splitlines():
            line = clean_line(raw_line)
            if not line:
                continue

            detected = self.detector.detect_heading(line)
            if detected:
                current_section = detected
                continue

            if current_section:
                section_lines[current_section].append(line)

        return {name: "\n".join(lines) for name, lines in section_lines.items()}
