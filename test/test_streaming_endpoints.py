import pytest
from services.agents.refinement_loop import run_self_refining_loop

MOCK_RESUME = """
Jane Doe
Software Engineer
Skills: Python, FastAPI, Docker, SQL
Experience:
Senior Developer at Acme Corp (2021-Present)
• Designed and shipped REST APIs using FastAPI and PostgreSQL.
• Automated deployments using Docker.
"""

MOCK_JD = """
Job Title: Backend Engineer
Requirements:
• 3+ years experience with Python and FastAPI
• Experience with Docker and relational databases
"""

def test_refinement_loop_progress_callback():
    events: list[dict] = []

    def mock_callback(event: dict):
        events.append(event)

    result = run_self_refining_loop(
        resume_text=MOCK_RESUME,
        jd_text=MOCK_JD,
        target_score=60.0,
        max_iterations=1,
        enforce_fact_check=False,
        progress_callback=mock_callback,
    )

    assert result is not None
    assert len(events) >= 3
    assert any("Perception" in e.get("agent", "") or "Drafter" in e.get("agent", "") for e in events)
    assert all("thought" in e for e in events)
    assert all("progress" in e for e in events)
