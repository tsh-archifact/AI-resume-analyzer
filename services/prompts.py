import json

from schemas.resume import JobDescriptionSkills, ResumeSkills


def build_skill_extraction_prompt(text: str, label: str) -> str:
    print("this is the label :" , label)
    print("this is the text : ", text )
    
    return f"""
Extract a clean list of skills from the {label} text below.

CRITICAL RULES:
1. EXTRACT ATOMIC SKILLS ONLY: e.g., "Python", "Node.js", "Express.js", "RESTful APIs".
2. NO SENTENCES OR PHRASES: Convert "Build backend services using Express.js" to simply "Express.js".
3. NO METADATA OR HEADERS: Ignore "Job Title:", "Location: Remote", "KEY RESPONSIBILITIES", "Department".
4. NO EDUCATION OR LOCATIONS: Ignore degrees, universities, cities, and countries.
5. CLEAN PREFIXES: If you see "Programming Language : Python3", extract ONLY "Python 3".

Return ONLY a valid JSON object matching this schema exactly:
{{"skills": ["Skill 1", "Skill 2", "Skill 3"]}}

Text:
{text[:6000]}
"""


def build_analysis_prompt(
    resume_text: str,
    jd_text: str,
    resume_skills: ResumeSkills,
    jd_skills: JobDescriptionSkills,
) -> str:
    return f"""
You are an expert recruiter and resume reviewer.
Compare the resume and job description.

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
You are an expert ATS Resume Optimization Engine and resume formatter.
Your task is to return a complete, polished resume that keeps the candidate truthful and follows the original resume's section order.

CRITICAL RULES:
1. START WITH THE CANDIDATE NAME: The first line must be the candidate's name, followed by one contact line.
2. KEEP THE ORIGINAL SECTION ORDER: Profile, Education, Projects, Skills, Languages, and any other existing sections must stay in the same order.
3. PRESERVE REAL CONTENT: Do not remove education, projects, phone number, email, location, or languages. Never use placeholders like "...[rest of resume]...".
4. IMPROVE FORMATTING: Add sensible line breaks between sections and entries. Keep a clean text layout suitable for a DOCX resume.
5. PROFILE: Keep or lightly improve the Profile into one clear professional summary paragraph. Do not add a separate "Professional Summary" section.
6. TARGET SKILLS ONLY FOR ATS KEYWORDS: Add missing JD hard skills, tools, frameworks, databases, and technical terms inside the existing Skills section only.
7. DO NOT ADD JD METADATA AS SKILLS: Never add job title, department, employment type, location, responsibilities, full sentences, education names, or city/country names as skills.
8. MAINTAIN SKILL CATEGORIES: Keep existing categories like "Programming Language", "Core Skill", "Databases", and "Soft Skills". Add new technical keywords to the most relevant existing category.
9. RAW TEXT ONLY: Return ONLY the complete, updated resume text. Do not include markdown fences (```), bolding, conversational filler, a document title, or prefixes like "Here is the updated resume:".

JOB DESCRIPTION:
{jd_text}

ORIGINAL RESUME:
{resume_text}
"""


# building the  prompt for the calculating the summary 
