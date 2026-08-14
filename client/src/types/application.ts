/**
 * Job Application & Privacy-Enforced Applicant Model Types.
 */

export type ApplicationStatus = 'Applied' | 'Screening' | 'Interview' | 'Offer' | 'Hired' | 'Rejected';

export interface Application {
  id: string;
  candidateId: string;
  candidateName: string;
  candidateAvatar: string;
  candidateEmail: string;
  candidateTitle: string;
  jobId: string;
  jobTitle: string;
  companyId: string;
  companyName: string;
  applyDate: string;
  matchScore: number; // 0 - 100
  status: ApplicationStatus;
  resumeUrl?: string;
  parsedSkills: string[];
}
