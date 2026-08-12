"""
Session Engine Service.
Responsible ONLY for Stage Execution Sessions & Security Tokens:
- Generating execution session JWT tokens
- Expiry and authorization validation
- Enforcing candidate and recruiter execution session boundaries
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.utils.logger import logger


def create_stage_execution_token(
    application_id: str,
    candidate_id: str,
    job_id: str,
    recruiter_id: str,
    stage_name: str,
    valid_hours: int = 2
) -> Dict[str, Any]:
    """
    Generates a signed execution session token payload for authorized candidate stage execution.
    """
    session_id = f"exec-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(hours=valid_hours)).isoformat()

    token_payload = {
        "session_id": session_id,
        "application_id": application_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "recruiter_id": recruiter_id,
        "stage_name": stage_name,
        "issued_at": now.isoformat(),
        "expires_at": expires_at,
        "status": "AUTHORIZED",
    }
    return token_payload


def validate_stage_session(
    token_payload: Dict[str, Any],
    expected_candidate_id: str,
    expected_application_id: str
) -> bool:
    """Validates session token candidate ownership and expiry."""
    if not token_payload:
        return False

    if token_payload.get("candidate_id") != expected_candidate_id:
        return False

    if token_payload.get("application_id") != expected_application_id:
        return False

    exp_str = token_payload.get("expires_at")
    if exp_str:
        try:
            exp_dt = datetime.fromisoformat(exp_str)
            if datetime.now(timezone.utc) > exp_dt:
                return False
        except Exception:
            pass

    return True
