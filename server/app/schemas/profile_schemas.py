"""
Pydantic Schemas for Candidate Profile Management.
Defines schemas for Personal Info, Professional Info, Education, Experience, Projects, Certifications, and Social Links.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class EducationItem(BaseModel):
    id: Optional[str] = None
    degree: str
    institution: str
    field_of_study: str
    start_year: str
    end_year: str
    grade: Optional[str] = ""


class ExperienceItem(BaseModel):
    id: Optional[str] = None
    company: str
    position: str
    employment_type: str = "Full-time"
    start_date: str
    end_date: Optional[str] = ""
    currently_working: bool = False
    responsibilities: str = ""


class ProjectItem(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    technologies: List[str] = []
    github_url: Optional[str] = ""
    live_demo_url: Optional[str] = ""


class CertificationItem(BaseModel):
    id: Optional[str] = None
    name: str
    organization: str
    issue_date: str
    credential_url: Optional[str] = ""


class PersonalInformationSchema(BaseModel):
    name: str
    email: str  # Read-only from user
    phone: Optional[str] = ""
    date_of_birth: Optional[str] = ""
    gender: Optional[str] = ""
    location: Optional[str] = ""
    current_city: Optional[str] = ""
    country: Optional[str] = "United States"


class ProfessionalInformationSchema(BaseModel):
    current_job_title: Optional[str] = "Software Engineer"
    years_of_experience: Optional[float] = 3.0
    preferred_job_role: Optional[str] = "Full Stack Engineer"
    preferred_work_mode: Optional[str] = "Remote"  # Remote | Hybrid | On-site
    expected_salary: Optional[str] = "$140,000"
    notice_period: Optional[str] = "Immediate"


class SocialLinksSchema(BaseModel):
    github: Optional[str] = ""
    linkedin: Optional[str] = ""
    portfolio: Optional[str] = ""
    personal_website: Optional[str] = ""


class CandidateProfileUpdateSchema(BaseModel):
    personal_information: Optional[PersonalInformationSchema] = None
    professional_information: Optional[ProfessionalInformationSchema] = None
    skills: Optional[List[str]] = None
    education: Optional[List[EducationItem]] = None
    experience: Optional[List[ExperienceItem]] = None
    projects: Optional[List[ProjectItem]] = None
    certifications: Optional[List[CertificationItem]] = None
    social_links: Optional[SocialLinksSchema] = None
    avatar: Optional[str] = None
