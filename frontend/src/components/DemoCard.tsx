import Link from 'next/link';
import { ReactNode } from 'react';

interface DemoCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  demoHref?: string;
  challengeHref?: string;
  isComingSoon?: boolean;
}

export default function DemoCard({ 
  icon, 
  title, 
  description, 
  demoHref, 
  challengeHref, 
  isComingSoon = false 
}: DemoCardProps) {
  if (isComingSoon) {
    return (
      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-6 bg-white rounded-lg border border-gray-200 opacity-60">
        <div className="flex items-center mb-3 sm:mb-0">
          {icon}
          <div className="ml-3">
            <h4 className="font-semibold text-gray-900 text-sm sm:text-base">{title}</h4>
            <p className="text-xs sm:text-sm text-gray-600">{description}</p>
          </div>
        </div>
        <span className="text-gray-400 text-xs sm:text-sm self-start sm:self-center">Coming Soon</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-6 bg-white rounded-xl border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md">
      <div className="flex items-center mb-4 sm:mb-0">
        {icon}
        <div className="ml-3">
          <h4 className="font-semibold text-gray-900 text-sm sm:text-base">{title}</h4>
          <p className="text-xs sm:text-sm text-gray-600">{description}</p>
        </div>
      </div>
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
        {demoHref && (
          <Link 
            href={demoHref} 
            className="flex-1 bg-gray-900 hover:bg-gray-800 text-white font-semibold py-2 sm:py-3 px-4 sm:px-6 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md text-center whitespace-nowrap text-sm sm:text-base"
          >
            Try Demo
          </Link>
        )}
        {challengeHref && (
          <Link
            href={challengeHref}
            className="flex-1 bg-white text-gray-900 font-semibold py-2 sm:py-3 px-4 sm:px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md text-center text-sm sm:text-base"
          >
            Challenges
          </Link>
        )}
      </div>
    </div>
  );
}
