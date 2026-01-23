'use client';

import { useState, useEffect, useRef } from 'react';
import {
  MagnifyingGlassIcon,
  CpuChipIcon,
  WrenchScrewdriverIcon,
  LightBulbIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ClockIcon,
  BeakerIcon,
  DocumentMagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

export interface ThinkingEvent {
  category: string;
  content: string;
  timestamp: string;
  agent?: string;
  tool?: string;
  target?: string;
  metadata?: Record<string, unknown>;
  progress?: number;
  duration_ms?: number;
}

interface ThinkingBlockProps {
  events: ThinkingEvent[];
  title?: string;
  maxHeight?: string;
  autoScroll?: boolean;
  collapsible?: boolean;
  defaultExpanded?: boolean;
  showTimestamps?: boolean;
  className?: string;
}

const categoryConfig: Record<string, { icon: React.ElementType; color: string; bgColor: string; label: string }> = {
  reasoning: {
    icon: LightBulbIcon,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 border-amber-200',
    label: 'Reasoning',
  },
  tool_use: {
    icon: WrenchScrewdriverIcon,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    label: 'Tool Use',
  },
  observation: {
    icon: DocumentMagnifyingGlassIcon,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    label: 'Observation',
  },
  planning: {
    icon: BeakerIcon,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50 border-indigo-200',
    label: 'Planning',
  },
  analysis: {
    icon: CpuChipIcon,
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-50 border-cyan-200',
    label: 'Analysis',
  },
  processing: {
    icon: ClockIcon,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50 border-gray-200',
    label: 'Processing',
  },
  agent: {
    icon: CpuChipIcon,
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    label: 'Agent',
  },
  error: {
    icon: ExclamationCircleIcon,
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
    label: 'Error',
  },
  complete: {
    icon: CheckCircleIcon,
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    label: 'Complete',
  },
  search: {
    icon: MagnifyingGlassIcon,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    label: 'Search',
  },
};

const defaultConfig = {
  icon: CpuChipIcon,
  color: 'text-gray-600',
  bgColor: 'bg-gray-50 border-gray-200',
  label: 'Processing',
};

function ThinkingEventItem({
  event,
  showTimestamp = true,
  isLatest = false,
}: {
  event: ThinkingEvent;
  showTimestamp?: boolean;
  isLatest?: boolean;
}) {
  const config = categoryConfig[event.category] || defaultConfig;
  const Icon = config.icon;
  const [isExpanded, setIsExpanded] = useState(false);

  const hasDetails = event.metadata && Object.keys(event.metadata).length > 0;
  const formattedTime = new Date(event.timestamp).toLocaleTimeString();

  return (
    <div
      className={`
        flex items-start gap-3 p-3 rounded-lg border transition-all duration-300
        ${config.bgColor}
        ${isLatest ? 'ring-2 ring-blue-400 ring-opacity-50' : ''}
      `}
    >
      {/* Icon */}
      <div className={`flex-shrink-0 mt-0.5 ${config.color}`}>
        <Icon className="w-5 h-5" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          {event.agent && (
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-white/50 text-gray-700">
              {event.agent}
            </span>
          )}
          {event.tool && event.tool !== 'agent_invoke' && event.tool !== 'agent_complete' && (
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/50 text-gray-600">
              {event.tool}
            </span>
          )}
          <span className={`text-xs font-medium ${config.color}`}>
            {config.label}
          </span>
        </div>

        {/* Main content */}
        <p className="text-sm text-gray-800 break-words">{event.content}</p>

        {/* Target (if present) */}
        {event.target && (
          <p className="text-xs text-gray-500 mt-1 font-mono bg-white/50 px-2 py-1 rounded inline-block max-w-full truncate">
            {event.target}
          </p>
        )}

        {/* Expandable details */}
        {hasDetails && (
          <div className="mt-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              {isExpanded ? (
                <ChevronDownIcon className="w-3 h-3" />
              ) : (
                <ChevronRightIcon className="w-3 h-3" />
              )}
              Details
            </button>
            {isExpanded && (
              <pre className="mt-2 p-2 bg-white/50 rounded text-xs font-mono overflow-x-auto">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            )}
          </div>
        )}

        {/* Footer: timestamp and duration */}
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
          {showTimestamp && <span>{formattedTime}</span>}
          {event.duration_ms !== undefined && event.duration_ms > 0 && <span>{event.duration_ms}ms</span>}
          {event.progress !== undefined && event.progress >= 0 && (
            <div className="flex items-center gap-1">
              <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-300"
                  style={{ width: `${event.progress}%` }}
                />
              </div>
              <span>{event.progress}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Pulse indicator for latest */}
      {isLatest && event.category !== 'complete' && event.category !== 'error' && (
        <div className="flex-shrink-0">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
        </div>
      )}
    </div>
  );
}

export default function ThinkingBlock({
  events,
  title = 'AI Processing',
  maxHeight = '400px',
  autoScroll = true,
  collapsible = true,
  defaultExpanded = true,
  showTimestamps = true,
  className = '',
}: ThinkingBlockProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevEventsLength = useRef(events.length);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current && events.length > prevEventsLength.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
    prevEventsLength.current = events.length;
  }, [events.length, autoScroll]);

  if (events.length === 0) {
    return null;
  }

  const latestEvent = events[events.length - 1];
  const isComplete = latestEvent?.category === 'complete';
  const hasError = events.some((e) => e.category === 'error');

  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden ${className}`}>
      {/* Header */}
      <div
        className={`
          flex items-center justify-between px-4 py-3 border-b border-gray-100
          ${collapsible ? 'cursor-pointer hover:bg-gray-50' : ''}
          ${isComplete ? 'bg-green-50' : hasError ? 'bg-red-50' : 'bg-gray-50'}
        `}
        onClick={() => collapsible && setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className={`
            w-8 h-8 rounded-lg flex items-center justify-center
            ${isComplete ? 'bg-green-100' : hasError ? 'bg-red-100' : 'bg-blue-100'}
          `}>
            {isComplete ? (
              <CheckCircleIcon className="w-5 h-5 text-green-600" />
            ) : hasError ? (
              <ExclamationCircleIcon className="w-5 h-5 text-red-600" />
            ) : (
              <CpuChipIcon className="w-5 h-5 text-blue-600" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{title}</h3>
            <p className="text-xs text-gray-500">
              {events.length} step{events.length !== 1 ? 's' : ''}
              {isComplete && ' - Complete'}
              {hasError && ' - Error occurred'}
            </p>
          </div>
        </div>

        {collapsible && (
          <ChevronDownIcon
            className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? '' : '-rotate-90'}`}
          />
        )}

        {/* Activity indicator */}
        {!isComplete && !hasError && (
          <div className="flex items-center gap-2 ml-4">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-xs text-gray-500 hidden sm:inline">Processing...</span>
          </div>
        )}
      </div>

      {/* Events list */}
      {isExpanded && (
        <div
          ref={scrollRef}
          className="p-4 space-y-3 overflow-y-auto"
          style={{ maxHeight }}
        >
          {events.map((event, index) => (
            <ThinkingEventItem
              key={`${event.timestamp}-${index}`}
              event={event}
              showTimestamp={showTimestamps}
              isLatest={index === events.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
