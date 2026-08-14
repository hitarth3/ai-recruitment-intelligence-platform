/**
 * Master Application Component & View Controller.
 * Manages SaaS Landing Page, Candidate/Recruiter Auth flows, and Role-Locked Dashboards.
 */

import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LandingPage } from './pages/Landing/LandingPage';
import { CandidateLogin } from './pages/Auth/CandidateLogin';
import { CandidateRegister } from './pages/Auth/CandidateRegister';
import { RecruiterLogin } from './pages/Auth/RecruiterLogin';
import { RecruiterRegister } from './pages/Auth/RecruiterRegister';
import { Layout } from './components/layout/Layout';
import { CandidateDashboard } from './pages/Candidate/CandidateDashboard';
import { CandidateProfilePage } from './pages/Candidate/CandidateProfilePage';
import { CandidateResumePage } from './pages/Candidate/CandidateResumePage';
import { ResumeOptimizerPage } from './pages/Candidate/ResumeOptimizerPage';
import { JobsPage } from './pages/Candidate/JobsPage';
import { AppliedJobsPage } from './pages/Candidate/AppliedJobsPage';
import { AICareerCoachPage } from './pages/Candidate/AICareerCoachPage';
import { CandidateSettingsPage } from './pages/Candidate/CandidateSettingsPage';
import { NotificationsPage } from './pages/Notifications/NotificationsPage';
import { RecruiterDashboard } from './pages/Recruiter/RecruiterDashboard';
import { CompanyProfilePage } from './pages/Recruiter/CompanyProfilePage';
import { PostJob } from './pages/Recruiter/PostJob';
import { ActiveJobsPage } from './pages/Recruiter/ActiveJobsPage';
import { ApplicationsOverviewPage } from './pages/Recruiter/ApplicationsOverviewPage';
import { JobApplicationsPage } from './pages/Recruiter/JobApplicationsPage';
import { WorkflowBuilderPage } from './pages/Recruiter/WorkflowBuilderPage';
import { HiringWorkflowPage } from './pages/Recruiter/HiringWorkflowPage';
import { HiringHistoryPage } from './pages/Recruiter/HiringHistoryPage';
import { RecruiterSettingsPage } from './pages/Recruiter/RecruiterSettingsPage';
import { RecruitmentStudioPage } from './pages/Recruiter/RecruitmentStudioPage';
import { CandidateExecutionPortal } from './pages/Candidate/CandidateExecutionPortal';
import { PlaceholderPage } from './pages/Placeholder/Placeholder';
import { CANDIDATE_SIDEBAR_ITEMS, RECRUITER_SIDEBAR_ITEMS } from './utils/constants';

type AuthView = 'landing' | 'candidate-login' | 'candidate-register' | 'recruiter-login' | 'recruiter-register';

