"""
FastAPI REST Router for Candidate Intelligence.
Endpoints:
- GET   /api/v1/recruiter/candidates (Fetch 360° candidate intelligence for company applications)
- GET   /api/v1/recruiter/candidates/{id} (Fetch single candidate intelligence profile)
- PATCH /api/v1/recruiter/applications/{id}/status (Update stage, update timeline, generate candidate notification)
- POST  /api/v1/recruiter/applications/{id}/notes (Add private recruiter note)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, Any, List, Optional
from app.api.v1.auth.dependencies import get_current_recruiter
from app.database.company_db import get_company_by_recruiter_id
from app.database.application_db import (
    get_recruiter_company_candidates,
    update_application_stage,
    add_application_note
)
from app.utils.logger import logger

recruiter_candidates_router = APIRouter(prefix="/recruiter", tags=["Candidate Intelligence"])


@recruiter_candidates_router.get("/candidates", response_model=Dict[str, Any])
async def list_recruiter_candidates(
    job_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    education: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    location: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Candidate Intelligence API for Recruiters.
    Returns 360° candidate intelligence objects strictly isolated to applications for the recruiter's company.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    candidates = await get_recruiter_company_candidates(
        company_id=company_id,
        recruiter_id=recruiter_id,
        job_id=job_id,
        status_filter=status,
        experience_filter=experience,
        education_filter=education,
        score_min=score_min,
        location_filter=location,
        search_query=search
    )

    return {
        "candidates": candidates,
        "total": len(candidates),
        "company_name": company.get("company_name", "Company") if company else "Company"
    }


@recruiter_candidates_router.get("/candidates/{candidate_id}", response_model=Dict[str, Any])
async def get_candidate_intelligence_detail(
    candidate_id: str,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Fetches single candidate 360° intelligence profile.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    candidates = await get_recruiter_company_candidates(
        company_id=company_id,
        recruiter_id=recruiter_id,
        search_query=""
    )

    matched = next((c for c in candidates if c["candidate_id"] == candidate_id or c["id"] == candidate_id), None)
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found or unauthorized."
        )

    return matched


@recruiter_candidates_router.patch("/applications/{application_id}/status", response_model=Dict[str, Any])
async def change_application_stage(
    application_id: str,
    payload: Dict[str, Any] = Body(...),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Updates application stage (Applied -> Screening -> Technical Interview -> HR Interview -> Offer -> Hired, Rejected, Withdrawn).
    Automatically updates MongoDB, records timeline event, and generates candidate in-app notification.
    """
    new_stage = payload.get("status") or payload.get("stage") or "Screening"
    recruiter_name = current_recruiter.get("full_name") or current_recruiter.get("email", "Recruiter").split("@")[0]

    updated = await update_application_stage(
        application_id=application_id,
        new_stage=new_stage,
        recruiter_name=recruiter_name
    )
    return updated


@recruiter_candidates_router.post("/applications/{application_id}/notes", response_model=Dict[str, Any])
async def post_recruiter_note(
    application_id: str,
    payload: Dict[str, Any] = Body(...),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Adds a private recruiter note. Notes are strictly hidden from candidates.
    """
    note_text = payload.get("note_text") or payload.get("notes") or ""
    if not note_text or not note_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note text cannot be empty."
        )

    recruiter_name = current_recruiter.get("full_name") or current_recruiter.get("email", "Recruiter").split("@")[0]
    note = await add_application_note(
        application_id=application_id,
        note_text=note_text,
        author_name=recruiter_name
    )
    return note
