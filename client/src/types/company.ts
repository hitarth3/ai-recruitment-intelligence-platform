/**
 * Company & Recruiter Profile Types.
 */

export interface RecruiterProfile {
  id: string;
  name: string;
  role: string;
  email: string;
  avatar: string;
}

export interface Company {
  id: string;
  name: string;
  logo: string;
  industry: string;
  size: string; // e.g. "250 Employees"
  location: string;
  website: string;
  description: string;
  recruiter: RecruiterProfile;
  openJobsCount: number;
}
