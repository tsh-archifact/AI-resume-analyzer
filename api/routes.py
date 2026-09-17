from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from utils.limiter import limiter
from fastapi import Request



from schemas.resume import (
    JobDescriptionSkills,
    LLMRecommendation,
    ResumeComparisonResponse,
    ResumeSkills,
)
from services.analysis_service import generate_llm_analysis
from services.profile_service import extract_profile
from services.structured_comparison_service import compare_profiles
from pydantic import BaseModel
from schemas.agent import RefinementLoopResult
from services.agents.auditor_agent import audit_resume_draft
from services.auth_service import get_current_user
from services.resume_rewrite_service import (
    resolve_job_description,
    rewrite_resume_with_agent,
)
from services.skill_service import calculate_similarity, compare_skill_lists, get_best_skill_list
from services.text_extraction_service import extract_text_from_file
from utils.file_utils import (
    RESUME_UPLOAD_EXTENSIONS,
    remove_temp_files,
    save_upload_to_temp_file,
    validate_upload_file,
    write_resume_docx,
)
from utils.logger import get_pipeline_logger
from services.markdown_converter_service import convert_cleaned_text_to_markdown

logger = get_pipeline_logger()



router = APIRouter()


@router.get("/health")
@limiter.limit("1/minute")
def health_check(request:Request):
    return {"status": "ok","IP":request.send_push_promise}


@router.post("/compare-skill-sections", response_model=ResumeComparisonResponse)
@limiter.limit("5/minute")
def compare_skill_sections(
    request:Request,
    resume_skills: ResumeSkills,
    job_description_skills: JobDescriptionSkills,
    _current_user: dict = Depends(get_current_user),
):
    similarity = compare_skill_lists(resume_skills.skills, job_description_skills.skills)
    score = similarity.match_score

    llm_analysis = LLMRecommendation(
        summary="Structured comparison completed.",
        overall_fit="Strong" if score >= 70 else "Moderate" if score >= 40 else "Weak",
        strengths=similarity.matched_skills,
        missing_skills=similarity.missing_skills,
        recommendations=[
            "Add missing skills to the resume.",
            "Align the experience section to the JD language.",
        ],
        model_used="heuristic",
    )

    return ResumeComparisonResponse(
        resume_file=None,
        job_description_file=None,
        resume_skills=resume_skills,
        job_description_skills=job_description_skills,
        similarity=similarity,
        llm_analysis=llm_analysis,
    )


