/**
 * Role-Based Authentication Context.
 * Connects frontend sessions to FastAPI JWT backend endpoints.
 */

import React, { createContext, useContext, useState } from 'react';
import { User, AuthState } from '../types/auth';
import {
  authService,
  CandidateRegisterPayload,
  CandidateLoginPayload,
  RecruiterStep1Payload,
  RecruiterVerifyPayload,
  RecruiterLoginPayload,
  ForgotPasswordPayload,
  ResetPasswordPayload,
} from '../services/authService';

export interface AuthContextType extends AuthState {
  token: string | null;
  loginCandidate: (payload: CandidateLoginPayload) => Promise<void>;
  loginRecruiter: (payload: RecruiterLoginPayload) => Promise<User>;
  registerCandidate: (payload: CandidateRegisterPayload) => Promise<void>;
  registerRecruiterStep1: (payload: RecruiterStep1Payload) => Promise<{ message: string; email: string }>;
  verifyRecruiterEmail: (payload: RecruiterVerifyPayload) => Promise<void>;
  forgotRecruiterPassword: (payload: ForgotPasswordPayload) => Promise<{ message: string; email: string }>;
  resetRecruiterPassword: (payload: ResetPasswordPayload) => Promise<{ message: string }>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [authState, setAuthState] = useState<AuthState>(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser) as User;
        return { user: parsed, isAuthenticated: true, role: parsed.role };
      } catch (e) {
        console.error('Failed to parse saved user:', e);
      }
    }
    return { user: null, isAuthenticated: false, role: null };
  });

  const setSession = (accessToken: string, user: User) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(user));
    setToken(accessToken);
    setAuthState({
      user,
      isAuthenticated: true,
      role: user.role,
    });
  };

  const loginCandidate = async (payload: CandidateLoginPayload) => {
    const res = await authService.loginCandidate(payload);
    setSession(res.access_token, res.user as User);
  };

  const loginRecruiter = async (payload: RecruiterLoginPayload): Promise<User> => {
    const res = await authService.loginRecruiter(payload);
    const userObj = res.user as User;
    setSession(res.access_token, userObj);
    return userObj;
  };

  const registerCandidate = async (payload: CandidateRegisterPayload) => {
    const res = await authService.registerCandidate(payload);
    setSession(res.access_token, res.user as User);
  };

  const registerRecruiterStep1 = async (payload: RecruiterStep1Payload) => {
    return await authService.registerRecruiterStep1(payload);
  };

  const verifyRecruiterEmail = async (payload: RecruiterVerifyPayload) => {
    const res = await authService.verifyRecruiterEmail(payload);
    setSession(res.access_token, res.user as User);
  };

  const forgotRecruiterPassword = async (payload: ForgotPasswordPayload) => {
    return await authService.forgotRecruiterPassword(payload);
  };

  const resetRecruiterPassword = async (payload: ResetPasswordPayload) => {
    return await authService.resetRecruiterPassword(payload);
  };

  const logout = () => {
    authService.logout();
    setToken(null);
    setAuthState({ user: null, isAuthenticated: false, role: null });
  };

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        token,
        loginCandidate,
        loginRecruiter,
        registerCandidate,
        registerRecruiterStep1,
        verifyRecruiterEmail,
        forgotRecruiterPassword,
        resetRecruiterPassword,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
