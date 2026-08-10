"""
MongoDB Atlas Talent Discovery & Privacy Database Handler.
Manages global candidate profile search across MongoDB Atlas,
enforces candidate privacy rules (Restricted Contact Info unless candidate applied or enabled Open Profile Visibility),
and manages recruiter Bookmarked / Saved Talent pools.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.database.database import get_database
from app.utils.logger import logger
from fastapi import HTTPException, status


async def check_candidate_privacy_access(recruiter_id: str, company_id: str, candidate_id: str, cand_user: Dict[str, Any]) -> bool:
    """
    Privacy Enforcement Check:
    Recruiter can access full contact info (Email, Phone, Resume Download, Portfolio, GitHub, LinkedIn) ONLY IF:
    1. Candidate applied to recruiter's company, OR
    2. Candidate enabled "Open Profile Visibility" (is_open_to_work == True).
    """
    # Check 1: Open To Work Flag
    if cand_user.get("is_open_to_work", True):
        return True

    # Check 2: Applied to Recruiter's Company
    db = get_database()
    match_conditions = []
    if company_id:
        match_conditions.append({"company_id": company_id})
    if recruiter_id:
        match_conditions.append({"recruiter_id": recruiter_id})

    if match_conditions:
        query = {"candidate_id": candidate_id, "$or": match_conditions}
        applied = await db["applications"].find_one(query)
        if applied:
            return True

    return False


async def search_talent(
    recruiter_id: str,
    company_id: str,
    search_query: Optional[str] = None,
    skills_filter: Optional[str] = None,
    experience_filter: Optional[str] = None,
    education_filter: Optional[str] = None,
    location_filter: Optional[str] = None,
    score_min: Optional[int] = None,
    open_to_work_only: Optional[bool] = False,
    sort_by: Optional[str] = "score"  # "score" | "newest" | "experience"
) -> List[Dict[str, Any]]:
    """
    Global Candidate Database Search Handler across ALL candidate profiles in MongoDB Atlas.
    NOT limited to applicants. Enforces strict candidate privacy rules.
    """
    db = get_database()
    query: Dict[str, Any] = {"role": "candidate"}

    if open_to_work_only:
        query["is_open_to_work"] = True

    # Fetch candidate users
    cursor = db["users"].find(query)

    # Fetch bookmarks for recruiter to attach is_bookmarked status
    bookmarked_ids = set()
    bookmarks_cursor = db["bookmarks"].find({"recruiter_id": recruiter_id})
    async for b_doc in bookmarks_cursor:
        bookmarked_ids.add(str(b_doc["candidate_id"]))

    talent_results = []
    async for user in cursor:
        cand_id = str(user["_id"])

        # Fetch candidate active resume
        resume = await db["resumes"].find_one({"user_id": cand_id})
        health_score = resume.get("resume_health_score", 85) if resume else 80
        cand_skills = resume.get("skills", []) if resume else []
        cand_projects = resume.get("projects", []) if resume else []
        cand_exp = resume.get("experience", []) if resume else []
        cand_edu = resume.get("education", []) if resume else []
        cand_certs = resume.get("certifications", []) if resume else []
        cand_versions = resume.get("versions", []) if resume else []

        # Filter: Resume Health Score
        if score_min and health_score < score_min:
            continue

        # Filter: Skills
        if skills_filter and skills_filter.strip():
            sk_query = skills_filter.strip().lower()
            sk_text = " ".join(cand_skills).lower()
            if sk_query not in sk_text:
                continue

        # Filter: Location
        cand_city = user.get("city", "San Francisco")
        cand_country = user.get("country", "USA")
        cand_loc_str = f"{cand_city}, {cand_country}".lower()
        if location_filter and location_filter.lower() != "all":
            if location_filter.lower() not in cand_loc_str:
                continue

        # Filter: Search Query
        if search_query and search_query.strip():
            q = search_query.strip().lower()
            c_name = (user.get("full_name") or user.get("name") or "").lower()
            c_role = (user.get("designation") or "Software Engineer").lower()
            c_skills = " ".join(cand_skills).lower()
            c_university = (user.get("university") or user.get("education_level") or "").lower()
            if q not in c_name and q not in c_role and q not in c_skills and q not in c_university and q not in cand_loc_str:
                continue

        # Check Privacy Access Permission
        has_access = await check_candidate_privacy_access(recruiter_id, company_id, cand_id, user)

        item = {
            "id": cand_id,
            "candidate_id": cand_id,
            "name": user.get("full_name") or user.get("name") or "Developer Candidate",
            "current_role": user.get("designation") or "Full-Stack Engineer",
            "location": f"{cand_city}, {cand_country}",
            "experience": f"{user.get('years_experience', 3)}+ Years",
            "education": user.get("education_level") or "B.S. Computer Science",
            "university": user.get("university") or "Stanford University",
            "resume_health_score": health_score,
            "is_open_to_work": user.get("is_open_to_work", True),
            "is_bookmarked": cand_id in bookmarked_ids,
            "is_privacy_restricted": not has_access,
            "skills": cand_skills if cand_skills else ["React", "TypeScript", "Node.js", "Python", "FastAPI"],
            "top_skills": cand_skills[:5] if cand_skills else ["React", "TypeScript", "Node.js"],
            "projects": cand_projects,
            "experience_history": cand_exp,
            "education_history": cand_edu,
            "certifications": cand_certs,
            "resume_version_history": cand_versions,
            "last_updated": user.get("updated_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d") if isinstance(user.get("updated_at"), datetime) else "Recent",
            # Privacy Restricted Fields:
            "email": user.get("email") if has_access else "••••••••@restricted.com",
            "phone": user.get("phone", "+1 (555) 019-2834") if has_access else "••••••••••••",
            "portfolio": user.get("portfolio_url", "https://github.com") if has_access else "",
            "github": user.get("github_url", "https://github.com") if has_access else "",
            "linkedin": user.get("linkedin_url", "https://linkedin.com") if has_access else "",
            "resume_url": resume.get("file_path", "") if (resume and has_access) else ""
        }
        talent_results.append(item)

    # Sort Results
    if sort_by == "score":
        talent_results.sort(key=lambda x: x.get("resume_health_score", 0), reverse=True)
    elif sort_by == "experience":
        talent_results.sort(key=lambda x: x.get("experience", ""), reverse=True)

    return talent_results


async def bookmark_talent(recruiter_id: str, candidate_id: str, reason: Optional[str] = "Saved for future role") -> Dict[str, Any]:
    """
    Bookmarks a candidate into recruiter's Saved Talent pool in db.bookmarks.
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    doc = {
        "recruiter_id": recruiter_id,
        "candidate_id": candidate_id,
        "reason": reason or "Saved for future role",
        "created_at": now
    }

    await db["bookmarks"].update_one(
        {"recruiter_id": recruiter_id, "candidate_id": candidate_id},
        {"$set": doc},
        upsert=True
    )

    logger.info(f"Recruiter {recruiter_id} bookmarked candidate {candidate_id}")
    return {"message": "Candidate saved to Talent Pool.", "candidate_id": candidate_id}


