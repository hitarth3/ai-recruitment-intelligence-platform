"""
FastAPI REST Router for the Workflow Engine.
All recruiter actions (Approve & Advance, Reject, Skip, Repeat, Override AI)
route through this router which delegates to the centralized WorkflowEngine service.
Backend is the single source of truth. NO frontend state controls stage transitions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
from app.api.v1.auth.dependencies import get_current_user
from app.services.workflow_engine import (
    advance_workflow_stage,
    reject_application,
    skip_stage,
    save_execution_result,
    get_application_workflow_state,
)
from app.database.application_db import get_application_by_id
from app.utils.logger import logger

workflow_router = APIRouter(prefix="/workflow", tags=["Workflow Engine"])


def _get_recruiter_name(current_user: dict) -> str:
    return current_user.get("full_name") or current_user.get("name") or current_user.get("email", "Recruiter")


@workflow_router.get("/state/{application_id}", response_model=Dict[str, Any])
async def get_workflow_state(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Returns live workflow state for an application: current stage, stage statuses,
    timeline, execution results, and audit log.
    """
    state = await get_application_workflow_state(application_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    return state


@workflow_router.post("/advance", response_model=Dict[str, Any])
async def advance_stage(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Advances candidate to the next (or specified) hiring stage.
    Marks current stage Completed, activates next stage, appends timeline event,
    generates candidate notification, and updates MongoDB Atlas atomically.
    """
    application_id = payload.get("application_id")
    target_stage = payload.get("target_stage")  # Optional: specific target stage name
    notes = payload.get("notes", "")

    if not application_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application_id is required.")

    recruiter_id = str(current_user.get("_id", ""))
    recruiter_name = _get_recruiter_name(current_user)

    try:
        result = await advance_workflow_stage(
            application_id=application_id,
            recruiter_id=recruiter_id,
            recruiter_name=recruiter_name,
            notes=notes,
            target_stage_name=target_stage,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "message": f"Candidate advanced to '{result['current_stage']}'.",
        "result": result,
    }


@workflow_router.post("/reject", response_model=Dict[str, Any])
async def reject_candidate(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Rejects a candidate application. Sets status to Rejected, appends timeline event,
    generates candidate notification, and archives to db.hiring_history.
    """
    application_id = payload.get("application_id")
    reason = payload.get("reason", "")

    if not application_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application_id is required.")

    recruiter_id = str(current_user.get("_id", ""))
    recruiter_name = _get_recruiter_name(current_user)

    try:
        result = await reject_application(
            application_id=application_id,
            recruiter_id=recruiter_id,
            recruiter_name=recruiter_name,
            reason=reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"message": "Candidate application rejected and archived.", "result": result}


@workflow_router.post("/skip", response_model=Dict[str, Any])
async def skip_workflow_stage(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Skips a hiring stage and activates the next one.
    """
    application_id = payload.get("application_id")
    stage_name = payload.get("stage_name")
    reason = payload.get("reason", "")

    if not application_id or not stage_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application_id and stage_name are required.")

    recruiter_id = str(current_user.get("_id", ""))
    recruiter_name = _get_recruiter_name(current_user)

    try:
        result = await skip_stage(
            application_id=application_id,
            stage_name=stage_name,
            recruiter_id=recruiter_id,
            recruiter_name=recruiter_name,
            reason=reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"message": f"Stage '{stage_name}' skipped.", "result": result}


@workflow_router.post("/override-ai", response_model=Dict[str, Any])
async def override_ai_score(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Allows recruiter to override the AI-generated match score for a stage.
    Saves override result to stage_executions and appends timeline event.
    """
    application_id = payload.get("application_id")
    stage_name = payload.get("stage_name", "AI Resume Screening")
    override_score = payload.get("override_score")
    notes = payload.get("notes", "")

    if not application_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application_id is required.")

    recruiter_name = _get_recruiter_name(current_user)

    result = await save_execution_result(
        application_id=application_id,
        stage_name=stage_name,
        engine_type="Resume Engine",
        result_payload={
            "override_score": override_score,
            "override_notes": notes,
            "overridden_by": recruiter_name,
            "type": "RECRUITER_OVERRIDE",
        },
        performed_by=recruiter_name,
        execution_status="Overridden",
    )

    return {"message": "AI score override saved successfully.", "result": result}


@workflow_router.post("/save-execution", response_model=Dict[str, Any])
async def save_stage_execution_result(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Saves stage execution result from any engine (Assessment, Interview, Portfolio, Offer).
    Called by candidate execution portal when submitting a stage.
    """
    application_id = payload.get("application_id")
    stage_name = payload.get("stage_name")
    engine_type = payload.get("engine_type", "Assessment Engine")
    result_payload = payload.get("result_payload", {})
    execution_status = payload.get("execution_status", "Submitted")

    if not application_id or not stage_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application_id and stage_name are required.")

    performed_by = _get_recruiter_name(current_user)

    result = await save_execution_result(
        application_id=application_id,
        stage_name=stage_name,
        engine_type=engine_type,
        result_payload=result_payload,
        performed_by=performed_by,
        execution_status=execution_status,
    )

    return {"message": "Stage execution result saved.", "result": result}
