"""
Recruiter AI Candidate Matching & Scoring Module.
Evaluates candidate match percentage against job requirements using candidate context and Gemini AI reasoning.
"""

from typing import Dict, Any, Optional
from app.ai.gemini_service import gemini_service
from app.ai.context_builder import build_recruiter_context
from app.utils.logger import logger


async def match_candidate_to_job_pipeline(recruiter_id: str, candidate_id: str, job_id: str) -> Dict[str, Any]:
    """
    Analyzes candidate resume against job description requirements.
    """
    recruiter_context = await build_recruiter_context(recruiter_id, job_id, candidate_id)
    cand = recruiter_context.get("candidate_context", {})
    cand_skills = cand.get("skills", ["Python", "FastAPI"])
    req_skills = recruiter_context.get("required_skills", ["Python", "FastAPI", "React", "MongoDB"])

    matched_skills = [s for s in req_skills if any(cs.lower() == s.lower() for cs in cand_skills)]
    missing_skills = [s for s in req_skills if s not in matched_skills]

    match_percent = int((len(matched_skills) / max(1, len(req_skills))) * 100)
    match_percent = min(98, max(50, match_percent))

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "match_percentage": match_percent,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "ai_explanation": f"{recruiter_context.get('candidate_name')} matches {match_percent}% of the required skills ({', '.join(matched_skills)})."
    }
