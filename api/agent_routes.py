import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from schemas.agent import RefinementLoopResult
from services.auth_service import get_current_user
from services.markdown_converter_service import convert_cleaned_text_to_markdown
from services.resume_rewrite_service import rewrite_resume_with_agent
from services.text_extraction_service import extract_text_from_file
from utils.file_utils import (
    RESUME_UPLOAD_EXTENSIONS,
    remove_temp_files,
    resolve_job_description,
    save_upload_to_temp_file,
    validate_upload_file,
    write_resume_docx,
)
from utils.logger import get_pipeline_logger

logger = get_pipeline_logger()

router = APIRouter()


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
    """Direct resume rewrite executing the agent reflection loop and returning a styled DOCX file."""
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


@router.post("/agent/rewrite-stream")
async def agent_rewrite_stream_endpoint(
    resume: UploadFile = File(...),
    job_description: UploadFile | None = File(None),
    job_description_text: str | None = Form(None),
    target_score: float = Form(80.0),
    max_iterations: int = Form(3),
    _current_user: dict = Depends(get_current_user),
):
    """Streams live multi-agent reflection loop progress and thoughts as Drafter, Auditor, and Fact-Checker iterate."""
    username = _current_user.get("username", "anonymous")
    logger.info(f"[PIPELINE START: AGENT REWRITE STREAM] User '{username}' started streaming rewrite (Target: {target_score}, Max: {max_iterations})")

    validate_upload_file(resume, RESUME_UPLOAD_EXTENSIONS)
    resume_path = await save_upload_to_temp_file(resume)
    jd_path, jd_text, _ = await resolve_job_description(job_description, job_description_text)

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
                    "thought": f"Extracting text from resume ({resume.filename}) and target job description...",
                    "progress": 10,
                })
                raw_resume_text = extract_text_from_file(resume_path)
                resume_markdown = convert_cleaned_text_to_markdown(raw_resume_text, document_title=Path(resume.filename or "Resume").stem)
                jd_markdown = convert_cleaned_text_to_markdown(jd_text, document_title="Job Description")

                push_event({
                    "type": "thought",
                    "agent": "Supervisor Agent",
                    "title": "Initiating Reflection Loop",
                    "thought": f"Starting autonomous Drafter -> ATS Auditor -> Fact-Checker loop. Target score: {target_score}%.",
                    "progress": 20,
                })

                def on_progress(p: dict):
                    push_event({"type": "thought", **p})

                result = rewrite_resume_with_agent(
                    resume_text=resume_markdown,
                    jd_text=jd_markdown,
                    target_score=target_score,
                    max_iterations=max_iterations,
                    progress_callback=on_progress,
                )

                push_event({
                    "type": "complete",
                    "agent": "Supervisor Agent",
                    "title": "Rewrite Complete",
                    "thought": f"Multi-agent rewrite completed ({result.iterations_count} iterations). Score: {result.initial_score}% -> {result.final_score}%.",
                    "progress": 100,
                    "result": result.model_dump(mode="json"),
                })
            except Exception as exc:
                logger.error(f"[PIPELINE ERROR: REWRITE STREAM] {exc}")
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
