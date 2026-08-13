"""
Pydantic API Schemas for Notification Module endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.notification import (
    NotificationType,
    NotificationCategory,
    NotificationPriority,
    ActionType,
    DeliveryChannels
)


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    category: str
    priority: str
    title: str
    message: str
    is_read: bool
    read_at: Optional[str] = None
    action_type: str = "OPEN_NOTIFICATION"
    action_payload: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    source_module: str = "system"
    source_event: str = "SYSTEM_EVENT"
    delivery_channels: Dict[str, bool] = {"in_app": True, "email": False, "browser_push": False, "mobile_push": False}
    created_at: str
    updated_at: str


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPreferencesRequest(BaseModel):
    application_updates: Optional[bool] = None
    interview_updates: Optional[bool] = None
    resume_updates: Optional[bool] = None
    job_recommendations: Optional[bool] = None
    ai_updates: Optional[bool] = None
    system_updates: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None


class NotificationPreferencesResponse(BaseModel):
    user_id: str
    application_updates: bool
    interview_updates: bool
    resume_updates: bool
    job_recommendations: bool
    ai_updates: bool
    system_updates: bool
    email_notifications_enabled: bool
