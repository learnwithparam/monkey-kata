'use client';

import { useState, useEffect, useCallback, use } from 'react';
import Link from 'next/link';
import { 
  DocumentTextIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import ChallengeLoader from '@/components/challenges/ChallengeLoader';
import ChallengeError from '@/components/challenges/ChallengeError';
import MarkdownRenderer from '@/components/challenges/MarkdownRenderer';
import TableOfContents from '@/components/challenges/TableOfContents';
import { processMarkdown } from '@/lib/markdown';

interface Challenge {
  demo_name: string;
  content: string;
}

interface ChallengePageProps {
  params: Promise<{
    slug: string;
  }>;
}

export default function ChallengePage({ params }: ChallengePageProps) {
  const resolvedParams = use(params);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processedContent, setProcessedContent] = useState<string>('');

  // Demo name mapping for display
  const getDisplayName = (demoName: string) => {
    const mapping: Record<string, string> = {
      'bedtime_story_generator': 'Bedtime Stories for Kids',
      'website_rag': 'Website FAQ Chatbot'
    };
    return mapping[demoName] || demoName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Get demo page URL for back navigation
  const getDemoUrl = (demoName: string) => {
    const mapping: Record<string, string> = {
      'bedtime_story_generator': '/demos/bedtime-story',
      'website_rag': '/demos/website-rag'
    };
    return mapping[demoName] || '/';
  };

  const fetchChallenge = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Convert hyphen slug to underscore for API (e.g., bedtime-story-generator -> bedtime_story_generator)
      const apiSlug = resolvedParams.slug.replace(/-/g, '_');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/challenges/${apiSlug}`);
      if (!response.ok) {
        throw new Error('Failed to fetch challenge');
      }
      
      const data = await response.json();
      setChallenge(data);
      
      // Process markdown content
      if (data.content) {
        const html = await processMarkdown(data.content);
        setProcessedContent(html);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch challenge');
    } finally {
      setLoading(false);
    }
  }, [resolvedParams.slug]);

  useEffect(() => {
    fetchChallenge();
  }, [fetchChallenge]);

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section with Background Pattern */}
      <div
        className="relative text-white py-12 sm:py-16 overflow-hidden"
        style={{
          backgroundColor: '#111827',
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3E%3Cdefs%3E%3Cpattern id='mesh' width='100' height='100' patternUnits='userSpaceOnUse'%3E%3Cline x1='0' y1='50' x2='100' y2='50' stroke='%238b5cf6' stroke-width='2' opacity='0.4'/%3E%3Cline x1='50' y1='0' x2='50' y2='100' stroke='%2314b8a6' stroke-width='2' opacity='0.4'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23mesh)'/%3E%3C/svg%3E")`,
        }}
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header with Back Button */}
          <div className="mb-8">
            <Link
              href={challenge ? getDemoUrl(challenge.demo_name) : '/'}
              className="inline-flex items-center gap-2 text-gray-300 hover:text-white transition-colors mb-6"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span className="font-medium">Back to Demo</span>
            </Link>
          </div>

          {/* Title Section */}
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center mr-4" style={{ backgroundColor: 'rgba(139, 92, 246, 0.2)' }}>
              <DocumentTextIcon className="w-7 h-7" style={{ color: 'var(--brand-purple)' }} />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-2 leading-tight">
                {challenge ? getDisplayName(challenge.demo_name) : 'Loading...'} Challenge
              </h1>
              <p className="text-base sm:text-lg text-gray-300">Complete learning objectives and hands-on exercises</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content with Responsive Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {loading && (
          <ChallengeLoader message="Loading challenge..." />
        )}

        {error && (
          <ChallengeError
            message={error}
            onRetry={fetchChallenge}
          />
        )}

        {!loading && !error && challenge && processedContent && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
            {/* Main Content */}
            <div className="lg:col-span-9">
              <MarkdownRenderer
                content={challenge.content}
              />
              
              {/* Table of Contents - Mobile */}
              <div className="lg:hidden mt-8">
                <TableOfContents content={processedContent} />
              </div>
            </div>

            {/* Table of Contents - Desktop Sidebar */}
            <aside className="hidden lg:block lg:col-span-3" aria-label="Table of contents">
              <div className="sticky top-24">
                <TableOfContents content={processedContent} />
              </div>
            </aside>
          </div>
        )}
      </div>
    </div>
  );
}
