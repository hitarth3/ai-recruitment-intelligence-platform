"""
FastAPI REST API Router for Candidate Profile Management.
Endpoints:
- GET  /api/v1/candidate/profile
- PUT  /api/v1/candidate/profile
- POST /api/v1/candidate/profile/image
"""

import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.api.v1.auth.dependencies import get_current_candidate
from app.schemas.profile_schemas import CandidateProfileUpdateSchema
from app.database.profile_db import get_candidate_profile, update_candidate_profile, update_candidate_avatar
from app.utils.logger import logger

router = APIRouter(prefix="/candidate/profile", tags=["Candidate Profile"])


@router.get("", summary="Get Candidate Profile")
async def get_profile(current_candidate: dict = Depends(get_current_candidate)):
    """
    Returns candidate profile document with dynamic Profile Completion percentage from MongoDB Atlas.
    """
    user_id = current_candidate["id"]
    profile = await get_candidate_profile(user_id)
    return profile


@router.put("", summary="Update Candidate Profile")
async def update_profile(
    body: CandidateProfileUpdateSchema,
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Updates candidate profile fields in MongoDB Atlas (personal info, professional info, skills, education, experience, projects, certifications, social links).
    """
    user_id = current_candidate["id"]
    update_data = body.model_dump(exclude_unset=True)
    updated_profile = await update_candidate_profile(user_id, update_data)
    logger.info(f"Updated profile for candidate user: {user_id}")
    return updated_profile


@router.post("/image", summary="Upload Profile Image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Uploads profile avatar image file, stores in server/uploads/avatars/, and updates image URL in MongoDB Atlas.
    """
    user_id = current_candidate["id"]

    # Validate image MIME type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only image files (PNG, JPG, JPEG, WEBP) are allowed."
        )

    upload_dir = os.path.join("uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"avatar_{user_id}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # In production/local, generate avatar URL
    image_url = f"http://localhost:8000/static/avatars/{filename}"
    updated_profile = await update_candidate_avatar(user_id, image_url)
    logger.info(f"Uploaded profile image for candidate: {user_id}")
    return {"message": "Profile image uploaded successfully.", "profile_image_url": image_url, "profile": updated_profile}
