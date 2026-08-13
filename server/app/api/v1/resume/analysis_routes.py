"""
FastAPI REST API Router for Candidate AI Resume Analyzer & Resume Health Report.
Endpoints:
- POST /api/v1/resume/analyze (Triggers PyMuPDF & Scorer -> Updates resume_analysis and versions)
- GET  /api/v1/resume/analysis (Gets stored resume_analysis report for candidate)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.auth.dependencies import get_current_candidate
from app.database.resume_db import get_user_resume
from app.database.profile_db import get_candidate_profile
from app.database.database import get_database
from app.services.resume_analyzer_service import analyze_candidate_resume
from app.schemas.analyzer_schemas import ResumeHealthReportSchema
from app.utils.logger import logger

router = APIRouter(prefix="/resume", tags=["Candidate AI Resume Analyzer"])


@router.post("/analyze", response_model=ResumeHealthReportSchema, summary="Run AI Resume Health Analyzer")
async def run_resume_analyzer(current_candidate: dict = Depends(get_current_candidate)):
    """
    Analyzes candidate's uploaded PDF resume & profile, computes Resume Health Score (0-100), updates active analysis, and records a version entry.
    """
    user_id = current_candidate["id"]
    resume = await get_user_resume(user_id)
    if not resume or not resume.get("file_path"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active resume PDF found. Please upload a resume on the My Resume page before running analysis."
        )

    profile = await get_candidate_profile(user_id)
    report = analyze_candidate_resume(resume["file_path"], profile)

    db = get_database()
    
    # Store version in versions array
    version_entry = {
        "version_id": f"v{int(datetime.now(timezone.utc).timestamp())}",
        "upload_date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "resume_health_score": report["resume_health_score"],
        "ats_readiness": report["ats_readiness"],
        "analysis": report
    }

    await db.resumes.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "resume_analysis": report,
                "upload_status": "Ready",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$push": {
                "versions": version_entry
            }
        }
    )

    logger.info(f"📊 Analyzed resume for candidate {user_id}: Health Score {report['resume_health_score']}/100")
    return report


@router.get("/analysis", summary="Get Stored Resume Health Report")
async def get_resume_analysis(current_candidate: dict = Depends(get_current_candidate)):
    """
    Returns stored Resume Health Report for authenticated candidate from MongoDB Atlas.
    """
    user_id = current_candidate["id"]
    resume = await get_user_resume(user_id)
    
    if not resume or not resume.get("resume_analysis") or len(resume.get("resume_analysis", {})) == 0:
        # If no analysis run yet, run initial analysis automatically
        if resume and resume.get("file_path"):
            profile = await get_candidate_profile(user_id)
            report = analyze_candidate_resume(resume["file_path"], profile)
            db = get_database()
            await db.resumes.update_one(
                {"user_id": user_id},
                {"$set": {"resume_analysis": report, "upload_status": "Ready"}}
            )
            return {"analysis": report}
        return {"analysis": None}

    return {"analysis": resume["resume_analysis"]}
