"""
FastAPI REST Router for Company Profile & Onboarding.
Implements GET /me, POST /, PUT /, and POST /logo endpoints for Recruiters.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.api.v1.auth.dependencies import get_current_recruiter
from app.schemas.company import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyLogoUploadRequest,
    CompanyResponse
)
from app.database.company_db import (
    get_company_by_recruiter_id,
    get_company_by_id,
    create_company_profile,
    update_company_profile,
    update_company_logo
)
from app.utils.logger import logger

company_router = APIRouter(prefix="/company", tags=["Company Profile"])


@company_router.get("/me", response_model=Dict[str, Any])
async def get_my_company(current_recruiter: dict = Depends(get_current_recruiter)):
    """
    Fetches company profile for the logged-in recruiter.
    Returns 404 if profile has not been completed yet.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Please complete company onboarding."
        )
    return company


@company_router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreateRequest,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Creates a new Company Profile document in MongoDB Atlas.
    Default verification_status = "Self Registered".
    Updates Recruiter user document: sets company_id and profile_completed = True.
    """
    recruiter_id = str(current_recruiter["_id"])
    
    # Check if recruiter already has a company
    existing = await get_company_by_recruiter_id(recruiter_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recruiter already has an active Company Profile. Use PUT /company to update."
        )

    company_payload = payload.model_dump()
    new_company = await create_company_profile(recruiter_id, company_payload)
    return new_company


@company_router.put("/", response_model=Dict[str, Any])
async def update_company(
    payload: CompanyUpdateRequest,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Updates existing Company Profile details.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found to update."
        )

    update_data = payload.model_dump(exclude_unset=True)
    updated = await update_company_profile(company["id"], update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company profile."
        )
    return updated


@company_router.post("/logo", response_model=Dict[str, Any])
async def upload_company_logo(
    payload: CompanyLogoUploadRequest,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Uploads or replaces company logo image URI.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found to upload logo."
        )

    updated = await update_company_logo(company["id"], payload.company_logo)
    return updated
