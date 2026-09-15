import json
import re
from typing import Any

from config.llm_setup import get_llm_api_key, get_llm_client, get_llm_model
from schemas.agent import (
    ATSAuditResult,
    ATSCritiqueItem,
    CritiqueCategory,
    CritiqueSeverity,
)
from services.skill_service import extract_skills_from_text, normalize_skill


# Powerful action verbs commonly favored by ATS parsers and hiring managers
_STRONG_ACTION_VERBS = {
    "accelerated", "accomplished", "achieved", "administered", "advanced",
    "analyzed", "architected", "automated", "built", "centralized",
    "championed", "collaborated", "configured", "consolidated", "constructed",
    "created", "customized", "decreased", "delivered", "deployed",
    "designed", "developed", "devised", "directed", "eliminated",
    "engineered", "enhanced", "established", "executed", "expanded",
    "expedited", "formulated", "founded", "generated", "guided",
    "implemented", "improved", "increased", "initiated", "innovated",
    "installed", "instituted", "integrated", "introduced", "launched",
    "led", "leveraged", "managed", "maximized", "mentored",
    "migrated", "minimized", "modernized", "negotiated", "optimized",
    "orchestrated", "overhauled", "oversaw", "partnered", "pioneered",
    "planned", "produced", "programmed", "promoted", "re-engineered",
    "reduced", "refined", "refactored", "resolved", "restructured",
    "revamped", "saved", "scaled", "simplified", "spearheaded",
    "standardized", "streamlined", "strengthened", "supervised", "surpassed",
    "transformed", "troubleshot", "upgraded", "validated", "yielded",
}

# Regex patterns for identifying quantified metrics (%, $, scale, performance numbers)
_METRIC_PATTERNS = [
    re.compile(r"\b\d+(?:\.\d+)?%\b"),                                      # percentages (e.g. 40%, 12.5%)
    re.compile(r"\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*[kKmMbB])?\b"),         # currency ($50k, $1.2M)
    re.compile(r"\b\d+(?:\.\d+)?\s*[xX]\b"),                                 # multipliers (3x, 10x)
    re.compile(r"\b\d{1,3}(?:,\d{3})+\b"),                                  # large comma numbers (10,000)
    re.compile(r"\b\d+\+?\s*(?:users|clients|customers|accounts|qps|rps|ms|seconds|hours|engineers|members|teams|projects)\b", re.I),
]

_BULLET_LINE_PATTERN = re.compile(r"^\s*[-*•–—]\s*(.+)$", re.MULTILINE)


def _extract_bullets(text: str) -> list[str]:
    """Extract bullet points from text, falling back to non-empty lines if bullets aren't formatted with standard symbols."""
    bullets = _BULLET_LINE_PATTERN.findall(text)
    if bullets:
        return [b.strip() for b in bullets if b.strip()]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [line for line in lines if len(line) > 25 and not line.endswith(":")]


def _calculate_keyword_coverage(draft_text: str, target_skills: list[str]) -> tuple[float, list[str], list[str]]:
    """Determine which target skills are present in the draft and return the coverage score."""
    if not target_skills:
        return 100.0, [], []

    draft_lower = draft_text.lower()
    matched = []
    missing = []

    for skill in target_skills:
        clean = normalize_skill(skill)
        if not clean:
            continue
        # Check either exact word boundary or substring match for compound skills
        escaped = re.escape(clean.lower())
        if re.search(r"(?:^|[\s,;|/()\-._])" + escaped + r"(?:$|[\s,;|/()\-._])", draft_lower):
            matched.append(clean)
        else:
            missing.append(clean)

    total = len(matched) + len(missing)
    score = round((len(matched) / total) * 100.0, 1) if total > 0 else 100.0
    return score, matched, missing


def _evaluate_metrics(bullets: list[str]) -> tuple[float, list[ATSCritiqueItem]]:
    """Evaluate whether bullet points contain quantified impact metrics."""
    if not bullets:
        return 30.0, [
            ATSCritiqueItem(
                category=CritiqueCategory.METRICS,
                severity=CritiqueSeverity.HIGH,
                issue="No distinct experience bullet points found to measure impact.",
                suggestion="Format experience entries as bullet points starting with action verbs and include metrics (e.g., % improvement, scale).",
            )
        ]

    bullets_with_metrics = 0
    unquantified_examples = []

    for bullet in bullets:
        has_metric = any(pattern.search(bullet) for pattern in _METRIC_PATTERNS)
        if has_metric:
            bullets_with_metrics += 1
        elif len(unquantified_examples) < 2:
            unquantified_examples.append(bullet[:90] + ("..." if len(bullet) > 90 else ""))

    metric_ratio = bullets_with_metrics / len(bullets)
    score = round(min(metric_ratio * 125.0, 100.0), 1)  # 80%+ bullets with metrics yields 100

    critiques: list[ATSCritiqueItem] = []
    if score < 70.0:
        suggestion_msg = "Add quantified results (e.g. 'reduced latency by 35%', 'scaled to 50k users') to bullets."
        if unquantified_examples:
            suggestion_msg += f" For example, quantify: '{unquantified_examples[0]}'"
        critiques.append(
            ATSCritiqueItem(
                category=CritiqueCategory.METRICS,
                severity=CritiqueSeverity.HIGH if score < 40 else CritiqueSeverity.MEDIUM,
                issue=f"Only {bullets_with_metrics} of {len(bullets)} bullet points contain quantified metrics.",
                suggestion=suggestion_msg,
            )
        )

    return score, critiques


