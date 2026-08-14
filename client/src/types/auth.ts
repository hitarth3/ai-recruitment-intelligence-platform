/**
 * Authentication & User Profile Data Types.
 */

export type UserRole = 'candidate' | 'recruiter';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  title?: string;
  phone?: string;
  location?: string;
  // Recruiter specific fields
  companyId?: string;
  companyName?: string;
  designation?: string;
  isVerified?: boolean;
  email_verified?: boolean;
  profile_completed?: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  role: UserRole | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  user: User;
}
