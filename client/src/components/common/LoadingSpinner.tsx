/**
 * Reusable Loading Spinner Component.
 */

import React from 'react';
import { cn } from '../../utils/helpers';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', className }) => {
  const sizes = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };

  return (
    <div className="flex items-center justify-center p-4">
      <div
        className={cn(
          "animate-spin rounded-full border-indigo-600 border-t-transparent dark:border-indigo-400 dark:border-t-transparent",
          sizes[size],
          className
        )}
      />
    </div>
  );
};
