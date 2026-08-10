"""
MongoDB Atlas Company Collection Handler.
Manages company profile CRUD, link between Recruiter and Company,
and dynamic profile completion calculation.
Default verification_status = "Self Registered".
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from bson import ObjectId
from app.database.database import get_database
from app.utils.logger import logger


def calculate_company_completion(company: Dict[str, Any]) -> Tuple[int, List[str]]:
    """
    Dynamically computes company profile completion percentage (0 - 100%)
    and returns a list of missing fields to guide recruiters.
    Do NOT store static percentage in the database.
    """
    total_score = 0
    missing_fields = []

    # 1. Basic Info
    if company.get("company_name"):
        total_score += 15
    else:
        missing_fields.append("Company Name")

    if company.get("industry"):
        total_score += 10
    else:
        missing_fields.append("Industry")

    if company.get("company_size"):
        total_score += 10
    else:
        missing_fields.append("Company Size")

    if company.get("company_logo"):
        total_score += 10
    else:
        missing_fields.append("Company Logo")

    # 2. Contact & Web
    if company.get("website"):
        total_score += 5
    else:
        missing_fields.append("Website URL")

    if company.get("linkedin"):
        total_score += 5
    else:
        missing_fields.append("LinkedIn Company Page")

    if company.get("company_email") or company.get("company_phone"):
        total_score += 5
    else:
        missing_fields.append("Contact Information (Email/Phone)")

    # 3. Location
    if company.get("country") and company.get("city"):
        total_score += 10
    else:
        missing_fields.append("Location (Country & City)")

    # 4. About & Culture
    if company.get("description") and len(company.get("description", "")) >= 20:
        total_score += 15
    else:
        missing_fields.append("Company Description")

    if company.get("mission") or company.get("vision") or company.get("culture"):
        total_score += 10
    else:
        missing_fields.append("Mission, Vision or Culture statement")

    if company.get("benefits") and len(company.get("benefits", [])) > 0:
        total_score += 5
    else:
        missing_fields.append("Company Perks & Benefits")

    percentage = min(100, total_score)
    return percentage, missing_fields


async def get_company_by_id(company_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves company profile by ObjectId or string ID safely.
    Ensures _id and id are string values to prevent Pydantic serialization errors.
    """
    try:
        db = get_database()
        company = None
        try:
            company = await db["companies"].find_one({"_id": ObjectId(company_id)})
        except Exception:
            company = await db["companies"].find_one({"_id": company_id})

        if company:
            company["_id"] = str(company["_id"])
            company["id"] = company["_id"]
            comp_perc, missing = calculate_company_completion(company)
            company["profile_completion_percentage"] = comp_perc
            company["missing_fields"] = missing
        return company
    except Exception as err:
        logger.error(f"Error finding company by ID {company_id}: {err}")
        return None


