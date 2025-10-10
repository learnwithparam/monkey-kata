'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  XMarkIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { marked } from 'marked';
import mermaid from 'mermaid';

interface Challenge {
  demo_name: string;
  content: string;
}

interface ChallengesModalProps {
  isOpen: boolean;
  onClose: () => void;
  demoName: string;
}

export default function ChallengesModal({ isOpen, onClose, demoName }: ChallengesModalProps) {
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

  const fetchChallenge = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/challenges/${demoName}`);
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
  }, [demoName]);

  useEffect(() => {
    if (isOpen && demoName) {
      fetchChallenge();
    }
  }, [isOpen, demoName, fetchChallenge]);

  // Render Mermaid diagrams
  useEffect(() => {
    if (challenge && contentRef.current) {
      const mermaidElements = contentRef.current.querySelectorAll('pre code.language-mermaid');
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-2 sm:p-4">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className="relative bg-white rounded-xl sm:rounded-2xl shadow-2xl w-full max-w-5xl max-h-[95vh] sm:max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200">
            <div className="flex items-center min-w-0 flex-1">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-purple-100 rounded-lg sm:rounded-xl flex items-center justify-center mr-3 sm:mr-4 flex-shrink-0">
                <DocumentTextIcon className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600" />
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg sm:text-2xl font-bold text-gray-900 truncate">
                  {getDisplayName(demoName)} Challenge Guide
                </h2>
                <p className="text-xs sm:text-sm text-gray-600 hidden sm:block">Complete learning objectives and hands-on exercises</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0 ml-2"
            >
              <XMarkIcon className="w-5 h-5 sm:w-6 sm:h-6 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 sm:p-6 overflow-y-auto max-h-[calc(95vh-120px)] sm:max-h-[calc(90vh-120px)]">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                <span className="ml-3 text-gray-600">Loading challenge...</span>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                <div className="flex items-center">
                  <div className="w-5 h-5 text-red-600 mr-2">⚠️</div>
                  <span className="text-red-800 font-medium">Error loading challenge</span>
                </div>
                <p className="text-red-700 text-sm mt-1">{error}</p>
                <button
                  onClick={fetchChallenge}
                  className="mt-3 text-red-600 hover:text-red-800 text-sm font-medium"
                >
                  Try again
                </button>
              </div>
            )}

            {!loading && !error && challenge && (
              <div className="prose prose-lg max-w-none">
                <div
                  ref={contentRef}
                  className="[&>h1]:text-4xl [&>h1]:font-bold [&>h1]:text-gray-900 [&>h1]:mb-6 [&>h1]:mt-8 [&>h1]:leading-tight [&>h2]:text-3xl [&>h2]:font-bold [&>h2]:text-gray-900 [&>h2]:mb-4 [&>h2]:mt-8 [&>h2]:leading-tight [&>h3]:text-2xl [&>h3]:font-semibold [&>h3]:text-gray-800 [&>h3]:mb-3 [&>h3]:mt-6 [&>h3]:leading-snug [&>h4]:text-xl [&>h4]:font-semibold [&>h4]:text-gray-800 [&>h4]:mb-2 [&>h4]:mt-4 [&>h4]:leading-snug [&>p]:text-gray-700 [&>p]:mb-4 [&>p]:leading-relaxed [&>ul]:mb-4 [&>ul]:space-y-2 [&>ul]:list-disc [&>ul]:pl-6 [&>ol]:mb-4 [&>ol]:space-y-2 [&>ol]:list-decimal [&>ol]:pl-6 [&>li]:text-gray-700 [&>li]:mb-1 [&>blockquote]:mb-4 [&>blockquote]:pl-4 [&>blockquote]:border-l-4 [&>blockquote]:border-blue-500 [&>blockquote]:italic [&>blockquote]:text-gray-600 [&>blockquote]:bg-blue-50 [&>blockquote]:py-2 [&>blockquote]:rounded-r-lg [&>code]:text-sm [&>code]:font-mono [&>code]:bg-gray-100 [&>code]:text-gray-800 [&>code]:px-2 [&>code]:py-1 [&>code]:rounded [&>code]:border [&>code]:border-gray-200 [&>pre]:mb-6 [&>pre]:overflow-x-auto [&>pre]:rounded-lg [&>pre]:border [&>pre]:border-gray-300 [&>pre]:bg-gray-900 [&>pre]:text-gray-100 [&>pre]:p-4 [&>pre]:shadow-lg [&>pre_code]:text-gray-100 [&>pre_code]:bg-transparent [&>pre_code]:p-0 [&>pre_code]:border-0 [&>pre_code]:text-sm [&>pre_code]:font-mono [&>pre_code]:leading-relaxed [&>img]:rounded-lg [&>img]:shadow-sm [&>img]:mb-4 [&>table]:w-full [&>table]:border-collapse [&>table]:mb-4 [&>table]:rounded-lg [&>table]:overflow-hidden [&>table]:border [&>table]:border-gray-300 [&>th]:border [&>th]:border-gray-300 [&>th]:px-4 [&>th]:py-3 [&>th]:bg-gray-50 [&>th]:font-semibold [&>th]:text-gray-900 [&>th]:text-left [&>td]:border [&>td]:border-gray-300 [&>td]:px-4 [&>td]:py-3 [&>td]:text-gray-700 [&>a]:text-blue-600 [&>a]:no-underline [&>a]:hover:underline [&>a]:font-medium [&>strong]:text-gray-900 [&>strong]:font-semibold [&>pre.mermaid]:bg-white [&>pre.mermaid]:border-0 [&>pre.mermaid]:p-0 [&>pre.mermaid]:overflow-visible [&>pre.mermaid]:shadow-none"
                  dangerouslySetInnerHTML={{
                    __html: marked(challenge.content, {
                      breaks: true,
                      gfm: true
                    }) as string
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}