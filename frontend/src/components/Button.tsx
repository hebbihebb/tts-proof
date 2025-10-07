import { ButtonHTMLAttributes, ReactNode } from 'react';
import { Loader2Icon } from 'lucide-react';
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: ReactNode;
}
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  className = '',
  disabled,
  ...props
}: ButtonProps) => {
  const baseStyles = 'rounded-lg font-medium transition-colors flex items-center justify-center';
  const variantStyles = {
    primary: 'bg-catppuccin-mauve hover:bg-catppuccin-mauve/90 text-white shadow-lg',
    secondary: 'bg-light-surface0 hover:bg-light-surface1 dark:bg-catppuccin-surface0 dark:hover:bg-catppuccin-surface1 text-light-text dark:text-catppuccin-text',
    outline: 'border border-light-surface1 dark:border-catppuccin-surface1 hover:bg-light-surface0 dark:hover:bg-catppuccin-surface0 text-light-text dark:text-catppuccin-text'
  };
  const sizeStyles = {
    sm: 'text-sm px-3 py-1.5',
    md: 'px-4 py-2',
    lg: 'text-lg px-6 py-3'
  };
  const disabledStyles = 'opacity-60 cursor-not-allowed pointer-events-none';
  return <button className={`
        ${baseStyles} 
        ${variantStyles[variant]} 
        ${sizeStyles[size]} 
        ${isLoading || disabled ? disabledStyles : ''}
        ${className}
      `} disabled={isLoading || disabled} {...props}>
      {isLoading && <Loader2Icon className="w-4 h-4 mr-2 animate-spin" />}
      {!isLoading && icon && <span className="mr-2">{icon}</span>}
      {children}
    </button>;
};