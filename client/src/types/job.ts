/**
 * Job Posting Data Types.
 */

export interface Job {
  id: string;
  companyId: string;
  companyName: string;
  companyLogo: string;
  title: string;
  department: string;
  location: string;
  salaryRange: string;
  employmentType: 'Full-time' | 'Part-time' | 'Contract' | 'Remote';
  experienceYears: string;
  description: string;
  skills: string[];
  postedDate: string;
  applicantCount: number;
  isUrgent?: boolean;
}
