"""
FastAPI Authentication API Routes for Candidate & Recruiter Management.
Implements Phase 1 Recruiter Authentication & Email Verification Architecture:
- POST /auth/recruiter/register (Generates OTP, stores temp data, sends email - NO account created yet)
- POST /auth/recruiter/verify-email (Verifies OTP, creates recruiter account, sends welcome email)
- POST /auth/recruiter/login (Validates password & email_verified, returns JWT token)
- POST /auth/recruiter/forgot-password (Generates reset OTP, sends email)
- POST /auth/recruiter/reset-password (Verifies OTP, updates bcrypt password, invalidates previous sessions)
- GET  /auth/me
- POST /auth/logout
"""

import secrets
from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import (
    CandidateRegisterSchema,
    CandidateLoginSchema,
    RecruiterRegisterRequest,
    RecruiterVerifyEmailRequest,
    RecruiterLoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.database.auth_db import (
    find_user_by_email,
    create_candidate,
)
from app.database.recruiter_auth_db import (
    find_recruiter_by_email,
    create_recruiter_account,
    update_recruiter_password,
)
from app.database.otp_db import (
    store_otp,
    verify_otp,
    delete_otp,
    check_resend_allowed,
    increment_resend_count,
)
from app.database.profile_db import get_candidate_profile
from app.core.security import hash_password, verify_password, create_access_token
from app.services.email_service import EmailService
from app.api.v1.auth.dependencies import get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])


def _generate_6digit_otp() -> str:
    """Generates cryptographically secure 6-digit OTP string."""
    return str(secrets.randbelow(900000) + 100000)


# ==========================================
# CANDIDATE AUTHENTICATION ENDPOINTS (STABLE)
# ==========================================

@router.post("/candidate/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_candidate(body: CandidateRegisterSchema):
    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    existing_user = await find_user_by_email(body.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    user_data = body.model_dump()
    user_info = await create_candidate(user_data)
    access_token = create_access_token(data={"sub": user_info["id"], "role": "candidate", "email": user_info["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "candidate",
        "user": user_info
    }


@router.post("/candidate/login", response_model=TokenResponse)
async def login_candidate(body: CandidateLoginSchema):
    user = await find_user_by_email(body.email)
    if not user or user.get("role") != "candidate":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    user_id = str(user["_id"])
    profile = await get_candidate_profile(user_id)

    user_info = {
        "id": user_id,
        "name": user["name"],
        "email": user["email"],
        "role": "candidate",
        "title": profile.get("professional_information", {}).get("current_job_title", "Candidate") if profile else "Candidate",
        "avatar": profile.get("profile_image_url", "") if profile else ""
    }

    access_token = create_access_token(data={"sub": user_id, "role": "candidate", "email": user["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "candidate",
        "user": user_info
    }


# ==========================================
# PHASE 1 RECRUITER AUTHENTICATION ENDPOINTS
# ==========================================

@router.post("/recruiter/register", status_code=status.HTTP_200_OK)
async def register_recruiter_step1(body: RecruiterRegisterRequest):
    """
    Step 1: Validates recruiter registration details.
    Generates 6-digit OTP, stores temporary registration data in db.otp_tokens, and sends OTP email.
    CRITICAL: Does NOT create user account in MongoDB until email OTP is verified!
    """
    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match. Please verify password confirmation."
        )
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )

    clean_email = body.email.lower().strip()
    existing_user = await find_user_by_email(clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    # Check resend attempt rate limits
    allowed, resend_msg = await check_resend_allowed(clean_email, "REGISTER")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=resend_msg
        )

    # Hash password with bcrypt
    hashed_pwd = hash_password(body.password)
    temp_payload = {
        "name": body.name.strip(),
        "email": clean_email,
        "password_hash": hashed_pwd
    }

    # Generate 6-digit OTP and store in db.otp_tokens (SHA-256 hashed)
    otp_code = _generate_6digit_otp()
    await store_otp(
        email=clean_email,
        otp_code=otp_code,
        purpose="REGISTER",
        temp_data=temp_payload
    )

    # Dispatch OTP email via Centralized Email Service
    EmailService.send_otp(clean_email, body.name.strip(), otp_code, purpose="REGISTER")

    return {
        "message": "Verification OTP sent successfully to your email address. Please enter code to complete registration.",
        "email": clean_email
    }


@router.post("/recruiter/verify-email", status_code=status.HTTP_201_CREATED)
async def verify_recruiter_email(body: RecruiterVerifyEmailRequest):
    """
    Step 2: Verifies 6-digit OTP code against db.otp_tokens.
    Upon successful OTP match:
    - Creates Recruiter account in MongoDB Atlas (role='recruiter', email_verified=True, profile_completed=False)
    - Deletes OTP token document immediately
    - Sends Welcome Email
    """
    clean_email = body.email.lower().strip()
    
    # Verify OTP
    is_valid, msg, temp_data = await verify_otp(
        email=clean_email,
        otp_code=body.otp_code.strip(),
        purpose="REGISTER"
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    if not temp_data or "name" not in temp_data or "password_hash" not in temp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration session data missing or expired. Please register again."
        )

    # Check again if account was created in parallel
    existing = await find_recruiter_by_email(clean_email)
    if existing:
        await delete_otp(clean_email, "REGISTER")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already verified and registered."
        )

    # Create Recruiter document in db.users
    recruiter_account = await create_recruiter_account(temp_data)

    # Delete OTP token document immediately
    await delete_otp(clean_email, "REGISTER")

    # Send Welcome Email
    EmailService.send_welcome_email(clean_email, recruiter_account["name"])

    # Issue JWT token
    access_token = create_access_token(data={
        "sub": recruiter_account["id"],
        "role": "recruiter",
        "email": clean_email,
        "token_version": recruiter_account.get("token_version", 1)
    })

    return {
        "message": "Recruiter email verified and account successfully created!",
        "access_token": access_token,
        "token_type": "bearer",
        "role": "recruiter",
        "user": {
            "id": recruiter_account["id"],
            "name": recruiter_account["name"],
            "email": recruiter_account["email"],
            "role": "recruiter",
            "email_verified": True,
            "profile_completed": False
        }
    }


@router.post("/recruiter/login", response_model=TokenResponse)
async def login_recruiter(body: RecruiterLoginRequest):
    """
    Authenticates recruiter credentials, checks email_verified==True, and returns JWT token.
    """
    clean_email = body.email.lower().strip()
    user = await find_user_by_email(clean_email)
    
    if not user or user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    if not user.get("email_verified", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please verify your email before signing in."
        )

    user_id = str(user["_id"])
    token_version = user.get("token_version", 1)
    profile_completed = user.get("profile_completed", False)

    user_info = {
        "id": user_id,
        "name": user["name"],
        "email": user["email"],
        "role": "recruiter",
        "email_verified": True,
        "profile_completed": profile_completed
    }

    access_token = create_access_token(data={
        "sub": user_id,
        "role": "recruiter",
        "email": user["email"],
        "token_version": token_version
    })

    logger.info(f"Logged in Recruiter: {clean_email} (Profile Completed: {profile_completed})")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "recruiter",
        "user": user_info
    }


@router.post("/recruiter/forgot-password")
async def forgot_password_recruiter(body: ForgotPasswordRequest):
    """
    Generates 6-digit password reset OTP code and dispatches email.
    Deletes any previous PASSWORD_RESET OTP for this email first.
    """
    clean_email = body.email.lower().strip()
    recruiter = await find_user_by_email(clean_email)
    
    if not recruiter or recruiter.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recruiter account found matching this email address."
        )

    allowed, resend_msg = await check_resend_allowed(clean_email, "PASSWORD_RESET")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=resend_msg
        )

    otp_code = _generate_6digit_otp()
    await store_otp(
        email=clean_email,
        otp_code=otp_code,
        purpose="PASSWORD_RESET"
    )

    EmailService.send_password_reset(clean_email, recruiter.get("name", "Recruiter"), otp_code)

    return {
        "message": "Password reset 6-digit verification code sent to your email address.",
        "email": clean_email
    }


