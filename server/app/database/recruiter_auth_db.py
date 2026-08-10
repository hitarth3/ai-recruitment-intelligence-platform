"""
MongoDB Atlas Recruiter User Database Handler.
Manages recruiter user accounts with strict separation from Company Profiles.
Schema fields:
- name (str)
- email (str - unique)
- password_hash (str - bcrypt)
- role = "recruiter"
- email_verified = True
- profile_completed = False
- token_version = 1
- created_at (datetime)
- updated_at (datetime)
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bson import ObjectId
from app.database.database import get_database
from app.utils.logger import logger


async def find_recruiter_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Finds a recruiter document by lowercase email.
    """
    clean_email = email.lower().strip()
    db = get_database()
    user = await db["users"].find_one({"email": clean_email, "role": "recruiter"})
    if user:
        user["id"] = str(user["_id"])
    return user


async def create_recruiter_account(recruiter_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new Recruiter account document AFTER successful email OTP verification.
    Sets role="recruiter", email_verified=True, profile_completed=False, token_version=1.
    Does NOT store company information.
    """
    clean_email = recruiter_data["email"].lower().strip()
    now = datetime.now(timezone.utc)
    db = get_database()
    
    recruiter_doc = {
        "name": recruiter_data["name"].strip(),
        "email": clean_email,
        "password_hash": recruiter_data["password_hash"],
        "role": "recruiter",
        "email_verified": True,
        "profile_completed": False,
        "token_version": 1,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db["users"].insert_one(recruiter_doc)
    recruiter_doc["id"] = str(result.inserted_id)
    recruiter_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Created Verified Recruiter Account: {clean_email} [ID: {recruiter_doc['id']}]")
    return recruiter_doc


async def update_recruiter_password(email: str, new_password_hash: str) -> bool:
    """
    Updates the recruiter's bcrypt password hash and increments token_version to invalidate previous JWTs.
    """
    clean_email = email.lower().strip()
    now = datetime.now(timezone.utc)
    db = get_database()
    
    result = await db["users"].update_one(
        {"email": clean_email, "role": "recruiter"},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": now
            },
            "$inc": {"token_version": 1}
        }
    )
    
    success = result.modified_count > 0
    if success:
        logger.info(f"Updated password & incremented token_version for recruiter: {clean_email}")
    return success


async def mark_recruiter_profile_completed(user_id: str) -> bool:
    """
    Updates profile_completed flag to True when company profile onboarding finishes in future module.
    """
    now = datetime.now(timezone.utc)
    db = get_database()
    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_completed": True, "updated_at": now}}
    )
    return result.modified_count > 0
