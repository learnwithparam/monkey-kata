'use client';

import { useEffect, useRef } from 'react';

export default function MermaidRenderer() {
  const initializedRef = useRef(false);
  const mermaidInstanceRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any

  useEffect(() => {
    let observer: MutationObserver | null = null;
    let timeoutId: NodeJS.Timeout | null = null;

    const initMermaid = async () => {
      try {
        // Dynamically import mermaid
        const mermaid = (await import('mermaid')).default;
        
        // Only initialize once
        if (!initializedRef.current) {
          mermaid.initialize({
            startOnLoad: false, // We'll render manually
            theme: 'default',
            themeVariables: {
              primaryColor: '#8b5cf6',
              primaryTextColor: '#1f2937',
              primaryBorderColor: '#e5e7eb',
              lineColor: '#6b7280',
              sectionBkgColor: '#f9fafb',
              altSectionBkgColor: '#ffffff',
              gridColor: '#e5e7eb',
              textColor: '#1f2937',
              taskBkgColor: '#8b5cf6',
              taskTextColor: '#ffffff',
              taskTextLightColor: '#ffffff',
              taskTextOutsideColor: '#1f2937',
              taskTextClickableColor: '#3b82f6',
              activeTaskBkgColor: '#14b8a6',
              activeTaskBorderColor: '#14b8a6',
              section0: '#f9fafb',
              section1: '#ffffff',
              section2: '#f3f4f6',
              section3: '#e5e7eb',
            },
            flowchart: {
              useMaxWidth: true,
              htmlLabels: true,
            },
          });
          initializedRef.current = true;
          mermaidInstanceRef.current = mermaid;
        }

        const renderMermaidDiagrams = async () => {
          const challengeContent = document.querySelector('.challenge-content');
          if (!challengeContent) return;

          const mermaidElements = challengeContent.querySelectorAll('pre[data-mermaid="true"]:not([data-rendered="true"])');
          
          if (mermaidElements.length === 0) return;

          const mermaid = mermaidInstanceRef.current;
          if (!mermaid) return;

          for (let i = 0; i < mermaidElements.length; i++) {
            const element = mermaidElements[i] as HTMLElement;
            const codeElement = element.querySelector('code');
            
            if (codeElement && !element.hasAttribute('data-rendered')) {
              const mermaidCode = codeElement.textContent || '';
              if (!mermaidCode.trim()) continue;

              try {
                const id = `mermaid-${i}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                
                // Create a div for the mermaid diagram
                const mermaidDiv = document.createElement('div');
                mermaidDiv.className = 'mermaid';
                mermaidDiv.id = id;
                mermaidDiv.textContent = mermaidCode;
                
                // Mark as rendered before replacing
                element.setAttribute('data-rendered', 'true');
                
                // Replace the pre element with the mermaid div
                element.parentNode?.replaceChild(mermaidDiv, element);
                
                // Render the diagram
                await mermaid.run({
                  nodes: [mermaidDiv],
                });
              } catch (error) {
                console.error('Error rendering Mermaid diagram:', error);
                element.setAttribute('data-rendered', 'true'); // Mark as rendered even if failed
              }
            }
          }
        };

        // Initial render attempt
        renderMermaidDiagrams();

        // Watch for content changes using MutationObserver
        const challengeContent = document.querySelector('.challenge-content');
        if (challengeContent) {
          observer = new MutationObserver(() => {
            // Debounce to avoid too many calls
            if (timeoutId) clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
              renderMermaidDiagrams();
            }, 100);
          });

          observer.observe(challengeContent, {
            childList: true,
            subtree: true,
          });
        }

        // Also try rendering after a short delay to catch late-loading content
        const delayedRender = setTimeout(() => {
          renderMermaidDiagrams();
        }, 500);

        return () => {
          if (observer) observer.disconnect();
          if (timeoutId) clearTimeout(timeoutId);
          clearTimeout(delayedRender);
        };
      } catch (error) {
        console.error('Error initializing Mermaid:', error);
      }
    };

    initMermaid();
  }, []);

  return null;
}

