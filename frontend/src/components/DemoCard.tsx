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
      <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
        <div className="flex items-center">
          {icon}
          <div>
            <h4 className="font-semibold text-gray-900">{title}</h4>
            <p className="text-sm text-gray-600">{description}</p>
          </div>
        </div>
        <span className="text-gray-400 text-sm">Coming Soon</span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between p-6 bg-white rounded-xl border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md">
      <div className="flex items-center">
        {icon}
        <div>
          <h4 className="font-semibold text-gray-900">{title}</h4>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        {demoHref && (
          <Link 
            href={demoHref} 
            className="flex-1 bg-gray-900 hover:bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md text-center whitespace-nowrap"
          >
            Try Demo
          </Link>
        )}
        {challengeHref && (
          <Link
            href={challengeHref}
            className="flex-1 bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md text-center"
          >
            Challenges
          </Link>
        )}
      </div>
    </div>
  );
}
