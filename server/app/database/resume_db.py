"""
MongoDB Database Handler for Resume Management & Versioning.
Operates on resumes collection in MongoDB Atlas.
Supports versioning (v1, v2, v3...), invalid file rejection, PDF/DOCX analysis updates, and active resume tracking.
"""

import os
from datetime import datetime, timezone
from app.database.database import get_database
from app.services.resume_analyzer_service import analyze_candidate_resume
from app.database.profile_db import get_candidate_profile
from app.services.notification_service import NotificationService


def format_file_size(size_in_bytes: int) -> str:
    """
    Formats byte size to human-readable string (e.g. 2.4 MB).
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"


async def save_or_replace_resume(user_id: str, original_filename: str, file_path: str, file_size: int, file_url: str = "") -> dict:
    """
    Saves a new resume version for candidate in MongoDB Atlas.
    Validates document structure. If invalid non-resume document, raises ValueError.
    Appends new version (v1, v2, v3...) to versions array without overwriting version history.
    """
    db = get_database()

    # 1. Fetch candidate profile & run dynamic analysis
    profile = await get_candidate_profile(user_id) or {}
    analysis = analyze_candidate_resume(file_path, profile)

    # 2. STRICT INVALID RESUME CHECK: If document is NOT a resume, STOP immediately.
    if not analysis.get("is_valid", True):
        # Remove uploaded temporary invalid file from disk
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        error_msg = analysis.get("error_message") or "This document does not appear to be a valid resume. Please upload a professional resume containing sections such as Education, Experience, Skills and Projects."
        raise ValueError(error_msg)

    # 3. Handle Resume Versioning
    existing = await db.resumes.find_one({"user_id": user_id})
    existing_versions = existing.get("versions", []) if existing else []
    
    new_version_num = len(existing_versions) + 1
    version_id = f"v{new_version_num}"

    version_entry = {
        "version_id": version_id,
        "version_number": new_version_num,
        "upload_date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "original_filename": original_filename,
        "file_path": file_path,
        "resume_url": file_url or f"/static/resumes/{os.path.basename(file_path)}",
        "file_size": file_size,
        "file_size_formatted": format_file_size(file_size),
        "resume_health_score": analysis["resume_health_score"],
        "ats_readiness": analysis["ats_readiness"],
        "ats_parse_rate": analysis["ats_parse_rate"],
        "ai_summary": f"Version {new_version_num} uploaded on {datetime.now(timezone.utc).strftime('%B %d, %Y')}. Score: {analysis['resume_health_score']}/100.",
        "analysis": analysis,
        "skills": analysis["skills"]
    }

    all_versions = existing_versions + [version_entry]

    resume_doc = {
        "user_id": user_id,
        "active_version_number": new_version_num,
        "original_filename": original_filename,
        "file_path": file_path,
        "resume_url": file_url or f"/static/resumes/{os.path.basename(file_path)}",
        "file_size": file_size,
        "file_size_formatted": format_file_size(file_size),
        "upload_date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "upload_status": "Ready",
        "resume_analysis": analysis,
        "versions": all_versions,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    # Upsert active resume record per candidate
    await db.resumes.update_one(
        {"user_id": user_id},
        {"$set": resume_doc},
        upsert=True
    )

    # 4. Emit real event notification via NotificationService
    try:
        await NotificationService.create_notification(
            user_id=user_id,
            type="RESUME_UPLOADED",
            category="Resume",
            priority="Medium",
            title=f"Resume Version {new_version_num} Uploaded",
            message=f"'{original_filename}' has been saved as Version {new_version_num} with a Resume Health Score of {analysis['resume_health_score']}/100.",
            action_type="OPEN_RESUME",
            action_payload={"tab": "my-resume"},
            metadata={"filename": original_filename, "score": analysis["resume_health_score"], "version": new_version_num},
            source_module="resume_manager",
            source_event="RESUME_UPLOADED_EVENT"
        )
    except Exception:
        pass

    saved = await db.resumes.find_one({"user_id": user_id})
    saved["id"] = str(saved["_id"])
    if "_id" in saved:
        saved["_id"] = str(saved["_id"])
    return saved


# Alias for backward compatibility
create_resume_record = save_or_replace_resume


async def get_user_resume(user_id: str) -> dict | None:
    """
    Fetches candidate's active resume document from MongoDB Atlas. Converts BSON _id to string for FastAPI JSON serialization.
    """
    db = get_database()
    resume = await db.resumes.find_one({"user_id": user_id})
    if resume:
        resume["id"] = str(resume["_id"])
        if "_id" in resume:
            resume["_id"] = str(resume["_id"])
    return resume


async def update_resume_analysis(user_id: str, analysis: dict) -> bool:
    """
    Updates the active resume_analysis payload for candidate in MongoDB Atlas.
    """
    db = get_database()
    res = await db.resumes.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "resume_analysis": analysis,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    return res.modified_count > 0


async def delete_user_resume(user_id: str) -> bool:
    """
    Deletes candidate's active resume document from MongoDB Atlas and removes PDF file from disk.
    """
    db = get_database()
    existing = await db.resumes.find_one({"user_id": user_id})
    if not existing:
        return False

    if existing.get("file_path") and os.path.exists(existing["file_path"]):
        try:
            os.remove(existing["file_path"])
        except Exception:
            pass

    res = await db.resumes.delete_one({"user_id": user_id})
    return res.deleted_count > 0
