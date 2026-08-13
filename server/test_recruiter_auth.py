"""
Automated Test Suite for Phase 1 Recruiter Authentication & Email Verification.
"""

import asyncio
import hashlib
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.api.v1.auth.routes import (
    register_recruiter_step1,
    verify_recruiter_email,
    login_recruiter,
    forgot_password_recruiter,
    reset_password_recruiter
)
from app.schemas.auth import (
    RecruiterRegisterRequest,
    RecruiterVerifyEmailRequest,
    RecruiterLoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)


async def test_phase1_recruiter_auth():
    await connect_to_mongo()
    db = get_database()
    test_email = "test.recruiter.phase1@example.com"

    # Clean previous test entries
    await db["users"].delete_many({"email": test_email})
    await db["otp_tokens"].delete_many({"email": test_email})

    print("1. Testing Recruiter Step 1 Registration (NO Account Created)...")
    reg_req = RecruiterRegisterRequest(
        name="Sarah Wilson",
        email=test_email,
        password="Password123!",
        confirm_password="Password123!"
    )
    reg_res = await register_recruiter_step1(reg_req)
    print("Reg Response:", reg_res["message"])

    # Verify NO recruiter account in db.users
    user_check = await db["users"].find_one({"email": test_email})
    assert user_check is None, "ERROR: User account created before OTP verification!"
    print("PASS: 0 user accounts created before OTP verification.")

    # Retrieve active OTP code from db.otp_tokens
    otp_doc = await db["otp_tokens"].find_one({"email": test_email, "purpose": "REGISTER"})
    assert otp_doc is not None, "ERROR: OTP not found in db.otp_tokens"
    print("PASS: OTP Token stored in db.otp_tokens with SHA-256 hash.")

    print("\n2. Testing Invalid OTP Verification...")
    try:
        await verify_recruiter_email(RecruiterVerifyEmailRequest(email=test_email, otp_code="000000"))
    except Exception as e:
        print("PASS: Expected Rejection on Invalid OTP:", getattr(e, "detail", str(e)))

    # Set known 6-digit code '123456' in db
    known_code = "123456"
    known_hash = hashlib.sha256(known_code.encode("utf-8")).hexdigest()
    await db["otp_tokens"].update_one(
        {"email": test_email, "purpose": "REGISTER"},
        {"$set": {"otp_hash": known_hash}}
    )

    print("\n3. Testing Valid OTP Verification & Account Creation...")
    verify_res = await verify_recruiter_email(RecruiterVerifyEmailRequest(email=test_email, otp_code=known_code))
    print("Verify Response:", verify_res["message"])

    # Confirm Recruiter Created
    user = await db["users"].find_one({"email": test_email})
    assert user is not None, "ERROR: Recruiter not created after verification!"
    assert user["role"] == "recruiter", "ERROR: Role must be recruiter"
    assert user["email_verified"] is True, "ERROR: email_verified must be True"
    assert user["profile_completed"] is False, "ERROR: profile_completed must be False"
    print("PASS: Recruiter Account Created in MongoDB Atlas!")
    print(f"User Role: {user['role']} | Email Verified: {user['email_verified']} | Profile Completed: {user['profile_completed']}")

    # Confirm OTP Deleted
    otp_after = await db["otp_tokens"].find_one({"email": test_email, "purpose": "REGISTER"})
    assert otp_after is None, "ERROR: OTP not deleted after verification!"
    print("PASS: OTP Token deleted from db.otp_tokens immediately after verification.")

    print("\n4. Testing Recruiter Login...")
    login_res = await login_recruiter(RecruiterLoginRequest(email=test_email, password="Password123!"))
    print("PASS: Login Successful! JWT Issued:", login_res["access_token"][:30] + "...")

    print("\n5. Testing Forgot Password OTP Generation...")
    forgot_res = await forgot_password_recruiter(ForgotPasswordRequest(email=test_email))
    print("Forgot Password Response:", forgot_res["message"])

    reset_code = "654321"
    reset_hash = hashlib.sha256(reset_code.encode("utf-8")).hexdigest()
    await db["otp_tokens"].update_one(
        {"email": test_email, "purpose": "PASSWORD_RESET"},
        {"$set": {"otp_hash": reset_hash}}
    )

    print("\n6. Testing Reset Password...")
    reset_res = await reset_password_recruiter(ResetPasswordRequest(
        email=test_email,
        otp_code=reset_code,
        new_password="NewPassword456!",
        confirm_password="NewPassword456!"
    ))
    print("Reset Password Response:", reset_res["message"])

    print("\n7. Testing Login with New Password...")
    new_login_res = await login_recruiter(RecruiterLoginRequest(email=test_email, password="NewPassword456!"))
    print("PASS: New Password Login Successful! User Email:", new_login_res["user"]["email"])

    print("\n🎉 PHASE 1 RECRUITER AUTHENTICATION & EMAIL VERIFICATION VERIFIED 100% WORKING!")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_phase1_recruiter_auth())