@router.post("/compare-resume", response_model=ResumeComparisonResponse)
async def compare_resume(
    resume: UploadFile = File(...),
    job_description: UploadFile | None = File(None),
    job_description_text: str | None = Form(None),
    _current_user: dict = Depends(get_current_user),
):
    username = _current_user.get("username", "anonymous")
    logger.info(f"[PIPELINE START: COMPARE] User '{username}' initiated resume comparison for file: {resume.filename}")

    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path, jd_text, jd_filename = await resolve_job_description(job_description, job_description_text)

        logger.info(f"[PIPELINE STEP 1: EXTRACTION] Extracting raw text from resume ({resume.filename}) and JD ({jd_filename})...")
        raw_resume_text = extract_text_from_file(resume_path)

        # Convert both to structured Markdown format
        logger.info(f"[PIPELINE STEP 2: MARKDOWN] Converting extracted texts into structured Markdown format...")
        resume_markdown = convert_cleaned_text_to_markdown(raw_resume_text, document_title=Path(resume.filename or "Resume").stem)
        jd_markdown = convert_cleaned_text_to_markdown(jd_text, document_title=Path(jd_filename or "Job Description").stem)
        logger.info(
            f"[PIPELINE STEP 2: MARKDOWN COMPLETED] Resume: {resume_markdown} md chars | JD: {jd_markdown} md chars."
        )

        try:
            logger.info("[PIPELINE STEP 3: PROFILES] Extracting structured candidate & JD profiles via LLM & spaCy...")
            resume_profile = extract_profile(resume_markdown, "resume")
            jd_profile = extract_profile(jd_markdown, "job_description")
            logger.info(
                f"[PIPELINE STEP 3: PROFILES COMPLETED] Candidate Experience: {resume_profile.total_years_experience} yrs, Skills: {len(resume_profile.skills)} | JD Required Skills: {len(jd_profile.required_skills)}, Min Experience: {jd_profile.experience_requirement.minimum_years} yrs."
            )
        except RuntimeError as error:
            logger.error(f"[PIPELINE ERROR: PROFILES] Profile extraction failed: {error}")
            raise HTTPException(status_code=503, detail=str(error)) from error

        resume_skills = ResumeSkills(skills=[skill.name for skill in resume_profile.skills] or resume_profile.keywords)
        jd_skill_values = [skill.name for skill in jd_profile.required_skills + jd_profile.preferred_skills]
        jd_skills = JobDescriptionSkills(skills=jd_skill_values or jd_profile.keywords)

        logger.info("[PIPELINE STEP 4: SIMILARITY] Computing rapidfuzz skill similarity and experience weighting...")
        similarity = calculate_similarity(resume_skills, jd_skills)
        structured_comparison = compare_profiles(resume_profile, jd_profile)
        logger.info(
            f"[PIPELINE STEP 4: SIMILARITY COMPLETED] Match score: {similarity.match_score}%, Overall score: {structured_comparison.overall_score}%. Matched: {len(similarity.matched_skills)}, Missing: {len(similarity.missing_skills)}."
        )

        logger.info("[PIPELINE STEP 5: ATS AUDIT] Running ATS Auditor Agent on resume markdown...")
        agent_audit = audit_resume_draft(resume_markdown, jd_markdown, target_skills=jd_skills.skills)
        logger.info(
            f"[PIPELINE STEP 5: ATS AUDIT COMPLETED] Overall ATS Score: {agent_audit.overall_score}/100, Keyword Coverage: {agent_audit.keyword_score}%, Critiques: {len(agent_audit.critiques)}."
        )

        logger.info(f"[PIPELINE COMPLETE: COMPARE] Resume comparison finished successfully for '{resume.filename}'.")

        return ResumeComparisonResponse(
            resume_file=resume.filename,
            job_description_file=jd_filename,
            resume_skills=resume_skills,
            job_description_skills=jd_skills,
            similarity=similarity,
            llm_analysis=generate_llm_analysis(resume_markdown, jd_markdown, resume_skills, jd_skills),
            resume_profile=resume_profile,
            job_description_profile=jd_profile,
            structured_comparison=structured_comparison,
            agent_audit=agent_audit,
        )
    finally:
        remove_temp_files(resume_path, jd_path)


@router.get("/agent/templates")
def get_templates_endpoint():
    """Returns available DOCX resume templates with typography and persona metadata."""
    from services.docx_generator_service import get_available_templates

    return {"templates": get_available_templates()}


