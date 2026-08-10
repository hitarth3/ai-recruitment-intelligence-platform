"""
MongoDB Atlas OTP Token Database Handler.
Manages persistent OTP token lifecycle for registration, password reset, and email changes.
Fields:
- email (str)
- otp_hash (str - SHA-256 digest)
- purpose (str - REGISTER | PASSWORD_RESET | EMAIL_CHANGE)
- expires_at (datetime)
- attempt_count (int)
- resend_count (int)
- temp_data (dict - temporary registration payload if REGISTER)
- created_at (datetime)
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from app.database.database import get_database
from app.utils.logger import logger


def _hash_otp(otp_code: str) -> str:
    """
    Computes secure SHA-256 hash digest of the 6-digit OTP string.
    Bcrypt is reserved strictly for user passwords.
    """
    return hashlib.sha256(otp_code.strip().encode("utf-8")).hexdigest()


async def store_otp(
    email: str,
    otp_code: str,
    purpose: str,
    temp_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Deletes any existing active OTP for (email, purpose), computes SHA-256 hash,
    and inserts new 10-minute OTP record into db.otp_tokens.
    """
    clean_email = email.lower().strip()
    db = get_database()
    otp_collection = db["otp_tokens"]
    
    # 1. Delete previous OTPs for this email and purpose to ensure only ONE active OTP exists
    await otp_collection.delete_many({"email": clean_email, "purpose": purpose})
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=10)
    
    otp_doc = {
        "email": clean_email,
        "otp_hash": _hash_otp(otp_code),
        "purpose": purpose,
        "expires_at": expires_at,
        "attempt_count": 0,
        "resend_count": 0,
        "temp_data": temp_data or {},
        "created_at": now
    }
    
    result = await otp_collection.insert_one(otp_doc)
    otp_doc["_id"] = str(result.inserted_id)
    logger.info(f"Stored OTP for {clean_email} [{purpose}]. Expires at {expires_at.strftime('%H:%M:%S UTC')}")
    return otp_doc


async def verify_otp(
    email: str,
    otp_code: str,
    purpose: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Verifies 6-digit OTP code against db.otp_tokens.
    Validates expiration, max attempts (<= 5), and SHA-256 hash match.
    Returns (success: bool, message: str, temp_data: dict | None).
    """
    clean_email = email.lower().strip()
    db = get_database()
    otp_collection = db["otp_tokens"]
    
    otp_doc = await otp_collection.find_one({"email": clean_email, "purpose": purpose})
    if not otp_doc:
        return False, "OTP code not found or expired. Please request a new verification code.", None
    
    now = datetime.now(timezone.utc)
    expires_at = otp_doc["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if now > expires_at:
        await otp_collection.delete_one({"_id": otp_doc["_id"]})
        return False, "OTP verification code has expired (10 min limit). Please request a new code.", None
    
    attempt_count = otp_doc.get("attempt_count", 0)
    if attempt_count >= 5:
        await otp_collection.delete_one({"_id": otp_doc["_id"]})
        return False, "Maximum verification attempts exceeded (5/5). Please request a new verification code.", None
    
    # Increment attempt count
    await otp_collection.update_one(
        {"_id": otp_doc["_id"]},
        {"$inc": {"attempt_count": 1}}
    )
    
    submitted_hash = _hash_otp(otp_code)
    if submitted_hash != otp_doc["otp_hash"]:
        remaining = 5 - (attempt_count + 1)
        return False, f"Invalid verification code. {remaining} attempt(s) remaining.", None
    
    # Successful match
    temp_data = otp_doc.get("temp_data", {})
    return True, "OTP verified successfully.", temp_data


async def delete_otp(email: str, purpose: str) -> bool:
    """
    Immediately deletes OTP token record after successful verification.
    """
    clean_email = email.lower().strip()
    db = get_database()
    result = await db["otp_tokens"].delete_many({"email": clean_email, "purpose": purpose})
    return result.deleted_count > 0


async def check_resend_allowed(email: str, purpose: str) -> Tuple[bool, str]:
    """
    Enforces maximum resend attempts (max 3 resends per purpose).
    """
    clean_email = email.lower().strip()
    db = get_database()
    otp_doc = await db["otp_tokens"].find_one({"email": clean_email, "purpose": purpose})
    if not otp_doc:
        return True, "Resend allowed."
    
    resend_count = otp_doc.get("resend_count", 0)
    if resend_count >= 3:
        return False, "Maximum resend limit reached (3/3). Please wait 10 minutes before trying again."
    
    return True, "Resend allowed."


async def increment_resend_count(email: str, purpose: str):
    """
    Increments resend count for active OTP record.
    """
    clean_email = email.lower().strip()
    db = get_database()
    await db["otp_tokens"].update_one(
        {"email": clean_email, "purpose": purpose},
        {"$inc": {"resend_count": 1}}
    )
