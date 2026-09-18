import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from schemas.resume import (
    JobDescriptionSkills,
    LLMRecommendation,
    ResumeComparisonResponse,
    ResumeSkills,
)
from services.analysis_service import generate_llm_analysis
from services.auth_service import get_current_user
from services.markdown_converter_service import convert_cleaned_text_to_markdown
from services.profile_service import extract_profile
from services.skill_service import calculate_similarity, compare_skill_lists
from services.structured_comparison_service import compare_profiles
from services.text_extraction_service import extract_text_from_file
from services.agents.auditor_agent import audit_resume_draft
from utils.file_utils import (
    RESUME_UPLOAD_EXTENSIONS,
    remove_temp_files,
    resolve_job_description,
    save_upload_to_temp_file,
    validate_upload_file,
)
from utils.limiter import limiter
from utils.logger import get_pipeline_logger

logger = get_pipeline_logger()

router = APIRouter()


@router.get("/health")
@limiter.limit("1/minute")
def health_check(request: Request):
    return {"status": "ok"}


@router.post("/compare-skill-sections", response_model=ResumeComparisonResponse)
@limiter.limit("5/minute")
def compare_skill_sections(
    request: Request,
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
        logger.info("[PIPELINE STEP 2: MARKDOWN] Converting extracted texts into structured Markdown format...")
        resume_markdown = convert_cleaned_text_to_markdown(raw_resume_text, document_title=Path(resume.filename or "Resume").stem)
        jd_markdown = convert_cleaned_text_to_markdown(jd_text, document_title=Path(jd_filename or "Job Description").stem)
        logger.info(
            f"[PIPELINE STEP 2: MARKDOWN COMPLETED] Resume: {len(resume_markdown)} md chars | JD: {len(jd_markdown)} md chars."
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


@router.post("/compare-resume-stream")
async def compare_resume_stream(
    resume: UploadFile = File(...),
    job_description: UploadFile | None = File(None),
    job_description_text: str | None = Form(None),
    _current_user: dict = Depends(get_current_user),
):
    """Streams live agent thoughts and reasoning progress while comparing a resume to a job description."""
    username = _current_user.get("username", "anonymous")
    logger.info(f"[PIPELINE START: COMPARE STREAM] User '{username}' started streaming comparison for: {resume.filename}")

    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)
    resume_path = await save_upload_to_temp_file(resume)
    jd_path, jd_text, jd_filename = await resolve_job_description(job_description, job_description_text)

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def push_event(event: dict):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        def worker():
            try:
                push_event({
                    "type": "thought",
                    "agent": "Perception Agent",
                    "title": "Ingesting Documents",
                    "thought": f"Extracting text from candidate resume ({resume.filename}) and target JD ({jd_filename})...",
                    "progress": 15,
                })
                raw_resume_text = extract_text_from_file(resume_path)

                push_event({
                    "type": "thought",
                    "agent": "Markdown Converter",
                    "title": "Structuring Markdown",
                    "thought": "Standardizing section headings (Summary, Experience, Skills, Education)...",
                    "progress": 30,
                })
                resume_markdown = convert_cleaned_text_to_markdown(raw_resume_text, document_title=Path(resume.filename or "Resume").stem)
                jd_markdown = convert_cleaned_text_to_markdown(jd_text, document_title=Path(jd_filename or "Job Description").stem)

                push_event({
                    "type": "thought",
                    "agent": "Profile Extraction Agent",
                    "title": "Analyzing Profiles",
                    "thought": "Extracting candidate achievements and JD requirements via spaCy NLP & LLM...",
                    "progress": 50,
                })
                resume_profile = extract_profile(resume_markdown, "resume")
                jd_profile = extract_profile(jd_markdown, "job_description")

                resume_skills = ResumeSkills(skills=[skill.name for skill in resume_profile.skills] or resume_profile.keywords)
                jd_skill_values = [skill.name for skill in jd_profile.required_skills + jd_profile.preferred_skills]
                jd_skills = JobDescriptionSkills(skills=jd_skill_values or jd_profile.keywords)

                push_event({
                    "type": "thought",
                    "agent": "Similarity Engine",
                    "title": "Computing Match Scores",
                    "thought": "Computing RapidFuzz semantic skill overlap and experience weighting...",
                    "progress": 70,
                })
                similarity = calculate_similarity(resume_skills, jd_skills)
                structured_comparison = compare_profiles(resume_profile, jd_profile)

                push_event({
                    "type": "thought",
                    "agent": "ATS Auditor Critic",
                    "title": "Auditing ATS Readiness",
                    "thought": f"Auditing keyword match density ({similarity.match_score}%) and Flesch-Kincaid readability grade...",
                    "progress": 85,
                })
                agent_audit = audit_resume_draft(resume_markdown, jd_markdown, target_skills=jd_skills.skills)

                push_event({
                    "type": "thought",
                    "agent": "Recruiter Advisor",
                    "title": "Synthesizing Recommendations",
                    "thought": "Formulating tailored recommendations, matched strengths, and missing skill gaps...",
                    "progress": 95,
                })
                llm_analysis = generate_llm_analysis(resume_markdown, jd_markdown, resume_skills, jd_skills)

                response_obj = ResumeComparisonResponse(
                    resume_file=resume.filename,
                    job_description_file=jd_filename,
                    resume_skills=resume_skills,
                    job_description_skills=jd_skills,
                    similarity=similarity,
                    llm_analysis=llm_analysis,
                    resume_profile=resume_profile,
                    job_description_profile=jd_profile,
                    structured_comparison=structured_comparison,
                    agent_audit=agent_audit,
                )

                push_event({
                    "type": "complete",
                    "agent": "Supervisor Agent",
                    "title": "Comparison Complete",
                    "thought": f"Role comparison complete! Match score: {similarity.match_score}%, ATS overall: {structured_comparison.overall_score}%.",
                    "progress": 100,
                    "result": response_obj.model_dump(mode="json"),
                })
            except Exception as exc:
                logger.error(f"[PIPELINE ERROR: COMPARE STREAM] {exc}")
                push_event({"type": "error", "error": str(exc)})
            finally:
                remove_temp_files(resume_path, jd_path)

        asyncio.create_task(asyncio.to_thread(worker))

        while True:
            event = await queue.get()
            yield json.dumps(event) + "\n"
            if event.get("type") in ("complete", "error"):
                break

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
