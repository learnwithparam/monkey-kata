import Link from 'next/link';
import { ReactNode } from 'react';

interface DemoCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  demoHref?: string;
  challengeHref?: string;
  isComingSoon?: boolean;
  learnings?: string[];
}

export default function DemoCard({ 
  icon, 
  title, 
  description, 
  demoHref, 
  challengeHref, 
  isComingSoon = false,
  learnings
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
    <div className="group flex flex-col sm:flex-row justify-between p-5 sm:p-6 bg-white rounded-xl border border-gray-200 hover:border-purple-200/50 transition-all duration-300 shadow-sm hover:shadow-lg hover:-translate-y-0.5">
      <div className="flex flex-col mb-4 sm:mb-0 flex-1 mr-4">
        <div className="flex items-start sm:items-center mb-3">
          <div className="flex-shrink-0 group-hover:scale-110 transition-transform duration-300">{icon}</div>
          <h4 className="ml-4 font-semibold text-gray-900 text-base sm:text-lg group-hover:text-gray-950 transition-colors">{title}</h4>
        </div>
        
        <p className="text-sm sm:text-base text-gray-600 leading-relaxed mb-4">{description}</p>
        
        {learnings && learnings.length > 0 && (
          <div className="mt-auto bg-gray-50 rounded-lg p-3 sm:p-4 border border-gray-100">
            <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">What you'll learn</h5>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5">
              {learnings.map((learning, idx) => (
                <li key={idx} className="flex items-start text-sm text-gray-700">
                  <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-purple-500 flex-shrink-0 mr-2"></div>
                  <span>{learning}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="flex flex-col justify-center gap-2 sm:gap-3 flex-shrink-0 min-w-[140px]">
        {demoHref && (
          <Link 
            href={demoHref} 
            className="flex-1 bg-gray-900 hover:bg-gray-800 text-white font-semibold py-2.5 sm:py-3 px-5 sm:px-6 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md text-center whitespace-nowrap text-sm sm:text-base hover:scale-105 flex items-center justify-center"
          >
            Try Demo
          </Link>
        )}
        {challengeHref && (
          <Link
            href={challengeHref}
            className="flex-1 bg-white text-gray-900 font-semibold py-2.5 sm:py-3 px-5 sm:px-6 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all duration-200 shadow-sm hover:shadow-md text-center text-sm sm:text-base flex items-center justify-center"
          >
            Challenges
          </Link>
        )}
      </div>
    </div>
  );
}
