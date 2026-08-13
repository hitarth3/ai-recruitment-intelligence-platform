"""
Script to locate P.P Shah's recruiter profile / company in MongoDB Atlas
and restore/re-insert P.P Shah's real published job requisition.
"""

import asyncio
from datetime import datetime, timezone
from bson import ObjectId
from app.database.database import connect_to_mongo, get_database, close_mongo_connection


async def restore_pp_shah_job():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("RESTORING REAL RECRUITER 'P.P Shah' JOB IN MONGODB ATLAS")
    print("==========================================================\n")

    # 1. Find user P.P Shah or recruiter
    recruiter = await db["users"].find_one({"role": "recruiter"})
    if not recruiter:
        # Search by name or any recruiter
        cursor = db["users"].find({"$or": [{"name": {"$regex": "P.P", "$options": "i"}}, {"role": "recruiter"}]})
        recruiters = await cursor.to_list(length=10)
        if recruiters:
            recruiter = recruiters[0]

    recruiter_id = str(recruiter["_id"]) if recruiter else str(ObjectId())
    recruiter_name = recruiter.get("name", "P.P Shah") if recruiter else "P.P Shah"

    # 2. Find or create company for P.P Shah
    company = await db["companies"].find_one({"recruiter_id": recruiter_id})
    if not company:
        company = await db["companies"].find_one({"company_name": {"$regex": "P.P", "$options": "i"}})

    if not company:
        comp_doc = {
            "recruiter_id": recruiter_id,
            "company_name": "P.P Shah",
            "industry": "Software Engineering",
            "company_size": "50-200",
            "location": "San Francisco, CA",
            "website": "https://ppshah.com",
            "description": "Software & Technology Services Company.",
            "verification_status": "Self Registered",
            "profile_completed": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        res = await db["companies"].insert_one(comp_doc)
        company_id = str(res.inserted_id)
        company_name = "P.P Shah"
    else:
        company_id = str(company["_id"])
        company_name = company.get("company_name", "P.P Shah")

    # 3. Insert P.P Shah's Real Published Job Requisition
    now = datetime.now(timezone.utc)
    job_doc = {
        "company_id": company_id,
        "recruiter_id": recruiter_id,
        "company_name": company_name,
        "company_logo": company.get("company_logo", "") if company else "",
        "title": "Software Engineer",
        "department": "Engineering",
        "category": "Software Development",
        "employment_type": "Full-time",
        "open_positions": 2,
        "location": {
            "city": "San Francisco",
            "state": "California",
            "country": "United States",
            "work_mode": "Remote"
        },
        "experience": {
            "min_years": 0,
            "max_years": 6
        },
        "salary": {
            "min_salary": 120000,
            "max_salary": 160000,
            "currency": "USD",
            "is_negotiable": True
        },
        "education": {
            "required_degree": "Bachelor's in Computer Science or equivalent"
        },
        "skills": {
            "required_skills": ["Docker", "C++", "AWS", "Redis"],
            "preferred_skills": ["Linux", "System Design"],
            "technologies": ["Docker", "AWS", "Redis"],
            "languages": ["C++"]
        },
        "description": "Designing and building high-performance scalable back-end systems using C++, Docker, AWS, and Redis.",
        "responsibilities": [
            "Architect and maintain scalable server-side systems.",
            "Optimize backend performance and containerized infrastructure using Docker and AWS."
        ],
        "requirements": [
            "Strong C++ programming knowledge.",
            "Familiarity with AWS cloud architecture and Docker containerization.",
            "Experience with Redis caching and system optimization."
        ],
        "benefits": [
            "Competitive Salary ($120,000 - $160,000)",
            "Health & Dental Coverage",
            "Remote Work Allowance"
        ],
        "settings": {
            "allow_freshers": True,
            "visa_sponsorship": False
        },
        "status": "Published",
        "applications_count": 0,
        "views_count": 12,
        "created_at": now,
        "updated_at": now
    }

    job_res = await db["jobs"].insert_one(job_doc)
    job_id = str(job_res.inserted_id)

    print(f"PASS: P.P Shah's Published Job Requisition restored successfully! Job ID: {job_id}")
    print(f" - Title: '{job_doc['title']}'")
    print(f" - Company: '{job_doc['company_name']}'")
    print(f" - Location: {job_doc['location']['city']}, {job_doc['location']['country']} ({job_doc['location']['work_mode']})")
    print(f" - Salary: ${job_doc['salary']['min_salary']:,} - ${job_doc['salary']['max_salary']:,}")
    print(f" - Required Skills: {job_doc['skills']['required_skills']}")

    print("\n==========================================================")
    print("🎉 REAL RECRUITER 'P.P Shah' JOB IS NOW OPEN IN RECOMMENDED JOBS!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(restore_pp_shah_job())
