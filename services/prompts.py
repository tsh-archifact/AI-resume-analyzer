import json

from schemas.resume import JobDescriptionSkills, ResumeSkills


def build_skill_extraction_prompt(text: str, label: str) -> str:
    return f"""
You are a resume and job-description information extraction system.
Extract skills from the {label} text below.

Rules:
- Extract only skills explicitly present in the source text.
- Return atomic skills, tools, frameworks, platforms, databases, methods, and technologies.
- Convert sentences into skill names. For example, "built APIs with Express.js" becomes "Express.js".
- Do not extract job titles, employers, locations, degrees, responsibilities, benefits, or section headings.
- Preserve meaningful versions, such as "Python 3" or ".NET 8".
- Do not infer equivalent skills. If the text says "Postgres", return "Postgres"; do not silently change it to "PostgreSQL".
- Remove duplicates while preserving the clearest source wording.

Return ONLY a valid JSON object matching this schema exactly:
{{"skills": ["Skill 1", "Skill 2", "Skill 3"]}}

Text:
{text[:6000]}
"""


def build_profile_extraction_prompt(text: str, document_type: str) -> str:
    if document_type == "resume":
        schema = {
            "keywords": ["Python"],
            "skills": [{"name": "Python", "category": "technical", "years_experience": 3.0, "evidence": [{"text": "...", "confidence": 0.9}]}],
            "total_years_experience": 3.0,
            "experience_periods": [{"title": "Software Engineer", "company": "Example", "start_date": "2021", "end_date": "present", "evidence": []}],
            "experience_evidence": [{"text": "3 years of experience", "confidence": 0.95}],
        }
    else:
        schema = {
            "keywords": ["Python"],
            "required_skills": [{"name": "Python", "category": "technical", "years_experience": None, "evidence": []}],
            "preferred_skills": [],
            "experience_requirement": {"minimum_years": 3.0, "preferred_years": None, "evidence": []},
        }
    return f"""
You are a factual resume and job-description parser. Extract structured data from this {document_type}.

The source document is authoritative. Do not use outside knowledge to add facts, expand abbreviations, or
assume that a related technology is equivalent. If a value is not explicitly supported, use null or an empty
array. Do not guess years, dates, skills, employers, or responsibilities.

Return only valid JSON matching this schema:
{json.dumps(schema)}

Rules:
- `keywords` must be atomic technologies, tools, methods, or domain skills explicitly present in the document.
- Each skill evidence item must be an exact or near-exact short quote from the source.
- For a resume, prefer an explicit total-experience statement only when it clearly refers to the candidate.
- If calculating from dated roles, use the dates in the source and do not double-count overlapping roles.
- Do not count education dates, internships, unrelated dates, or dates without an identifiable role as employment.
- For a job description, put mandatory language such as "required", "must have", or "minimum" in `required_skills`.
- Put language such as "preferred", "nice to have", or "bonus" in `preferred_skills`.
- If the JD does not state a requirement category clearly, use the surrounding wording and preserve uncertainty in evidence.
- `minimum_years` must represent an explicit minimum requirement, not a guess from seniority words such as "senior".
- `preferred_years` must represent an explicit preferred target, not a guess.
- Confidence describes extraction certainty; it is not proof. Keep it between 0 and 1.
- Return an empty array or null when evidence is absent.

Document:
{text[:12000]}
"""


def build_analysis_prompt(
    resume_text: str,
    jd_text: str,
    resume_skills: ResumeSkills,
    jd_skills: JobDescriptionSkills,
) -> str:
    return f"""
You are a careful recruiter and resume-matching analyst.
Compare the resume and job description using only facts supported by the supplied text and extracted skills.
Do not invent candidate experience, achievements, dates, skills, or qualifications.

Return ONLY a single JSON object. No markdown fences, no explanations, no extra text.
Required keys and types:
{{
  "summary": "string",
  "overall_fit": "Strong|Moderate|Weak",
  "strengths": ["string"],
  "required_skills":["string"],
  "nice_to_have_skills":["string"],
  "missing_skills": ["string"],
  "recommendations": ["string"],
  "model_used": "string"
}}

Important:
- Do not include any keys beyond these eight.
- Keep lists as arrays of strings.
- Keep summary short and professional.
- Use exact values like "Strong", "Moderate", or "Weak" in overall_fit.
- Treat required skills as more important than preferred skills.
- Mention a skill as a strength only when the resume contains direct evidence or an exact extracted skill match.
- Mention a skill as missing only when it is required by the JD and not supported by the resume.
- Do not treat similar wording as proof of identical tools unless the relationship is unambiguous.
- If experience is unclear, say that it is unclear instead of estimating it.
- Recommendations must be actionable and truthful; never recommend adding an unsupported skill as if it were real.

Resume text:
{resume_text[:4000]}

Job description text:
{jd_text[:4000]}

Resume skills:
{json.dumps(resume_skills.skills, ensure_ascii=False)}

Job description skills:
{json.dumps(jd_skills.skills, ensure_ascii=False)}
"""


def build_resume_rewrite_prompt(resume_text: str, jd_text: str) -> str:
    return f"""
You are an expert ATS resume editor and factual document formatter.
Rewrite the resume to improve relevance to the job description while preserving the candidate's truth.
The original resume is the only source of candidate facts.

CRITICAL RULES:
1. Start with the candidate name and preserve the contact information.
2. Preserve the original section order and all truthful education, projects, employers, dates, contact details, and languages.
3. Never invent or upgrade a skill, responsibility, metric, employer, title, date, certification, or achievement.
4. Do not add a JD skill merely because it appears in the job description. Add or retain it only if supported by the original resume.
5. You may improve grammar, clarity, ordering, formatting, and keyword placement without changing factual meaning.
6. Keep measurable results only when they already exist in the original resume. Do not create percentages or numbers.
7. Keep the existing skill categories where possible and place supported keywords in the most relevant category.
8. Do not add job-description metadata, responsibilities, benefits, locations, or full sentences as skills.
9. Do not remove truthful content merely because it is not relevant to the JD.
10. Return ONLY the complete updated resume text, with no markdown fences, commentary, placeholders, or introductory sentence.

JOB DESCRIPTION:
{jd_text}

ORIGINAL RESUME:
{resume_text}
"""


# building the  prompt for the calculating the summary 