@router.post("/rewrite-resume")
async def rewrite_resume_endpoint(
    resume: UploadFile = File(...),
    job_description: UploadFile | None = File(None),
    job_description_text: str | None = Form(None),
    template_id: str = Form("modern_teal"),
    _current_user: dict = Depends(get_current_user),
):
    username = _current_user.get("username", "anonymous")
    logger.info(f"[PIPELINE START: DIRECT REWRITE] User '{username}' requested DOCX rewrite for: {resume.filename} (Template: {template_id})")

    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path, jd_text, _ = await resolve_job_description(job_description, job_description_text)

        raw_resume_text = extract_text_from_file(resume_path)
        logger.info("[PIPELINE STEP: MARKDOWN] Converting resume and JD to Markdown for rewrite...")
        resume_markdown = convert_cleaned_text_to_markdown(raw_resume_text, document_title=Path(resume.filename or "Resume").stem)
        jd_markdown = convert_cleaned_text_to_markdown(jd_text, document_title="Job Description")

        try:
            logger.info("[PIPELINE STEP: AGENT REWRITE] Executing multi-agent reflection loop...")
            agent_result = rewrite_resume_with_agent(resume_markdown, jd_markdown)
            rewritten_text = agent_result.final_draft
            logger.info(
                f"[PIPELINE STEP: AGENT REWRITE COMPLETED] Score: {agent_result.initial_score} -> {agent_result.final_score} ({agent_result.iterations_count} iterations)."
            )
        except RuntimeError as error:
            logger.error(f"[PIPELINE ERROR: REWRITE] Agent rewrite failed: {error}")
            raise HTTPException(status_code=503, detail=str(error)) from error

        logger.info(f"[PIPELINE STEP: EXPORT] Generating DOCX output with template '{template_id}'...")
        docx_path = write_resume_docx(rewritten_text, template_id=template_id)

        headers = {
            "X-Agent-Initial-Score": str(agent_result.initial_score),
            "X-Agent-Final-Score": str(agent_result.final_score),
            "X-Agent-Score-Improvement": str(agent_result.score_improvement),
            "X-Agent-Iterations": str(agent_result.iterations_count),
            "X-Agent-Fact-Clean": str(agent_result.final_fact_check.is_clean if agent_result.final_fact_check else True).lower(),
        }

        logger.info(f"[PIPELINE COMPLETE: DIRECT REWRITE] Generated DOCX ({docx_path}) successfully.")
        safe_template_name = template_id.replace(" ", "_").lower()
        return FileResponse(
            docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"rewritten_resume_{safe_template_name}.docx",
            headers=headers,
        )
    finally:
        remove_temp_files(resume_path, jd_path)


@router.post("/agent/rewrite", response_model=RefinementLoopResult)
async def agent_rewrite_endpoint(
    resume: UploadFile = File(...),
    job_description: UploadFile | None = File(None),
    job_description_text: str | None = Form(None),
    target_score: float = Form(80.0),
    max_iterations: int = Form(3),
    _current_user: dict = Depends(get_current_user),
):
    """Returns the full multi-agent reflection loop result as structured JSON."""
    username = _current_user.get("username", "anonymous")
    logger.info(f"[PIPELINE START: AGENT REWRITE] User '{username}' initiated agent rewrite (Target: {target_score}, Max Iterations: {max_iterations})")

    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path, jd_text, _ = await resolve_job_description(job_description, job_description_text)

        raw_resume_text = extract_text_from_file(resume_path)
        logger.info("[PIPELINE STEP: MARKDOWN] Converting resume and JD to Markdown before drafting...")
        resume_markdown = convert_cleaned_text_to_markdown(raw_resume_text, document_title=Path(resume.filename or "Resume").stem)
        jd_markdown = convert_cleaned_text_to_markdown(jd_text, document_title="Job Description")

        try:
            logger.info("[PIPELINE STEP: MULTI-AGENT LOOP] Starting Drafter -> Auditor -> Fact-Checker cycle...")
            result = rewrite_resume_with_agent(
                resume_text=resume_markdown,
                jd_text=jd_markdown,
                target_score=target_score,
                max_iterations=max_iterations,
            )
            logger.info(
                f"[PIPELINE COMPLETE: AGENT REWRITE] Iterations: {result.iterations_count}, Initial: {result.initial_score}%, Final: {result.final_score}%, Improvement: +{result.score_improvement}%. Target met: {result.target_score_met}."
            )
            return result
        except RuntimeError as error:
            logger.error(f"[PIPELINE ERROR: AGENT REWRITE] Agent loop failed: {error}")
            raise HTTPException(status_code=503, detail=str(error)) from error
    finally:
        remove_temp_files(resume_path, jd_path)


class ExportDocxPayload(BaseModel):
    content: str
    template_id: str = "modern_teal"


@router.post("/agent/export-docx")
def export_docx_endpoint(
    payload: ExportDocxPayload,
    _current_user: dict = Depends(get_current_user),
):
    """Generates an ATS-friendly DOCX file from rewritten resume markdown or text using the selected template."""
    docx_path = write_resume_docx(payload.content, template_id=payload.template_id)
    safe_template_name = payload.template_id.replace(" ", "_").lower()
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"optimized_resume_{safe_template_name}.docx",
    )

