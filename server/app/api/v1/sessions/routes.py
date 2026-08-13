"""
FastAPI REST Router for Recruitment Session Manager.
Enforces session security, token issuance, and validation for stage execution.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
from app.api.v1.auth.dependencies import get_current_user
from app.database.recruitment_session_db import (
    create_recruitment_session,
    validate_recruitment_session
)

sessions_router = APIRouter(prefix="/sessions", tags=["Recruitment Session Manager"])


@sessions_router.post("/create", response_model=Dict[str, Any])
async def create_session(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Creates an authorized recruitment execution session for an application & stage.
    """
    application_id = payload.get("application_id")
    candidate_id = payload.get("candidate_id")
    recruiter_id = payload.get("recruiter_id")
    job_id = payload.get("job_id")
    stage_id = payload.get("stage_id", "current-stage")
    engine_type = payload.get("engine_type", "Resume Engine")

    if not application_id or not candidate_id or not job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="application_id, candidate_id, and job_id are required."
        )

    session = await create_recruitment_session(
        application_id=application_id,
        candidate_id=candidate_id,
        recruiter_id=recruiter_id or str(current_user["_id"]),
        job_id=job_id,
        stage_id=stage_id,
        engine_type=engine_type
    )

    return {"message": "Recruitment session authorized.", "session": session}


@sessions_router.get("/validate/{session_id}", response_model=Dict[str, Any])
async def validate_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Validates user ownership and expiration of execution session.
    """
    user_id = str(current_user["_id"])
    session = await validate_recruitment_session(session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid, expired, or unauthorized recruitment session."
        )
    return {"valid": True, "session": session}