async def get_company_by_recruiter_id(recruiter_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves company associated with recruiter user ID or created_by field.
    Handles ObjectId string conversion safely to avoid InvalidId exceptions.
    Ensures _id and id are string values to prevent Pydantic serialization errors.
    """
    try:
        db = get_database()
        
        user = None
        try:
            user = await db["users"].find_one({"_id": ObjectId(recruiter_id)})
        except Exception:
            user = await db["users"].find_one({"_id": recruiter_id})
        
        company = None
        if user and user.get("company_id"):
            comp_id_raw = str(user["company_id"])
            try:
                company = await db["companies"].find_one({"_id": ObjectId(comp_id_raw)})
            except Exception:
                company = await db["companies"].find_one({"_id": comp_id_raw})
        
        if not company:
            try:
                company = await db["companies"].find_one({"created_by": recruiter_id})
            except Exception:
                pass

        if not company:
            try:
                company = await db["companies"].find_one({"created_by": str(recruiter_id)})
            except Exception:
                pass

        if company:
            company["_id"] = str(company["_id"])
            company["id"] = company["_id"]
            comp_perc, missing = calculate_company_completion(company)
            company["profile_completion_percentage"] = comp_perc
            company["missing_fields"] = missing

        return company
    except Exception as err:
        logger.error(f"Error finding company by recruiter {recruiter_id}: {err}")
        return None


async def create_company_profile(recruiter_id: str, company_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new Company Profile document in db.companies safely.
    Default verification_status = "Self Registered".
    Updates Recruiter user document in db.users: sets company_id and profile_completed = True.
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    doc = {
        "company_name": str(company_payload.get("company_name") or "Company").strip(),
        "company_logo": company_payload.get("company_logo", ""),
        "industry": str(company_payload.get("industry") or "Software & IT").strip(),
        "company_size": str(company_payload.get("company_size") or "51-200 employees").strip(),
        "company_type": company_payload.get("company_type", "Product"),
        "founded_year": company_payload.get("founded_year"),
        "website": str(company_payload.get("website") or "").strip(),
        "linkedin": str(company_payload.get("linkedin") or "").strip(),
        "company_email": company_payload.get("company_email", ""),
        "company_phone": str(company_payload.get("company_phone") or "").strip(),
        "country": str(company_payload.get("country") or "").strip(),
        "state": str(company_payload.get("state") or "").strip(),
        "city": str(company_payload.get("city") or "").strip(),
        "postal_code": str(company_payload.get("postal_code") or "").strip(),
        "description": str(company_payload.get("description") or "").strip(),
        "mission": str(company_payload.get("mission") or "").strip(),
        "vision": str(company_payload.get("vision") or "").strip(),
        "culture": str(company_payload.get("culture") or "").strip(),
        "benefits": company_payload.get("benefits", []),
        "work_mode": company_payload.get("work_mode", "Hybrid"),
        "social_links": company_payload.get("social_links", {}),
        "verification_status": "Self Registered",
        "created_by": str(recruiter_id),
        "created_at": now,
        "updated_at": now
    }

    result = await db["companies"].insert_one(doc)
    company_id_str = str(result.inserted_id)
    doc["_id"] = company_id_str
    doc["id"] = company_id_str

    try:
        user_query = {"_id": ObjectId(recruiter_id)}
    except Exception:
        user_query = {"_id": recruiter_id}

    await db["users"].update_one(
        user_query,
        {
            "$set": {
                "company_id": company_id_str,
                "company_name": doc["company_name"],
                "profile_completed": True,
                "updated_at": now
            }
        }
    )

    comp_perc, missing = calculate_company_completion(doc)
    doc["profile_completion_percentage"] = comp_perc
    doc["missing_fields"] = missing

    logger.info(f"Created Company Profile: '{doc['company_name']}' [ID: {company_id_str}] for Recruiter {recruiter_id}")
    return doc


async def update_company_profile(company_id: str, update_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Updates an existing company profile safely.
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    clean_data = {k: v for k, v in update_payload.items() if v is not None}
    clean_data["updated_at"] = now

    try:
        query = {"_id": ObjectId(company_id)}
    except Exception:
        query = {"_id": company_id}

    await db["companies"].update_one(
        query,
        {"$set": clean_data}
    )

    updated_company = await get_company_by_id(company_id)
    if updated_company:
        updated_company["_id"] = str(updated_company["_id"])
        updated_company["id"] = updated_company["_id"]
        if "company_name" in clean_data:
            await db["users"].update_many(
                {"company_id": company_id},
                {"$set": {"company_name": clean_data["company_name"]}}
            )

    logger.info(f"Updated Company Profile ID: {company_id}")
    return updated_company


async def update_company_logo(company_id: str, logo_uri: str) -> Optional[Dict[str, Any]]:
    """
    Updates company logo image URI.
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    try:
        query = {"_id": ObjectId(company_id)}
    except Exception:
        query = {"_id": company_id}

    await db["companies"].update_one(
        query,
        {"$set": {"company_logo": logo_uri, "updated_at": now}}
    )
    ret = await get_company_by_id(company_id)
    if ret:
        ret["_id"] = str(ret["_id"])
        ret["id"] = ret["_id"]
    return ret
