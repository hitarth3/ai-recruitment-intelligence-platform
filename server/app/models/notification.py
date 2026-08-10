"""
MongoDB Notification Data Models & Enums.
Production-grade schema definitions for Notification documents and Notification Preferences.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    APPLICATION_SHORTLISTED = "APPLICATION_SHORTLISTED"
    APPLICATION_REJECTED = "APPLICATION_REJECTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    INTERVIEW_CANCELLED = "INTERVIEW_CANCELLED"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
    RESUME_UPLOADED = "RESUME_UPLOADED"
    RESUME_ANALYZED = "RESUME_ANALYZED"
    RESUME_REANALYSIS_REQUIRED = "RESUME_REANALYSIS_REQUIRED"
    JOB_RECOMMENDATION = "JOB_RECOMMENDATION"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    OTHER = "OTHER"


class NotificationCategory(str, Enum):
    APPLICATION = "Application"
    INTERVIEW = "Interview"
    RESUME = "Resume"
    JOB_RECOMMENDATION = "Job Recommendation"
    RECRUITER_UPDATE = "Recruiter Update"
    AI = "AI"
    CAREER = "Career"
    SYSTEM = "System"
    ANALYTICS = "Analytics"
    OTHER = "Other"


class NotificationPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ActionType(str, Enum):
    OPEN_JOB = "OPEN_JOB"
    OPEN_APPLICATION = "OPEN_APPLICATION"
    OPEN_INTERVIEW = "OPEN_INTERVIEW"
    OPEN_RESUME = "OPEN_RESUME"
    OPEN_COMPANY = "OPEN_COMPANY"
    OPEN_NOTIFICATION = "OPEN_NOTIFICATION"
    CUSTOM = "CUSTOM"


class DeliveryChannels(BaseModel):
    in_app: bool = True
    email: bool = False
    browser_push: bool = False
    mobile_push: bool = False


class NotificationPreferencesModel(BaseModel):
    user_id: str
    application_updates: bool = True
    interview_updates: bool = True
    resume_updates: bool = True
    job_recommendations: bool = True
    ai_updates: bool = True
    system_updates: bool = True
    email_notifications_enabled: bool = False