@router.post("/recruiter/reset-password")
async def reset_password_recruiter(body: ResetPasswordRequest):
    """
    Verifies 6-digit OTP code and updates recruiter bcrypt password hash.
    Deletes OTP token immediately and increments token_version to invalidate previous JWTs.
    """
    if body.new_password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match. Please verify password confirmation."
        )
    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters in length."
        )

    clean_email = body.email.lower().strip()
    is_valid, msg, _ = await verify_otp(
        email=clean_email,
        otp_code=body.otp_code.strip(),
        purpose="PASSWORD_RESET"
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    new_pwd_hash = hash_password(body.new_password)
    updated = await update_recruiter_password(clean_email, new_pwd_hash)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password. Please check user account."
        )

    await delete_otp(clean_email, "PASSWORD_RESET")

    return {
        "message": "Password reset successfully! You can now log in with your new password."
    }


# ==========================================
# SESSION & USER PROFILE ENDPOINTS
# ==========================================

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    role = current_user.get("role")

    if role == "candidate":
        profile = await get_candidate_profile(user_id)
        personal = profile.get("personal_information", {}) if profile else {}
        professional = profile.get("professional_information", {}) if profile else {}
        return {
            "user": {
                "id": user_id,
                "name": current_user.get("name", "Candidate"),
                "email": current_user.get("email"),
                "role": "candidate",
                "phone": personal.get("phone", ""),
                "location": personal.get("location", ""),
                "title": professional.get("current_job_title", "Candidate"),
                "avatar": profile.get("profile_image_url", "") if profile else ""
            }
        }
    else:
        return {
            "user": {
                "id": user_id,
                "name": current_user.get("name", "Recruiter"),
                "email": current_user.get("email"),
                "role": "recruiter",
                "email_verified": current_user.get("email_verified", True),
                "profile_completed": current_user.get("profile_completed", False)
            }
        }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    logger.info(f"Logged out user: {current_user['email']}")
    return {"message": "Logged out successfully."}
