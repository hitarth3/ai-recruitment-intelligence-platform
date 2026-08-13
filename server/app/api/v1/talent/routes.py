"""
FastAPI REST Router for Talent Discovery & Saved Talent.
Endpoints:
- GET    /api/v1/talent/search (Global database candidate search with privacy enforcement)
- GET    /api/v1/talent/bookmarks (Retrieve saved talent pool)
- GET    /api/v1/talent/{id} (Retrieve candidate profile with privacy enforcement)
- POST   /api/v1/talent/bookmark (Bookmark candidate to talent pool)
- DELETE /api/v1/talent/bookmark/{id} (Remove candidate from talent pool)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, Any, List, Optional
from app.api.v1.auth.dependencies import get_current_recruiter
from app.database.company_db import get_company_by_recruiter_id
from app.database.talent_discovery_db import (
    search_talent,
    bookmark_talent,
    remove_bookmark,
    get_bookmarked_talent
)
from app.utils.logger import logger

talent_router = APIRouter(prefix="/talent", tags=["Talent Discovery"])


@talent_router.get("/search", response_model=Dict[str, Any])
async def discover_talent(
    search: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    education: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    open_to_work: Optional[bool] = Query(False),
    sort_by: Optional[str] = Query("score"),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Global Talent Discovery Endpoint across all candidate profiles in MongoDB Atlas.
    Not limited to applicants. Enforces candidate privacy controls.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    candidates = await search_talent(
        recruiter_id=recruiter_id,
        company_id=company_id,
        search_query=search,
        skills_filter=skills,
        experience_filter=experience,
        education_filter=education,
        location_filter=location,
        score_min=score_min,
        open_to_work_only=open_to_work,
        sort_by=sort_by
    )

    return {
        "candidates": candidates,
        "total": len(candidates)
    }


@talent_router.get("/bookmarks", response_model=Dict[str, Any])
async def get_saved_talent_pool(current_recruiter: dict = Depends(get_current_recruiter)):
    """
    Retrieves recruiter's Saved Talent pool.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    bookmarked = await get_bookmarked_talent(recruiter_id=recruiter_id, company_id=company_id)
    return {
        "saved_talent": bookmarked,
        "total": len(bookmarked)
    }


@talent_router.get("/{candidate_id}", response_model=Dict[str, Any])
async def get_talent_profile_by_id(
    candidate_id: str,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Retrieves candidate profile for Talent Discovery view.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    candidates = await search_talent(
        recruiter_id=recruiter_id,
        company_id=company_id,
        search_query=""
    )

    matched = next((c for c in candidates if c["candidate_id"] == candidate_id or c["id"] == candidate_id), None)
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found."
        )

    return matched


@talent_router.post("/bookmark", response_model=Dict[str, Any])
async def save_candidate_to_talent_pool(
    payload: Dict[str, Any] = Body(...),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Bookmarks candidate into recruiter's Saved Talent pool.
    """
    candidate_id = payload.get("candidate_id")
    if not candidate_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate ID is required."
        )

    recruiter_id = str(current_recruiter["_id"])
    reason = payload.get("reason", "Saved for future role")

    res = await bookmark_talent(recruiter_id=recruiter_id, candidate_id=candidate_id, reason=reason)
    return res


@talent_router.delete("/bookmark/{candidate_id}", response_model=Dict[str, Any])
async def remove_candidate_from_talent_pool(
    candidate_id: str,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Removes candidate from recruiter's Saved Talent pool.
    """
    recruiter_id = str(current_recruiter["_id"])
    removed = await remove_bookmark(recruiter_id=recruiter_id, candidate_id=candidate_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark record not found."
        )
    return {"message": "Candidate removed from Saved Talent pool.", "candidate_id": candidate_id}
