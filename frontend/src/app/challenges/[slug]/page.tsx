'use client';

import { useState, useEffect, useRef, useCallback, use } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  DocumentTextIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import mermaid from 'mermaid';
import ChallengeLoader from '@/components/challenges/ChallengeLoader';
import ChallengeError from '@/components/challenges/ChallengeError';
import MarkdownRenderer from '@/components/challenges/MarkdownRenderer';

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
  const router = useRouter();
  const resolvedParams = use(params);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch challenge');
    } finally {
      setLoading(false);
    }
  }, [resolvedParams.slug]);

  useEffect(() => {
    fetchChallenge();
  }, [fetchChallenge]);

  // Render Mermaid diagrams
  useEffect(() => {
    if (challenge && contentRef.current) {
      const mermaidElements = contentRef.current.querySelectorAll('pre code.language-mermaid');
      console.log('Found mermaid code blocks:', mermaidElements.length);
      
      if (mermaidElements.length > 0) {
        mermaid.initialize({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
        });
        
        mermaidElements.forEach(async (codeElement, index) => {
          const preElement = codeElement.parentElement;
          if (!preElement) return;
          
          const id = `mermaid-${index}-${Date.now()}`;
          const mermaidCode = codeElement.textContent || '';
          console.log('Found Mermaid code:', mermaidCode);
          
          try {
            const { svg } = await mermaid.render(id, mermaidCode);
            preElement.innerHTML = svg;
            preElement.className = 'mermaid-diagram flex justify-center items-center bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 my-6 shadow-sm';
          } catch (error) {
            console.warn('Failed to render Mermaid diagram:', error);
            preElement.innerHTML = `<div class="flex justify-center items-center bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 my-6 shadow-sm"><pre class="bg-white p-4 rounded-lg text-sm font-mono text-gray-700 shadow-inner">${mermaidCode}</pre></div>`;
          }
        });
      }
    }
  }, [challenge]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-6">
            {/* Back Button */}
            <Link
              href={challenge ? getDemoUrl(challenge.demo_name) : '/'}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mr-6"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span className="font-medium">Back to Demo</span>
            </Link>
            
            {/* Title Section */}
            <div className="flex items-center">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                <DocumentTextIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {challenge ? getDisplayName(challenge.demo_name) : 'Loading...'} Challenge Guide
                </h1>
                <p className="text-sm text-gray-600">Complete learning objectives and hands-on exercises</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <ChallengeLoader message="Loading challenge..." />
        )}

        {error && (
          <ChallengeError
            message={error}
            onRetry={fetchChallenge}
          />
        )}

        {!loading && !error && challenge && (
          <MarkdownRenderer
            content={challenge.content}
            className="[&>h1]:text-4xl [&>h1]:font-bold [&>h1]:text-gray-900 [&>h1]:mb-6 [&>h1]:mt-8 [&>h1]:leading-tight [&>h2]:text-3xl [&>h2]:font-bold [&>h2]:text-gray-900 [&>h2]:mb-4 [&>h2]:mt-8 [&>h2]:leading-tight [&>h3]:text-2xl [&>h3]:font-semibold [&>h3]:text-gray-800 [&>h3]:mb-3 [&>h3]:mt-6 [&>h3]:leading-snug [&>h4]:text-xl [&>h4]:font-semibold [&>h4]:text-gray-800 [&>h4]:mb-2 [&>h4]:mt-4 [&>h4]:leading-snug [&>p]:text-gray-700 [&>p]:mb-4 [&>p]:leading-relaxed [&>ul]:mb-4 [&>ul]:space-y-2 [&>ul]:list-disc [&>ul]:pl-6 [&>ol]:mb-4 [&>ol]:space-y-2 [&>ol]:list-decimal [&>ol]:pl-6 [&>li]:text-gray-700 [&>li]:mb-1 [&>blockquote]:mb-4 [&>blockquote]:pl-4 [&>blockquote]:border-l-4 [&>blockquote]:border-blue-500 [&>blockquote]:italic [&>blockquote]:text-gray-600 [&>blockquote]:bg-blue-50 [&>blockquote]:py-2 [&>blockquote]:rounded-r-lg [&>code]:text-sm [&>code]:font-mono [&>code]:bg-gray-100 [&>code]:text-gray-800 [&>code]:px-2 [&>code]:py-1 [&>code]:rounded [&>code]:border [&>code]:border-gray-200 [&>pre]:mb-6 [&>pre]:overflow-x-auto [&>pre]:rounded-lg [&>pre]:border [&>pre]:border-gray-300 [&>pre]:bg-gray-900 [&>pre]:text-gray-100 [&>pre]:p-4 [&>pre]:shadow-lg [&>pre_code]:text-gray-100 [&>pre_code]:bg-transparent [&>pre_code]:p-0 [&>pre_code]:border-0 [&>pre_code]:text-sm [&>pre_code]:font-mono [&>pre_code]:leading-relaxed [&>img]:rounded-lg [&>img]:shadow-sm [&>img]:mb-4 [&>table]:w-full [&>table]:border-collapse [&>table]:mb-4 [&>table]:rounded-lg [&>table]:overflow-hidden [&>table]:border [&>table]:border-gray-300 [&>th]:border [&>th]:border-gray-300 [&>th]:px-4 [&>th]:py-3 [&>th]:bg-gray-50 [&>th]:font-semibold [&>th]:text-gray-900 [&>th]:text-left [&>td]:border [&>td]:border-gray-300 [&>td]:px-4 [&>td]:py-3 [&>td]:text-gray-700 [&>a]:text-blue-600 [&>a]:no-underline [&>a]:hover:underline [&>a]:font-medium [&>strong]:text-gray-900 [&>strong]:font-semibold [&>pre.mermaid]:bg-white [&>pre.mermaid]:border-0 [&>pre.mermaid]:p-0 [&>pre.mermaid]:overflow-visible [&>pre.mermaid]:shadow-none"
          />
        )}
      </div>
    </div>
  );
}
