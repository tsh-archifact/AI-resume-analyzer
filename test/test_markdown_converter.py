import pytest
from services.markdown_converter_service import convert_cleaned_text_to_markdown
from services.text_extraction_service import clean_text


SAMPLE_RESUME = """
John Doe
Software Engineer | Python & Cloud Developer
Contact: john.doe@example.com | (555) 123-4567 | San Francisco, CA

Professional Summary:
Dynamic backend software engineer with 4+ years of experience designing scalable microservices.

Technical Skills:
Programming: Python, JavaScript, TypeScript, Go
Frameworks: FastAPI, Flask, React, Node.js
Databases: PostgreSQL, Redis, MongoDB
Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD, Git

Work Experience:
Senior Backend Engineer at TechCorp Inc. (2022 - Present)
• Architected event-driven microservices processing 15M+ daily requests using FastAPI and Kafka.
• Reduced PostgreSQL query latency by 45% through composite indexing and query refactoring.

Education:
B.S. in Computer Science - University of California, Berkeley (2016 - 2020)
• Graduated with Honors (GPA 3.8/4.0)

Certifications:
• AWS Certified Solutions Architect - Associate
"""

SAMPLE_JD = """
Job Title: Senior Backend Software Engineer
Company: CloudScale Technologies

About the Role:
We are looking for an experienced Senior Backend Engineer to architect, build, and scale
our distributed cloud platform and mission-critical microservices.

Key Responsibilities:
• Design and implement highly available RESTful APIs and microservices using Python and FastAPI.
• Optimize PostgreSQL database queries, connection pooling, and caching strategies using Redis.

Required Qualifications:
Backend Development: 4+ years of professional backend engineering experience with Python.
Frameworks: Deep experience with modern API frameworks such as FastAPI.
Databases: Strong proficiency in relational databases (PostgreSQL, MySQL).

Preferred Qualifications:
• Experience with Kubernetes orchestration, Helm charts, and Terraform.
"""


def test_resume_markdown_conversion():
    cleaned = clean_text(SAMPLE_RESUME)
    md = convert_cleaned_text_to_markdown(cleaned, document_title="John Doe - Resume")

    assert "# John Doe - Resume" in md
    assert "## Professional Summary" in md
    assert "## Technical Skills" in md
    assert "## Work Experience" in md
    assert "## Education" in md
    assert "## Certifications" in md
    assert "FastAPI" in md


def test_job_description_markdown_conversion():
    cleaned = clean_text(SAMPLE_JD)
    md = convert_cleaned_text_to_markdown(cleaned, document_title="CloudScale - Job Description")

    assert "# CloudScale - Job Description" in md
    assert "## About the Role" in md or "## Key Responsibilities" in md
    assert "## Required Qualifications" in md
    assert "## Preferred Qualifications" in md
    assert "PostgreSQL" in md


def test_empty_text_conversion():
    md = convert_cleaned_text_to_markdown("", document_title="Empty Doc")
    assert md == ""
