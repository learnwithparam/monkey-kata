import { marked } from 'marked';
import { useEffect, useRef } from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Extend window interface for mermaid
declare global {
  interface Window {
    mermaid?: {
      init: (config?: unknown, elements?: NodeListOf<Element>) => void;
    };
  }
}

export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      // Render markdown
      const html = marked(content) as string;
      contentRef.current.innerHTML = html;

      // Handle mermaid diagrams
      const mermaidElements = contentRef.current.querySelectorAll('pre code.language-mermaid');
      mermaidElements.forEach((element) => {
        const mermaidCode = element.textContent;
        if (mermaidCode) {
          const mermaidDiv = document.createElement('div');
          mermaidDiv.className = 'mermaid';
          mermaidDiv.textContent = mermaidCode;
          element.parentElement?.replaceWith(mermaidDiv);
        }
      });

      // Render mermaid diagrams
      if (window.mermaid) {
        window.mermaid.init(undefined, contentRef.current.querySelectorAll('.mermaid'));
      }
    }
  }, [content]);

  return (
    <div 
      ref={contentRef}
      className={`prose prose-lg max-w-none ${className}`}
    />
  );
}
