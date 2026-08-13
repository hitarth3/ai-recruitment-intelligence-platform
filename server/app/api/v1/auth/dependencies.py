"""
FastAPI Dependency Injection for Authentication & Role-Based Authorization.
Protects routes using Bearer JWT tokens and enforces candidate vs recruiter access rules.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from app.core.security import decode_access_token
from app.database.database import get_database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/recruiter/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Extracts and validates JWT Bearer token, returning active user document from MongoDB Atlas.
    Converts BSON _id to string for JSON serialization safety.
    Checks token_version validity if present in token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials. Token invalid or expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    token_ver = payload.get("token_version")
    if not user_id:
        raise credentials_exception

    db = get_database()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})

    if not user:
        raise credentials_exception

    # Check token version invalidation if present
    if token_ver is not None and user.get("token_version") is not None:
        if token_ver != user.get("token_version"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired due to a password change or security update. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user["id"] = str(user["_id"])
    if "_id" in user:
        user["_id"] = str(user["_id"])
    return user


async def get_current_candidate(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Enforces candidate role authorization. Rejects recruiter tokens with 403 Forbidden.
    """
    if current_user.get("role") != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. Candidate authorization required for this resource."
        )
    return current_user


async def get_current_recruiter(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Enforces recruiter role authorization. Rejects candidate tokens with 403 Forbidden.
    """
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. Recruiter authorization required for this resource."
        )
    return current_user
