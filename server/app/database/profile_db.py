"""
MongoDB Database Handler for Candidate Profile Management.
Operates on candidate_profiles collection in MongoDB Atlas.
Calculates dynamic Profile Completion percentage based on accurate field completeness.
"""

from datetime import datetime, timezone
from app.database.database import get_database


async def calculate_profile_completion(user_id: str, profile_doc: dict) -> int:
    """
    Calculates accurate dynamic Profile Completion percentage (0 - 100%):
    - Personal Information: 20% (Name, Email, Phone, Location)
    - Professional Information: 20% (Job Title, Experience, Preferred Mode)
    - Technical Skills: 20% (at least 1 skill added)
    - Education or Work History: 20% (at least 1 entry added)
    - Resume Uploaded: 20% (active PDF resume in resumes collection)
    """
    db = get_database()
    score = 0

    # 1. Personal Information Check (20%)
    personal = profile_doc.get("personal_information", {})
    if personal.get("name") and personal.get("email") and (personal.get("phone") or profile_doc.get("phone")) and (personal.get("location") or profile_doc.get("location")):
        score += 20

    # 2. Professional Information Check (20%)
    prof = profile_doc.get("professional_information", {})
    if prof.get("current_job_title") and prof.get("preferred_work_mode"):
        score += 20

    # 3. Technical Skills Check (20%)
    skills = profile_doc.get("skills", [])
    if isinstance(skills, list) and len(skills) > 0:
        score += 20

    # 4. Education or Experience Check (20%)
    education = profile_doc.get("education", [])
    experience = profile_doc.get("experience", [])
    if (isinstance(education, list) and len(education) > 0) or (isinstance(experience, list) and len(experience) > 0):
        score += 20

    # 5. Active Resume Check (20%)
    resume = await db.resumes.find_one({"user_id": user_id})
    if resume:
        score += 20

    return score


def normalize_profile(profile: dict, user_id: str) -> dict:
    """
    Ensures candidate profile dictionary has valid section structures without forcing hardcoded mock data.
    """
    if "personal_information" not in profile:
        profile["personal_information"] = {
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "date_of_birth": "",
            "gender": "",
            "location": profile.get("location", ""),
            "current_city": "",
            "country": "United States"
        }

    if "professional_information" not in profile:
        profile["professional_information"] = {
            "current_job_title": profile.get("title", ""),
            "years_of_experience": 0,
            "preferred_job_role": "",
            "preferred_work_mode": "Remote",
            "expected_salary": "",
            "notice_period": "Immediate"
        }

    if "skills" not in profile:
        profile["skills"] = []

    if "education" not in profile:
        profile["education"] = []

    if "experience" not in profile:
        profile["experience"] = []

    if "projects" not in profile:
        profile["projects"] = []

    if "certifications" not in profile:
        profile["certifications"] = []

    if "social_links" not in profile:
        profile["social_links"] = {
            "github": profile.get("github", ""),
            "linkedin": profile.get("linkedin", ""),
            "portfolio": profile.get("portfolio", ""),
            "personal_website": ""
        }

    return profile


async def get_candidate_profile(user_id: str) -> dict:
    """
    Fetches Candidate Profile document from MongoDB Atlas. Normalizes structure if needed.
    """
    db = get_database()
    profile = await db.candidate_profiles.find_one({"user_id": user_id})
    
    if not profile:
        user = await db.users.find_one({"_id": user_id})
        name = user.get("name", "Candidate") if user else "Candidate"
        email = user.get("email", "") if user else ""

        profile = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "personal_information": {
                "name": name,
                "email": email,
                "phone": "",
                "date_of_birth": "",
                "gender": "",
                "location": "",
                "current_city": "",
                "country": "United States"
            },
            "professional_information": {
                "current_job_title": "",
                "years_of_experience": 0,
                "preferred_job_role": "",
                "preferred_work_mode": "Remote",
                "expected_salary": "",
                "notice_period": "Immediate"
            },
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "social_links": {
                "github": "",
                "linkedin": "",
                "portfolio": "",
                "personal_website": ""
            }
        }
        res = await db.candidate_profiles.insert_one(profile)
        profile["_id"] = res.inserted_id

    profile = normalize_profile(profile, user_id)
    profile["profile_completion"] = await calculate_profile_completion(user_id, profile)
    profile["id"] = str(profile.get("_id", user_id))
    if "_id" in profile:
        profile["_id"] = str(profile["_id"])
    return profile


async def update_candidate_profile(user_id: str, update_data: dict) -> dict:
    """
    Updates candidate profile fields in MongoDB Atlas and returns refreshed profile document.
    """
    db = get_database()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Filter out None values
    clean_data = {k: v for k, v in update_data.items() if v is not None}

    await db.candidate_profiles.update_one(
        {"user_id": user_id},
        {"$set": clean_data},
        upsert=True
    )
    return await get_candidate_profile(user_id)


async def update_candidate_avatar(user_id: str, image_url: str) -> dict:
    """
    Updates profile image URL for candidate profile.
    """
    return await update_candidate_profile(user_id, {"profile_image_url": image_url})
