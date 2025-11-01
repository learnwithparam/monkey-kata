'use client';

import { useEffect, useState, useCallback } from 'react';
import ZoomModal from './ZoomModal';

export default function ImageZoomHandler() {
  const [zoomState, setZoomState] = useState<{
    isOpen: boolean;
    src: string;
    type: 'image' | 'mermaid';
  }>({
    isOpen: false,
    src: '',
    type: 'image',
  });

  const handleClick = useCallback((e: Event) => {
    const target = e.target as HTMLElement;
    const mouseEvent = e as MouseEvent;
    const challengeContent = target.closest('.challenge-content');
    if (!challengeContent) return;

    if (target.tagName === 'IMG') {
      mouseEvent.preventDefault();
      mouseEvent.stopPropagation();
      setZoomState({
        isOpen: true,
        src: (target as HTMLImageElement).src,
        type: 'image',
      });
      return;
    }

    const mermaidDiv = target.closest('.mermaid, div.mermaid');
    if (mermaidDiv) {
      mouseEvent.preventDefault();
      mouseEvent.stopPropagation();
      
      const svg = mermaidDiv.querySelector('svg');
      if (svg) {
        const svgClone = svg.cloneNode(true) as SVGElement;
        const container = document.createElement('div');
        container.appendChild(svgClone);
        setZoomState({
          isOpen: true,
          src: container.innerHTML,
          type: 'mermaid',
        });
      } else {
        setZoomState({
          isOpen: true,
          src: mermaidDiv.innerHTML,
          type: 'mermaid',
        });
      }
    }
  }, []);

  const setupClickHandlers = useCallback(() => {
    const challengeContent = document.querySelector('.challenge-content');
    if (!challengeContent) return;

    challengeContent.addEventListener('click', handleClick, true);

    const images = challengeContent.querySelectorAll('img');
    images.forEach(img => {
      img.style.cursor = 'pointer';
      if (!img.classList.contains('zoom-image-handled')) {
        img.classList.add('zoom-image-handled');
      }
    });

    const mermaidDiagrams = challengeContent.querySelectorAll('.mermaid, div.mermaid');
    mermaidDiagrams.forEach(diagram => {
      const el = diagram as HTMLElement;
      el.style.cursor = 'pointer';
      if (!el.classList.contains('zoom-mermaid-handled')) {
        el.classList.add('zoom-mermaid-handled');
      }
    });

    return () => {
      challengeContent.removeEventListener('click', handleClick, true);
    };
  }, [handleClick]);

  useEffect(() => {
    const cleanup = setupClickHandlers();
    const challengeContent = document.querySelector('.challenge-content');
    if (!challengeContent) return cleanup || undefined;

    const observer = new MutationObserver(() => {
      setupClickHandlers();
    });

    observer.observe(challengeContent, {
      childList: true,
      subtree: true,
    });

    const timeoutId = setTimeout(() => {
      setupClickHandlers();
    }, 1000);

    return () => {
      observer.disconnect();
      if (cleanup) cleanup();
      clearTimeout(timeoutId);
    };
  }, [setupClickHandlers]);

  return (
    <ZoomModal
      isOpen={zoomState.isOpen}
      onClose={() => setZoomState({ isOpen: false, src: '', type: 'image' })}
      content={zoomState.type === 'image' ? zoomState.src : zoomState.src}
      type={zoomState.type}
    />
  );
}

