"""
Pydantic Schemas for Candidate Resume Improvement Center.
Models 6-category score breakdown with loss explanations, 100% dynamic AI checklists, priority recommendations with +X score delta estimates & reasons, and the 'Reach 90 Roadmap' widget.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ScoreBreakdownCategory(BaseModel):
    category: str = Field(..., description="Projects | Experience | Skills | Education | Formatting | ATS Keywords")
    score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=0)
    loss_reason: str = Field(..., description="Explanation of why points were lost in this section")


class DynamicChecklistItem(BaseModel):
    id: str
    title: str
    category: str = Field(default="Skills")
    completed: bool = Field(default=False)
    impact: str = Field(default="High")


class PriorityRecommendationItem(BaseModel):
    id: str
    title: str
    reason: str = Field(..., description="Explanation of why this recommendation was generated")
    estimated_increase: int = Field(..., description="Estimated score increase e.g. +6, +4, +3")
    priority: str = Field(..., description="High | Medium | Low")
    action_type: str = Field(default="career_coach")
    prompt_context: str = Field(..., description="Context prompt to send to AI Career Coach upon clicking action button")


class Reach90Step(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_impact: str = Field(..., description="e.g. +4, +5")
    prompt_context: str


class Reach90Roadmap(BaseModel):
    current_score: int
    target_goal: int = Field(default=90)
    expected_new_score: str = Field(default="89-92")
    steps: List[Reach90Step] = Field(default_factory=list)


class ResumeVersionSchema(BaseModel):
    version_id: str
    version_number: int
    upload_date: str
    original_filename: str = Field(default="Resume.pdf")
    resume_health_score: int
    ats_readiness: str
    ats_parse_rate: int
    ai_summary: str
    skills: List[str] = Field(default_factory=list)


class VersionComparisonSchema(BaseModel):
    v1_id: str
    v2_id: str
    v1_score: int
    v2_score: int
    score_delta: int
    v1_readiness: str
    v2_readiness: str
    added_skills: List[str] = Field(default_factory=list)
    removed_skills: List[str] = Field(default_factory=list)
    improved_areas: List[str] = Field(default_factory=list)
    still_missing_skills: List[str] = Field(default_factory=list)
    explanation: str = Field(..., description="AI explanation of why score changed")


class ImprovementCenterResponse(BaseModel):
    current_version: int
    current_score: int
    current_readiness: str
    current_parse_rate: int
    last_analysis_date: str
    resume_summary: str
    versions: List[ResumeVersionSchema]
    score_breakdown: List[ScoreBreakdownCategory]
    strengths: List[str]
    weaknesses: List[str]
    formatting_issues: List[str]
    missing_skills: List[str]
    missing_sections: List[str]
    ai_improvement_summary: str
    checklist: List[DynamicChecklistItem]
    completed_checklist_count: int
    total_checklist_count: int
    recommendations: List[PriorityRecommendationItem]
    reach_90_roadmap: Reach90Roadmap
