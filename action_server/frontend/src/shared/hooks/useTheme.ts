import { useEffect, useCallback } from 'react';
import { useActionServerContext } from '@/shared/context/actionServerContext';

type Theme = 'light' | 'dark' | 'system';

/**
 * Hook to manage theme state and apply dark class to document.
 * Handles system preference detection and localStorage persistence.
 */
export const useTheme = () => {
  const { viewSettings, setViewSettings } = useActionServerContext();
  const theme = viewSettings.theme as Theme;

  // Determine effective theme (resolve 'system' to actual theme)
  const getEffectiveTheme = useCallback((): 'light' | 'dark' => {
    if (theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return theme;
  }, [theme]);

  // Apply theme class to document
  useEffect(() => {
    const effectiveTheme = getEffectiveTheme();
    const root = document.documentElement;

    if (effectiveTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [getEffectiveTheme]);

  // Listen for system theme changes when in 'system' mode
  useEffect(() => {
    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      const root = document.documentElement;
      if (e.matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [theme]);

  const setTheme = useCallback(
    (newTheme: Theme) => {
      setViewSettings((curr) => ({ ...curr, theme: newTheme }));
    },
    [setViewSettings],
  );

  const toggleTheme = useCallback(() => {
    setViewSettings((curr) => ({
      ...curr,
      theme: curr.theme === 'dark' ? 'light' : 'dark',
    }));
  }, [setViewSettings]);

  const cycleTheme = useCallback(() => {
    setViewSettings((curr) => {
      const order: Theme[] = ['light', 'dark', 'system'];
      const currentIndex = order.indexOf(curr.theme as Theme);
      const nextIndex = (currentIndex + 1) % order.length;
      return { ...curr, theme: order[nextIndex] };
    });
  }, [setViewSettings]);

  return {
    theme,
    effectiveTheme: getEffectiveTheme(),
    setTheme,
    toggleTheme,
    cycleTheme,
    isDark: getEffectiveTheme() === 'dark',
  };
};

/**
 * Get initial theme from localStorage or system preference.
 * Used to set initial theme before React hydration to prevent flash.
 */
export const getInitialTheme = (): Theme => {
  if (typeof window === 'undefined') return 'light';

  try {
    const stored = localStorage.getItem('view-settings');
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.theme === 'dark' || parsed.theme === 'light' || parsed.theme === 'system') {
        return parsed.theme;
      }
    }
  } catch {
    // Ignore parse errors
  }

  // Default to system preference
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};
