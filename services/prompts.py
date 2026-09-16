import json

from schemas.resume import JobDescriptionSkills, ResumeSkills


def build_profile_extraction_prompt(text: str, document_type: str) -> str:

    if document_type == "resume":
        schema = {
            "keywords": ["Python"],
            "skills": [
                {
                    "name": "Python",
                    "category": "technical",
                    "years_experience": None,
                    "evidence": [
                        {
                            "text": "...",
                            "confidence": 0.9
                        }
                    ]
                }
            ],
            "total_years_experience": None,
            "experience_periods": [],
            "experience_evidence": []
        }

    else:
        schema = {
            "keywords": ["Python"],
            "required_skills": [
                {
                    "name": "Python",
                    "category": "technical",
                    "years_experience": None,
                    "evidence": []
                }
            ],
            "preferred_skills": [],
            "experience_requirement": {
                "minimum_years": None,
                "preferred_years": None,
                "evidence": []
            }
        }

    return f"""
You are a factual resume and job-description parser.

Extract structured information ONLY from the provided source document.

The source document is authoritative. Do not use outside knowledge to add facts,
infer experience, or assume that a related technology is equivalent.

Return only valid JSON matching this schema:

{json.dumps(schema)}

GENERAL RULES:

1. Search the ENTIRE document.
   Do not restrict extraction to a section named "Skills".

2. For resumes, extract skills and technologies from ALL relevant sections,
   including:
   - Profile / Summary
   - Skills
   - Work Experience
   - Projects
   - Project descriptions
   - Responsibilities
   - Certifications
   - Education, when a skill is explicitly stated
   - Achievements and other technical sections

3. If a technology is explicitly mentioned in a project description,
   responsibility, or experience description, it MUST be considered as
   resume skill evidence even if it is absent from the dedicated Skills section.

4. Do not infer a skill merely because another related skill is present.

   Example:
   MongoDB does not mean the resume explicitly says PostgreSQL.
   Python does not mean the resume explicitly says Django.
   HTML does not mean the resume explicitly says CSS.

5. However, if the source explicitly contains the technology anywhere in the
   document, extract it.

6. Preserve the wording used by the source document.
   Do not normalize aliases during extraction.

   Example:
   "Python3" should remain "Python3".
   "SQL Lite" should remain "SQL Lite".

7. Skill evidence must be an exact or near-exact short quote from the source.

8. A project description is valid evidence of practical use of a technology.

9. Do not invent years of experience.

10. Only calculate years of experience when supported by explicit dates or
    explicit experience statements.

11. Do not count education dates, unrelated dates, or project dates as employment.

12. Confidence represents extraction certainty, not skill proficiency.

13. Return null or an empty array when evidence is absent.

DOCUMENT:

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
