import sys
from pathlib import Path
from services.markdown_converter_service import convert_cleaned_text_to_markdown, convert_file_to_markdown
from services.text_extraction_service import clean_text

SAMPLE_RESUME = """
John Doe
Software Engineer | Python & Cloud Developer
Contact: john.doe@example.com | (555) 123-4567 | San Francisco, CA

Professional Summary:
Dynamic backend software engineer with 4+ years of experience designing scalable microservices,
optimizing database performance, and building automated data pipelines with Python and Docker.

Technical Skills:
Programming: Python, JavaScript, TypeScript, Go
Frameworks: FastAPI, Flask, React, Node.js
Databases: PostgreSQL, Redis, MongoDB
Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD, Git

Work Experience:
Senior Backend Engineer at TechCorp Inc. (2022 - Present)
• Architected event-driven microservices processing 15M+ daily requests using FastAPI and Kafka.
• Reduced PostgreSQL query latency by 45% through composite indexing and query refactoring.
• Automated deployment pipelines using Docker and GitHub Actions, cutting release cycles from 2 days to 30 mins.
• Mentored 4 junior developers in REST API design and automated testing practices.

Software Developer at InnovateLabs (2020 - 2022)
• Developed full-stack dashboard applications serving 50,000+ monthly active users using Python and React.
• Integrated Stripe payment gateways and third-party REST APIs with 99.9% uptime.
• Implemented Redis caching layer reducing database read operations by 60%.

Projects:
AI Resume Analyzer & ATS Copilot
• Built multi-agent reflection pipeline using FastAPI, spaCy, and OpenAI.
• Evaluated candidate ATS match scores with fuzzy token set ratio scoring.

Education:
B.S. in Computer Science - University of California, Berkeley (2016 - 2020)
• Graduated with Honors (GPA 3.8/4.0)

Certifications:
• AWS Certified Solutions Architect - Associate
"""

SAMPLE_JD = """
Job Title: Senior Backend Software Engineer
Company: CloudScale Technologies
Location: Remote (US / Global)

About the Role:
We are looking for an experienced Senior Backend Engineer to architect, build, and scale
our distributed cloud platform and mission-critical microservices.

Key Responsibilities:
• Design and implement highly available RESTful APIs and microservices using Python and FastAPI.
• Optimize PostgreSQL database queries, connection pooling, and caching strategies using Redis.
• Deploy and maintain containerized applications on Kubernetes clusters in AWS cloud infrastructure.
• Drive code quality through test-driven development, automated CI/CD pipelines, and rigorous peer code reviews.
• Collaborate closely with frontend engineers, product managers, and security auditors.

Required Qualifications:
Backend Development: 4+ years of professional backend engineering experience with Python, Go, or Java.
Frameworks: Deep experience with modern API frameworks such as FastAPI, Flask, or Django.
Databases: Strong proficiency in relational databases (PostgreSQL, MySQL) and query performance optimization.
Distributed Systems: Hands-on experience with message queues (Kafka, RabbitMQ) and caching systems (Redis).
Cloud & Containers: Practical experience with AWS (ECS, EKS, S3, RDS) and Docker containerization.

Preferred Qualifications:
• Experience with Kubernetes orchestration, Helm charts, and Terraform infrastructure-as-code.
• Understanding of NLP, LLM integrations, or agentic frameworks.
• Prior experience working in high-growth SaaS startups.

What We Offer:
• Competitive compensation ($150,000 - $190,000) and generous equity packages.
• Comprehensive medical, dental, and vision insurance with 100% premium coverage.
• $2,500 annual professional development and learning stipend.
• Flexible remote-first work environment.
"""

def main():
    print("=" * 75)
    print("      MARKDOWN CONVERTER: RESUME & JOB DESCRIPTION PREVIEW")
    print("=" * 75)

    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
        if not target_path.exists():
            print(f"Error: File not found: {target_path}")
            return
        out_name = f"converted_{target_path.stem}.md"
        out_file = Path("logs") / out_name
        print(f"\n[1] CONVERTING FILE: {target_path.name}")
        markdown_output = convert_file_to_markdown(target_path)
        out_file.write_text(markdown_output, encoding="utf-8")
        print(f"-> Saved to: {out_file.resolve()}")
        return

    # 1. Convert Resume
    resume_out = Path("logs/converted_resume.md")
    print("\n[A] CONVERTING RESUME TO MARKDOWN...")
    cleaned_resume = clean_text(SAMPLE_RESUME)
    resume_md = convert_cleaned_text_to_markdown(
        cleaned_resume,
        document_title="John Doe - Software Engineer",
        save_path=resume_out,
    )
    print(f"-> Saved Resume to: {resume_out.resolve()}")

    # 2. Convert Job Description
    jd_out = Path("logs/converted_jd.md")
    print("\n[B] CONVERTING JOB DESCRIPTION TO MARKDOWN...")
    cleaned_jd = clean_text(SAMPLE_JD)
    jd_md = convert_cleaned_text_to_markdown(
        cleaned_jd,
        document_title="Senior Backend Software Engineer - CloudScale",
        save_path=jd_out,
    )
    print(f"-> Saved Job Description to: {jd_out.resolve()}")

    # Print section breakdown for Job Description
    jd_sections = [line for line in jd_md.splitlines() if line.startswith("#")]
    print("\n" + "=" * 75)
    print("            JOB DESCRIPTION: DETECTED SECTIONS BREAKDOWN")
    print("=" * 75)
    for idx, sec in enumerate(jd_sections, 1):
        print(f"  [{idx:02d}] {sec}")

    print("\n" + "=" * 75)
    print("              JOB DESCRIPTION: CONVERTED MARKDOWN OUTPUT")
    print("=" * 75)
    print(jd_md)
    print("=" * 75)
    print("Files created:")
    print(f" 1. Resume Markdown:          {resume_out.resolve()}")
    print(f" 2. Job Description Markdown: {jd_out.resolve()}")
    print("=" * 75)

if __name__ == "__main__":
    main()
