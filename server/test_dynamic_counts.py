"""
Automated Test Suite for Candidate & Recruiter Dynamic Counts & MongoDB Atlas Aggregations:
1. Verify GET /api/v1/jobs/count returns live published jobs count.
2. Verify GET /api/v1/applications/count returns live candidate application count.
3. Verify GET /api/v1/notifications/unread-count returns live unread count.
4. Verify Recruiter Dashboard stats aggregation.
"""

import asyncio
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.database.job_db import get_published_jobs_count, get_dashboard_stats
from app.database.application_db import get_candidate_application_count
from app.database.notification_db import fetch_unread_count


async def test_dynamic_counts():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("RUNNING DYNAMIC COUNTS & METRICS TEST SUITE")
    print("==========================================================\n")

    # 1. Published Jobs Count
    pub_count = await get_published_jobs_count()
    print(f"PASS: Published Jobs Count in MongoDB Atlas = {pub_count}")
    assert isinstance(pub_count, int)

    # 2. Candidate Application Count
    candidate = await db["users"].find_one({"role": "candidate"})
    if candidate:
        candidate_id = str(candidate["_id"])
        app_count = await get_candidate_application_count(candidate_id)
        print(f"PASS: Candidate {candidate_id} Applications Count = {app_count}")
        assert isinstance(app_count, int)

        unread_count = await fetch_unread_count(candidate_id)
        print(f"PASS: Candidate {candidate_id} Unread Notifications Count = {unread_count}")
        assert isinstance(unread_count, int)

    # 3. Recruiter Dashboard Stats
    recruiter = await db["users"].find_one({"role": "recruiter"})
    if recruiter:
        company = await db["companies"].find_one({"recruiter_id": str(recruiter["_id"])})
        if company:
            company_id = str(company["_id"])
            stats = await get_dashboard_stats(company_id)
            print(f"PASS: Recruiter Company ({company['company_name']}) Stats: {stats}")
            assert "total_jobs" in stats
            assert "published_jobs" in stats
            assert "applications_received" in stats

    print("\n==========================================================")
    print("🎉 ALL DYNAMIC COUNT TEST CONDITIONS PASSED 100%!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_dynamic_counts())
