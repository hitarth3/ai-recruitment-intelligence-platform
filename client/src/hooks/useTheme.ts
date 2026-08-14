/**
 * Custom Hook: useTheme
 * Access theme state and controls anywhere in the app.
 */

import { useContext } from 'react';
import { ThemeContext, ThemeContextType } from '../context/ThemeContext';

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
