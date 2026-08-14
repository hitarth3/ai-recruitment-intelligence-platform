/**
 * Top Navbar Component for Authenticated App Workspace.
 * Displays global search, theme toggle, notifications dropdown preview, user profile, and role indicator.
 * Includes click-outside detection to automatically close open dropdown menus.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Search, Bell, Menu, User, LogOut, ChevronDown, CheckCircle, Sparkles, Building2, ExternalLink, CheckCheck } from 'lucide-react';
import { ThemeToggle } from '../common/ThemeToggle';
import { Input } from '../common/Input';
import { Badge } from '../common/Badge';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { companyService } from '../../services/companyService';

export interface NavbarProps {
  onToggleMobileSidebar: () => void;
  onNavigateTab?: (tabId: string) => void;
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: string;
  priority: string;
  is_read: boolean;
  created_at: string;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobileSidebar, onNavigateTab }) => {
  const { user, role, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [latestNotifications, setLatestNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [companyName, setCompanyName] = useState<string>('');

  const notificationsRef = useRef<HTMLDivElement | null>(null);
  const profileMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetchUnreadCount();
    if (role === 'recruiter') {
      fetchRecruiterCompany();
    }
  }, [role]);

  const fetchRecruiterCompany = async () => {
    try {
      const comp = await companyService.getMyCompany();
      if (comp && comp.company_name) {
        setCompanyName(comp.company_name);
      }
    } catch (err) {
      // ignore
    }
  };

  // Click Outside Detection Handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        profileMenuRef.current &&
        !profileMenuRef.current.contains(event.target as Node)
      ) {
        setShowProfileMenu(false);
      }
      if (
        notificationsRef.current &&
        !notificationsRef.current.contains(event.target as Node)
      ) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/notifications/unread-count');
      setUnreadCount(res.data.unread_count || 0);
    } catch (err) {
      setUnreadCount(0);
    }
  };

  const fetchDropdownNotifications = async () => {
    try {
      setLoading(true);
      const res = await api.get('/notifications?limit=5');
      setLatestNotifications(res.data.notifications || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch (err) {
      setLatestNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenNotifications = () => {
    if (!showNotifications) {
      fetchDropdownNotifications();
    }
    setShowNotifications(!showNotifications);
    setShowProfileMenu(false);
  };

  const handleMarkAllRead = async () => {
    try {
      await api.patch('/notifications/read-all');
      setUnreadCount(0);
      setLatestNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (err) {
      // ignore
    }
  };

  const handleViewAll = () => {
    setShowNotifications(false);
    if (onNavigateTab) {
      onNavigateTab('notifications');
    }
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-6 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 transition-colors">
      {/* Left: Mobile Toggle & Global Search */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          onClick={onToggleMobileSidebar}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 lg:hidden"
          aria-label="Toggle mobile menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Search Input */}
        <div className="relative w-full hidden sm:block">
          <Input
            placeholder="Search candidates, jobs, or workspace... (Ctrl + K)"
            icon={<Search className="w-4 h-4" />}
            className="bg-slate-50 dark:bg-slate-950/60 border-slate-200/80 dark:border-slate-800 text-xs py-2 pr-10"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 hidden md:flex items-center gap-0.5 text-[10px] font-semibold text-slate-400 dark:text-slate-500 bg-white dark:bg-slate-800 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700 pointer-events-none">
            ⌘K
          </div>
        </div>
      </div>

      {/* Right Actions: Theme Toggle, Role Badge, Notifications, User Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Active Role Indicator Badge */}
        <Badge variant={role === 'recruiter' ? 'purple' : 'primary'} size="sm" className="hidden sm:inline-flex">
          {role === 'recruiter' ? `Recruiter: ${companyName || user?.companyName || (user as any)?.company_name || 'Organization'}` : 'Candidate Mode'}
        </Badge>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* Notifications Dropdown */}
        <div className="relative" ref={notificationsRef}>
          <button
            onClick={handleOpenNotifications}
            className="relative p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-4 h-4 px-1 bg-indigo-600 dark:bg-indigo-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white dark:ring-slate-900">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Overlay Menu */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-4 z-50 text-slate-900 dark:text-slate-100">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Notifications
                  </h4>
                  {unreadCount > 0 && (
                    <span className="text-[10px] font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 px-2 py-0.5 rounded-full">
                      {unreadCount} New
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <CheckCheck className="w-3.5 h-3.5" />
                    <span>Mark all read</span>
                  </button>
                )}
              </div>

              <div className="py-2 space-y-2 max-h-72 overflow-y-auto">
                {loading ? (
                  <div className="py-6 text-center text-xs text-slate-400">Loading notifications...</div>
                ) : latestNotifications.length > 0 ? (
                  latestNotifications.map((item) => (
                    <div
                      key={item.id}
                      onClick={handleViewAll}
                      className={`flex items-start gap-3 p-2.5 rounded-xl border transition-all cursor-pointer ${
                        item.is_read
                          ? 'bg-slate-50/50 dark:bg-slate-950/40 border-transparent hover:bg-slate-100 dark:hover:bg-slate-800/60'
                          : 'bg-indigo-50/60 dark:bg-indigo-950/40 border-indigo-200/60 dark:border-indigo-900/60 hover:bg-indigo-100/60'
                      }`}
                    >
                      <div className="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/60 text-indigo-600 dark:text-indigo-300 flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">{item.title}</p>
                        <p className="text-[11px] text-slate-600 dark:text-slate-300 line-clamp-2 mt-0.5">{item.message}</p>
                        <span className="text-[10px] text-slate-400 mt-1 block">{item.created_at ? new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently'}</span>
                      </div>
                      {!item.is_read && (
                        <span className="w-2 h-2 rounded-full bg-indigo-600 dark:bg-indigo-400 shrink-0 mt-1" />
                      )}
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-xs text-slate-400 space-y-1">
                    <p className="font-semibold text-slate-600 dark:text-slate-300">No new notifications</p>
                    <p className="text-[11px] text-slate-400">You're all caught up!</p>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-center">
                <button
                  onClick={handleViewAll}
                  className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center justify-center gap-1.5 w-full py-1 cursor-pointer"
                >
                  <span>View All Notifications</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-1 hidden sm:block" />

        {/* User Profile Dropdown */}
        <div className="relative" ref={profileMenuRef}>
          <button
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowNotifications(false);
            }}
            className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <img
              src={user?.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80'}
              alt={user?.name || 'User'}
              className="w-8 h-8 rounded-full object-cover ring-2 ring-indigo-500/20"
            />
            <div className="text-left hidden md:block">
              <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 leading-none">
                {user?.name || 'User'}
              </p>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-tight mt-0.5">
                {user?.title || user?.designation || (role === 'candidate' ? 'Candidate' : 'Recruiter')}
              </p>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400 hidden md:block" />
          </button>

          {/* Profile Menu Overlay */}
          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-2 z-50 text-slate-900 dark:text-slate-100">
              <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800">
                <p className="text-xs font-semibold">{user?.name}</p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Log Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
