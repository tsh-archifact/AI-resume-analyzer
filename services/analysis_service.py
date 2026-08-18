import json

from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model, get_llm_provider
from schemas.resume import JobDescriptionSkills, LLMRecommendation, ResumeSkills
from services.prompts import build_analysis_prompt


def parse_structured_llm_response(raw_content: str, model_name: str) -> LLMRecommendation:
    parsed = json.loads(raw_content)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")

    normalized = {
        "summary": str(parsed.get("summary") or ""),
        "overall_fit": str(parsed.get("overall_fit") or "Moderate"),
        "strengths": parsed.get("strengths") if isinstance(parsed.get("strengths"), list) else [],
        "missing_skills": parsed.get("missing_skills") if isinstance(parsed.get("missing_skills"), list) else [],
        "recommendations": parsed.get("recommendations") if isinstance(parsed.get("recommendations"), list) else [],
        "model_used": str(parsed.get("model_used") or model_name),
    }

    return LLMRecommendation.model_validate(normalized)


def build_rule_based_analysis(resume_skills: ResumeSkills, jd_skills: JobDescriptionSkills, model_used: str) -> LLMRecommendation:
    jd_skill_set = {skill.lower() for skill in jd_skills.skills}
    resume_skill_set = {skill.lower() for skill in resume_skills.skills}
    missing = [skill for skill in jd_skills.skills if skill.lower() not in resume_skill_set]

    return LLMRecommendation(
        summary="LLM analysis is unavailable. Returning a rule-based recruiter-style assessment.",
        overall_fit="Moderate" if missing else "Strong",
        strengths=[skill for skill in resume_skills.skills if skill.lower() in jd_skill_set],
        missing_skills=missing[:5],
        recommendations=[
            "Add missing skills to the resume in a visible skills section.",
            "Align the summary and experience bullets with the job description language.",
        ],
        model_used=model_used,
    )


def generate_llm_analysis(
    resume_text: str,
    jd_text: str,
    resume_skills: ResumeSkills,
    jd_skills: JobDescriptionSkills,
) -> LLMRecommendation:
    provider = get_llm_provider()
    model_name = get_llm_model()

    if not get_llm_api_key():
        return build_rule_based_analysis(resume_skills, jd_skills, f"{provider}-heuristic")

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are an HR and hiring expert. Compare resumes against job descriptions and provide concise, practical suggestions.",
                },
                {"role": "user", "content": build_analysis_prompt(resume_text, jd_text, resume_skills, jd_skills)},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")

        return parse_structured_llm_response(content, model_name)
    except Exception:
        return build_rule_based_analysis(resume_skills, jd_skills, f"{provider}-fallback")