export const MainContent: React.FC = () => {
  const { isAuthenticated, role, user } = useAuth();
  const [authView, setAuthView] = useState<AuthView>('landing');
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [coachPrompt, setCoachPrompt] = useState<string>('');
  const [selectedJobId, setSelectedJobId] = useState<string>('');

  // Listen for custom navigation events to pass prompt context directly to AI Career Coach
  React.useEffect(() => {
    const handleCoachNav = (e: any) => {
      if (e.detail?.prompt) {
        setCoachPrompt(e.detail.prompt);
      }
      setActiveTab('career-coach');
    };
    window.addEventListener('navigate-to-career-coach', handleCoachNav);
    return () => window.removeEventListener('navigate-to-career-coach', handleCoachNav);
  }, []);

  // Reset activeTab to 'dashboard' whenever user session or role changes to prevent stale tab IDs
  React.useEffect(() => {
    if (isAuthenticated) {
      setActiveTab('dashboard');
    }
  }, [isAuthenticated, role, user?.id]);

  // Handle Unauthenticated View Routing (Landing Page & Auth Forms)
  if (!isAuthenticated) {
    switch (authView) {
      case 'candidate-login':
        return (
          <CandidateLogin
            onBackToLanding={() => setAuthView('landing')}
            onSwitchToRegister={() => setAuthView('candidate-register')}
            onSwitchToRecruiter={() => setAuthView('recruiter-login')}
          />
        );
      case 'candidate-register':
        return (
          <CandidateRegister
            onBackToLanding={() => setAuthView('landing')}
            onSwitchToLogin={() => setAuthView('candidate-login')}
          />
        );
      case 'recruiter-login':
        return (
          <RecruiterLogin
            onBackToLanding={() => setAuthView('landing')}
            onSwitchToRegister={() => setAuthView('recruiter-register')}
            onSwitchToCandidate={() => setAuthView('candidate-login')}
          />
        );
      case 'recruiter-register':
        return (
          <RecruiterRegister
            onBackToLanding={() => setAuthView('landing')}
            onSwitchToLogin={() => setAuthView('recruiter-login')}
          />
        );
      case 'landing':
      default:
        return (
          <LandingPage
            onNavigateToAuth={(selectedRole, mode) => {
              setAuthView(`${selectedRole}-${mode}` as AuthView);
            }}
          />
        );
    }
  }

  // Handle First-Time Login Recruiter Profile Onboarding Flow
  if (role === 'recruiter' && user?.profile_completed === false) {
    return (
      <Layout activeTab="company-profile" setActiveTab={setActiveTab}>
        <CompanyProfilePage />
      </Layout>
    );
  }

  // Handle Authenticated Role-Locked Dashboard Routing
  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      {role === 'candidate' ? (
        activeTab === 'dashboard' ? (
          <CandidateDashboard onNavigateTab={setActiveTab} />
        ) : activeTab === 'my-profile' || activeTab === 'profile' ? (
          <CandidateProfilePage />
        ) : activeTab === 'my-resume' || activeTab === 'resume' ? (
          <CandidateResumePage />
        ) : activeTab === 'resume-optimizer' || activeTab === 'improvement-center' || activeTab === 'resume-history' || activeTab === 'resume-analyzer' ? (
          <ResumeOptimizerPage
            onNavigateToCareerCoach={(prompt?: string) => {
              setCoachPrompt(prompt || '');
              setActiveTab('career-coach');
            }}
          />
        ) : activeTab === 'jobs' || activeTab === 'recommended-jobs' ? (
          <JobsPage onNavigateTab={setActiveTab} />
        ) : activeTab === 'candidate-execution' ? (
          <CandidateExecutionPortal
            applicationId={selectedJobId}
            onBack={() => setActiveTab('applied-jobs')}
          />
        ) : activeTab === 'applied-jobs' || activeTab === 'my-applications' ? (
          <AppliedJobsPage onNavigateTab={setActiveTab} />
        ) : activeTab === 'career-coach' || activeTab === 'ai-career-coach' || activeTab === 'resume-chat' || activeTab === 'coach' ? (
          <AICareerCoachPage initialPrompt={coachPrompt} />
        ) : activeTab === 'settings' ? (
          <CandidateSettingsPage onNavigateTab={setActiveTab} />
        ) : activeTab === 'notifications' ? (
          <NotificationsPage onNavigateTab={setActiveTab} />
        ) : (
          <CandidateDashboard onNavigateTab={setActiveTab} />
        )
      ) : role === 'recruiter' ? (
        activeTab === 'dashboard' ? (
          <RecruiterDashboard onNavigateTab={setActiveTab} />
        ) : activeTab === 'recruitment-studio' || activeTab === 'studio' ? (
          <RecruitmentStudioPage
            initialJobId={selectedJobId}
            onNavigateTab={setActiveTab}
          />
        ) : activeTab === 'company-profile' ? (
          <CompanyProfilePage />
        ) : activeTab === 'post-job' ? (
          <PostJob
            onBackToDashboard={() => setActiveTab('dashboard')}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        ) : activeTab === 'active-jobs' || activeTab === 'my-jobs' ? (
          <ActiveJobsPage onNavigateTab={setActiveTab} />
        ) : activeTab === 'applications' ? (
          <ApplicationsOverviewPage
            onSelectJobForApplications={(jId) => {
              setSelectedJobId(jId);
              setActiveTab('job-applications');
            }}
            onSelectJobForWorkflow={(jId) => {
              setSelectedJobId(jId);
              setActiveTab('workflow-builder');
            }}
            onNavigateTab={setActiveTab}
          />
        ) : activeTab === 'job-applications' ? (
          <JobApplicationsPage
            jobId={selectedJobId}
            onBack={() => setActiveTab('applications')}
            onNavigateTab={setActiveTab}
          />
        ) : activeTab === 'workflow-builder' ? (
          <WorkflowBuilderPage
            jobId={selectedJobId}
            onBack={() => setActiveTab('applications')}
            onSaved={() => setActiveTab('applications')}
          />
        ) : activeTab === 'hiring-workflow' || activeTab === 'talent-pipeline' ? (
          <HiringWorkflowPage
            onOpenWorkflowBuilder={(jId) => {
              setSelectedJobId(jId);
              setActiveTab('workflow-builder');
            }}
            onNavigateTab={setActiveTab}
          />
        ) : activeTab === 'hiring-history' ? (
          <HiringHistoryPage onNavigateTab={setActiveTab} />
        ) : activeTab === 'notifications' ? (
          <NotificationsPage onNavigateTab={setActiveTab} />
        ) : activeTab === 'settings' ? (
          <RecruiterSettingsPage />
        ) : (
          <RecruiterDashboard onNavigateTab={setActiveTab} />
        )
      ) : (
        <CandidateDashboard onNavigateTab={setActiveTab} />
      )}
    </Layout>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <MainContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
