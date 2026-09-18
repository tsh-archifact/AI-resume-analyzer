import unittest
from unittest.mock import patch

from schemas.agent import CritiqueCategory, CritiqueSeverity
from services.agents.fact_checker_agent import (
    convert_fact_check_to_critiques,
    verify_resume_truthfulness,
)
from services.agents.refinement_loop import run_self_refining_loop


SOURCE_RESUME = """
Jane Doe
Backend Developer

Skills: Python, FastAPI, SQLite, Git

Experience:
Software Engineer at Acme Corp
- Developed REST APIs in Python and FastAPI.
- Maintained internal SQLite databases.
"""

GROUNDED_DRAFT = """
# Summary
Results-oriented Backend Developer with experience in Python, FastAPI, and SQLite.

# Skills
Python, FastAPI, SQLite, Git

# Experience
Software Engineer | Acme Corp
- Engineered robust REST APIs in Python and FastAPI, increasing test coverage to 95%.
- Maintained internal SQLite databases and managed version control with Git.
"""

HALLUCINATED_DRAFT = """
# Summary
Cloud Architect with deep expertise in Kubernetes, AWS, and Solidity.

# Skills
Python, FastAPI, Kubernetes, AWS, Solidity, Blockchain

# Experience
Senior Architect | QuantumTech Inc
- Architected Kubernetes microservices on AWS cloud infrastructure.
- Developed smart contracts using Solidity.
"""


class TestFactChecker(unittest.TestCase):
    def test_grounded_draft_is_clean(self):
        result = verify_resume_truthfulness(
            draft_text=GROUNDED_DRAFT,
            source_resume=SOURCE_RESUME,
        )

        self.assertTrue(result.is_clean)
        self.assertEqual(len(result.hallucinated_skills), 0)
        self.assertEqual(result.grounding_score, 100.0)

    def test_hallucinated_draft_detected(self):
        result = verify_resume_truthfulness(
            draft_text=HALLUCINATED_DRAFT,
            source_resume=SOURCE_RESUME,
        )

        self.assertFalse(result.is_clean)
        self.assertLess(result.grounding_score, 100.0)
        # Should flag ungrounded skills
        self.assertTrue(any(s in result.hallucinated_skills for s in ["Kubernetes", "AWS", "Solidity", "Blockchain"]))
        self.assertGreater(len(result.warnings), 0)

        # Critiques generated
        critiques = convert_fact_check_to_critiques(result)
        self.assertGreater(len(critiques), 0)
        self.assertEqual(critiques[0].severity, CritiqueSeverity.HIGH)
        self.assertEqual(critiques[0].category, CritiqueCategory.RELEVANCE)

    @patch("services.agents.refinement_loop.refine_draft")
    def test_refinement_loop_catches_hallucinations(self, mock_refine):
        # When initial draft has hallucinations, the loop passes fact-check critique to refiner
        mock_refine.return_value = GROUNDED_DRAFT

        loop_result = run_self_refining_loop(
            resume_text=SOURCE_RESUME,
            jd_text="Job: Python Backend Engineer with FastAPI",
            target_score=70.0,
            max_iterations=2,
            initial_draft=HALLUCINATED_DRAFT,
            enforce_fact_check=True,
        )

        # Iteration 1 had hallucination, iteration 2 was cleaned up
        self.assertEqual(loop_result.iterations_count, 2)
        self.assertFalse(loop_result.iteration_history[0].fact_check.is_clean)
        self.assertTrue(loop_result.final_fact_check.is_clean)


if __name__ == "__main__":
    unittest.main()
