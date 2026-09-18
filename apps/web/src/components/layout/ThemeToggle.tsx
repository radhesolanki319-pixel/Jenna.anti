'use client';

import { useTheme } from '../providers/ThemeProvider';
import { Sun, Moon, Laptop } from 'lucide-react';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1 text-xs">
      <button
        onClick={() => setTheme('light')}
        aria-label="Light theme"
        className={`flex items-center gap-1 rounded px-2 py-1 transition-colors ${
          theme === 'light' ? 'bg-primary-500 text-white' : 'text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'
        }`}
      >
        <Sun className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Light</span>
      </button>
      <button
        onClick={() => setTheme('dark')}
        aria-label="Dark theme"
        className={`flex items-center gap-1 rounded px-2 py-1 transition-colors ${
          theme === 'dark' ? 'bg-primary-500 text-white' : 'text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'
        }`}
      >
        <Moon className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Dark</span>
      </button>
      <button
        onClick={() => setTheme('system')}
        aria-label="System theme"
        className={`flex items-center gap-1 rounded px-2 py-1 transition-colors ${
          theme === 'system' ? 'bg-primary-500 text-white' : 'text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'
        }`}
      >
        <Laptop className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">System</span>
      </button>
    </div>
  );
}
