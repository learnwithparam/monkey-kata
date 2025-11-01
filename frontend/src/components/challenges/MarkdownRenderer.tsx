'use client';

import { useEffect, useState } from 'react';
import { processMarkdown } from '@/lib/markdown';
import MermaidRenderer from './MermaidRenderer';
import ImageZoomHandler from './ImageZoomHandler';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  const [processedContent, setProcessedContent] = useState<string>('');

  useEffect(() => {
    const processContent = async () => {
      try {
        const html = await processMarkdown(content);
        setProcessedContent(html);
      } catch (error) {
        console.error('Error processing markdown:', error);
        setProcessedContent(content); // Fallback to raw content
      }
    };

    processContent();
  }, [content]);

  return (
    <div className={`prose prose-lg sm:prose-xl max-w-none ${className}`}>
      <div
        className="challenge-content blog-content"
        dangerouslySetInnerHTML={{ __html: processedContent }}
      />
      {processedContent && <MermaidRenderer />}
      <ImageZoomHandler />
    </div>
  );
}
