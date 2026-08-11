"""
AI Resume Analyzer Pipeline Module.
Combines deterministic PDF/DOCX extraction, PyMuPDF/python-docx parsing, and rule-based 6-category score calculation with Gemini AI reasoning insights.
Stores results in MongoDB Atlas for persistence and zero redundant Gemini calls.
"""

from typing import Dict, Any
from app.ai.gemini_service import gemini_service
from app.ai.context_builder import build_candidate_context
from app.ai.prompt_builder import build_resume_analysis_prompt
from app.services.resume_analyzer_service import analyze_candidate_resume as deterministic_analyzer
from app.services.improvement_service import generate_dynamic_checklist, generate_priority_recommendations, generate_reach_90_roadmap
from app.database.resume_db import update_resume_analysis
from app.utils.logger import logger


async def run_ai_resume_analysis_pipeline(user_id: str, file_path: str, profile_data: dict, force_reanalyze: bool = False) -> Dict[str, Any]:
    """
    Executes the Complete 5-Stage Resume Analysis Pipeline:
    PDF/DOCX -> Text Parsing -> Deterministic 6-Category Score -> Gemini AI Insights -> MongoDB Persistence.
    """
    # 1. Execute PDF/DOCX Extraction & Rule-based 6-Category Health Score Calculation
    analysis_report = deterministic_analyzer(file_path, profile_data)
    
    # If Document Validation fails (non-resume document, blank PDF, invoice, notes, code file, etc.)
    if not analysis_report.get("is_valid", True):
        logger.warning(f"Invalid non-resume document submitted by user {user_id}: {analysis_report.get('error_message')}")
        return analysis_report

    # 2. Build Structured CandidateContext
    candidate_context = await build_candidate_context(user_id)
    candidate_context["resume_health_score"] = analysis_report["resume_health_score"]
    candidate_context["ats_readiness"] = analysis_report["ats_readiness"]
    candidate_context["score_breakdown"] = analysis_report["score_breakdown"]

    # 3. Call Gemini AI Service for High-Level Natural Language Reasoning Insights (If configured)
    if gemini_service.is_configured:
        prompt = build_resume_analysis_prompt(candidate_context)
        ai_json = gemini_service.generate_json(prompt)
        
        if ai_json and isinstance(ai_json, dict):
            if ai_json.get("summary"):
                analysis_report["summary"] = ai_json["summary"]
            if ai_json.get("strengths") and len(ai_json["strengths"]) > 0:
                analysis_report["strengths"] = ai_json["strengths"]
            if ai_json.get("weaknesses") and len(ai_json["weaknesses"]) > 0:
                analysis_report["weaknesses"] = ai_json["weaknesses"]
            if ai_json.get("formatting_issues") and len(ai_json["formatting_issues"]) > 0:
                analysis_report["formatting_suggestions"] = ai_json["formatting_issues"]

    # 4. Generate 100% Dynamic AI Improvement Checklist & Priority Engine
    resume_doc_mock = {"file_path": file_path, "resume_analysis": analysis_report}
    dynamic_checklist = generate_dynamic_checklist(resume_doc_mock, profile_data)
    priority_recs = generate_priority_recommendations(resume_doc_mock, analysis_report["resume_health_score"])
    reach_90 = generate_reach_90_roadmap(analysis_report["resume_health_score"])

    completed_count = len([c for c in dynamic_checklist if c.get("completed")])

    final_payload = {
        **analysis_report,
        "checklist": dynamic_checklist,
        "completed_checklist_count": completed_count,
        "total_checklist_count": len(dynamic_checklist),
        "recommendations": priority_recs,
        "reach_90_roadmap": reach_90,
    }

    # 5. Store in MongoDB Atlas (Persisted for fast revisits without re-calling Gemini)
    await update_resume_analysis(user_id, final_payload)
    logger.info(f"AI Resume Analysis pipeline completed and saved to MongoDB Atlas for candidate {user_id}.")

    return final_payload
