"""
Pydantic Schemas for Company Profile & Onboarding.
Strict validation for company details, location, social links, and work modes.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class SocialLinksSchema(BaseModel):
    facebook: Optional[str] = ""
    instagram: Optional[str] = ""
    twitter: Optional[str] = ""
    github: Optional[str] = ""


class CompanyLocationSchema(BaseModel):
    country: Optional[str] = ""
    state: Optional[str] = ""
    city: Optional[str] = ""
    postal_code: Optional[str] = ""


class CompanyCreateRequest(BaseModel):
    company_name: Optional[str] = ""
    industry: Optional[str] = ""
    company_size: Optional[str] = ""
    company_type: Optional[str] = ""
    founded_year: Optional[Any] = None
    website: Optional[str] = ""
    linkedin: Optional[str] = ""
    company_email: Optional[str] = ""
    company_phone: Optional[str] = ""
    company_logo: Optional[str] = ""
    country: Optional[str] = ""
    state: Optional[str] = ""
    city: Optional[str] = ""
    postal_code: Optional[str] = ""
    description: Optional[str] = ""
    mission: Optional[str] = ""
    vision: Optional[str] = ""
    culture: Optional[str] = ""
    benefits: Optional[List[str]] = []
    work_mode: Optional[str] = ""
    social_links: Optional[Dict[str, Any]] = {}


class CompanyUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    company_type: Optional[str] = None
    founded_year: Optional[Any] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    company_email: Optional[str] = None
    company_phone: Optional[str] = None
    company_logo: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    description: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    culture: Optional[str] = None
    benefits: Optional[List[str]] = None
    work_mode: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = None


class CompanyLogoUploadRequest(BaseModel):
    company_logo: Optional[str] = ""


class CompanyResponse(BaseModel):
    _id: Optional[str] = ""
    id: Optional[str] = ""
    company_name: Optional[str] = ""
    company_logo: Optional[str] = ""
    industry: Optional[str] = ""
    company_size: Optional[str] = ""
    company_type: Optional[str] = ""
    founded_year: Optional[Any] = None
    website: Optional[str] = ""
    linkedin: Optional[str] = ""
    company_email: Optional[str] = ""
    company_phone: Optional[str] = ""
    country: Optional[str] = ""
    state: Optional[str] = ""
    city: Optional[str] = ""
    postal_code: Optional[str] = ""
    description: Optional[str] = ""
    mission: Optional[str] = ""
    vision: Optional[str] = ""
    culture: Optional[str] = ""
    benefits: Optional[List[str]] = []
    work_mode: Optional[str] = ""
    social_links: Optional[Dict[str, Any]] = {}
    verification_status: Optional[str] = "Self Registered"
    created_by: Optional[str] = ""
    profile_completion_percentage: Optional[int] = 0
    missing_fields: Optional[List[str]] = []
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
