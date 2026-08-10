"""
Pydantic Schemas for Candidate Job Applications.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ApplicationCreateRequest(BaseModel):
    job_id: str = Field(..., description="Target Job Requisition ObjectId String")
    notes: Optional[str] = Field(None, description="Optional note or message to recruiter")


class ApplicationResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    company_id: str
    recruiter_id: str
    resume_version_id: str
    applied_at: datetime
    status: str
    ai_match: Optional[Dict[str, Any]] = None
    notes: Optional[str] = ""
    created_at: datetime
    updated_at: datetime
    job: Optional[Dict[str, Any]] = None
