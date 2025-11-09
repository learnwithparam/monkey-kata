'use client';

import { useRef, useEffect } from 'react';
import { marked } from 'marked';
import { 
  InformationCircleIcon, 
  ExclamationCircleIcon,
  CheckBadgeIcon 
} from '@heroicons/react/24/outline';
import { normalizeSpacing } from '@/utils/textFormatting';

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isTyping?: boolean;
  tool_calls?: Array<{
    tool_name: string;
    arguments: Record<string, unknown>;
    result: string;
    timestamp: string;
  }>;
  sources?: Array<{
    url: string;
    content: string;
  }>;
  approval?: {
    approval_id: string;
    step_name: string;
    step_number: number;
    content: Record<string, unknown>;
  };
}

interface ChatMessagesProps {
  messages: ChatMessage[];
  currentAnswer?: string;
  emptyState?: {
    icon?: React.ReactNode;
    title: string;
    description: string;
  };
  onToggleToolCall?: (messageId: string) => void;
  expandedToolCalls?: Set<string>;
  onToggleSource?: (messageId: string) => void;
  expandedSources?: Set<string>;
  renderApproval?: (approval: ChatMessage['approval']) => React.ReactNode;
}

export default function ChatMessages({
  messages,
  currentAnswer = '',
  emptyState,
  onToggleToolCall,
  expandedToolCalls = new Set(),
  onToggleSource,
  expandedSources = new Set(),
  renderApproval,
}: ChatMessagesProps) {
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    // Scroll the inner container, not the window
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAnswer]);

  const displayMessages = [...messages];
  if (currentAnswer) {
    displayMessages.push({
      id: 'current-answer',
      type: 'assistant',
      content: normalizeSpacing(currentAnswer),
      timestamp: new Date(),
      isTyping: true,
    });
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {displayMessages.length === 0 && emptyState && (
        <div className="flex-1 flex items-center justify-center text-center text-gray-500 py-12">
          <div>
            {emptyState.icon}
            <p className="text-lg font-medium mt-4">{emptyState.title}</p>
            <p className="text-sm text-gray-400">{emptyState.description}</p>
          </div>
        </div>
      )}

      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto pr-2 mb-4 min-h-0 scroll-smooth">
        <div className="space-y-4">
          {displayMessages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} group`}
            >
              <div className={`flex items-start space-x-3 max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center shadow-sm ${
                  message.type === 'user' 
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600' 
                    : message.type === 'assistant'
                    ? 'bg-gradient-to-br from-gray-700 to-gray-800'
                    : 'bg-blue-100'
                }`}>
                  {message.type === 'user' ? (
                    <span className="text-white text-xs font-semibold">You</span>
                  ) : message.type === 'assistant' ? (
                    <span className="text-white text-xs font-semibold">AI</span>
                  ) : (
                    <InformationCircleIcon className="w-4 h-4 text-blue-600" />
                  )}
                </div>

                {/* Message Bubble */}
                <div className={`relative ${message.type === 'user' ? 'ml-1' : 'mr-1'}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl shadow-sm ${
                      message.type === 'user'
                        ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-sm'
                        : message.type === 'assistant'
                        ? 'bg-white text-gray-900 border border-gray-200 rounded-bl-sm shadow-sm'
                        : 'bg-blue-50 text-blue-800 border border-blue-200 rounded-bl-sm'
                    }`}
                  >
                    {message.isTyping ? (
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1.5">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
                        </div>
                        <span className="text-sm text-gray-500 font-medium">Thinking...</span>
                      </div>
                    ) : (
                      <>
                        {message.type === 'system' && (
                          <div className="flex items-start space-x-2 mb-3">
                            {message.content.includes('Successfully') || message.content.includes('completed') ? (
                              <CheckBadgeIcon className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                            ) : message.content.includes('Error') || message.content.includes('Failed') || message.content.includes('❌') || message.content.includes('⚠️') ? (
                              <ExclamationCircleIcon className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                            ) : (
                              <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                            )}
                          </div>
                        )}
                        
                        <div className="prose prose-sm max-w-none">
                          <div
                            className={`leading-relaxed 
                              [&>p]:mb-3 [&>p:last-child]:mb-0 
                              [&>ul]:list-disc [&>ul]:list-outside [&>ul]:mb-3 [&>ul]:pl-6 [&>ul]:space-y-1.5 
                              [&>ol]:list-decimal [&>ol]:list-outside [&>ol]:mb-3 [&>ol]:pl-6 [&>ol]:space-y-1.5 
                              [&>li]:text-gray-700 [&>li]:mb-1 [&>li]:leading-relaxed
                              [&>ul>li]:pl-1 [&>ol>li]:pl-1
                              [&>ul>ul]:mt-2 [&>ul>ul]:mb-2 [&>ul>ul]:list-[circle] [&>ul>ul]:pl-6
                              [&>ul>ul>ul]:list-[square] 
                              [&>ol>ol]:mt-2 [&>ol>ol]:mb-2 [&>ol>ol]:list-[lower-alpha] [&>ol>ol]:pl-6
                              [&>ol>ol>ol]:list-[lower-roman]
                              [&>strong]:font-semibold [&>strong]:text-gray-900 
                              [&>em]:italic [&>em]:text-gray-800 
                              [&>code]:bg-gray-100 [&>code]:px-2 [&>code]:py-1 [&>code]:rounded-md [&>code]:text-sm [&>code]:font-mono [&>code]:text-gray-800
                              [&>pre]:bg-gray-100 [&>pre]:p-3 [&>pre]:rounded-lg [&>pre]:text-sm [&>pre]:font-mono [&>pre]:overflow-x-auto [&>pre]:mb-3
                              [&>pre>code]:bg-transparent [&>pre>code]:p-0
                              [&>h1]:text-lg [&>h1]:font-bold [&>h1]:text-gray-900 [&>h1]:mb-3 [&>h1]:mt-4
                              [&>h2]:text-base [&>h2]:font-bold [&>h2]:text-gray-900 [&>h2]:mb-3 [&>h2]:mt-4
                              [&>h3]:text-sm [&>h3]:font-bold [&>h3]:text-gray-900 [&>h3]:mb-2 [&>h3]:mt-3
                              [&>blockquote]:border-l-4 [&>blockquote]:border-gray-300 [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:text-gray-600 [&>blockquote]:mb-3 [&>blockquote]:my-3
                              [&>a]:text-blue-600 [&>a]:underline [&>a]:hover:text-blue-800
                              [&>table]:w-full [&>table]:border-collapse [&>table]:mb-3 [&>table]:mt-3
                              [&>table>thead]:bg-gray-100
                              [&>table>thead>tr>th]:border [&>table>thead>tr>th]:border-gray-300 [&>table>thead>tr>th]:px-3 [&>table>thead>tr>th]:py-2 [&>table>thead>tr>th]:text-left [&>table>thead>tr>th]:font-semibold
                              [&>table>tbody>tr>td]:border [&>table>tbody>tr>td]:border-gray-300 [&>table>tbody>tr>td]:px-3 [&>table>tbody>tr>td]:py-2
                              [&>table>tbody>tr:nth-child(even)]:bg-gray-50
                              [&>hr]:border-gray-300 [&>hr]:my-4
                              ${
                              message.type === 'user' 
                                ? 'text-white [&>strong]:text-white [&>em]:text-blue-100 [&>li]:text-blue-100 [&>h1]:text-white [&>h2]:text-white [&>h3]:text-white [&>blockquote]:text-blue-100 [&>blockquote]:border-blue-400 [&>code]:bg-blue-700 [&>code]:text-blue-100 [&>pre]:bg-blue-700 [&>pre]:text-blue-100 [&>a]:text-blue-200 [&>a:hover]:text-blue-100 [&>table>thead]:bg-blue-800 [&>table>thead>tr>th]:border-blue-600 [&>table>thead>tr>th]:text-blue-100 [&>table>tbody>tr>td]:border-blue-600 [&>table>tbody>tr:nth-child(even)]:bg-blue-900 [&>hr]:border-blue-400'
                                : 'text-gray-800'
                            }`}
                            dangerouslySetInnerHTML={{
                              __html: marked(normalizeSpacing(message.content || ''), { 
                                breaks: true, 
                                gfm: true
                              }) as string
                            }}
                          />
                        </div>
                        
                        {message.tool_calls && message.tool_calls.length > 0 && onToggleToolCall && (
                          <div className="mt-4 pt-3 border-t border-gray-200">
                            <button
                              onClick={() => onToggleToolCall(message.id)}
                              className="flex items-center text-xs font-medium text-gray-600 hover:text-gray-900 transition-colors group/tool"
                            >
                              <span className="mr-2 transition-transform group-hover/tool:scale-110 text-gray-400">
                                {expandedToolCalls.has(message.id) ? '▼' : '▶'}
                              </span>
                              <span className="bg-gray-100 hover:bg-gray-200 px-2.5 py-1 rounded-full transition-colors">
                                {message.tool_calls.length} tool{message.tool_calls.length !== 1 ? 's' : ''} used
                              </span>
                            </button>
                            {expandedToolCalls.has(message.id) && (
                              <div className="mt-3 space-y-3 animate-in slide-in-from-top-2 duration-200">
                                {message.tool_calls.map((toolCall, index) => (
                                  <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-3 hover:bg-gray-100 transition-colors">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                                        {toolCall.tool_name}
                                      </span>
                                      <span className="text-xs text-gray-400">
                                        {new Date(toolCall.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                      </span>
                                    </div>
                                    <div className="text-xs text-gray-600 mb-2 font-mono">
                                      <span className="font-semibold">Args:</span> {JSON.stringify(toolCall.arguments, null, 2)}
                                    </div>
                                    <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                                      <span className="font-semibold">Result:</span> {toolCall.result}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {message.sources && message.sources.length > 0 && onToggleSource && (
                          <div className="mt-4 pt-3 border-t border-gray-200">
                            <button
                              onClick={() => onToggleSource(message.id)}
                              className="flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors group/source"
                            >
                              <span className="mr-2 transition-transform group-hover/source:scale-110">
                                {expandedSources.has(message.id) ? '▼' : '▶'}
                              </span>
                              <span className="bg-gray-100 px-2 py-1 rounded-full">
                                {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                              </span>
                            </button>
                            {expandedSources.has(message.id) && (
                              <div className="mt-3 space-y-3 animate-in slide-in-from-top-2 duration-200">
                                {message.sources.map((source, index) => (
                                  <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-3 hover:bg-gray-100 transition-colors">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Source {index + 1}</span>
                                      <span className="text-xs text-gray-400">{source.url}</span>
                                    </div>
                                    <div className="text-sm text-gray-700 leading-relaxed">{source.content}</div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {message.approval && renderApproval && (
                          <div className="mt-4">
                            {renderApproval(message.approval)}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                  
                  {/* Timestamp */}
                  {!message.isTyping && (
                    <div className={`text-xs text-gray-400 mt-1.5 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
}

