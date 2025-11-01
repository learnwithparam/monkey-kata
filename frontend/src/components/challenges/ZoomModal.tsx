'use client';

import { useEffect, useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ZoomModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: string | React.ReactNode;
  type: 'image' | 'mermaid';
}

export default function ZoomModal({ isOpen, onClose, content, type }: ZoomModalProps) {
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const [mermaidSize, setMermaidSize] = useState({ width: 0, height: 0 });
  const [mermaidContainerRef, setMermaidContainerRef] = useState<HTMLDivElement | null>(null);

  // Handle keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Calculate optimal Mermaid diagram size
  useEffect(() => {
    if (!isOpen || type !== 'mermaid' || !mermaidContainerRef) return;

    let retryCount = 0;
    const maxRetries = 10;

    const calculateMermaidSize = () => {
      const svg = mermaidContainerRef.querySelector('svg');
      if (!svg) {
        if (retryCount < maxRetries) {
          retryCount++;
          setTimeout(calculateMermaidSize, 100);
        }
        return;
      }

      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;
      const padding = 120;
      const maxWidth = windowWidth - padding;
      const maxHeight = windowHeight - padding;

      let svgWidth: number = 0;
      let svgHeight: number = 0;

      const viewBox = svg.getAttribute('viewBox');
      if (viewBox) {
        const parts = viewBox.split(' ');
        if (parts.length >= 4) {
          svgWidth = parseFloat(parts[2]);
          svgHeight = parseFloat(parts[3]);
        }
      }

      if (!svgWidth || !svgHeight || isNaN(svgWidth) || isNaN(svgHeight)) {
        svgWidth = parseFloat(svg.getAttribute('width') || '0');
        svgHeight = parseFloat(svg.getAttribute('height') || '0');
      }

      if (!svgWidth || !svgHeight || isNaN(svgWidth) || isNaN(svgHeight)) {
        const svgElement = svg as unknown as HTMLElement;
        svgWidth = svg.clientWidth || svgElement.offsetWidth || 800;
        svgHeight = svg.clientHeight || svgElement.offsetHeight || 600;
      }

      if (!svgWidth || !svgHeight || svgWidth <= 0 || svgHeight <= 0) {
        svgWidth = maxWidth;
        svgHeight = maxHeight * 0.75;
      }

      const svgAspectRatio = svgWidth / svgHeight;
      const windowAspectRatio = maxWidth / maxHeight;

      let optimalWidth: number;
      let optimalHeight: number;

      if (svgAspectRatio > windowAspectRatio) {
        optimalWidth = maxWidth;
        optimalHeight = optimalWidth / svgAspectRatio;
      } else {
        optimalHeight = maxHeight;
        optimalWidth = optimalHeight * svgAspectRatio;
      }

      setMermaidSize({ width: optimalWidth, height: optimalHeight });
    };

    calculateMermaidSize();
  }, [isOpen, type, mermaidContainerRef]);

  // Calculate optimal image size
  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const naturalWidth = img.naturalWidth;
    const naturalHeight = img.naturalHeight;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const padding = 120;
    const maxWidth = windowWidth - padding;
    const maxHeight = windowHeight - padding;

    const imageAspectRatio = naturalWidth / naturalHeight;
    const windowAspectRatio = maxWidth / maxHeight;

    let optimalWidth: number;
    let optimalHeight: number;

    if (imageAspectRatio > windowAspectRatio) {
      optimalWidth = maxWidth;
      optimalHeight = optimalWidth / imageAspectRatio;
    } else {
      optimalHeight = maxHeight;
      optimalWidth = optimalHeight * imageAspectRatio;
    }

    setImageSize({ width: optimalWidth, height: optimalHeight });
    setIsImageLoaded(true);
  };

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative bg-white rounded-lg shadow-2xl max-w-[95vw] max-h-[95vh] flex items-center justify-center overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: '95vw',
          maxHeight: '95vh',
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 bg-white/90 hover:bg-white text-gray-900 rounded-full p-2 shadow-lg transition-all duration-200 hover:scale-110"
          aria-label="Close zoom view"
        >
          <XMarkIcon className="w-6 h-6" />
        </button>

        {/* Content */}
        {type === 'image' ? (
          typeof content === 'string' ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={content}
              alt="Full size view"
              className="rounded-lg shadow-2xl"
              style={{
                width: imageSize.width > 0 ? `${imageSize.width}px` : 'auto',
                height: imageSize.height > 0 ? `${imageSize.height}px` : 'auto',
                maxWidth: '95vw',
                maxHeight: '95vh',
                objectFit: 'contain',
                opacity: isImageLoaded ? 1 : 0,
                transition: 'opacity 0.3s ease-in-out',
                userSelect: 'none',
                WebkitUserSelect: 'none',
                touchAction: 'pan-x pan-y pinch-zoom',
              }}
              onLoad={handleImageLoad}
              draggable={false}
            />
          ) : (
            content
          )
        ) : (
          <div
            ref={setMermaidContainerRef}
            className="mermaid-zoom-container"
            style={{
              width: mermaidSize.width > 0 ? `${mermaidSize.width}px` : 'auto',
              height: mermaidSize.height > 0 ? `${mermaidSize.height}px` : 'auto',
              touchAction: 'pan-x pan-y pinch-zoom',
            }}
            dangerouslySetInnerHTML={{ __html: typeof content === 'string' ? content : '' }}
          />
        )}
      </div>
    </div>
  );
}

