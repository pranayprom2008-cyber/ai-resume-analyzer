"""
Unit and Integration Test Suite for AI Resume Analyzer & ATS Engine
Executes automated checks across Parser, SkillExtractor, ATSScorer, and FastAPI Endpoints.
"""

import os
import sys
import unittest

# Add backend directory to system path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from parser import ResumeParser
from skill_extractor import SkillExtractor
from ats_scorer import ATSScorer
from fastapi.testclient import TestClient
from main import app


class TestResumeParser(unittest.TestCase):
    """Verifies text extraction, regex contact detection, and sectioning."""

    def setUp(self):
        self.sample_text = """
Jane Doe
jane.doe@university.edu | +1 (555) 019-2834 | github.com/janedoe | linkedin.com/in/janedoe

EDUCATION
Bachelor of Science in Computer Science, 2025

TECHNICAL SKILLS
Languages: Python, C++, SQL
Frameworks: PyTorch, React, FastAPI

PROJECTS
Autonomous Drone Navigation:
- Developed path-planning algorithm using Python and OpenCV.
- Improved tracking accuracy by 28% and reduced obstacle collision.

EXPERIENCE
AI Research Intern (Summer 2024):
- Engineered data pipeline processing 50,000 images per hour.
"""

    def test_contact_info_extraction(self):
        contacts = ResumeParser.extract_contact_info(self.sample_text)
        self.assertEqual(contacts["email"], "jane.doe@university.edu")
        self.assertIn("janedoe", contacts["github"])
        self.assertIn("janedoe", contacts["linkedin"])

    def test_section_segmentation(self):
        parsed = ResumeParser.parse(self.sample_text, is_pdf=False)
        self.assertIn("education", parsed["sections"])
        self.assertIn("skills", parsed["sections"])
        self.assertIn("projects", parsed["sections"])
        self.assertIn("experience", parsed["sections"])
        self.assertGreater(parsed["word_count"], 40)

    def test_pdf_parsing_from_disk(self):
        pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_resumes", "sample_aiml_resume.pdf"))
        if os.path.exists(pdf_path):
            parsed = ResumeParser.parse(pdf_path, is_pdf=True)
            self.assertGreater(len(parsed["cleaned_text"]), 100)
            self.assertEqual(parsed["contact_info"]["email"], "pranayprom2008@gmail.com")


class TestSkillExtractor(unittest.TestCase):
    """Verifies skill taxonomy detection, multi-word matching, and alias resolution."""

    def test_multi_word_skill_extraction(self):
        text = "Experienced in Natural Language Processing, Machine Learning, and Computer Vision."
        result = SkillExtractor.extract_skills(text)
        self.assertIn("Natural Language Processing", result["all_skills"])
        self.assertIn("Machine Learning", result["all_skills"])
        self.assertIn("Computer Vision", result["all_skills"])

    def test_alias_normalization(self):
        text = "Built models using sklearn and stored data in postgres. Orchestrated with k8s."
        result = SkillExtractor.extract_skills(text)
        self.assertIn("Scikit-Learn", result["all_skills"])
        self.assertIn("PostgreSQL", result["all_skills"])
        self.assertIn("Kubernetes", result["all_skills"])

    def test_language_boundary_cases(self):
        text = "Proficient in C, C++, and Python programming."
        result = SkillExtractor.extract_skills(text)
        self.assertIn("C", result["all_skills"])
        self.assertIn("C++", result["all_skills"])
        self.assertIn("Python", result["all_skills"])


class TestATSScorer(unittest.TestCase):
    """Verifies mathematical scoring bounds, semantic similarity, and recommendations."""

    def setUp(self):
        self.resume = """
John Smith
john.smith@test.com | 9876543210
EDUCATION: B.Tech in Computer Science
TECHNICAL SKILLS: Python, PyTorch, Scikit-Learn, OpenCV, FastAPI, Docker, Git
PROJECTS:
- Engineered an end-to-end computer vision pipeline improving FPS by 40%.
- Deployed FastAPI backend handling 2000 requests per minute.
"""
        self.jd = """
Looking for an AI/ML Engineer with Python, PyTorch, Scikit-Learn, TensorFlow, and Docker skills.
Candidate must understand REST APIs and computer vision concepts.
"""

    def test_scoring_pipeline(self):
        report = ATSScorer.score_resume(self.resume, self.jd)
        self.assertGreaterEqual(report["overall_score"], 0.0)
        self.assertLessEqual(report["overall_score"], 100.0)
        self.assertIn("PyTorch", report["skills"]["matched"])
        self.assertIn("TensorFlow", report["skills"]["missing"])
        self.assertGreater(len(report["recommendations"]), 0)


class TestFastAPIIntegration(unittest.TestCase):
    """Verifies FastAPI REST endpoints and client responses."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_presets_endpoint(self):
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        self.assertIn("aiml_intern", response.json())

    def test_analyze_endpoint(self):
        payload = {
            "job_description": "Seeking Python and FastAPI developer with knowledge of Docker.",
            "resume_text": "Alex Hunter. Experienced in Python and FastAPI. Email: alex@test.com | Phone: 1234567890."
        }
        response = self.client.post("/api/analyze", data=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("overall_score", data)
        self.assertIn("skills", data)


if __name__ == "__main__":
    unittest.main()
