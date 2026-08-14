/**
 * Production React Error Boundary Component.
 * Prevents white screens by catching unhandled JavaScript/React rendering errors
 * and displaying a styled recovery panel with details and a refresh/home button.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Unhandled React Error Boundary Catch:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-6 font-sans">
          <div className="max-w-2xl w-full bg-slate-950 border border-rose-900/50 p-8 rounded-2xl shadow-2xl space-y-6">
            <div className="flex items-center gap-3 text-rose-500">
              <AlertTriangle className="w-8 h-8 shrink-0 animate-pulse" />
              <div>
                <h1 className="text-xl font-extrabold text-white">Application Exception Intercepted</h1>
                <p className="text-xs text-rose-400 font-mono mt-0.5">
                  A React rendering error occurred. Page recovered safely.
                </p>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-xs font-mono overflow-x-auto text-rose-300 max-h-48">
              <strong className="text-rose-400 block mb-1">Error Message:</strong>
              {this.state.error?.message || 'Unknown runtime error'}
              {this.state.errorInfo?.componentStack && (
                <div className="mt-3 text-[11px] text-slate-400 border-t border-slate-800 pt-2 whitespace-pre-wrap">
                  {this.state.errorInfo.componentStack}
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={this.handleReset}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 font-bold text-xs flex items-center gap-2 transition-all cursor-pointer shadow-md"
              >
                <RefreshCw className="w-4 h-4" /> Reload Workspace
              </button>
              <button
                onClick={() => {
                  window.location.href = '/';
                }}
                className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 font-semibold text-xs flex items-center gap-2 transition-all cursor-pointer"
              >
                <Home className="w-4 h-4" /> Go to Login / Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
