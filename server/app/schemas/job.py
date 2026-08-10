"""
Pydantic Schemas for Multi-Step Job Posting Wizard & Job Requisition Management.
Validates 7-step wizard fields: Basic Info, Location, Exp & Salary, Skills, Description, Settings, Preview.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class JobLocationSchema(BaseModel):
    country: Optional[str] = ""
    state: Optional[str] = ""
    city: Optional[str] = ""
    work_mode: Optional[str] = "Hybrid"  # Hybrid | Remote | Onsite


class JobExperienceSchema(BaseModel):
    min_years: int = Field(0, ge=0)
    max_years: int = Field(0, ge=0)


class JobSalarySchema(BaseModel):
    min_salary: Optional[float] = 0
    max_salary: Optional[float] = 0
    currency: Optional[str] = "USD"
    is_negotiable: Optional[bool] = False


class JobEducationSchema(BaseModel):
    required_degree: Optional[str] = "Bachelor's Degree"
    preferred_degree: Optional[str] = ""


class JobSkillsSchema(BaseModel):
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    technologies: List[str] = []
    frameworks: List[str] = []
    databases: List[str] = []
    cloud: List[str] = []
    tools: List[str] = []
    soft_skills: List[str] = []
    languages: List[str] = []


class JobSettingsSchema(BaseModel):
    deadline: Optional[str] = ""
    joining_date: Optional[str] = ""
    allow_freshers: Optional[bool] = False
    visa_sponsorship: Optional[bool] = False


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, description="Job Title (Required)")
    department: str = Field(..., min_length=2, description="Department (Required)")
    category: str = Field(..., min_length=2, description="Job Category (Required)")
    employment_type: str = Field("Full-time", description="Full-time | Part-time | Contract | Internship")
    open_positions: int = Field(1, ge=1)

    location: Optional[JobLocationSchema] = JobLocationSchema()
    experience: Optional[JobExperienceSchema] = JobExperienceSchema()
    salary: Optional[JobSalarySchema] = JobSalarySchema()
    education: Optional[JobEducationSchema] = JobEducationSchema()
    skills: Optional[JobSkillsSchema] = JobSkillsSchema()

    description: str = Field(..., min_length=20, description="Detailed Description (Required)")
    responsibilities: Optional[List[str]] = []
    requirements: Optional[List[str]] = []
    benefits: Optional[List[str]] = []

    settings: Optional[JobSettingsSchema] = JobSettingsSchema()
    status: Optional[str] = "Published"  # Draft | Published | Closed | Archived


class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = None
    employment_type: Optional[str] = None
    open_positions: Optional[int] = None

    location: Optional[JobLocationSchema] = None
    experience: Optional[JobExperienceSchema] = None
    salary: Optional[JobSalarySchema] = None
    education: Optional[JobEducationSchema] = None
    skills: Optional[JobSkillsSchema] = None

    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None

    settings: Optional[JobSettingsSchema] = None
    status: Optional[str] = None


class JobStatusPatchRequest(BaseModel):
    status: str = Field(..., description="Draft | Published | Closed | Archived")


class JobResponse(BaseModel):
    id: str
    company_id: str
    recruiter_id: str
    company_name: str
    company_logo: Optional[str] = ""
    title: str
    department: str
    category: str
    employment_type: str
    open_positions: int
    location: Dict[str, Any]
    experience: Dict[str, Any]
    salary: Dict[str, Any]
    education: Dict[str, Any]
    skills: Dict[str, Any]
    description: str
    responsibilities: List[str] = []
    requirements: List[str] = []
    benefits: List[str] = []
    settings: Dict[str, Any]
    status: str
    applications_count: int = 0
    views_count: int = 0
    created_at: Any
    updated_at: Any
