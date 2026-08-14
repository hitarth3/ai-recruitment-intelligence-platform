/**
 * Reusable Card Component.
 * Modern SaaS container card with light and dark mode styles.
 */

import React from 'react';
import { cn } from '../../utils/helpers';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hoverEffect = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl border border-slate-200/80 bg-white p-5 text-slate-900 shadow-sm transition-all duration-200",
          "dark:border-slate-800/80 dark:bg-slate-900 dark:text-slate-100",
          hoverEffect && "hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-md",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("flex flex-col gap-1 mb-4", className)} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className, children, ...props }) => (
  <h3 className={cn("text-base font-semibold text-slate-900 dark:text-slate-100 tracking-tight", className)} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ className, children, ...props }) => (
  <p className={cn("text-xs text-slate-500 dark:text-slate-400", className)} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("", className)} {...props}>
    {children}
  </div>
);
