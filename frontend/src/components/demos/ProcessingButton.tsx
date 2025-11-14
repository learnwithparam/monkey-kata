import { GlobeAltIcon } from '@heroicons/react/24/outline';
import { ReactNode } from 'react';

interface ProcessingButtonProps {
  isLoading: boolean;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
  icon?: ReactNode;
  className?: string;
}

export default function ProcessingButton({ isLoading, onClick, disabled, children, icon, className }: ProcessingButtonProps) {
  // If className is provided and contains color/styling overrides, use it fully
  // Otherwise, merge with defaults
  const hasColorOverride = className && (className.includes('bg-') || className.includes('text-') || className.includes('btn-'));
  const baseClasses = "w-full btn-accent disabled:opacity-50 disabled:cursor-not-allowed py-4 text-lg font-semibold";
  const finalClassName = className 
    ? (hasColorOverride 
        ? className 
        : `${baseClasses} ${className}`.replace(/\s+w-full\s+/g, ' ').trim())
    : baseClasses;
  
  return (
    <button
      onClick={onClick}
      disabled={isLoading || disabled}
      className={finalClassName}
    >
      {isLoading ? (
        <span className="flex items-center justify-center">
          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Processing...
        </span>
      ) : (
        <span className="flex items-center justify-center">
          {icon || <GlobeAltIcon className="w-5 h-5 mr-3" />}
          {children}
        </span>
      )}
    </button>
  );
}
