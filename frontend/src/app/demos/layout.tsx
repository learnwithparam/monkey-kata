import Link from 'next/link';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

export default function DemosLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Global Demo Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center">
          <Link 
            href="/" 
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200 group font-medium"
          >
            <div className="p-1.5 rounded-full bg-gray-100 group-hover:bg-gray-200 transition-colors mr-3">
              <ArrowLeftIcon className="w-4 h-4" />
            </div>
            Back to Home
          </Link>
        </div>
      </nav>
      
      {/* Demo Content - Rendered with existing padding/margins from pages */}
      {children}
    </div>
  );
}
