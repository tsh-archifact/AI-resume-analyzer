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
    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path, jd_text, jd_filename = await resolve_job_description(job_description, job_description_text)

        resume_text = extract_text_from_file(resume_path)

        try:
            resume_profile = extract_profile(resume_text, "resume")
            jd_profile = extract_profile(jd_text, "job_description")
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

        resume_skills = ResumeSkills(skills=[skill.name for skill in resume_profile.skills] or resume_profile.keywords)
        jd_skill_values = [skill.name for skill in jd_profile.required_skills + jd_profile.preferred_skills]
        jd_skills = JobDescriptionSkills(skills=jd_skill_values or jd_profile.keywords)
        agent_audit = audit_resume_draft(resume_text, jd_text, target_skills=jd_skills.skills)
        return ResumeComparisonResponse(
            resume_file=resume.filename,
            job_description_file=jd_filename,
            resume_skills=resume_skills,
            job_description_skills=jd_skills,
            similarity=calculate_similarity(resume_skills,jd_skills),
            llm_analysis=generate_llm_analysis(resume_text, jd_text, resume_skills, jd_skills),
            resume_profile=resume_profile,
            job_description_profile=jd_profile,
            structured_comparison=compare_profiles(resume_profile, jd_profile),
            agent_audit=agent_audit,
        )
    finally:
        remove_temp_files(resume_path, jd_path)


@router.post("/rewrite-resume")
async def rewrite_resume_endpoint(
    resume: UploadFile = File(...),
    job_description: UploadFile | None = File(None),
    job_description_text: str | None = Form(None),
    _current_user: dict = Depends(get_current_user),
):
    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path, jd_text, _ = await resolve_job_description(job_description, job_description_text)

        resume_text = extract_text_from_file(resume_path)
        try:
            agent_result = rewrite_resume_with_agent(resume_text, jd_text)
            rewritten_text = agent_result.final_draft
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        docx_path = write_resume_docx(rewritten_text)

        headers = {
            "X-Agent-Initial-Score": str(agent_result.initial_score),
            "X-Agent-Final-Score": str(agent_result.final_score),
            "X-Agent-Score-Improvement": str(agent_result.score_improvement),
            "X-Agent-Iterations": str(agent_result.iterations_count),
            "X-Agent-Fact-Clean": str(agent_result.final_fact_check.is_clean if agent_result.final_fact_check else True).lower(),
        }

        return FileResponse(
            docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="rewritten_resume.docx",
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
    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path, jd_text, _ = await resolve_job_description(job_description, job_description_text)

        resume_text = extract_text_from_file(resume_path)
        try:
            return rewrite_resume_with_agent(
                resume_text=resume_text,
                jd_text=jd_text,
                target_score=target_score,
                max_iterations=max_iterations,
            )
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
    finally:
        remove_temp_files(resume_path, jd_path)


class ExportDocxPayload(BaseModel):
    content: str


@router.post("/agent/export-docx")
def export_docx_endpoint(
    payload: ExportDocxPayload,
    _current_user: dict = Depends(get_current_user),
):
    """Generates an ATS-friendly DOCX file from rewritten resume markdown or text."""
    docx_path = write_resume_docx(payload.content)
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="optimized_resume.docx",
    )