def _evaluate_structure_and_verbs(bullets: list[str], draft_text: str) -> tuple[float, list[ATSCritiqueItem], list[str]]:
    """Evaluate action verbs, standard section headers, and bullet clarity."""
    critiques: list[ATSCritiqueItem] = []
    strengths: list[str] = []

    # Check for standard ATS section headers
    lower_text = draft_text.lower()
    headers_found = [
        h for h in ["experience", "education", "skills", "projects", "summary"]
        if re.search(r"(?:^|\n)\s*(?:#+\s*)?" + h + r"\b", lower_text)
    ]
    header_score = min((len(headers_found) / 3.0) * 100.0, 100.0)

    # Check action verbs on bullets
    verb_bullets_count = 0
    weak_verb_examples = []

    for bullet in bullets:
        first_word = re.sub(r"^[^\w]+", "", bullet).split()[0].lower() if bullet.split() else ""
        if first_word in _STRONG_ACTION_VERBS:
            verb_bullets_count += 1
        elif len(weak_verb_examples) < 2 and first_word:
            weak_verb_examples.append(first_word)

    verb_score = (verb_bullets_count / len(bullets) * 100.0) if bullets else 50.0
    structure_score = round(0.5 * header_score + 0.5 * verb_score, 1)

    if verb_score < 70.0:
        critiques.append(
            ATSCritiqueItem(
                category=CritiqueCategory.ACTION_VERBS,
                severity=CritiqueSeverity.MEDIUM,
                issue="Multiple bullet points start with passive words or responsibilities rather than strong action verbs.",
                suggestion="Begin each bullet point with a high-impact past-tense verb (e.g., 'Spearheaded', 'Optimized', 'Engineered', 'Automated').",
            )
        )
    else:
        strengths.append("Strong action-verb coverage across experience bullet points.")

    if len(headers_found) >= 3:
        strengths.append(f"Clear ATS-friendly section headers detected ({', '.join(headers_found).title()}).")

    return structure_score, critiques, strengths


def _get_llm_semantic_critique(draft_text: str, jd_text: str) -> list[ATSCritiqueItem]:
    """Optional LLM pass to discover high-level alignment gaps; gracefully skipped if LLM is unavailable."""
    if not get_llm_api_key():
        return []

    prompt = f"""You are an expert ATS auditor. Analyze this resume draft against the target job description.
Identify up to 3 high-priority flaws or missing alignments.

Return ONLY a strict JSON object formatted like:
{{
  "critiques": [
    {{
      "category": "relevance",
      "severity": "high",
      "issue": "Brief description of the gap",
      "suggestion": "Specific, actionable instruction to resolve it"
    }}
  ]
}}

RESUME DRAFT:
{draft_text[:3500]}

JOB DESCRIPTION:
{jd_text[:2500]}
"""
    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a strict ATS auditor. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            return []
        data = json.loads(content)
        items = []
        for item in data.get("critiques", []):
            if isinstance(item, dict) and "issue" in item and "suggestion" in item:
                cat = item.get("category", "relevance").lower()
                sev = item.get("severity", "medium").lower()
                items.append(
                    ATSCritiqueItem(
                        category=CritiqueCategory(cat) if cat in CritiqueCategory.__members__.values() else CritiqueCategory.RELEVANCE,
                        severity=CritiqueSeverity(sev) if sev in CritiqueSeverity.__members__.values() else CritiqueSeverity.MEDIUM,
                        issue=str(item["issue"]),
                        suggestion=str(item["suggestion"]),
                    )
                )
        return items
    except Exception:
        # LLM semantic critique is an enhancement; deterministic auditor ensures reliability
        return []


def audit_resume_draft(
    draft_text: str,
    jd_text: str,
    target_skills: list[str] | None = None,
    use_llm_critique: bool = False,
) -> ATSAuditResult:
    """
    Evaluates a resume draft against a target job description and returns an ATSAuditResult.
    
    Composite Score Weights:
    - 40% Keyword Coverage
    - 30% Metric & Quantification Density
    - 30% Structure, Headers & Action Verbs
    """
    if target_skills is None:
        target_skills = extract_skills_from_text(jd_text, section_name="job_description_skills")

    keyword_score, matched_skills, missing_skills = _calculate_keyword_coverage(draft_text, target_skills)
    bullets = _extract_bullets(draft_text)
    metric_score, metric_critiques = _evaluate_metrics(bullets)
    structure_score, structure_critiques, strengths = _evaluate_structure_and_verbs(bullets, draft_text)

    all_critiques = list(metric_critiques + structure_critiques)

    if missing_skills:
        top_missing = missing_skills[:6]
        all_critiques.insert(
            0,
            ATSCritiqueItem(
                category=CritiqueCategory.KEYWORDS,
                severity=CritiqueSeverity.HIGH if keyword_score < 60 else CritiqueSeverity.MEDIUM,
                issue=f"Draft is missing {len(missing_skills)} key technical skill(s) from the target job: {', '.join(top_missing)}.",
                suggestion=f"Integrate matching experience or core competencies for: {', '.join(top_missing)}.",
            ),
        )
    else:
        strengths.append("Excellent keyword alignment with all target job competencies.")

    if keyword_score >= 80.0:
        strengths.append(f"High technical keyword match ({keyword_score}%).")
    if metric_score >= 75.0:
        strengths.append(f"Well-quantified achievements across experience entries ({metric_score}%).")

    if use_llm_critique:
        semantic_critiques = _get_llm_semantic_critique(draft_text, jd_text)
        all_critiques.extend(semantic_critiques)

    overall_score = round(
        (0.40 * keyword_score) + (0.30 * metric_score) + (0.30 * structure_score),
        1,
    )

    return ATSAuditResult(
        overall_score=overall_score,
        keyword_score=keyword_score,
        metric_score=metric_score,
        structure_score=structure_score,
        matched_keywords=matched_skills,
        missing_keywords=missing_skills,
        strengths=strengths,
        critiques=all_critiques,
    )
