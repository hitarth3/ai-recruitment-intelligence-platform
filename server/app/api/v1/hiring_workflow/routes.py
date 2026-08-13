"""
FastAPI REST Router for Intelligent Hiring Workflow (Kanban Board).
Endpoints:
- GET   /api/v1/hiring-workflow (Retrieve Kanban pipeline columns & candidate cards for company)
- PATCH /api/v1/hiring-workflow/{applicationId} (Update candidate hiring stage via drag-and-drop)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, Any, List, Optional
from app.api.v1.auth.dependencies import get_current_recruiter
from app.database.company_db import get_company_by_recruiter_id
from app.database.application_db import get_dynamic_hiring_workflow_kanban, update_application_stage_dynamic
from app.utils.logger import logger

hiring_workflow_router = APIRouter(prefix="/hiring-workflow", tags=["Hiring Workflow"])


@hiring_workflow_router.get("", response_model=Dict[str, Any])
@hiring_workflow_router.get("/", response_model=Dict[str, Any])
async def get_hiring_workflow_pipeline(
    job_id: Optional[str] = Query(None),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Retrieves real MongoDB candidate applications grouped into dynamic Kanban stage columns for a specific job requisition.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    data = await get_dynamic_hiring_workflow_kanban(job_id=job_id or "", company_id=company_id, recruiter_id=recruiter_id)
    data["company_name"] = company.get("company_name", "Company") if company else "Company"
    return data


@hiring_workflow_router.patch("/{application_id}", response_model=Dict[str, Any])
async def move_candidate_hiring_stage(
    application_id: str,
    payload: Dict[str, Any] = Body(...),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Drag & Drop Stage Transition Handler.
    Updates candidate stage in MongoDB, appends event to application timeline,
    and generates candidate in-app notification. Auto-archives Selected / Rejected candidates to Hiring History.
    """
    new_stage = payload.get("status") or payload.get("stage") or payload.get("new_stage")
    if not new_stage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target stage is required."
        )

    action_type = payload.get("action_type") or "Moved Stage"
    recruiter_name = current_recruiter.get("full_name") or current_recruiter.get("email", "Recruiter").split("@")[0]

    updated = await update_application_stage_dynamic(
        application_id=application_id,
        target_stage=new_stage,
        recruiter_name=recruiter_name,
        action_type=action_type
    )

    return {
        "message": f"Candidate moved to '{updated.get('current_stage')}' stage.",
        "application": updated
    }
