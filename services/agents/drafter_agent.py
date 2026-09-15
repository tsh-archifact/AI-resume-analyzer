from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from schemas.agent import ATSCritiqueItem
from services.prompts import build_resume_rewrite_prompt


def build_refinement_prompt(
    current_draft: str,
    jd_text: str,
    source_resume: str,
    critiques: list[ATSCritiqueItem],
) -> str:
    """Constructs a targeted prompt instructing the LLM to fix specific ATS audit issues."""
    critique_bullets = "\n".join(
        f"- [{item.category.value.upper()}] ({item.severity.value}): {item.issue}\n  Action: {item.suggestion}"
        for item in critiques
    )

    return f"""You are an elite ATS resume optimizer. Your task is to REFINE an existing resume draft to address specific critique points raised by an automated ATS Auditor.

AUDIT CRITIQUES TO RESOLVE:
{critique_bullets}

GUIDELINES FOR REVISION:
1. Address each critique above directly.
2. If keywords are missing, weave them naturally into relevant experience bullet points and the core skills section if supported by the original candidate resume.
3. If metric density is low, ensure achievements highlight concrete outcomes, scale, or performance numbers.
4. If action verbs are weak, replace passive openings with powerful verbs (e.g., 'Spearheaded', 'Architected', 'Optimized', 'Automated').
5. Maintain 100% truthfulness to the candidate's original resume: never invent fake jobs, degrees, or employers.
6. Return ONLY the complete updated resume text. No markdown fences, no conversational explanations.

CURRENT DRAFT (TO IMPROVE):
{current_draft}

ORIGINAL RESUME (SOURCE OF TRUTH):
{source_resume}

TARGET JOB DESCRIPTION:
{jd_text}
"""


def generate_initial_draft(resume_text: str, jd_text: str) -> str:
    """Generates the initial resume draft targeting the job description."""
    if not get_llm_api_key():
        raise RuntimeError("Resume drafting unavailable: LLM API key is not configured.")

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer. Rewrite resumes to match job descriptions while keeping them truthful and ATS-friendly.",
                },
                {"role": "user", "content": build_resume_rewrite_prompt(resume_text, jd_text)},
            ],
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise RuntimeError("Resume drafter returned an empty response.")
        return content.strip()
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Resume drafter failed: {error}") from error


def refine_draft(
    current_draft: str,
    jd_text: str,
    source_resume: str,
    critiques: list[ATSCritiqueItem],
) -> str:
    """Revises a resume draft based on specific ATS auditor critique items."""
    if not get_llm_api_key():
        raise RuntimeError("Resume refinement unavailable: LLM API key is not configured.")

    if not critiques:
        return current_draft

    try:
        client = get_llm_client()
        prompt = build_refinement_prompt(current_draft, jd_text, source_resume, critiques)
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume optimizer that refines drafts based on ATS audit feedback.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise RuntimeError("Resume refiner returned an empty response.")
        return content.strip()
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Resume refiner failed: {error}") from error
