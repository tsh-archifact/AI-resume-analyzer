from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from services.prompts import build_resume_rewrite_prompt
from utils.file_utils import resolve_job_description


def rewrite_resume_with_llm(resume_text: str, jd_text: str) -> str:
    if not get_llm_api_key():
        raise RuntimeError("Resume rewrite unavailable: LLM API key is not configured.")

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0.3,
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
            raise RuntimeError("Resume rewrite unavailable: the LLM returned an empty response.")
        return content.strip()
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Resume rewrite unavailable: LLM request failed: {error}") from error


def rewrite_resume_with_agent(
    resume_text: str,
    jd_text: str,
    target_score: float = 80.0,
    max_iterations: int = 3,
    enforce_fact_check: bool = True,
):
    """Executes the autonomous multi-agent reflection loop (Drafter + Auditor + Fact-Checker)."""
    if not get_llm_api_key():
        raise RuntimeError("Resume rewrite unavailable: LLM API key is not configured.")

    from services.agents.refinement_loop import run_self_refining_loop

    try:
        return run_self_refining_loop(
            resume_text=resume_text,
            jd_text=jd_text,
            target_score=target_score,
            max_iterations=max_iterations,
            enforce_fact_check=enforce_fact_check,
        )
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(f"Agentic resume rewrite failed: {error}") from error

