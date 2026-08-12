"""
Offer Engine Service.
Responsible ONLY for Offer Generation & Acceptance Archival:
- Generating offer letter details (Salary, Benefits, Joining Date, Work Location)
- Processing candidate response (Accept, Decline, Revision)
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.utils.logger import logger


def generate_offer_letter_payload(
    job_title: str,
    company_name: str,
    annual_salary: float,
    benefits: str,
    joining_date: str,
    work_location: str = "Hybrid"
) -> Dict[str, Any]:
    """Generates structured offer letter payload."""
    return {
        "job_title": job_title,
        "company_name": company_name,
        "annual_salary": annual_salary,
        "benefits": benefits,
        "joining_date": joining_date,
        "work_location": work_location,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "OFFER_EXTENDED",
    }
