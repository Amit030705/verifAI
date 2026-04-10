from __future__ import annotations

import unittest

from app.services.extractor import ResumeExtractor


SAMPLE_RESUME = """
Ansh Bhatt
ansh@example.com
+91 9999911111

Education
Abdul Kalam Technical University
B.Tech in Computer Science and Engineering
2023-2027
The Union Academy Sr. Sec. School
Higher Secondary Education
2021-2023

Professional Experience
House of Couton Pvt. Ltd.
AI & Web Development Intern
Jan 2025 - Dec 2025
- Integrated AI modules into operational workflows.
- Built backend services and optimized API latency.

VerifAI Labs
Backend Developer Intern
Jan 2024 - Jun 2024
- Developed REST APIs for recruitment analytics.

Projects
YuktiERP | Flask, Python, PostgreSQL
- ERP workflow management platform for institutes.
- Implemented role-based modules for admin and faculty.

Smart Interview Assistant | FastAPI, React
- Built interview question generation and scoring API.

Skills
Python
FastAPI
React
PostgreSQL

Certifications
AWS Cloud Practitioner
"""


class SegmentationPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.extractor = ResumeExtractor()

    def test_education_records_are_split(self) -> None:
        result = self.extractor.extract(SAMPLE_RESUME).data
        education = result["education"]
        self.assertEqual(len(education), 2)
        self.assertIn("Abdul Kalam Technical University", education[0]["institution"])
        self.assertIn("B.Tech", education[0]["degree"])
        self.assertIn("The Union Academy", education[1]["institution"])

    def test_experience_records_are_split(self) -> None:
        result = self.extractor.extract(SAMPLE_RESUME).data
        experience = result["experience"]
        self.assertEqual(len(experience), 2)
        self.assertIn("House of Couton", experience[0]["company"])
        self.assertIn("Intern", experience[0]["role"])
        self.assertGreaterEqual(len(experience[0]["description"]), 1)
        self.assertIn("VerifAI Labs", experience[1]["company"])

    def test_projects_are_split(self) -> None:
        result = self.extractor.extract(SAMPLE_RESUME).data
        projects = result["projects"]
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]["title"], "YuktiERP")
        self.assertGreaterEqual(len(projects[0]["tech_stack"]), 1)
        self.assertEqual(projects[1]["title"], "Smart Interview Assistant")


if __name__ == "__main__":
    unittest.main()
