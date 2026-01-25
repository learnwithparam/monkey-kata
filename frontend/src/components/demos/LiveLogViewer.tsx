'use client';

import React, { useEffect, useRef } from 'react';
import { CommandLineIcon, PauseIcon, PlayIcon } from '@heroicons/react/24/outline';

interface LogEntry {
  timestamp: string;
  content: string;
  type: string;
}

interface LiveLogViewerProps {
  logs: LogEntry[];
  isVisible: boolean;
  className?: string;
  autoScroll?: boolean;
}

export default function LiveLogViewer({ 
  logs, 
  isVisible, 
  className = '',
  autoScroll = true 
}: LiveLogViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isAutoScroll, setIsAutoScroll] = React.useState(autoScroll);

  useEffect(() => {
    if (isAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isAutoScroll, isVisible]);

  if (!isVisible) return null;

  return (
    <div className={`flex flex-col rounded-lg overflow-hidden border border-gray-800 bg-[#0d1117] text-gray-300 font-mono text-xs sm:text-sm shadow-xl ${className} max-h-[500px]`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#161b22] border-b border-gray-800 shrink-0">
        <div className="flex items-center gap-2">
          <CommandLineIcon className="w-4 h-4 text-green-500" />
          <span className="font-semibold text-gray-200">System Logs</span>
          <span className="px-1.5 py-0.5 rounded-full bg-gray-800 text-xs text-gray-400">
            {logs.length} lines
          </span>
        </div>
        <button
          onClick={() => setIsAutoScroll(!isAutoScroll)}
          className={`p-1 rounded hover:bg-gray-700 transition-colors ${isAutoScroll ? 'text-green-500' : 'text-gray-500'}`}
          title={isAutoScroll ? "Pause auto-scroll" : "Resume auto-scroll"}
        >
          {isAutoScroll ? <PauseIcon className="w-4 h-4" /> : <PlayIcon className="w-4 h-4" />}
        </button>
      </div>

      {/* Log Content */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-1 h-96 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
      >
        {logs.length === 0 ? (
          <div className="text-gray-600 italic">Waiting for system output...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex gap-3 hover:bg-[#161b22] px-1 -mx-1 rounded">
              <span className="text-gray-600 shrink-0 select-none">
                {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
              <span className="break-all whitespace-pre-wrap font-mono text-gray-300">
                {log.content}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
