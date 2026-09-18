from collections.abc import Callable
from typing import Any

from schemas.agent import (
    AgentIterationStep,
    ATSAuditResult,
    RefinementLoopResult,
)
from services.agents.auditor_agent import audit_resume_draft
from services.agents.drafter_agent import build_refinement_prompt, generate_initial_draft, refine_draft
from services.agents.fact_checker_agent import convert_fact_check_to_critiques, verify_resume_truthfulness
from services.skill_service import extract_skills_from_text


def run_self_refining_loop(
    resume_text: str,
    jd_text: str,
    target_skills: list[str] | None = None,
    target_score: float = 80.0,
    max_iterations: int = 3,
    initial_draft: str | None = None,
    use_llm_semantic_critique: bool = False,
    enforce_fact_check: bool = True,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> RefinementLoopResult:
    """
    Executes an autonomous Draft -> Critique -> Fact-Check -> Refine loop.
    
    The Drafter, Auditor, and Fact-Checker collaborate:
    1. Auditor audits the current draft for ATS keyword and metric density.
    2. Fact-Checker verifies the draft against the original resume to detect hallucinations.
    3. If score >= target_score and the draft is factually grounded, the loop halts early.
    4. Otherwise, combined ATS and grounding critiques are fed back to the Drafter to refine the draft.
    5. Repeats until target_score and factuality are achieved or max_iterations is reached.
    """
    if target_skills is None:
        if progress_callback:
            progress_callback({
                "agent": "Perception Agent",
                "title": "Extracting Target Skills",
                "thought": "Extracting key competencies and technical qualifications from the target job description...",
                "progress": 10,
            })
        target_skills = extract_skills_from_text(jd_text, section_name="job_description_skills")

    iteration_history: list[AgentIterationStep] = []
    
    # --- Iteration 1: Initial Draft, Baseline Audit & Fact-Check ---
    if progress_callback:
        progress_callback({
            "agent": "Drafter Agent",
            "title": "Drafting Initial Resume",
            "thought": "Transforming candidate experience using the Google XYZ formula (Accomplished [X], measured by [Y], by doing [Z])...",
            "iteration": 1,
            "progress": 25,
        })
    current_draft = initial_draft if initial_draft is not None else generate_initial_draft(resume_text, jd_text)

    if progress_callback:
        progress_callback({
            "agent": "ATS Auditor Critic",
            "title": "Auditing Baseline Draft",
            "thought": "Auditing draft for keyword coverage, action verbs, and Flesch-Kincaid reading grade level...",
            "iteration": 1,
            "progress": 40,
        })
    audit = audit_resume_draft(
        current_draft,
        jd_text,
        target_skills=target_skills,
        use_llm_critique=use_llm_semantic_critique,
    )

    if progress_callback and enforce_fact_check:
        progress_callback({
            "agent": "Fact-Checking Guardrail",
            "title": "Verifying Factual Grounding",
            "thought": "Cross-checking rewritten skills and claims against the original resume to prevent hallucinations...",
            "iteration": 1,
            "progress": 55,
        })
    fact_check = verify_resume_truthfulness(current_draft, resume_text) if enforce_fact_check else None

    # Combine ATS critiques with any fact-check violation critiques
    active_critiques = list(audit.critiques)
    if fact_check and not fact_check.is_clean:
        active_critiques.extend(convert_fact_check_to_critiques(fact_check))

    initial_score = audit.overall_score
    best_draft = current_draft
    best_audit = audit
    best_fact_check = fact_check

    refinement_prompt_note = None
    if active_critiques and (audit.overall_score < target_score or (fact_check and not fact_check.is_clean)):
        refinement_prompt_note = f"Resolved {len(active_critiques)} critique item(s)."

    iteration_history.append(
        AgentIterationStep(
            iteration=1,
            draft_snippet=current_draft[:250] + ("..." if len(current_draft) > 250 else ""),
            audit_result=audit,
            fact_check=fact_check,
            refinement_prompt_used=refinement_prompt_note,
        )
    )

    # If the initial draft meets target threshold, is factually clean, or max_iterations <= 1, return immediately
    initial_clean = fact_check.is_clean if fact_check else True
    if progress_callback:
        progress_callback({
            "agent": "Supervisor Agent",
            "title": "Pass 1 Evaluation",
            "thought": f"Pass 1 evaluated: ATS Score is {audit.overall_score}% (Target: {target_score}%). Grounding verified: {initial_clean}.",
            "score": audit.overall_score,
            "iteration": 1,
            "progress": 65,
        })

    if (audit.overall_score >= target_score and initial_clean) or max_iterations <= 1:
        if progress_callback:
            progress_callback({
                "agent": "Supervisor Agent",
                "title": "Optimization Complete",
                "thought": f"Target threshold met on pass 1 ({best_audit.overall_score}% >= {target_score}%). Finalizing output.",
                "score": best_audit.overall_score,
                "progress": 100,
            })
        return RefinementLoopResult(
            final_draft=best_draft,
            initial_score=initial_score,
            final_score=best_audit.overall_score,
            score_improvement=0.0,
            iterations_count=1,
            target_score_met=best_audit.overall_score >= target_score and initial_clean,
            target_score=target_score,
            iteration_history=iteration_history,
            final_audit=best_audit,
            final_fact_check=best_fact_check,
        )

    # --- Subsequent Iterations: Targeted Refinement Loop ---
    for iteration_num in range(2, max_iterations + 1):
        if not active_critiques:
            break

        if progress_callback:
            progress_callback({
                "agent": "Drafter Agent",
                "title": f"Refining Draft (Pass {iteration_num})",
                "thought": f"Refining resume bullets to address {len(active_critiques)} feedback items from ATS Auditor and Fact-Checker...",
                "iteration": iteration_num,
                "progress": min(65 + (iteration_num - 1) * 10, 88),
            })

        refined_draft = refine_draft(
            current_draft=best_draft,
            jd_text=jd_text,
            source_resume=resume_text,
            critiques=active_critiques,
        )

        if progress_callback:
            progress_callback({
                "agent": "ATS Auditor Critic",
                "title": f"Re-Auditing Draft (Pass {iteration_num})",
                "thought": f"Checking keyword coverage and readability grade on refined draft (Pass {iteration_num})...",
                "iteration": iteration_num,
                "progress": min(70 + (iteration_num - 1) * 10, 92),
            })

        new_audit = audit_resume_draft(
            refined_draft,
            jd_text,
            target_skills=target_skills,
            use_llm_critique=use_llm_semantic_critique,
        )

        if progress_callback and enforce_fact_check:
            progress_callback({
                "agent": "Fact-Checking Guardrail",
                "title": f"Verifying Truthfulness (Pass {iteration_num})",
                "thought": f"Cross-checking refined draft {iteration_num} against source resume to guarantee zero hallucinations...",
                "iteration": iteration_num,
                "progress": min(75 + (iteration_num - 1) * 10, 95),
            })

        new_fact_check = verify_resume_truthfulness(refined_draft, resume_text) if enforce_fact_check else None

        active_critiques = list(new_audit.critiques)
        if new_fact_check and not new_fact_check.is_clean:
            active_critiques.extend(convert_fact_check_to_critiques(new_fact_check))

        prompt_note = f"Addressed critiques. Score: {new_audit.overall_score}, Clean: {new_fact_check.is_clean if new_fact_check else True}"

        iteration_history.append(
            AgentIterationStep(
                iteration=iteration_num,
                draft_snippet=refined_draft[:250] + ("..." if len(refined_draft) > 250 else ""),
                audit_result=new_audit,
                fact_check=new_fact_check,
                refinement_prompt_used=prompt_note,
            )
        )

        # Prioritize truthfulness: A clean, grounded draft always supersedes a hallucinated draft.
        # When both are clean (or both ungrounded), prefer the higher-scoring draft.
        is_clean_now = new_fact_check.is_clean if new_fact_check else True
        was_clean = best_fact_check.is_clean if best_fact_check else True
        should_replace = False
        if not was_clean and is_clean_now:
            should_replace = True
        elif is_clean_now and new_audit.overall_score >= best_audit.overall_score:
            should_replace = True
        elif not was_clean and not is_clean_now and new_audit.overall_score >= best_audit.overall_score:
            should_replace = True

        if should_replace:
            best_draft = refined_draft
            best_audit = new_audit
            best_fact_check = new_fact_check

        if best_audit.overall_score >= target_score and is_clean_now:
            break

    score_improvement = round(best_audit.overall_score - initial_score, 1)
    target_met = best_audit.overall_score >= target_score and (best_fact_check.is_clean if best_fact_check else True)

    if progress_callback:
        progress_callback({
            "agent": "Supervisor Agent",
            "title": "Refinement Complete",
            "thought": f"Multi-agent refinement complete! Initial ATS: {initial_score}% -> Final ATS: {best_audit.overall_score}% ({score_improvement:+} pts). Fact-check clean: {best_fact_check.is_clean if best_fact_check else True}.",
            "score": best_audit.overall_score,
            "progress": 100,
        })

    return RefinementLoopResult(
        final_draft=best_draft,
        initial_score=initial_score,
        final_score=best_audit.overall_score,
        score_improvement=score_improvement,
        iterations_count=len(iteration_history),
        target_score_met=target_met,
        target_score=target_score,
        iteration_history=iteration_history,
        final_audit=best_audit,
        final_fact_check=best_fact_check,
    )
