from fastapi import HTTPException, UploadFile

from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from services.prompts import build_resume_rewrite_prompt
from services.text_extraction_service import extract_text_from_file
from utils.file_utils import JOB_DESCRIPTION_UPLOAD_EXTENSIONS, save_upload_to_temp_file, validate_upload_file


async def resolve_job_description(
    job_description: UploadFile | None,
    job_description_text: str | None,
) -> tuple[str | None, str, str]:
    if job_description is not None and job_description_text and job_description_text.strip():
        raise HTTPException(status_code=400, detail="Provide either job_description or job_description_text, not both.")

    if job_description is None and not job_description_text:
        raise HTTPException(status_code=400, detail="Provide a job_description file or job_description_text.")

    if job_description_text is not None:
        text = job_description_text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="job_description_text must not be empty.")
        return None, text, "job_description_text"

    validate_upload_file(job_description, JOB_DESCRIPTION_UPLOAD_EXTENSIONS)
    job_description_path = await save_upload_to_temp_file(job_description)
    return job_description_path, extract_text_from_file(job_description_path), job_description.filename or "job_description"


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

