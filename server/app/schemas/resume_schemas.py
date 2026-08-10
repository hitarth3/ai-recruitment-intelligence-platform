"""
Pydantic Schemas for Resume Management.
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional


class ResumeResponseSchema(BaseModel):
    id: str
    user_id: str
    original_filename: str
    resume_url: str
    file_size: int
    file_size_formatted: str
    upload_date: str
    upload_status: str = "Uploaded"  # Uploaded | Processing | Ready
    resume_analysis: Dict[str, Any] = {}
