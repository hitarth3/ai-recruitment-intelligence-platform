"""
MongoDB Database Handler for Candidate Settings Management.
Operates on user_settings collection in MongoDB Atlas.
Provides persistence for account details, security settings, notification preferences,
privacy controls, appearance themes, regional preferences, connected accounts, and account deletion.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from app.database.database import get_database
from app.core.security import verify_password, hash_password
from app.utils.logger import logger


async def get_candidate_settings(user_id: str) -> Dict[str, Any]:
    """
    Fetches candidate settings from db.user_settings.
    If not found, initializes default settings linked to user profile and account details.
    """
    db = get_database()
    settings = await db.user_settings.find_one({"user_id": user_id})

    # Fetch candidate user & profile info for default values
    user = await db.users.find_one({"_id": ObjectId(user_id) if len(user_id) == 24 else user_id})
    profile = await db.candidate_profiles.find_one({"user_id": user_id})

    user_name = user.get("name", "Candidate") if user else "Candidate"
    user_email = user.get("email", "") if user else ""
    user_phone = (profile.get("personal_information", {}).get("phone") or user.get("phone", "")) if profile else ""
    profile_photo = (profile.get("profile_image_url", "")) if profile else ""
    github_link = (profile.get("social_links", {}).get("github", "")) if profile else ""
    linkedin_link = (profile.get("social_links", {}).get("linkedin", "")) if profile else ""
    portfolio_link = (profile.get("social_links", {}).get("portfolio", "")) if profile else ""
    personal_web_link = (profile.get("social_links", {}).get("personal_website", "")) if profile else ""

    if not settings:
        settings = {
            "user_id": user_id,
            "account": {
                "name": user_name,
                "email": user_email,
                "phone": user_phone,
                "username": user_email.split("@")[0] if "@" in user_email else user_name.lower().replace(" ", ""),
                "profile_photo": profile_photo
            },
            "notifications": {
                "job_recommendations": True,
                "application_updates": True,
                "interview_updates": True,
                "resume_analysis": True,
                "system_notifications": True,
                "email_notifications": False
            },
            "privacy": {
                "profile_visibility": "Recruiters Only",  # Public | Recruiters Only | Private
                "resume_visibility_applied_only": True,
                "allow_indexing": True,
                "data_sharing": False
            },
            "appearance": {
                "theme": "system",  # system | light | dark
                "font_size": "Medium",
                "compact_mode": False
            },
            "preferences": {
                "language": "English (US)",
                "timezone": "America/New_York (UTC-5)",
                "date_format": "MM/DD/YYYY"
            },
            "connected_accounts": {
                "github": github_link,
                "linkedin": linkedin_link,
                "portfolio": portfolio_link,
                "personal_website": personal_web_link
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.user_settings.insert_one(settings)

    # Ensure all required nested sections exist
    settings["id"] = str(settings.get("_id", user_id))
    if "_id" in settings:
        settings["_id"] = str(settings["_id"])

    # Keep account details synced with candidate_profile / user if empty
    if not settings.get("account", {}).get("name"):
        settings["account"]["name"] = user_name
    if not settings.get("account", {}).get("email"):
        settings["account"]["email"] = user_email

    return settings


async def update_candidate_settings_section(user_id: str, section: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates specific settings section (account, notifications, privacy, appearance, preferences, connected_accounts).
    Also updates db.candidate_profiles and db.users when account or connected_accounts change to ensure consistency.
    """
    db = get_database()
    now = datetime.now(timezone.utc).isoformat()

    # Get current settings
    settings = await get_candidate_settings(user_id)
    settings[section] = {**settings.get(section, {}), **payload}
    settings["updated_at"] = now

    await db.user_settings.update_one(
        {"user_id": user_id},
        {"$set": {section: settings[section], "updated_at": now}},
        upsert=True
    )

    # Sync back to candidate_profiles and users collections if account or connected_accounts are updated
    if section == "account":
        user_name = payload.get("name")
        user_email = payload.get("email")
        user_phone = payload.get("phone")

        if user_name or user_email:
            user_update = {}
            if user_name:
                user_update["name"] = user_name
            if user_email:
                user_update["email"] = user_email
            await db.users.update_one(
                {"$or": [{"_id": ObjectId(user_id) if len(user_id) == 24 else user_id}, {"_id": user_id}]},
                {"$set": user_update}
            )

        if user_name or user_email or user_phone:
            profile_update = {}
            if user_name:
                profile_update["personal_information.name"] = user_name
                profile_update["name"] = user_name
            if user_email:
                profile_update["personal_information.email"] = user_email
                profile_update["email"] = user_email
            if user_phone:
                profile_update["personal_information.phone"] = user_phone

            await db.candidate_profiles.update_one(
                {"user_id": user_id},
                {"$set": profile_update}
            )

    elif section == "connected_accounts":
        social_links = {
            "github": payload.get("github", ""),
            "linkedin": payload.get("linkedin", ""),
            "portfolio": payload.get("portfolio", ""),
            "personal_website": payload.get("personal_website", "")
        }
        await db.candidate_profiles.update_one(
            {"user_id": user_id},
            {"$set": {"social_links": social_links}}
        )

    logger.info(f"Updated settings section '{section}' for candidate user: {user_id}")
    return await get_candidate_settings(user_id)


async def change_candidate_password(user_id: str, current_password: str, new_password: str) -> Dict[str, Any]:
    """
    Validates candidate's current password and updates password hash in db.users.
    """
    db = get_database()

    try:
        query = {"_id": ObjectId(user_id)}
    except Exception:
        query = {"_id": user_id}

    user = await db.users.find_one(query)
    if not user:
        user = await db.users.find_one({"id": user_id})

    if not user:
        raise ValueError("User account not found.")

    hashed_pass = user.get("password_hash") or user.get("password")
    if not hashed_pass or not verify_password(current_password, hashed_pass):
        raise ValueError("Current password is incorrect.")

    if len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters long.")

    new_hash = hash_password(new_password)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    logger.info(f"Password changed successfully for user {user_id}")
    return {"message": "Password updated successfully."}


async def delete_candidate_account(user_id: str) -> Dict[str, Any]:
    """
    Permanently deletes candidate account and all associated documents from MongoDB Atlas.
    """
    db = get_database()

    try:
        user_obj_id = ObjectId(user_id)
        await db.users.delete_one({"_id": user_obj_id})
    except Exception:
        await db.users.delete_one({"_id": user_id})

    await db.candidate_profiles.delete_many({"user_id": user_id})
    await db.user_settings.delete_many({"user_id": user_id})
    await db.applications.delete_many({"candidate_id": user_id})
    await db.resumes.delete_many({"user_id": user_id})
    await db.notifications.delete_many({"user_id": user_id})

    logger.info(f"Permanently deleted candidate account and all data for user {user_id}")
    return {"message": "Account deleted successfully."}
