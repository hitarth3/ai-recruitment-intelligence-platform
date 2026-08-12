"""
Recruiter Engine Service.
Responsible ONLY for Recruiter Workspace & Studio Pipeline Data:
- Job posting data aggregation
- Recruitment Studio candidate pipeline data
- Company profile & requisition overview
"""

from typing import List, Dict, Any, Optional
from app.database.job_db import get_my_company_jobs, get_job_by_id
from app.database.application_db import get_recruiter_company_candidates
from app.services.workflow_engine import get_application_workflow_state
from app.utils.logger import logger


async def get_recruitment_studio_data(
    job_id: str,
    company_id: str,
    recruiter_id: str
) -> Dict[str, Any]:
    """
    Aggregates Recruitment Studio candidate pipeline and stage executions.
    """
    job = await get_job_by_id(job_id)
    applications = await get_recruiter_company_candidates(
        company_id=company_id,
        recruiter_id=recruiter_id,
        job_id=job_id
    )

    enriched = []
    for app in applications:
        app_id = app.get("id") or str(app.get("_id", ""))
        live = await get_application_workflow_state(app_id)
        if live:
            merged = {**app, **live}
            enriched.append(merged)
        else:
            enriched.append(app)

    return {
        "job": job,
        "total_candidates": len(enriched),
        "applications": enriched,
    }
