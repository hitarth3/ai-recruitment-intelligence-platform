"""
Notification Engine Service.
Responsible ONLY for Centralized Candidate & Recruiter Notifications:
- Dispatching candidate stage progression notifications
- Dispatching recruiter submission alerts
- In-app notification creation
"""

from typing import Dict, Any, Optional
from app.database.notification_db import create_notification
from app.utils.logger import logger


async def dispatch_stage_progression_notification(
    user_id: str,
    stage_name: str,
    job_title: str,
    new_status: str
) -> Dict[str, Any]:
    """
    Dispatches in-app notification to candidate when stage updates.
    """
    msg = f"Your application for '{job_title}' has updated to stage: {stage_name} [{new_status}]."
    title = f"Hiring Update: {stage_name}"

    try:
        notif = await create_notification(
            user_id=user_id,
            title=title,
            message=msg,
            notification_type="application"
        )
        return notif
    except Exception as e:
        logger.error(f"[NotificationEngine] Failed to dispatch notification: {e}")
        return {}
