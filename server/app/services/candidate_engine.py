"""
Candidate Engine Service.
Responsible ONLY for Candidate Dashboard & Application Data:
- Candidate applied jobs overview
- Current stage & execution authorization
- Candidate profile & resume version history
"""

from typing import List, Dict, Any, Optional
from app.database.application_db import get_candidate_applications
from app.services.workflow_engine import get_application_workflow_state
from app.utils.logger import logger


async def get_candidate_dashboard_data(candidate_id: str) -> Dict[str, Any]:
    """
    Fetches candidate's active applications enriched with live workflow stage state.
    """
    raw_apps = await get_candidate_applications(candidate_id)
    enriched = []

    for app in raw_apps:
        app_id = app.get("id") or str(app.get("_id", ""))
        state = await get_application_workflow_state(app_id)
        if state:
            if "job" in app:
                state["job"] = app["job"]
            enriched.append(state)
        else:
            enriched.append(app)

    return {
        "candidate_id": candidate_id,
        "total_applications": len(enriched),
        "applications": enriched,
    }
