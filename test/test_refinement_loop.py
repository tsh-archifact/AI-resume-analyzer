import unittest
from unittest.mock import patch

from schemas.agent import (
    ATSCritiqueItem,
    CritiqueCategory,
    CritiqueSeverity,
)
from services.agents.drafter_agent import build_refinement_prompt
from services.agents.refinement_loop import run_self_refining_loop


SAMPLE_RESUME = """
John Doe
Senior Backend Engineer

Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS

Experience:
Tech Corp
- Developed services in Python, FastAPI, and PostgreSQL.
- Deployed containers with Docker and Kubernetes on AWS.
- Configured Redis caching.
"""

SAMPLE_JD = """
Job Title: Senior Backend Engineer
Required Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS
Responsibilities:
- Build high-scale services in FastAPI and Python.
- Deploy with Docker and Kubernetes.
"""

STRONG_INITIAL_DRAFT = """
# Summary
Senior Backend Engineer with 6+ years specializing in Python, FastAPI, and AWS.

# Skills
Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS

# Experience
Lead Developer | Tech Corp
- Architected high-performance FastAPI microservices handling 25,000+ daily requests, improving throughput by 45%.
- Deployed Docker containers across Kubernetes clusters on AWS with 99.99% reliability.
- Optimized PostgreSQL queries and Redis caching, cutting latency by 50% and saving $15k yearly.

# Education
B.S. in Computer Science
"""

WEAK_INITIAL_DRAFT = """
John Doe
- Worked on python backend tasks.
- Responsible for helping team with database.
"""

IMPROVED_REFINED_DRAFT = """
# Summary
Experienced Software Engineer specializing in Python, FastAPI, and PostgreSQL.

# Skills
Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS

# Experience
Software Engineer | Tech Corp
- Engineered FastAPI services handling 10,000+ requests daily, cutting response latency by 35%.
- Automated deployment of Docker microservices on Kubernetes and AWS cloud infrastructure.
- Streamlined PostgreSQL database operations and integrated Redis cache, reducing query time by 40%.

# Education
B.S. in Computer Science
"""


class TestRefinementLoop(unittest.TestCase):
    def test_build_refinement_prompt_contains_critiques(self):
        critiques = [
            ATSCritiqueItem(
                category=CritiqueCategory.KEYWORDS,
                severity=CritiqueSeverity.HIGH,
                issue="Missing key skill: Kubernetes",
                suggestion="Add Kubernetes experience",
            ),
            ATSCritiqueItem(
                category=CritiqueCategory.METRICS,
                severity=CritiqueSeverity.MEDIUM,
                issue="Low metric density",
                suggestion="Quantify achievements",
            ),
        ]

        prompt = build_refinement_prompt(
            current_draft=WEAK_INITIAL_DRAFT,
            jd_text=SAMPLE_JD,
            source_resume=SAMPLE_RESUME,
            critiques=critiques,
        )

        self.assertIn("Missing key skill: Kubernetes", prompt)
        self.assertIn("Quantify achievements", prompt)
        self.assertIn("ORIGINAL RESUME", prompt)
        self.assertIn("TARGET JOB DESCRIPTION", prompt)

    def test_loop_exits_early_when_initial_draft_is_strong(self):
        result = run_self_refining_loop(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            target_score=75.0,
            max_iterations=3,
            initial_draft=STRONG_INITIAL_DRAFT,
        )

        self.assertEqual(result.iterations_count, 1)
        self.assertTrue(result.target_score_met)
        self.assertGreaterEqual(result.final_score, 75.0)
        self.assertEqual(len(result.iteration_history), 1)

    @patch("services.agents.refinement_loop.refine_draft")
    def test_loop_iterates_and_improves_weak_draft(self, mock_refine):
        # Mock refine_draft to return the improved draft on the second pass
        mock_refine.return_value = IMPROVED_REFINED_DRAFT

        result = run_self_refining_loop(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            target_score=80.0,
            max_iterations=3,
            initial_draft=WEAK_INITIAL_DRAFT,
        )

        self.assertEqual(result.iterations_count, 2)
        self.assertGreater(result.final_score, result.initial_score)
        self.assertGreater(result.score_improvement, 0.0)
        self.assertEqual(len(result.iteration_history), 2)
        mock_refine.assert_called_once()


if __name__ == "__main__":
    unittest.main()
