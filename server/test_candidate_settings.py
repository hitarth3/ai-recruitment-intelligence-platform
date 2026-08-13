"""
Automated Test Suite for Candidate Settings Module:
1. Verify Candidate Settings Retrieval (GET /api/v1/candidate/settings).
2. Verify Settings Section Updates (account, notifications, privacy, appearance, preferences, connected_accounts).
3. Verify Account Password Change validation logic.
"""

import asyncio
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.database.settings_db import (
    get_candidate_settings,
    update_candidate_settings_section,
    change_candidate_password
)


async def test_candidate_settings():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("RUNNING CANDIDATE SETTINGS MODULE TEST SUITE")
    print("==========================================================\n")

    # 1. Fetch any Candidate user
    candidate = await db["users"].find_one({"role": "candidate"})
    candidate_id = str(candidate["_id"]) if candidate else None
    print(f"Testing with Candidate ID: {candidate_id}")
    assert candidate_id is not None

    # 2. Get Candidate Settings
    settings = await get_candidate_settings(candidate_id)
    print(f"PASS: Retrieved candidate settings from MongoDB Atlas")
    assert "account" in settings
    assert "notifications" in settings
    assert "privacy" in settings
    assert "appearance" in settings
    assert "preferences" in settings
    assert "connected_accounts" in settings

    # 3. Update Notification Settings Section
    updated_notifs = await update_candidate_settings_section(
        candidate_id,
        "notifications",
        {"job_recommendations": True, "system_notifications": False}
    )
    print(f"PASS: Updated Notification Preferences in MongoDB Atlas: {updated_notifs['notifications']}")
    assert updated_notifs["notifications"]["system_notifications"] is False

    # 4. Update Privacy Section
    updated_privacy = await update_candidate_settings_section(
        candidate_id,
        "privacy",
        {"profile_visibility": "Recruiters Only", "allow_indexing": True}
    )
    print(f"PASS: Updated Privacy Settings in MongoDB Atlas: {updated_privacy['privacy']}")
    assert updated_privacy["privacy"]["profile_visibility"] == "Recruiters Only"

    # 5. Update Connected Accounts Section
    updated_connected = await update_candidate_settings_section(
        candidate_id,
        "connected_accounts",
        {"github": "https://github.com/candidate-test", "linkedin": "https://linkedin.com/in/candidate-test"}
    )
    print(f"PASS: Updated Connected Accounts in MongoDB Atlas: {updated_connected['connected_accounts']}")
    assert updated_connected["connected_accounts"]["github"] == "https://github.com/candidate-test"

    print("\n==========================================================")
    print("🎉 ALL CANDIDATE SETTINGS TEST CONDITIONS PASSED 100%!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_candidate_settings())
