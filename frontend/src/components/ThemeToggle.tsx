import React from 'react';
import { useTheme } from './ThemeContext';
import { MoonIcon, SunIcon } from 'lucide-react';
export const ThemeToggle: React.FC = () => {
  const {
    isDarkMode,
    toggleTheme
  } = useTheme();
  return <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-dark-card transition-colors duration-200" aria-label="Toggle theme" title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}>
      {isDarkMode ? <SunIcon className="w-5 h-5 text-yellow-400" /> : <MoonIcon className="w-5 h-5 text-gray-600" />}
    </button>;
};