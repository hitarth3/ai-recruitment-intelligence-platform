"""
FastAPI REST Router for Candidate Settings Management.
Endpoints:
- GET    /api/v1/candidate/settings
- PUT    /api/v1/candidate/settings/{section}
- POST   /api/v1/candidate/settings/change-password
- DELETE /api/v1/candidate/settings/account
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any
from pydantic import BaseModel, Field
from app.api.v1.auth.dependencies import get_current_candidate
from app.database.settings_db import (
    get_candidate_settings,
    update_candidate_settings_section,
    change_candidate_password,
    delete_candidate_account
)
from app.utils.logger import logger

router = APIRouter(prefix="/candidate/settings", tags=["Candidate Settings"])


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


@router.get("", summary="Get Candidate Settings")
async def get_settings(current_candidate: dict = Depends(get_current_candidate)):
    """
    Returns candidate settings document from MongoDB Atlas.
    """
    user_id = current_candidate["id"]
    settings = await get_candidate_settings(user_id)
    return settings


@router.put("/{section}", summary="Update Candidate Settings Section")
async def update_settings_section(
    section: str,
    payload: Dict[str, Any] = Body(...),
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Updates specific candidate settings section:
    'account', 'notifications', 'privacy', 'appearance', 'preferences', 'connected_accounts'
    """
    user_id = current_candidate["id"]
    valid_sections = ["account", "notifications", "privacy", "appearance", "preferences", "connected_accounts"]
    if section not in valid_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid settings section '{section}'. Valid options: {valid_sections}"
        )

    updated = await update_candidate_settings_section(user_id, section, payload)
    return updated


@router.post("/change-password", summary="Change Account Password")
async def change_password(
    body: ChangePasswordSchema,
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Validates current password and updates candidate account password in MongoDB Atlas.
    """
    if body.new_password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match."
        )

    user_id = current_candidate["id"]
    try:
        res = await change_candidate_password(user_id, body.current_password, body.new_password)
        return res
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )


@router.delete("/account", summary="Permanently Delete Account")
async def delete_account(
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Permanently deletes candidate account and all associated data from MongoDB Atlas.
    """
    user_id = current_candidate["id"]
    res = await delete_candidate_account(user_id)
    return res
