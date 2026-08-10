"""
MongoDB Database Handler for Centralized Notification System.
Operates on `notifications` and `notification_preferences` collections in MongoDB Atlas.
Creates required indexes and manages CRUD queries.
"""

from datetime import datetime, timezone
from bson import ObjectId
from typing import Dict, Any, List, Optional
from app.database.database import get_database
from app.utils.logger import logger


async def ensure_notification_indexes():
    """
    Creates compound indexes on `notifications` collection in MongoDB Atlas.
    """
    try:
        db = get_database()
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.notifications.create_index([("user_id", 1), ("is_read", 1)])
        await db.notifications.create_index([("user_id", 1), ("type", 1)])
        await db.notifications.create_index([("user_id", 1), ("priority", 1)])
        await db.notification_preferences.create_index([("user_id", 1)], unique=True)
        logger.info("Notification database indexes created successfully.")
    except Exception as e:
        logger.error(f"Error creating notification indexes: {e}")


def format_notification(doc: dict) -> dict:
    """Formats BSON MongoDB document to FastAPI JSON serializable dict."""
    if not doc:
        return {}
    doc["id"] = str(doc.get("_id", ""))
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def insert_notification(notification_data: dict) -> dict:
    """
    Inserts a single notification document into MongoDB Atlas.
    """
    db = get_database()
    now_str = datetime.now(timezone.utc).isoformat()
    
    doc = {
        "user_id": notification_data["user_id"],
        "type": notification_data.get("type", "SYSTEM"),
        "category": notification_data.get("category", "System"),
        "priority": notification_data.get("priority", "Medium"),
        "title": notification_data.get("title", "Notification"),
        "message": notification_data.get("message", ""),
        "is_read": False,
        "read_at": None,
        "action_type": notification_data.get("action_type", "OPEN_NOTIFICATION"),
        "action_payload": notification_data.get("action_payload", {}),
        "metadata": notification_data.get("metadata", {}),
        "source_module": notification_data.get("source_module", "system"),
        "source_event": notification_data.get("source_event", "SYSTEM_EVENT"),
        "delivery_channels": notification_data.get("delivery_channels", {
            "in_app": True,
            "email": False,
            "browser_push": False,
            "mobile_push": False
        }),
        "created_at": notification_data.get("created_at", now_str),
        "updated_at": notification_data.get("updated_at", now_str)
    }

    res = await db.notifications.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc["id"] = str(res.inserted_id)
    return doc


async def create_notification(
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "application"
) -> dict:
    """
    Helper function to create an in-app notification.
    """
    return await insert_notification({
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notification_type.upper(),
        "category": "Application",
        "priority": "High"
    })


async def fetch_user_notifications(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    read_status: Optional[str] = None,  # "all", "unread", "read"
    search: Optional[str] = None,
    sort_by: str = "newest"  # "newest", "oldest", "unread", "priority"
) -> tuple[List[dict], int, int]:
    """
    Queries notifications for user_id with pagination, category/priority/read filters, search, and sorting.
    """
    db = get_database()
    query: Dict[str, Any] = {"user_id": user_id}

    if category and category.lower() != "all":
        query["category"] = category

    if priority and priority.lower() != "all":
        query["priority"] = priority

    if read_status == "unread":
        query["is_read"] = False
    elif read_status == "read":
        query["is_read"] = True

    if search and search.strip():
        regex_pattern = {"$regex": search.strip(), "$options": "i"}
        query["$or"] = [
            {"title": regex_pattern},
            {"message": regex_pattern},
            {"type": regex_pattern},
            {"category": regex_pattern},
            {"metadata.company_name": regex_pattern},
            {"metadata.job_title": regex_pattern}
        ]

    # Calculate total matching count
    total = await db.notifications.count_documents(query)
    unread_count = await db.notifications.count_documents({"user_id": user_id, "is_read": False})

    # Determine sort order
    sort_spec = [("created_at", -1)]
    if sort_by == "oldest":
        sort_spec = [("created_at", 1)]
    elif sort_by == "unread":
        sort_spec = [("is_read", 1), ("created_at", -1)]
    elif sort_by == "priority":
        sort_spec = [("priority", 1), ("created_at", -1)]

    skip = (page - 1) * limit
    cursor = db.notifications.find(query).sort(sort_spec).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)

    formatted_items = [format_notification(item) for item in items]
    return formatted_items, total, unread_count


