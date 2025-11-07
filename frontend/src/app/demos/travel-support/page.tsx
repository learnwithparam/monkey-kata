'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ChatBubbleLeftRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import ChatInput from '@/components/demos/ChatInput';
import AlertMessage from '@/components/demos/AlertMessage';
import ChatMessages, { ChatMessage } from '@/components/demos/ChatMessages';

interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: string;
  timestamp: string;
}

interface Tool {
  name: string;
  description: string;
  example?: string;
}

export default function TravelSupportPage() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [expandedToolCalls, setExpandedToolCalls] = useState<Set<string>>(new Set());
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);

  useEffect(() => {
    // Fetch available tools on mount
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/travel-support/tools`)
      .then(res => res.json())
      .then(data => setAvailableTools(data.tools || []))
      .catch(err => console.error('Error fetching tools:', err));
  }, []);


  const toggleToolCall = (messageId: string) => {
    setExpandedToolCalls(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'> & { id?: string }) => {
    const newMessage: ChatMessage = {
      ...message,
      id: message.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const askQuestion = async () => {
    if (!message.trim()) {
      return;
    }

    const userMessage = message;
    setMessage('');
    setIsAsking(true);
    setCurrentAnswer('');

    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
    });

    // Add typing indicator
    const typingMessageId = `typing-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    addMessage({
      id: typingMessageId,
      type: 'assistant',
      content: '',
      isTyping: true,
    });

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/travel-support/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
          body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let done = false;
      let finalAnswer = '';
      let finalToolCalls: ToolCall[] = [];

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunk = decoder.decode(value);
        
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.error) {
                addMessage({
                  type: 'system',
                  content: `❌ Error: ${data.error}`,
                });
                setIsAsking(false);
                return;
              }

              if (data.tool_calls) {
                finalToolCalls = data.tool_calls;
                // Update message with tool calls
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.tool_calls = data.tool_calls;
                  }
                  return newMessages;
                });
              }
              
              if (data.content) {
                // Accumulate chunks for real-time display during streaming
                finalAnswer += data.content;
                setCurrentAnswer(prev => prev + data.content);
                
                // Update the typing message with accumulated content for real-time effect
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    // Use accumulated chunks for streaming display
                    typingMessage.content = finalAnswer;
                    typingMessage.isTyping = false;
                  }
                  return newMessages;
                });
              }
              
              if (data.done) {
                // Always use the final response from backend (properly formatted)
                // This overrides any accumulated chunks which might have formatting issues
                const finalContent = data.response || finalAnswer;
                
                // Update the typing message with final answer and tool calls
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    // Use final response which should be properly formatted
                    typingMessage.content = finalContent;
                    typingMessage.tool_calls = data.tool_calls || finalToolCalls;
                    typingMessage.isTyping = false;
                  }
                  return newMessages;
                });
                setCurrentAnswer('');
                setIsAsking(false);
              }
            } catch (e) {
              console.error('Error parsing streaming data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error asking question:', error);
      
      setMessages(prev => {
        return prev.filter(msg => msg.id !== typingMessageId);
      });
      
      addMessage({
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
      setIsAsking(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isAsking || !message.trim()) return;
      askQuestion();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Travel Customer Support Assistant
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Your AI-powered travel support assistant (like Booking.com) that helps with booking lookups, 
            hotel reservations, flight status, and taxi bookings. Demonstrates real-world function calling 
            for travel services.
          </p>
          <Link
            href="/challenges/travel-support"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md inline-block"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
          {/* Left Column - Available Tools */}
          <div className="lg:col-span-1">
            <div className="card p-4 sm:p-6 lg:p-8 h-full">
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                  <SparklesIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Support Tools</h2>
                  <p className="text-sm text-gray-600">Available functions</p>
                </div>
              </div>

              <div className="space-y-2.5">
                {availableTools.length > 0 ? (
                  availableTools.map((tool, index) => {
                    // Extract concise description (first sentence only, max 100 chars)
                    const fullDesc = tool.description || 'No description available';
                    const firstSentence = fullDesc.split('.')[0].trim();
                    const conciseDesc = firstSentence.length > 100 
                      ? firstSentence.substring(0, 100).trim() 
                      : firstSentence;
                    
                    return (
                      <div 
                        key={index} 
                        className="group border border-gray-200 rounded-lg p-3 hover:border-blue-300 hover:bg-blue-50/50 transition-all duration-200"
                      >
                        <h3 className="font-semibold text-gray-900 text-sm mb-1.5">
                          {tool.name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                        </h3>
                        <p className="text-xs text-gray-600 leading-relaxed mb-2">
                          {conciseDesc}
                        </p>
                        {tool.example && (
                          <div className="mt-2 pt-2 border-t border-gray-100">
                            <p className="text-xs text-gray-500 mb-1">Example:</p>
                            <p 
                              className="text-xs text-blue-600 italic cursor-pointer hover:text-blue-700"
                              onClick={() => setMessage(tool.example!)}
                            >
                              &quot;{tool.example}&quot;
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center py-8 text-gray-400 text-sm">
                    <SparklesIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>Loading tools...</p>
                  </div>
                )}
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-xs text-blue-800 font-medium mb-1.5">💡 Try asking:</p>
                  <ul className="text-xs text-blue-700 space-y-1.5">
                    <li>• &quot;What&apos;s my booking status for BK123456?&quot;</li>
                    <li>• &quot;Search hotels in Paris&quot;</li>
                    <li>• &quot;Book a taxi from airport to hotel&quot;</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Chat */}
          <div className="lg:col-span-1">
            <div className="card p-4 sm:p-6 lg:p-8 h-[700px] flex flex-col">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                    <ChatBubbleLeftRightIcon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Travel Support</h2>
                    <p className="text-sm text-gray-500">Professional customer assistance</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2 bg-green-50 border border-green-200 text-green-700 px-3 py-1.5 rounded-full text-xs font-semibold">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Online</span>
                </div>
              </div>

              {/* Chat Messages Area */}
              <ChatMessages
                messages={messages}
                currentAnswer={currentAnswer}
                emptyState={{
                  icon: <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />,
                  title: 'Welcome to Travel Support!',
                  description: 'Ask me about your booking, search hotels, check flight status, or book a taxi.'
                }}
                onToggleToolCall={toggleToolCall}
                expandedToolCalls={expandedToolCalls}
              />

              <div className="border-t border-gray-200 pt-4 mt-auto">
                  <div className="space-y-3">
                    {isAsking && (
                      <AlertMessage
                        type="info"
                      message="Processing your request..."
                      />
                    )}
                    
                    <ChatInput
                      value={message}
                      onChange={setMessage}
                      onSend={askQuestion}
                      onKeyPress={handleKeyPress}
                      disabled={isAsking}
                      isLoading={isAsking}
                    placeholder="Ask about bookings, hotels, flights, or taxi services..."
                    />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            This travel support assistant demonstrates real-world function calling. 
            Tools enable the assistant to access booking data and connect to hotel booking systems, 
            taxi services, and other travel services.
          </p>
        </div>
      </div>
    </div>
  );
}

