"""
MongoDB Database Handler for Authentication, User Profiles, and Companies.
Performs async Motor operations on MongoDB Atlas collections: users, candidate_profiles, recruiter_profiles, companies.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.database.database import get_database
from app.core.security import hash_password


async def find_user_by_email(email: str) -> dict | None:
    """
    Finds a user by email address in MongoDB Atlas users collection.
    """
    db = get_database()
    return await db.users.find_one({"email": email.lower()})


async def create_candidate(data: dict) -> dict:
    """
    Registers a new candidate user and creates candidate_profile document in MongoDB Atlas.
    """
    db = get_database()
    
    # 1. Create User document
    user_doc = {
        "email": data["email"].lower(),
        "password_hash": hash_password(data["password"]),
        "role": "candidate",
        "name": data["name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    user_result = await db.users.insert_one(user_doc)
    user_id = str(user_result.inserted_id)

    # 2. Create Candidate Profile document
    profile_doc = {
        "user_id": user_id,
        "name": data["name"],
        "email": data["email"].lower(),
        "phone": data.get("phone", ""),
        "location": data.get("location", ""),
        "title": "Software Engineering Candidate",
        "skills": ["Python", "JavaScript", "React", "FastAPI"],
        "github": data.get("github", ""),
        "linkedin": data.get("linkedin", ""),
        "portfolio": data.get("portfolio", ""),
        "profile_completion": 85,
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.candidate_profiles.insert_one(profile_doc)

    return {
        "id": user_id,
        "name": data["name"],
        "email": data["email"].lower(),
        "role": "candidate",
        "title": "Software Engineering Candidate"
    }


async def create_recruiter(data: dict) -> dict:
    """
    Registers a new recruiter user, creates/links company, and creates recruiter_profile in MongoDB Atlas.
    """
    db = get_database()
    
    # 1. Check or create Company document
    company_name = data["company_name"]
    company = await db.companies.find_one({"name": company_name})
    if not company:
        company_doc = {
            "name": company_name,
            "logo": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&auto=format&fit=crop&q=80",
            "industry": data.get("industry", "Software & Technology"),
            "size": data.get("company_size", "50-200 Employees"),
            "location": data.get("location", "San Francisco, CA"),
            "website": data.get("company_website", "https://example.com"),
            "description": f"{company_name} is an enterprise software organization.",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        comp_result = await db.companies.insert_one(company_doc)
        company_id = str(comp_result.inserted_id)
    else:
        company_id = str(company["_id"])

    # 2. Create User document
    user_doc = {
        "email": data["email"].lower(),
        "password_hash": hash_password(data["password"]),
        "role": "recruiter",
        "name": data["name"],
        "company_id": company_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    user_result = await db.users.insert_one(user_doc)
    user_id = str(user_result.inserted_id)

    # 3. Create Recruiter Profile document (with is_verified = False)
    recruiter_profile = {
        "user_id": user_id,
        "company_id": company_id,
        "company_name": company_name,
        "name": data["name"],
        "email": data["email"].lower(),
        "designation": data.get("designation", "Recruiter"),
        "is_verified": False,  # Recruiter verification badge requirement
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=100&auto=format&fit=crop&q=80",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.recruiter_profiles.insert_one(recruiter_profile)

    return {
        "id": user_id,
        "name": data["name"],
        "email": data["email"].lower(),
        "role": "recruiter",
        "company_id": company_id,
        "company_name": company_name,
        "designation": data.get("designation", "Recruiter"),
        "is_verified": False
    }


async def get_candidate_profile_by_user_id(user_id: str) -> dict | None:
    """
    Fetches candidate profile from candidate_profiles collection.
    """
    db = get_database()
    return await db.candidate_profiles.find_one({"user_id": user_id})


async def get_recruiter_profile_by_user_id(user_id: str) -> dict | None:
    """
    Fetches recruiter profile from recruiter_profiles collection.
    """
    db = get_database()
    return await db.recruiter_profiles.find_one({"user_id": user_id})