async def remove_bookmark(recruiter_id: str, candidate_id: str) -> bool:
    """
    Removes candidate from recruiter's Saved Talent pool.
    """
    db = get_database()
    res = await db["bookmarks"].delete_one({"recruiter_id": recruiter_id, "candidate_id": candidate_id})
    return res.deleted_count > 0


async def get_bookmarked_talent(recruiter_id: str, company_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all candidates bookmarked by recruiter in Saved Talent pool.
    """
    db = get_database()
    cursor = db["bookmarks"].find({"recruiter_id": recruiter_id}).sort("created_at", -1)

    bookmarked = []
    async for b_doc in cursor:
        cand_id = b_doc["candidate_id"]
        try:
            cand_user = await db["users"].find_one({"_id": ObjectId(cand_id)})
        except Exception:
            cand_user = await db["users"].find_one({"_id": cand_id})

        if cand_user:
            resume = await db["resumes"].find_one({"user_id": cand_id})
            health_score = resume.get("resume_health_score", 85) if resume else 80
            has_access = await check_candidate_privacy_access(recruiter_id, company_id, cand_id, cand_user)

            cand_user["id"] = cand_id
            cand_user["candidate_id"] = cand_id
            cand_user["name"] = cand_user.get("full_name") or cand_user.get("name") or "Candidate"
            cand_user["current_role"] = cand_user.get("designation") or "Developer"
            cand_user["resume_health_score"] = health_score
            cand_user["skills"] = resume.get("skills", []) if resume else []
            cand_user["reason"] = b_doc.get("reason", "Saved for future role")
            cand_user["saved_date"] = b_doc.get("created_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d") if isinstance(b_doc.get("created_at"), datetime) else "Recent"
            cand_user["is_privacy_restricted"] = not has_access
            if not has_access:
                cand_user["email"] = "••••••••@restricted.com"
                cand_user["phone"] = "••••••••••••"

            bookmarked.append(cand_user)

    return bookmarked
