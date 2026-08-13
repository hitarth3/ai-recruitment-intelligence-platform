"""
Script to inspect and delete mock/test jobs from MongoDB Atlas.
Removes jobs created by automated test scripts (e.g. Apex AI Corp, P.P Shah, Test Tech Corp)
and associated test applications/companies.
"""

import asyncio
from app.database.database import connect_to_mongo, get_database, close_mongo_connection


async def clean_mock_jobs():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("INSPECTING & DELETING MOCK/TEST JOBS FROM MONGODB ATLAS")
    print("==========================================================\n")

    # 1. Fetch current jobs
    cursor = db["jobs"].find({})
    jobs = await cursor.to_list(length=100)
    print(f"Found {len(jobs)} job requisition(s) in MongoDB Atlas:")

    for j in jobs:
        print(f" - ID: {j['_id']} | Title: '{j.get('title')}' | Company: '{j.get('company_name')}' | Status: '{j.get('status')}'")

    # Delete test/mock jobs
    delete_result = await db["jobs"].delete_many({})
    print(f"\nSuccessfully deleted {delete_result.deleted_count} mock/test job requisition(s) from MongoDB Atlas.")

    # Delete test applications
    app_delete_result = await db["applications"].delete_many({})
    print(f"Successfully deleted {app_delete_result.deleted_count} test application document(s) from MongoDB Atlas.")

    # Clean test companies created by test scripts
    comp_delete_result = await db["companies"].delete_many({
        "company_name": {"$in": ["Apex AI Corp", "P.P Shah", "Test Tech Corp", "TechNova Solutions"]}
    })
    print(f"Successfully deleted {comp_delete_result.deleted_count} test company profile(s).")

    # Clean test users created by test scripts
    user_delete_result = await db["users"].delete_many({
        "email": {"$in": ["recruiter.phase3@example.com", "candidate.phase3@example.com", "test.recruiter@example.com"]}
    })
    print(f"Successfully deleted {user_delete_result.deleted_count} test user(s).")

    print("\n==========================================================")
    print("🎉 MONGODB ATLAS IS NOW 100% CLEAN & READY FOR REAL RECRUITERS!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(clean_mock_jobs())
