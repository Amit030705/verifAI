from __future__ import annotations

import unittest

from app.models.response_model import JDAnalyzeResponse
from app.services.jd_analyzer_service import _apply_text_fallbacks


class JDConstraintFallbackTests(unittest.TestCase):
    def test_extracts_target_cgpa_backlog_and_placement_from_text(self) -> None:
        jd_text = "I need 5 students with no backlogs and 6 cgpa. include placed students if eligible."
        payload = JDAnalyzeResponse()

        normalized = _apply_text_fallbacks(jd_text=jd_text, payload=payload)

        self.assertEqual(normalized.target_student_count, 5)
        self.assertEqual(normalized.min_cgpa, 6.0)
        self.assertTrue(normalized.exclude_active_backlogs)
        self.assertEqual(normalized.placement_filter, "placed_or_unplaced")

    def test_unplaced_only_phrase_takes_unplaced_filter(self) -> None:
        jd_text = "Find 10 candidates, unplaced only, no active backlog, minimum 7 cgpa."
        payload = JDAnalyzeResponse()

        normalized = _apply_text_fallbacks(jd_text=jd_text, payload=payload)

        self.assertEqual(normalized.target_student_count, 10)
        self.assertEqual(normalized.min_cgpa, 7.0)
        self.assertTrue(normalized.exclude_active_backlogs)
        self.assertEqual(normalized.placement_filter, "unplaced_only")


if __name__ == "__main__":
    unittest.main()
