"""
MongoDB Database Handler for AI Career Coach Conversation History.
Operates on `career_coach_chats` collection in MongoDB Atlas.
Persists candidate messages and AI mentor replies for full conversation memory context.
"""

from datetime import datetime, timezone
from app.database.database import get_database
from app.utils.logger import logger


async def save_chat_message(user_id: str, user_text: str, ai_reply: str) -> dict:
    """
    Saves candidate message and AI mentor reply to MongoDB Atlas.
    """
    db = get_database()
    now_str = datetime.now(timezone.utc).isoformat()
    time_display = datetime.now(timezone.utc).strftime("%I:%M %p")

    user_msg = {
        "id": f"user-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "sender": "user",
        "text": user_text,
        "timestamp": time_display,
        "created_at": now_str
    }

    ai_msg = {
        "id": f"ai-{int(datetime.now(timezone.utc).timestamp() * 1000) + 1}",
        "sender": "ai",
        "text": ai_reply,
        "timestamp": time_display,
        "created_at": now_str
    }

    # Push messages into user's chat thread document
    await db.career_coach_chats.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "messages": {
                    "$each": [user_msg, ai_msg],
                    "$slice": -50  # Keep last 50 messages in MongoDB per candidate
                }
            },
            "$set": {
                "updated_at": now_str
            }
        },
        upsert=True
    )

    return {"user_msg": user_msg, "ai_msg": ai_msg}


async def get_candidate_chat_history(user_id: str, limit: int = 10) -> list:
    """
    Retrieves recent chat history for candidate from MongoDB Atlas.
    """
    db = get_database()
    chat_doc = await db.career_coach_chats.find_one({"user_id": user_id})
    if not chat_doc or "messages" not in chat_doc:
        return []
    
    messages = chat_doc.get("messages", [])
    return messages[-limit:]


async def clear_candidate_chat_history(user_id: str) -> bool:
    """
    Clears candidate's chat history in MongoDB Atlas.
    """
    db = get_database()
    res = await db.career_coach_chats.delete_one({"user_id": user_id})
    return res.deleted_count > 0
