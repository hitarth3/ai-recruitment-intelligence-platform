"""
Resume Engine Service.
Responsible ONLY for Resume Processing & Analytics:
- Resume parsing & skill extraction
- ATS Score calculation
- TF-IDF Cosine Similarity & Skill Gap analysis
- Hiring probability predictions (via ml_engine)
"""

from typing import Dict, Any, List, Optional
from app.ai.ml_engine import calculate_resume_match_ml, extract_skills_from_text, predict_hiring_probability
from app.services.ai_engine import explain_resume_match
from app.utils.logger import logger


def process_resume_screening(
    resume_text: str,
    job_description: str,
    required_skills: List[str] = None,
    job_title: str = "Software Engineer"
) -> Dict[str, Any]:
    """
    Executes complete ML-driven resume screening analysis.
    Uses scikit-learn for scores; delegates explanation to ai_engine.
    """
    # 1. Deterministic ML Evaluation
    ml_result = calculate_resume_match_ml(
        resume_text=resume_text,
        job_description=job_description,
        req_skills=required_skills
    )

    # 2. LLM Explanation
    explanation = explain_resume_match(
        resume_skills=ml_result.get("extracted_skills", []),
        matched_skills=ml_result.get("matched_skills", []),
        missing_skills=ml_result.get("missing_skills", []),
        job_title=job_title,
        overall_score=ml_result["overall_match_score"]
    )

    return {
        "overall_match_score": ml_result["overall_match_score"],
        "tf_idf_similarity": ml_result["tf_idf_similarity"],
        "skill_overlap_ratio": ml_result["skill_overlap_ratio"],
        "extracted_skills": ml_result["extracted_skills"],
        "matched_skills": ml_result["matched_skills"],
        "missing_skills": ml_result["missing_skills"],
        "classification": ml_result["classification"],
        "hiring_probability": ml_result["hiring_probability"],
        "llm_explanation": explanation,
    }
