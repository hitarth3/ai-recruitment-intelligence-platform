"""
Pydantic Schemas for Candidate Resume Health Analyzer & Resume Health Report.
Includes ATS Parse Rate %, Resume Health Score, and detailed diagnostic breakdowns.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ResumeHealthReportSchema(BaseModel):
    resume_health_score: int = Field(..., ge=0, le=100, description="Resume Health Score (0-100)")
    ats_readiness: str = Field(default="High", description="ATS Readiness rating (Very High | High | Needs Work | Invalid Document)")
    ats_parse_rate: int = Field(default=86, ge=0, le=100, description="ATS Text Parse Rate percentage (0-100%)")
    summary: str = Field(..., description="Executive summary of resume quality")
    skills: List[str] = Field(default_factory=list, description="Extracted technical skills")
    education: List[str] = Field(default_factory=list, description="Extracted education details")
    experience: List[str] = Field(default_factory=list, description="Extracted work experience entries")
    projects: List[str] = Field(default_factory=list, description="Extracted projects")
    certifications: List[str] = Field(default_factory=list, description="Extracted certifications")
    strengths: List[str] = Field(default_factory=list, description="Resume key strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Resume weaknesses to improve")
    formatting_suggestions: List[str] = Field(default_factory=list, description="Formatting & layout advice")
    missing_skills: List[str] = Field(default_factory=list, description="Missing high-demand general skills")
    learning_recommendations: List[str] = Field(default_factory=list, description="Recommended learning topics")
    career_recommendations: List[str] = Field(default_factory=list, description="Recommended target job roles")
    interview_readiness: int = Field(default=85, description="Interview Readiness score (0-100)")
    analyzed_at: str
