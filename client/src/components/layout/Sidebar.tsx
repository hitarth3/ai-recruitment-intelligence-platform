/**
 * Sidebar Navigation Component.
 * Permanently visible fixed layout on Desktop; slide-over drawer on Mobile/Tablet.
 * Features:
 * - Independent menu scrolling if items overflow
 * - Zero hardcoded counts on menu items
 * - High-contrast active tab state
 */

import React from 'react';
import {
  LayoutDashboard,
  Users,
  Briefcase,
  FileText,
  GitCompare,
  Target,
  Video,
  MessageSquare,
  BarChart3,
  Settings,
  LogOut,
  X,
  Sparkles,
  UserCheck,
  CheckCircle2,
  Bot,
  Bell,
  Building2,
  PlusCircle,
  Search,
  TrendingUp,
} from 'lucide-react';
import { CANDIDATE_SIDEBAR_ITEMS, RECRUITER_SIDEBAR_ITEMS } from '../../utils/constants';
import { cn } from '../../utils/helpers';
import { useAuth } from '../../context/AuthContext';

const ICON_MAP: Record<string, React.ElementType> = {
  LayoutDashboard,
  Users,
  Briefcase,
  FileText,
  GitCompare,
  Target,
  Video,
  MessageSquare,
  BarChart3,
  Settings,
  UserCheck,
  CheckCircle2,
  Bot,
  Bell,
  Building2,
  PlusCircle,
  Search,
  Sparkles,
  TrendingUp,
};

export interface SidebarProps {
  activeTab: string;
  setActiveTab: (tabId: string) => void;
  isOpenMobile: boolean;
  setIsOpenMobile: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isOpenMobile,
  setIsOpenMobile,
}) => {
  const { role, logout } = useAuth();
  const sidebarItems = role === 'recruiter' ? RECRUITER_SIDEBAR_ITEMS : CANDIDATE_SIDEBAR_ITEMS;

  const handleSelect = (tabId: string) => {
    setActiveTab(tabId);
    setIsOpenMobile(false);
  };

  return (
    <>
      {/* Mobile/Tablet Backdrop Overlay */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
          onClick={() => setIsOpenMobile(false)}
        />
      )}

      {/* Sidebar Container: Fixed 100vh on Desktop, Slide-over Drawer on Mobile */}
      <aside
        className={cn(
          "flex flex-col w-64 h-full bg-white border-r border-slate-200/80 transition-transform duration-300 ease-in-out shrink-0",
          "dark:bg-slate-900 dark:border-slate-800/80",
          "fixed inset-y-0 left-0 z-50 lg:static lg:z-auto lg:translate-x-0",
          isOpenMobile ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-slate-200/80 dark:border-slate-800/80 shrink-0">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => handleSelect('dashboard')}>
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white shadow-md shadow-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100 leading-tight">
                RecruitAI
              </h1>
              <p className="text-[10px] font-medium text-slate-400 dark:text-slate-500 tracking-wide uppercase">
                {role === 'recruiter' ? 'Recruiter Portal' : 'Candidate Portal'}
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsOpenMobile(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items Area with Independent Internal Scrolling */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            {role === 'recruiter' ? 'Recruiter Menu' : 'Candidate Menu'}
          </div>

          {sidebarItems.map((item) => {
            const Icon = ICON_MAP[item.iconName] || LayoutDashboard;
            const isActive = activeTab === item.id || (item.id === 'jobs' && (activeTab === 'recommended-jobs' || activeTab === 'jobs'));

            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 cursor-pointer group",
                  isActive
                    ? role === 'recruiter'
                      ? "bg-purple-50 text-purple-600 dark:bg-purple-950/60 dark:text-purple-400 font-semibold shadow-xs"
                      : "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400 font-semibold shadow-xs"
                    : "text-slate-600 hover:bg-slate-100/80 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-200"
                )}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Icon
                    className={cn(
                      "w-4 h-4 shrink-0 transition-colors",
                      isActive
                        ? role === 'recruiter'
                          ? "text-purple-600 dark:text-purple-400"
                          : "text-indigo-600 dark:text-indigo-400"
                        : "text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300"
                    )}
                  />
                  <span className="truncate">{item.label}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Footer Logout Button */}
        <div className="p-3 border-t border-slate-200/80 dark:border-slate-800/80 shrink-0">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600 dark:text-slate-400 dark:hover:bg-rose-950/40 dark:hover:text-rose-400 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4 text-slate-400 group-hover:text-rose-500" />
            <span>Log Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};
