/**
 * Master Application Layout Component.
 * Implements sticky/fixed viewport structure:
 * - Sidebar remains permanently visible on left (independent scrolling if menu overflows)
 * - Navbar remains fixed at top
 * - Main content area scrolls independently for long pages (Resume Optimizer, Jobs, Settings, etc.)
 * - Mobile/Tablet overlay drawer support
 */

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

export interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tabId: string) => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, setActiveTab }) => {
  const [isOpenMobile, setIsOpenMobile] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Permanent Fixed Sidebar for Desktop / Slide-over Drawer for Mobile */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOpenMobile={isOpenMobile}
        setIsOpenMobile={setIsOpenMobile}
      />

      {/* Main Content Workspace Column */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        {/* Fixed Sticky Top Navbar */}
        <Navbar
          onToggleMobileSidebar={() => setIsOpenMobile(!isOpenMobile)}
          onNavigateTab={setActiveTab}
        />

        {/* Independently Scrollable Main Content Workspace */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
