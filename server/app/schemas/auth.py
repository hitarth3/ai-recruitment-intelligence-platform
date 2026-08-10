"""
Pydantic Schemas for Authentication, User Registration & Email OTP Verification.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


# Candidate Registration Schema
class CandidateRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, description="Candidate full name")
    email: EmailStr = Field(..., description="Valid candidate email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    confirm_password: str = Field(..., min_length=6, description="Password confirmation")
    phone: str = Field(..., description="Phone number")
    location: str = Field(..., description="Candidate location")
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None


# Candidate Login Schema
class CandidateLoginSchema(BaseModel):
    email: EmailStr
    password: str


# Phase 1 Recruiter Registration Request Schema (Step 1 - Account Details only)
class RecruiterRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Recruiter full name")
    email: EmailStr = Field(..., description="Recruiter email address (any domain)")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    confirm_password: str = Field(..., min_length=6, description="Password confirmation")


# Legacy / Detailed Recruiter Registration Schema
class RecruiterRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, description="Recruiter full name")
    email: EmailStr = Field(..., description="Official work email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    confirm_password: str = Field(..., min_length=6, description="Password confirmation")


# Email OTP Verification Request Schema
class RecruiterVerifyEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Recruiter email address")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


# Recruiter Login Request Schema
class RecruiterLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Recruiter email address")
    password: str = Field(..., description="Password")


# Recruiter Login Schema (Alias)
class RecruiterLoginSchema(BaseModel):
    email: EmailStr
    password: str


# Forgot Password Request Schema
class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address")


# Reset Password Request Schema
class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    new_password: str = Field(..., min_length=6, description="New password")
    confirm_password: str = Field(..., min_length=6, description="Confirm new password")


# Token Response Schema
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: Dict[str, Any]
