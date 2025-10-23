'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { 
  GlobeAltIcon,
  DocumentTextIcon,
  CheckBadgeIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { marked } from 'marked';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import ChatInput from '@/components/demos/ChatInput';
import AlertMessage from '@/components/demos/AlertMessage';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  sources?: Array<{
    url: string;
    content: string;
  }>;
  isTyping?: boolean;
}

interface ProcessingStatus {
  url: string;
  status: string;
  progress: number;
  message: string;
  documents_count: number;
  error?: string;
}

export default function WebsiteRAGDemo() {
  const [url, setUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [sources, setSources] = useState<Array<{url: string; content: string}>>([]);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const questionInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleSource = (messageId: string) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAnswer]);

  const isValidUrl = (string: string) => {
    try {
      new URL(string);
      return true;
    } catch {
      return false;
    }
  };

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'> & { id?: string }) => {
    const newMessage: Message = {
      ...message,
      id: message.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const processUrl = async () => {
    if (!url.trim() || !isValidUrl(url)) {
      alert('Please enter a valid URL');
      return;
    }

    // Normalize URL to ensure consistent trailing slash handling
    let normalizedUrl = url.trim();
    if (!normalizedUrl.endsWith('/')) {
      normalizedUrl += '/';
    }

    setIsProcessing(true);
    addMessage({
      type: 'system',
      content: `Starting to process URL: ${normalizedUrl}`,
    });

    try {
      console.log('Sending URL to process:', normalizedUrl);
      console.log('API URL:', process.env.NEXT_PUBLIC_API_URL);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/website-rag/add-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: normalizedUrl,
          chunk_size: 500,
          chunk_overlap: 50,
        }),
      });

      console.log('Add URL response:', response.status, response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error('Failed to start processing');
      }

      const result = await response.json();
      console.log('Add URL result:', result);
      
      // Start polling for status with normalized URL
      pollProcessingStatus(normalizedUrl);
      
    } catch (error) {
      console.error('Error processing URL:', error);
      addMessage({
        type: 'system',
        content: `Error processing URL: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
            setIsProcessing(false);
    }
  };

  const pollProcessingStatus = async (urlToCheck: string) => {
    console.log('Starting to poll status for:', urlToCheck);
    const pollInterval = setInterval(async () => {
      try {
        console.log('Polling status for:', urlToCheck);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/website-rag/status/${encodeURIComponent(urlToCheck)}`);
        console.log('Status response:', response.status, response.ok);
        
        if (response.ok) {
          const status: ProcessingStatus = await response.json();
          console.log('Status data:', status);
          setProcessingStatus(status);
          
          if (status.status === 'completed') {
            console.log('Processing completed!');
            addMessage({
              type: 'system',
              content: `Successfully processed ${urlToCheck}! Found ${status.documents_count} document chunks. I'm now ready to answer questions as this website's AI assistant.`,
            });
            setIsProcessing(false);
            clearInterval(pollInterval);
          } else if (status.status === 'error') {
            console.log('Processing error:', status.error);
            addMessage({
              type: 'system',
              content: `❌ Error processing ${urlToCheck}: ${status.error || 'Unknown error'}`,
            });
            setIsProcessing(false);
            clearInterval(pollInterval);
          } else {
            console.log('Still processing, status:', status.status, 'progress:', status.progress);
          }
        } else {
          console.error('Status response not ok:', response.status);
        }
      } catch (error) {
        console.error('Error polling status:', error);
        clearInterval(pollInterval);
      setIsProcessing(false);
      }
    }, 1000);

    // Clear interval after 2 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (isProcessing) {
    setIsProcessing(false);
        addMessage({
          type: 'system',
          content: '⏰ Processing timeout. Please try again.',
        });
      }
    }, 120000);
  };

  const askQuestion = async () => {
    if (!question.trim() || !url.trim()) {
      alert('Please enter a question and make sure a URL is processed');
      return;
    }

    if (!processingStatus || processingStatus.status !== 'completed') {
      alert('Please wait for the URL to finish processing');
      return;
    }

    // Store the question and clear input immediately
    const userQuestion = question;
    setQuestion(''); // Clear input immediately
    setIsAsking(true);
    setCurrentAnswer('');
    setSources([]);

    // Add user message
    addMessage({
      type: 'user',
      content: userQuestion,
    });

    // Add typing indicator with unique ID
    const typingMessageId = `typing-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    addMessage({
      id: typingMessageId,
      type: 'assistant',
      content: '',
      isTyping: true,
    });

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/website-rag/ask/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          url: url,
          max_chunks: 3,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to ask question');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let done = false;
      let finalAnswer = '';
      let finalSources: Array<{url: string; content: string}> = [];

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunk = decoder.decode(value);
        
        // Parse SSE data
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              console.log('Received streaming data:', data);
              
              if (data.error) {
                console.error('Streaming error:', data.error);
                addMessage({
                  type: 'system',
                  content: `❌ Error: ${data.error}`,
                });
                setIsAsking(false);
                return;
              }

              if (data.sources) {
                console.log('Received sources:', data.sources);
                finalSources = data.sources;
                setSources(data.sources);
              }
              
              if (data.content) {
                console.log('Received content chunk:', data.content);
                finalAnswer += data.content;
                setCurrentAnswer(prev => prev + data.content);
                
                // Update the typing message with content
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.content = finalAnswer;
                    typingMessage.isTyping = false;
                  }
                  return newMessages;
                });
              }
              
              if (data.done) {
                console.log('Streaming completed. Final answer:', finalAnswer);
                // Update the typing message with final answer and sources
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.content = finalAnswer;
                    typingMessage.sources = finalSources;
                    typingMessage.isTyping = false;
                  }
                  return newMessages;
                });
                setCurrentAnswer('');
                setSources([]);
                setIsAsking(false);
                questionInputRef.current?.focus();
              }
            } catch (e) {
              console.error('Error parsing streaming data:', e, 'Line:', line);
              // Ignore parsing errors for incomplete chunks
            }
          }
        }
      }
    } catch (error) {
      console.error('Error asking question:', error);
      
      // Remove the typing indicator if there's an error
      setMessages(prev => {
        return prev.filter(msg => msg.id !== typingMessageId);
      });
      
      addMessage({
        type: 'system',
        content: `Error asking question: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
      setIsAsking(false);
    }
  };

  // const clearChat = () => {
  //   setMessages([]);
  //   setCurrentAnswer('');
  //   setSources([]);
  //   setQuestion('');
  // };

  // const clearAll = async () => {
  //   try {
  //     await fetch(`${process.env.NEXT_PUBLIC_API_URL}/website-rag/clear`, { method: 'POST' });
  //     setMessages([]);
  //     setCurrentAnswer('');
  //     setSources([]);
  //     setQuestion('');
  //     setUrl('');
  //     setProcessingStatus(null);
  //     setIsProcessing(false);
  //     setIsAsking(false);
  //   } catch (error) {
  //     console.error('Error clearing data:', error);
  //   }
  // };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isAsking || !question.trim()) return;
        askQuestion();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <GlobeAltIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Website Chatbot
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Transform any website into an intelligent assistant. Simply add a URL and start having meaningful conversations about their services and offerings.
          </p>
            <Link
              href="/challenges/website-rag"
              className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
            >
              View Learning Challenges
            </Link>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - URL Input */}
          <div className="space-y-6">
            <div className="card p-6 lg:p-8">
              <div className="flex items-center mb-8">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                  <GlobeAltIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Add Website URL</h2>
                  <p className="text-sm text-gray-600">Enter any website to start chatting</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="url" className="block text-sm font-semibold text-gray-700 mb-2">
                    Website URL *
                  </label>
                  <input
                    type="url"
                    id="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isProcessing}
                  />
                </div>

                <ProcessingButton
                  isLoading={isProcessing}
                  onClick={processUrl}
                  disabled={!url.trim() || !isValidUrl(url)}
                >
                  <span className="flex items-center justify-center">
                    Process Website
                  </span>
                </ProcessingButton>

                {/* Processing Status */}
                {processingStatus && (
                  <StatusIndicator
                    status={processingStatus.status}
                    message={processingStatus.message}
                    progress={processingStatus.progress}
                    documentsCount={processingStatus.documents_count}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Chat */}
          <div className="space-y-6">
            <div className="card p-6 lg:p-8 min-h-[600px]">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                    <DocumentTextIcon className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Chat with Website</h2>
                    <p className="text-sm text-gray-500">Ask questions about the website content</p>
                  </div>
                </div>
                {processingStatus && processingStatus.status === 'completed' && (
                  <div className="flex items-center space-x-2 bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-medium">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span>Ready</span>
                  </div>
                )}
            </div>

              {messages.length === 0 && !currentAnswer && (
                <div className="text-center text-gray-500 py-12">
                  <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium">Welcome to our Website Chatbot!</p>
                  <p className="text-sm">Add a website URL above and I&apos;ll become their AI assistant to help answer your questions.</p>
                </div>
              )}

              <div className="space-y-6 max-h-96 overflow-y-auto pr-2">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} group`}
                  >
                    <div className={`flex items-start space-x-3 max-w-[85%] ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                      {/* Avatar */}
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.type === 'user' 
                          ? 'bg-blue-100' 
                          : message.type === 'assistant'
                          ? 'bg-green-100'
                          : 'bg-amber-100'
                      }`}>
                        {message.type === 'user' ? (
                          <span className="text-blue-600 text-sm font-semibold">U</span>
                        ) : message.type === 'assistant' ? (
                          <span className="text-green-600 text-sm font-semibold">AI</span>
                        ) : (
                          <InformationCircleIcon className="w-4 h-4 text-amber-600" />
                        )}
                      </div>

                      {/* Message Bubble */}
                      <div className={`relative ${
                        message.type === 'user' ? 'ml-2' : 'mr-2'
                      }`}>
                        <div
                          className={`px-4 py-3 rounded-lg shadow-sm ${
                        message.type === 'user'
                              ? 'bg-blue-600 text-white rounded-br-md'
                              : message.type === 'assistant'
                              ? 'bg-white text-gray-900 border border-gray-200 rounded-bl-md'
                              : 'bg-amber-50 text-amber-800 border border-amber-200 rounded-bl-md'
                          }`}
                        >
                          {message.isTyping ? (
                            <div className="flex items-center space-x-3">
                              <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                              </div>
                              <span className="text-sm text-gray-500">AI is thinking...</span>
                          </div>
                          ) : (
                            <>
                              {message.type === 'system' && (
                                <div className="flex items-start space-x-2 mb-3">
                                  {message.content.includes('Successfully') ? (
                                    <CheckBadgeIcon className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                                  ) : message.content.includes('Error') || message.content.includes('Failed') ? (
                                    <ExclamationCircleIcon className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                                  ) : (
                                    <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                                  )}
                          </div>
                        )}
                              
                              <div className="prose prose-sm max-w-none">
                                <div
                                  className={`leading-relaxed [&>p]:mb-3 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:list-inside [&>ul]:mb-3 [&>ul]:space-y-2 [&>ol]:list-decimal [&>ol]:list-inside [&>ol]:mb-3 [&>ol]:space-y-2 [&>li]:text-gray-700 [&>strong]:font-semibold [&>strong]:text-gray-900 [&>em]:italic [&>em]:text-gray-800 [&>code]:bg-gray-100 [&>code]:px-2 [&>code]:py-1 [&>code]:rounded-md [&>code]:text-sm [&>code]:font-mono [&>pre]:bg-gray-100 [&>pre]:p-3 [&>pre]:rounded-lg [&>pre]:text-sm [&>pre]:font-mono [&>pre]:overflow-x-auto [&>h1]:text-lg [&>h1]:font-bold [&>h1]:text-gray-900 [&>h1]:mb-3 [&>h2]:text-base [&>h2]:font-bold [&>h2]:text-gray-900 [&>h2]:mb-3 [&>h3]:text-sm [&>h3]:font-bold [&>h3]:text-gray-900 [&>h3]:mb-2 [&>blockquote]:border-l-4 [&>blockquote]:border-gray-300 [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:text-gray-600 [&>blockquote]:mb-3 ${
                                    message.type === 'user' 
                                      ? 'text-white [&>strong]:text-white [&>em]:text-blue-100 [&>li]:text-blue-100 [&>h1]:text-white [&>h2]:text-white [&>h3]:text-white [&>blockquote]:text-blue-100 [&>code]:bg-blue-700 [&>code]:text-blue-100 [&>pre]:bg-blue-700 [&>pre]:text-blue-100'
                                      : 'text-gray-800'
                                  }`}
                                  dangerouslySetInnerHTML={{
                                    __html: marked(message.content, { breaks: true, gfm: true }) as string
                                  }}
                                />
                          </div>
                          
                          {message.sources && message.sources.length > 0 && (
                                <div className="mt-4 pt-3 border-t border-gray-200">
                                  <button
                                    onClick={() => toggleSource(message.id)}
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
                                            <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Source {index + 1}</span>
                                            <span className="text-xs text-gray-400">{source.url}</span>
                                          </div>
                                          <div className="text-sm text-gray-700 leading-relaxed">{source.content}</div>
                                </div>
                              ))}
                            </div>
                                  )}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                        
                        {/* Timestamp */}
                        <div className={`text-xs text-gray-400 mt-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}


              <div ref={messagesEndRef} />
            </div>

          {/* Question Input */}
              <div className="border-t border-gray-100 pt-6">
                <div className="space-y-4">
                  <ChatInput
                    value={question}
                    onChange={setQuestion}
                    onSend={askQuestion}
                    onKeyPress={handleKeyPress}
                    disabled={isAsking || !processingStatus || processingStatus.status !== 'completed'}
                    isLoading={isAsking}
                    placeholder="Ask me anything about our services..."
                  />
                  
                  {(!processingStatus || processingStatus.status !== 'completed') && (
                    <AlertMessage
                      type="warning"
                      message="Please process a URL first before asking questions."
                    />
                  )}
                  
                  {isAsking && (
                    <AlertMessage
                      type="info"
                      message="AI is thinking and will respond shortly..."
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            This AI chatbot represents the website and can answer questions about their services and offerings.
            <br />
            Try asking questions like &quot;What services do you offer?&quot; or &quot;How can I get started?&quot;
          </p>
        </div>
      </div>

    </div>
  );
}