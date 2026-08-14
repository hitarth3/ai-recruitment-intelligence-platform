/**
 * TypeScript Data Definitions.
 */

export interface Candidate {
  id: string;
  name: string;
  avatar?: string;
  role: string;
  matchScore: number; // 0 - 100
  applyDate: string;
  status: 'Applied' | 'Screening' | 'Interview' | 'Offer' | 'Hired' | 'Rejected';
  email: string;
  experienceYears: number;
}

export interface StatCardData {
  title: string;
  value: string | number;
  change: string;
  trend: 'up' | 'down';
  description: string;
  iconName: string;
}

export interface InterviewSchedule {
  id: string;
  candidateName: string;
  candidateAvatar?: string;
  position: string;
  time: string;
  type: 'Technical Round' | 'Culture Fit' | 'Final HR' | 'System Design';
  interviewer: string;
}

export interface AISuggestion {
  id: string;
  title: string;
  category: 'High Match' | 'Action Needed' | 'Optimization';
  description: string;
  actionText: string;
  type: 'positive' | 'warning' | 'info';
}

export interface PipelineStage {
  stage: string;
  count: number;
  color: string;
  percentage: number;
}
