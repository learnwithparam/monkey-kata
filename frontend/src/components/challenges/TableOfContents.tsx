'use client';

import { useState, useEffect } from 'react';
import { Bars3Icon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface TocItem {
  id: string;
  text: string;
  level: number;
}

interface TableOfContentsProps {
  content: string;
  className?: string;
}

export default function TableOfContents({ content, className = '' }: TableOfContentsProps) {
  const [tocItems, setTocItems] = useState<TocItem[]>([]);
  const [activeId, setActiveId] = useState<string>('');
  const [isExpanded, setIsExpanded] = useState(true);

  useEffect(() => {
    const headingRegex = /<h([1-6])[^>]*id="([^"]*)"[^>]*>(.*?)<\/h[1-6]>/gi;
    const headings: TocItem[] = [];
    let match;

    const decodeHtmlEntities = (text: string): string => {
      const textarea = document.createElement('textarea');
      textarea.innerHTML = text;
      return textarea.value;
    };

    while ((match = headingRegex.exec(content)) !== null) {
      const level = parseInt(match[1]);
      const id = match[2];
      let text = match[3].replace(/<[^>]*>/g, '');
      text = decodeHtmlEntities(text);
      
      if (text.trim()) {
        headings.push({ id, text: text.trim(), level });
      }
    }

    setTocItems(headings);
  }, [content]);

  useEffect(() => {
    const handleScroll = () => {
      const headingElements = tocItems.map(item => 
        document.getElementById(item.id)
      ).filter(Boolean);

      const scrollPosition = window.scrollY + 100;

      for (let i = headingElements.length - 1; i >= 0; i--) {
        const element = headingElements[i];
        if (element && element.offsetTop <= scrollPosition) {
          setActiveId(element.id);
          break;
        }
      }
    };

    if (tocItems.length > 0) {
      window.addEventListener('scroll', handleScroll);
      handleScroll();
    }

    return () => window.removeEventListener('scroll', handleScroll);
  }, [tocItems]);

  const scrollToHeading = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      const offsetTop = element.offsetTop - 80;
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
    }
  };

  if (tocItems.length === 0) {
    return null;
  }

  return (
    <nav 
      className={`bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden ${className}`}
      aria-label="Table of contents"
      role="navigation"
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 border-b border-gray-100 flex items-center justify-between hover:bg-gray-50 transition-colors lg:hidden"
        aria-expanded={isExpanded}
        aria-controls="toc-content"
      >
        <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
          <Bars3Icon className="w-4 h-4" style={{ color: 'var(--brand-purple)' }} />
          Table of Contents
        </h3>
        <ChevronRightIcon 
          className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} 
        />
      </button>

      <div 
        id="toc-content"
        className={`${isExpanded ? 'block' : 'hidden lg:block'}`}
      >
        <div className="px-4 py-3 border-b border-gray-100 hidden lg:block">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <Bars3Icon className="w-4 h-4" style={{ color: 'var(--brand-purple)' }} />
            Table of Contents
          </h3>
        </div>
        
        <div className="px-3 py-3 max-h-[60vh] lg:max-h-[calc(100vh-200px)] overflow-y-auto toc-scrollbar">
          <ul className="space-y-1" role="list">
            {tocItems.map((item, index) => (
              <li key={index}>
                <a
                  href={`#${item.id}`}
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToHeading(item.id);
                  }}
                  className={`block py-2 px-3 rounded-md text-sm transition-all duration-150 ${
                    activeId === item.id
                      ? 'text-brand-purple font-medium bg-brand-purple/10 border-l-2 border-brand-purple'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                  style={{ 
                    paddingLeft: `${12 + (item.level - 1) * 16}px`,
                    fontSize: item.level === 1 ? '14px' : item.level === 2 ? '13px' : '12px',
                    fontWeight: item.level === 1 ? '600' : item.level === 2 ? '500' : '400',
                    lineHeight: '1.5',
                  }}
                  aria-current={activeId === item.id ? 'location' : undefined}
                >
                  {item.text}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </nav>
  );
}

