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
      <div className="group flex flex-col sm:flex-row sm:items-center justify-between p-5 sm:p-6 bg-white rounded-xl border border-gray-200 opacity-60 hover:opacity-70 transition-all duration-300 shadow-sm">
        <div className="flex items-start sm:items-center mb-3 sm:mb-0">
          <div className="flex-shrink-0 opacity-50">{icon}</div>
          <div className="ml-4">
            <h4 className="font-semibold text-gray-900 text-base sm:text-lg mb-1">{title}</h4>
            <p className="text-sm sm:text-base text-gray-600 leading-relaxed">{description}</p>
          </div>
        </div>
        <span className="text-gray-400 text-xs sm:text-sm font-medium self-start sm:self-center px-3 py-1 bg-gray-50 rounded-full">Coming Soon</span>
      </div>
    );
  }

  return (
    <div className="group flex flex-col sm:flex-row sm:items-center justify-between p-5 sm:p-6 bg-white rounded-xl border border-gray-200 hover:border-purple-200/50 transition-all duration-300 shadow-sm hover:shadow-lg hover:-translate-y-0.5">
      <div className="flex items-start sm:items-center mb-4 sm:mb-0 flex-1">
        <div className="flex-shrink-0 group-hover:scale-110 transition-transform duration-300">{icon}</div>
        <div className="ml-4 flex-1">
          <h4 className="font-semibold text-gray-900 text-base sm:text-lg mb-1.5 group-hover:text-gray-950 transition-colors">{title}</h4>
          <p className="text-sm sm:text-base text-gray-600 leading-relaxed">{description}</p>
        </div>
      </div>
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 sm:ml-4">
        {demoHref && (
          <Link 
            href={demoHref} 
            className="flex-1 sm:flex-none bg-gray-900 hover:bg-gray-800 text-white font-semibold py-2.5 sm:py-3 px-5 sm:px-6 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md text-center whitespace-nowrap text-sm sm:text-base hover:scale-105"
          >
            Try Demo
          </Link>
        )}
        {challengeHref && (
          <Link
            href={challengeHref}
            className="flex-1 sm:flex-none bg-white text-gray-900 font-semibold py-2.5 sm:py-3 px-5 sm:px-6 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all duration-200 shadow-sm hover:shadow-md text-center text-sm sm:text-base"
          >
            Challenges
          </Link>
        )}
      </div>
    </div>
  );
}
