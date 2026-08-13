"""
FastAPI REST Router for Candidate Job Applications.
Implements POST /api/v1/applications, GET /api/v1/applications/me, GET /api/v1/applications/count, DELETE /api/v1/applications/{id}.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from app.api.v1.auth.dependencies import get_current_candidate
from app.schemas.application import ApplicationCreateRequest
from app.database.application_db import (
    create_application,
    get_candidate_applications,
    withdraw_application,
    get_candidate_application_count
)

applications_router = APIRouter(prefix="/applications", tags=["Candidate Job Applications"])


@applications_router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@applications_router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def submit_job_application(
    payload: ApplicationCreateRequest,
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Submits a candidate application for a Published Job Requisition.
    Automatically attaches candidate_id, job_id, company_id, recruiter_id, active resume_version_id,
    and generates an in-app notification.
    """
    candidate_id = str(current_candidate["_id"])
    app_doc = await create_application(
        candidate_id=candidate_id,
        job_id=payload.job_id,
        notes=payload.notes
    )
    return app_doc


@applications_router.get("/me", response_model=Dict[str, Any])
async def get_my_applications(
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Fetches all applications submitted by the authenticated candidate with joined job details.
    """
    candidate_id = str(current_candidate["_id"])
    apps = await get_candidate_applications(candidate_id)
    return {
        "applications": apps,
        "total": len(apps)
    }


@applications_router.get("/count", response_model=Dict[str, Any])
async def get_my_applications_count(
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Lightweight endpoint returning total count of applications submitted by candidate.
    """
    candidate_id = str(current_candidate["_id"])
    count = await get_candidate_application_count(candidate_id)
    return {"count": count}


@applications_router.delete("/{application_id}", response_model=Dict[str, Any])
async def withdraw_job_application(
    application_id: str,
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Withdraws candidate application if status is 'Applied' or 'Screening'.
    Updates status to 'Withdrawn' and decrements applications_count on job document.
    """
    candidate_id = str(current_candidate["_id"])
    updated_app = await withdraw_application(application_id, candidate_id)
    return updated_app


# --- RECRUITER APPLICATION & HIRING HISTORY ENDPOINTS ---
from app.api.v1.auth.dependencies import get_current_recruiter
from app.database.company_db import get_company_by_recruiter_id
from app.database.application_db import (
    get_job_applications,
    update_application_stage_dynamic,
    get_hiring_history
)
from fastapi import Query, Body


@applications_router.get("/job/{job_id}", response_model=Dict[str, Any])
async def list_job_applications_recruiter(
    job_id: str,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Fetches candidate applications submitted specifically for a given job_id.
    Excludes candidates who have reached final 'Selected', 'Rejected', or 'Withdrawn' status (archived in Hiring History).
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    candidates = await get_job_applications(job_id=job_id, company_id=company_id, recruiter_id=recruiter_id)
    return {
        "job_id": job_id,
        "candidates": candidates,
        "total": len(candidates)
    }


@applications_router.patch("/{application_id}/stage", response_model=Dict[str, Any])
async def transition_candidate_stage(
    application_id: str,
    payload: Dict[str, Any] = Body(...),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Dynamic Stage Transition Handler.
    - Moves candidate to target stage, skip stage, or override AI.
    - Appends to timeline history with timestamp, stage, action_type, and recruiter name.
    - Generates candidate in-app notification.
    - Auto-archives candidate to Hiring History if Selected, Rejected, or Withdrawn.
    """
    target_stage = payload.get("stage") or payload.get("target_stage") or payload.get("status") or "Screening"
    action_type = payload.get("action_type") or "Moved Stage"
    recruiter_name = current_recruiter.get("full_name") or current_recruiter.get("email", "Recruiter").split("@")[0]

    updated = await update_application_stage_dynamic(
        application_id=application_id,
        target_stage=target_stage,
        recruiter_name=recruiter_name,
        action_type=action_type
    )
    return updated


@applications_router.get("/hiring-history", response_model=Dict[str, Any])
async def list_hiring_history_records(
    decision: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Retrieves completed historical hiring decisions (Selected, Rejected, Withdrawn) permanently archived in MongoDB Atlas.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    history = await get_hiring_history(
        company_id=company_id,
        recruiter_id=recruiter_id,
        decision_filter=decision,
        search_query=search
    )
    return {
        "hiring_history": history,
        "total": len(history)
    }
