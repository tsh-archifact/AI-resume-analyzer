from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from schemas.resume import (
    JobDescriptionSkills,
    LLMRecommendation,
    ResumeComparisonResponse,
    ResumeSkills,
)
from services.analysis_service import generate_llm_analysis
from services.resume_rewrite_service import rewrite_resume_with_llm
from services.skill_service import calculate_similarity, compare_skill_lists, get_best_skill_list
from services.text_extraction_service import extract_text_from_file
from utils.file_utils import remove_temp_files, save_upload_to_temp_file, validate_upload_file, write_resume_docx


router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/compare-skill-sections", response_model=ResumeComparisonResponse)
def compare_skill_sections(
    resume_skills: ResumeSkills,
    job_description_skills: JobDescriptionSkills,
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
    job_description: UploadFile = File(...),
):
    for uploaded_file in (resume, job_description):
        validate_upload_file(uploaded_file)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path = await save_upload_to_temp_file(job_description)

        resume_text = extract_text_from_file(resume_path)
        jd_text = extract_text_from_file(jd_path)

        resume_skills = ResumeSkills(skills=get_best_skill_list(resume_text, "resume"))
        jd_skills = JobDescriptionSkills(skills=get_best_skill_list(jd_text, "job description"))

        return ResumeComparisonResponse(
            resume_file=resume.filename,
            job_description_file=job_description.filename,
            resume_skills=resume_skills,
            job_description_skills=jd_skills,
            similarity=calculate_similarity(resume_text, jd_text),
            llm_analysis=generate_llm_analysis(resume_text, jd_text, resume_skills, jd_skills),
        )
    finally:
        remove_temp_files(resume_path, jd_path)


@router.post("/rewrite-resume")
async def rewrite_resume_endpoint(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...),
):
    for uploaded_file in (resume, job_description):
        validate_upload_file(uploaded_file)

    resume_path = None
    jd_path = None

    try:
        resume_path = await save_upload_to_temp_file(resume)
        jd_path = await save_upload_to_temp_file(job_description)

        resume_text = extract_text_from_file(resume_path)
        jd_text = extract_text_from_file(jd_path)
        rewritten_text = rewrite_resume_with_llm(resume_text, jd_text)
        docx_path = write_resume_docx(rewritten_text)

        return FileResponse(
            docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="rewritten_resume.docx",
        )
    finally:
        remove_temp_files(resume_path, jd_path)
