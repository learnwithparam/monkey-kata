'use client';

import { useState, useEffect, useRef } from 'react';
import {
  FunnelIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  ChevronDoubleDownIcon,
} from '@heroicons/react/24/outline';
import type { ThinkingEvent } from './ThinkingBlock';

interface StreamingLogProps {
  events: ThinkingEvent[];
  onClear?: () => void;
  title?: string;
  maxHeight?: string;
  showFilters?: boolean;
  showExport?: boolean;
  className?: string;
}

type FilterCategory = 'all' | 'reasoning' | 'tool_use' | 'observation' | 'error';

const filterOptions: { value: FilterCategory; label: string }[] = [
  { value: 'all', label: 'All Events' },
  { value: 'reasoning', label: 'Reasoning' },
  { value: 'tool_use', label: 'Tools' },
  { value: 'observation', label: 'Observations' },
  { value: 'error', label: 'Errors' },
];

export default function StreamingLog({
  events,
  onClear,
  title = 'Processing Log',
  maxHeight = '300px',
  showFilters = true,
  showExport = true,
  className = '',
}: StreamingLogProps) {
  const [filter, setFilter] = useState<FilterCategory>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Filter events based on selected category
  const filteredEvents = events.filter((event) => {
    if (filter === 'all') return true;
    return event.category === filter;
  });

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events.length, autoScroll]);

  // Export events as JSON
  const handleExport = () => {
    const dataStr = JSON.stringify(events, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `thinking-log-${new Date().toISOString()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      reasoning: 'text-amber-400',
      tool_use: 'text-blue-400',
      observation: 'text-purple-400',
      planning: 'text-indigo-400',
      analysis: 'text-cyan-400',
      processing: 'text-gray-400',
      agent: 'text-green-400',
      error: 'text-red-400',
      complete: 'text-green-400',
    };
    return colors[category] || 'text-gray-400';
  };

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-700 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800">
        <h3 className="font-mono text-sm font-medium text-gray-200">{title}</h3>
        
        <div className="flex items-center gap-2">
          {/* Filter dropdown */}
          {showFilters && (
            <div className="relative">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as FilterCategory)}
                className="appearance-none bg-gray-700 text-gray-200 text-xs pl-7 pr-8 py-1.5 rounded border border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
              >
                {filterOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <FunnelIcon className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          )}

          {/* Auto-scroll toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1.5 rounded ${
              autoScroll
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-400 hover:text-gray-200'
            } transition-colors`}
            title={autoScroll ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}
          >
            <ChevronDoubleDownIcon className="w-4 h-4" />
          </button>

          {/* Export button */}
          {showExport && events.length > 0 && (
            <button
              onClick={handleExport}
              className="p-1.5 rounded bg-gray-700 text-gray-400 hover:text-gray-200 transition-colors"
              title="Export log"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
            </button>
          )}

          {/* Clear button */}
          {onClear && events.length > 0 && (
            <button
              onClick={onClear}
              className="p-1.5 rounded bg-gray-700 text-gray-400 hover:text-red-400 transition-colors"
              title="Clear log"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Log content */}
      <div
        ref={scrollRef}
        className="font-mono text-xs overflow-y-auto p-3 space-y-1"
        style={{ maxHeight }}
      >
        {filteredEvents.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            {events.length === 0 ? 'Waiting for events...' : 'No events match the current filter'}
          </div>
        ) : (
          filteredEvents.map((event, index) => {
            const time = new Date(event.timestamp).toLocaleTimeString('en-US', {
              hour12: false,
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            });

            return (
              <div
                key={`${event.timestamp}-${index}`}
                className="flex items-start gap-2 py-1 hover:bg-gray-800/50 rounded px-1 -mx-1"
              >
                {/* Timestamp */}
                <span className="text-gray-500 flex-shrink-0">[{time}]</span>

                {/* Category */}
                <span className={`flex-shrink-0 ${getCategoryColor(event.category)}`}>
                  [{event.category.toUpperCase().substring(0, 4)}]
                </span>

                {/* Agent */}
                {event.agent && (
                  <span className="text-green-400 flex-shrink-0">
                    {event.agent}:
                  </span>
                )}

                {/* Content */}
                <span className="text-gray-300 break-all">{event.content}</span>

                {/* Duration */}
                {event.duration_ms && (
                  <span className="text-gray-500 flex-shrink-0 ml-auto">
                    ({event.duration_ms}ms)
                  </span>
                )}
              </div>
            );
          })
        )}

        {/* Processing indicator */}
        {events.length > 0 && 
          events[events.length - 1].category !== 'complete' && 
          events[events.length - 1].category !== 'error' && (
          <div className="flex items-center gap-2 text-gray-500 pt-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            Processing...
          </div>
        )}
      </div>

      {/* Footer with stats */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-gray-700 bg-gray-800 text-xs text-gray-400">
        <span>
          {filteredEvents.length} of {events.length} events
        </span>
        {events.length > 0 && (
          <span>
            Started: {new Date(events[0].timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  );
}
