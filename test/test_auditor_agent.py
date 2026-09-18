import unittest
from schemas.agent import CritiqueCategory, CritiqueSeverity
from services.agents.auditor_agent import audit_resume_draft


SAMPLE_JD = """
Job Title: Senior Backend Engineer
Required Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS
Responsibilities:
- Architect high-throughput microservices handling 50k+ requests per second.
- Optimize database performance and implement caching layers.
- Deploy applications using Docker containers and Kubernetes clusters.
"""

WEAK_DRAFT = """
Summary:
Software developer looking for a good backend role.

Experience:
Company ABC
- Worked on python backend tasks.
- Responsible for helping team with database.
- Did some bugs fixing.

Education:
B.S. in Computer Science
"""

STRONG_DRAFT = """
# Summary
Results-driven Senior Backend Engineer with 6+ years of experience in Python, FastAPI, and cloud architecture.

# Skills
Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS, CI/CD

# Experience
Senior Software Engineer | CloudTech
- Architected resilient microservices in Python and FastAPI, reducing API latency by 42% for 100,000+ daily active users.
- Optimized PostgreSQL queries and deployed Redis caching, slashing database load by 35% and saving $24k annually in server costs.
- Deployed 15+ containerized services to Kubernetes clusters on AWS with 99.99% service uptime.
- Automated CI/CD deployment pipelines, cutting release cycle time by 4x.

# Education
Bachelor of Science in Computer Science | State University
"""


class TestAuditorAgent(unittest.TestCase):
    def test_auditor_weak_draft_identifies_gaps(self):
        result = audit_resume_draft(
            WEAK_DRAFT,
            SAMPLE_JD,
            target_skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL", "Redis", "AWS"],
        )

        self.assertLess(result.overall_score, 60.0)
        self.assertLess(result.metric_score, 50.0)
        # Should identify missing skills
        self.assertTrue("FastAPI" in result.missing_keywords or "Kubernetes" in result.missing_keywords)
        # Should contain critiques for missing keywords and metrics
        categories = [c.category for c in result.critiques]
        self.assertIn(CritiqueCategory.KEYWORDS, categories)
        self.assertIn(CritiqueCategory.METRICS, categories)

    def test_auditor_strong_draft_produces_high_score(self):
        result = audit_resume_draft(
            STRONG_DRAFT,
            SAMPLE_JD,
            target_skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL", "Redis", "AWS"],
        )

        self.assertGreaterEqual(result.overall_score, 80.0)
        self.assertGreaterEqual(result.keyword_score, 85.0)
        self.assertGreaterEqual(result.metric_score, 80.0)
        self.assertEqual(len(result.missing_keywords), 0)
        self.assertGreater(len(result.strengths), 0)

    def test_auditor_extracts_skills_from_jd_when_not_provided(self):
        result = audit_resume_draft(STRONG_DRAFT, SAMPLE_JD)
        self.assertGreater(result.overall_score, 60.0)
        self.assertIsInstance(result.matched_keywords, list)


if __name__ == "__main__":
    unittest.main()
