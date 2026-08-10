"""
MongoDB Database Handler for Recruitment Sessions & Dynamic Stage Executions.
Operates on `recruitment_sessions` and `stage_executions` collections in MongoDB Atlas.
"""

from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import Dict, Any, List, Optional
import uuid
from app.database.database import get_database
from app.utils.logger import logger


def format_doc(doc: dict) -> dict:
    if not doc:
        return {}
    doc["id"] = str(doc.get("_id", ""))
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def create_recruitment_session(
    application_id: str,
    candidate_id: str,
    recruiter_id: str,
    job_id: str,
    stage_id: str,
    engine_type: str,
    expiry_hours: int = 24
) -> dict:
    """
    Creates a secure, authorized recruitment execution session in MongoDB Atlas.
    """
    db = get_database()
    session_id = f"session-{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expiry_hours)

    session_doc = {
        "session_id": session_id,
        "application_id": application_id,
        "candidate_id": candidate_id,
        "recruiter_id": recruiter_id,
        "job_id": job_id,
        "stage_id": stage_id,
        "engine_type": engine_type,
        "is_active": True,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }

    await db.recruitment_sessions.insert_one(session_doc)
    return format_doc(session_doc)


async def validate_recruitment_session(session_id: str, user_id: str) -> Optional[dict]:
    """
    Validates execution session ownership, activity status, and expiration.
    """
    db = get_database()
    doc = await db.recruitment_sessions.find_one({"session_id": session_id, "is_active": True})
    if not doc:
        return None

    # Check expiration
    expires_at = datetime.fromisoformat(doc["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        await db.recruitment_sessions.update_one({"session_id": session_id}, {"$set": {"is_active": False}})
        return None

    # Check user ownership (must be candidate or recruiter)
    if doc["candidate_id"] != user_id and doc["recruiter_id"] != user_id:
        return None

    return format_doc(doc)


async def save_stage_execution(
    application_id: str,
    stage_id: str,
    engine_type: str,
    execution_payload: dict,
    created_by: str
) -> dict:
    """
    Saves or updates execution outcome in MongoDB `stage_executions` collection.
    """
    db = get_database()
    now_str = datetime.now(timezone.utc).isoformat()

    doc = {
        "application_id": application_id,
        "stage_id": stage_id,
        "engine_type": engine_type,
        "execution_payload": execution_payload,
        "created_by": created_by,
        "created_at": now_str,
        "updated_at": now_str,
    }

    await db.stage_executions.update_one(
        {"application_id": application_id, "stage_id": stage_id},
        {"$set": doc},
        upsert=True
    )
    return doc


async def get_stage_execution(application_id: str, stage_id: str) -> Optional[dict]:
    """
    Fetches execution outcome for an application stage.
    """
    db = get_database()
    doc = await db.stage_executions.find_one({"application_id": application_id, "stage_id": stage_id})
    return format_doc(doc) if doc else None