async def fetch_unread_count(user_id: str) -> int:
    """
    Returns unread notification count for user_id.
    """
    db = get_database()
    return await db.notifications.count_documents({"user_id": user_id, "is_read": False})


async def set_notification_read(notification_id: str, user_id: str) -> bool:
    """
    Marks a single notification as read.
    """
    db = get_database()
    try:
        query = {"user_id": user_id, "$or": [{"_id": ObjectId(notification_id)}, {"_id": notification_id}]}
    except Exception:
        query = {"_id": notification_id, "user_id": user_id}

    now_str = datetime.now(timezone.utc).isoformat()
    res = await db.notifications.update_one(
        query,
        {
            "$set": {
                "is_read": True,
                "read_at": now_str,
                "updated_at": now_str
            }
        }
    )
    return res.modified_count > 0


async def set_all_notifications_read(user_id: str) -> int:
    """
    Marks all notifications for user_id as read.
    """
    db = get_database()
    now_str = datetime.now(timezone.utc).isoformat()
    res = await db.notifications.update_many(
        {"user_id": user_id, "is_read": False},
        {
            "$set": {
                "is_read": True,
                "read_at": now_str,
                "updated_at": now_str
            }
        }
    )
    return res.modified_count


async def remove_notification(notification_id: str, user_id: str) -> bool:
    """
    Deletes a single notification document.
    """
    db = get_database()
    try:
        query = {"user_id": user_id, "$or": [{"_id": ObjectId(notification_id)}, {"_id": notification_id}]}
    except Exception:
        query = {"_id": notification_id, "user_id": user_id}

    res = await db.notifications.delete_one(query)
    return res.deleted_count > 0


async def remove_read_notifications(user_id: str) -> int:
    """
    Deletes all read notifications for user_id.
    """
    db = get_database()
    res = await db.notifications.delete_many({"user_id": user_id, "is_read": True})
    return res.deleted_count


async def fetch_user_preferences(user_id: str) -> dict:
    """
    Retrieves notification preferences document for user_id or returns defaults.
    """
    db = get_database()
    prefs = await db.notification_preferences.find_one({"user_id": user_id})
    if not prefs:
        return {
            "user_id": user_id,
            "application_updates": True,
            "interview_updates": True,
            "resume_updates": True,
            "job_recommendations": True,
            "ai_updates": True,
            "system_updates": True,
            "email_notifications_enabled": False
        }
    prefs["id"] = str(prefs.get("_id", ""))
    if "_id" in prefs:
        prefs["_id"] = str(prefs["_id"])
    return prefs


async def save_user_preferences(user_id: str, prefs_data: dict) -> dict:
    """
    Upserts notification preferences for user_id in MongoDB Atlas.
    """
    db = get_database()
    now_str = datetime.now(timezone.utc).isoformat()
    
    update_doc = {
        "user_id": user_id,
        "application_updates": prefs_data.get("application_updates", True),
        "interview_updates": prefs_data.get("interview_updates", True),
        "resume_updates": prefs_data.get("resume_updates", True),
        "job_recommendations": prefs_data.get("job_recommendations", True),
        "ai_updates": prefs_data.get("ai_updates", True),
        "system_updates": prefs_data.get("system_updates", True),
        "email_notifications_enabled": prefs_data.get("email_notifications_enabled", False),
        "updated_at": now_str
    }

    await db.notification_preferences.update_one(
        {"user_id": user_id},
        {"$set": update_doc},
        upsert=True
    )
    return await fetch_user_preferences(user_id)
