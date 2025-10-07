import React, { useEffect, useState, createContext, useContext } from 'react';
type ThemeContextType = {
  isDarkMode: boolean;
  toggleTheme: () => void;
};
const ThemeContext = createContext<ThemeContextType>({
  isDarkMode: false,
  toggleTheme: () => {}
});
export const ThemeProvider: React.FC<{
  children: React.ReactNode;
}> = ({
  children
}) => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);
  useEffect(() => {
    // Check if user has a preference saved in localStorage
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (savedTheme === 'dark' || !savedTheme && prefersDark) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);
  const toggleTheme = () => {
    setIsDarkMode(prev => {
      const newMode = !prev;
      if (newMode) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
      }
      return newMode;
    });
  };
  return <ThemeContext.Provider value={{
    isDarkMode,
    toggleTheme
  }}>
      {children}
    </ThemeContext.Provider>;
};
export const useTheme = () => useContext(ThemeContext);