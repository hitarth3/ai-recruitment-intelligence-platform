"""
FastAPI REST API Router for Centralized Notification Module.
Implements endpoints for listing, counting, filtering, search, sorting, read status updates, bulk deletions, and notification preferences.
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.v1.auth.dependencies import get_current_user
from app.services.notification_service import NotificationService
from app.api.v1.notifications.schemas import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse
)
from app.utils.logger import logger

router = APIRouter(prefix="/notifications", tags=["Notification Center"])


@router.get("", response_model=NotificationListResponse, summary="Get Paginated & Filtered User Notifications")
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by Category (Application, Interview, Resume, etc.)"),
    priority: Optional[str] = Query(None, description="Filter by Priority (High, Medium, Low)"),
    read_status: Optional[str] = Query("all", description="Read Status Filter (all, unread, read)"),
    search: Optional[str] = Query(None, description="Instant search term across title, message, and metadata"),
    sort_by: str = Query("newest", description="Sorting criteria (newest, oldest, unread, priority)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves user notifications from MongoDB Atlas with pagination, search, category/priority filtering, and sorting.
    """
    user_id = current_user["id"]
    items, total, unread_count = await NotificationService.get_user_notifications(
        user_id=user_id,
        page=page,
        limit=limit,
        category=category,
        priority=priority,
        read_status=read_status,
        search=search,
        sort_by=sort_by
    )

    total_pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "notifications": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "unread_count": unread_count
    }


@router.get("/unread-count", response_model=UnreadCountResponse, summary="Get Unread Notifications Count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """
    Returns unread notification count for Navbar Bell Badge.
    """
    user_id = current_user["id"]
    unread_count = await NotificationService.get_unread_count(user_id)
    return {"unread_count": unread_count}


@router.get("/preferences", response_model=NotificationPreferencesResponse, summary="Get Notification Preferences")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    """
    Retrieves user notification preferences.
    """
    user_id = current_user["id"]
    prefs = await NotificationService.get_preferences(user_id)
    return prefs


@router.put("/preferences", response_model=NotificationPreferencesResponse, summary="Update Notification Preferences")
async def update_preferences(
    prefs_req: NotificationPreferencesRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates user notification preferences in MongoDB Atlas.
    """
    user_id = current_user["id"]
    updated = await NotificationService.update_preferences(user_id, prefs_req.model_dump(exclude_unset=True))
    return updated


@router.patch("/read-all", summary="Mark All Notifications as Read")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """
    Marks all notifications for current user as read.
    """
    user_id = current_user["id"]
    modified_count = await NotificationService.mark_all_as_read(user_id)
    return {"message": "All notifications marked as read.", "modified_count": modified_count}


@router.patch("/{id}/read", summary="Mark Single Notification as Read")
async def mark_single_read(id: str, current_user: dict = Depends(get_current_user)):
    """
    Marks a single notification as read.
    """
    user_id = current_user["id"]
    success = await NotificationService.mark_as_read(id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return {"message": "Notification marked as read.", "id": id}


@router.delete("/read", summary="Delete All Read Notifications")
async def delete_read_notifications(current_user: dict = Depends(get_current_user)):
    """
    Deletes all read notifications for current user.
    """
    user_id = current_user["id"]
    deleted_count = await NotificationService.delete_read_notifications(user_id)
    return {"message": "Read notifications deleted successfully.", "deleted_count": deleted_count}


@router.delete("/{id}", summary="Delete Single Notification")
async def delete_single_notification(id: str, current_user: dict = Depends(get_current_user)):
    """
    Deletes a single notification.
    """
    user_id = current_user["id"]
    success = await NotificationService.delete_notification(id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return {"message": "Notification deleted successfully.", "id": id}
