"""
FastAPI REST API Routes for Candidate Resume Management & Versioning.
Exposes endpoints:
- POST /resume/upload (10MB limit, PDF & DOCX validation, strict non-resume document rejection, version tracking)
- GET  /resume (Fetch metadata of candidate's active resume & version history)
- PUT  /resume (Upload new resume version)
- DELETE /resume (Delete active resume)
- GET  /resume/file (Inline stream or download resume file via token)
"""

import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query, Header
from fastapi.responses import FileResponse
from app.api.v1.auth.dependencies import get_current_candidate
from app.core.security import decode_access_token
from app.database.resume_db import (
    create_resume_record,
    get_user_resume,
    delete_user_resume,
)
from app.utils.logger import logger

router = APIRouter(prefix="/resume", tags=["Resume Management"])

RESUMES_DIR = os.path.abspath(os.path.join("uploads", "resumes"))
os.makedirs(RESUMES_DIR, exist_ok=True)


async def get_candidate_optional_auth(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Decodes candidate authentication from either Authorization Bearer header OR ?token= query parameter.
    Allows standard browser <iframe src="/api/v1/resume/file?token=..."> to stream PDF seamlessly.
    """
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split("Bearer ")[1].strip()
    elif token:
        jwt_token = token.strip()

    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token or token query parameter."
        )

    payload = decode_access_token(jwt_token)
    if not payload or payload.get("role") != "candidate":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authentication credentials from token."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")

    return {"id": user_id, "email": payload.get("email", "")}


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload Candidate Resume (PDF/DOCX)")
async def upload_resume(
    file: UploadFile = File(...),
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Uploads candidate's PDF or DOCX resume with 10MB limit.
    Validates document structure. Rejects non-resume files with 400 Bad Request.
    Tracks resume version history (v1, v2, v3...).
    """
    lower_filename = file.filename.lower()
    ext = os.path.splitext(lower_filename)[1]

    # 1. Extension Validation (PDF or DOCX)
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF (.pdf) and Word (.docx) documents are allowed."
        )

    # 2. Read File Contents & Check 10MB Size Limit
    contents = await file.read()
    max_size_bytes = 10 * 1024 * 1024  # 10 MB
    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed limit of 10 MB."
        )

    user_id = current_candidate["id"]
    timestamp = int(datetime.now(timezone.utc).timestamp())
    safe_filename = f"resume_{user_id}_{timestamp}{ext}"
    file_path = os.path.abspath(os.path.join(RESUMES_DIR, safe_filename))

    # 3. Save File to Disk
    with open(file_path, "wb") as f:
        f.write(contents)

    # 4. Save & Validate Metadata in MongoDB Atlas
    try:
        resume_doc = await create_resume_record(
            user_id=user_id,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(contents)
        )
        logger.info(f"Uploaded resume version for candidate {user_id}: {file.filename} ({len(contents)} bytes)")
        return resume_doc
    except ValueError as ve:
        # Catch Invalid Document Classification and return 400 Bad Request with exact message
        logger.warning(f"Rejected invalid resume upload for user {user_id}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )


@router.get("", summary="Get Active Resume Details & Version History")
async def get_resume(current_candidate: dict = Depends(get_current_candidate)):
    """
    Returns candidate's active resume metadata document and full version history from MongoDB Atlas.
    """
    user_id = current_candidate["id"]
    resume = await get_user_resume(user_id)
    return {"resume": resume}


@router.put("", summary="Replace / Add New Resume Version")
async def replace_resume(
    file: UploadFile = File(...),
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Adds a new resume version (v2, v3...) to candidate's history.
    """
    return await upload_resume(file, current_candidate)


@router.delete("", summary="Delete Active Resume")
async def delete_resume(current_candidate: dict = Depends(get_current_candidate)):
    """
    Deletes candidate's active resume record and removes file from disk storage.
    """
    user_id = current_candidate["id"]
    deleted = await delete_user_resume(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active resume found to delete."
        )
    return {"message": "Resume deleted successfully."}


@router.get("/file", summary="Inline Stream or Download Resume File")
async def stream_resume_file(
    current_candidate: dict = Depends(get_candidate_optional_auth)
):
    """
    Streams active resume PDF/DOCX file inline for embedded browser viewing.
    Supports token in Authorization header OR ?token= query parameter.
    """
    user_id = current_candidate["id"]
    resume = await get_user_resume(user_id)

    if not resume or not resume.get("file_path"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active resume metadata found.")

    abs_path = os.path.abspath(resume["file_path"])
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resume file not found on disk: {abs_path}")

    ext = os.path.splitext(abs_path)[1].lower()
    media_type = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path=abs_path,
        media_type=media_type,
        filename=resume.get("original_filename", f"Resume{ext}"),
        headers={
            "Content-Disposition": f'inline; filename="{resume.get("original_filename", f"Resume{ext}")}"',
            "Access-Control-Allow-Origin": "*"
        }
    )
