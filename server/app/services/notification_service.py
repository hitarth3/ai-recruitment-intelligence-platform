"""
Centralized Notification Service Module.
Service layer used by all application modules to emit and manage in-app notifications.
Enforces notification preferences checks and standardizes payload schemas.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.database import notification_db
from app.utils.logger import logger


class NotificationService:
    """
    Centralized Singleton Notification Service.
    No other module directly queries MongoDB for notifications.
    """

    @staticmethod
    async def create_notification(
        user_id: str,
        type: str,
        category: str,
        priority: str,
        title: str,
        message: str,
        action_type: str = "OPEN_NOTIFICATION",
        action_payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_module: str = "system",
        source_event: str = "SYSTEM_EVENT",
        delivery_channels: Optional[Dict[str, bool]] = None
    ) -> Optional[dict]:
        """
        Creates and stores a notification document in MongoDB Atlas if user preferences allow it.
        """
        try:
            # 1. Check user notification preference toggles
            prefs = await notification_db.fetch_user_preferences(user_id)
            
            category_lower = category.lower()
            if "application" in category_lower and not prefs.get("application_updates", True):
                logger.info(f"Notification suppressed for {user_id}: Application updates disabled in preferences.")
                return None
            if "interview" in category_lower and not prefs.get("interview_updates", True):
                logger.info(f"Notification suppressed for {user_id}: Interview updates disabled in preferences.")
                return None
            if "resume" in category_lower and not prefs.get("resume_updates", True):
                logger.info(f"Notification suppressed for {user_id}: Resume updates disabled in preferences.")
                return None
            if "recommendation" in category_lower and not prefs.get("job_recommendations", True):
                logger.info(f"Notification suppressed for {user_id}: Job recommendation updates disabled in preferences.")
                return None
            if "ai" in category_lower and not prefs.get("ai_updates", True):
                logger.info(f"Notification suppressed for {user_id}: AI updates disabled in preferences.")
                return None
            if "system" in category_lower and not prefs.get("system_updates", True):
                logger.info(f"Notification suppressed for {user_id}: System updates disabled in preferences.")
                return None

            # 2. Formulate Notification Document
            now_str = datetime.now(timezone.utc).isoformat()
            notification_data = {
                "user_id": user_id,
                "type": type,
                "category": category,
                "priority": priority,
                "title": title,
                "message": message,
                "action_type": action_type,
                "action_payload": action_payload or {},
                "metadata": metadata or {},
                "source_module": source_module,
                "source_event": source_event,
                "delivery_channels": delivery_channels or {
                    "in_app": True,
                    "email": prefs.get("email_notifications_enabled", False),
                    "browser_push": False,
                    "mobile_push": False
                },
                "created_at": now_str,
                "updated_at": now_str
            }

            saved = await notification_db.insert_notification(notification_data)
            logger.info(f"🔔 Notification created for user {user_id} [{type}]: '{title}'")
            return saved

        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {e}")
            return None

    @staticmethod
    async def get_user_notifications(
        user_id: str,
        page: int = 1,
        limit: int = 20,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        read_status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest"
    ) -> tuple[List[dict], int, int]:
        """
        Retrieves user notifications with pagination, filtering, search, and sorting.
        """
        return await notification_db.fetch_user_notifications(
            user_id=user_id,
            page=page,
            limit=limit,
            category=category,
            priority=priority,
            read_status=read_status,
            search=search,
            sort_by=sort_by
        )

    @staticmethod
    async def get_unread_count(user_id: str) -> int:
        """
        Retrieves unread notification count.
        """
        return await notification_db.fetch_unread_count(user_id)

    @staticmethod
    async def mark_as_read(notification_id: str, user_id: str) -> bool:
        """
        Marks a single notification as read.
        """
        return await notification_db.set_notification_read(notification_id, user_id)

    @staticmethod
    async def mark_all_as_read(user_id: str) -> int:
        """
        Marks all unread notifications as read.
        """
        return await notification_db.set_all_notifications_read(user_id)

    @staticmethod
    async def delete_notification(notification_id: str, user_id: str) -> bool:
        """
        Deletes a single notification.
        """
        return await notification_db.remove_notification(notification_id, user_id)

    @staticmethod
    async def delete_read_notifications(user_id: str) -> int:
        """
        Deletes all read notifications.
        """
        return await notification_db.remove_read_notifications(user_id)

    @staticmethod
    async def get_preferences(user_id: str) -> dict:
        """
        Retrieves notification preferences.
        """
        return await notification_db.fetch_user_preferences(user_id)

    @staticmethod
    async def update_preferences(user_id: str, prefs_data: dict) -> dict:
        """
        Updates notification preferences.
        """
        return await notification_db.save_user_preferences(user_id, prefs_data)
