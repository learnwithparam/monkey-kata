'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  GlobeAltIcon,
  PaperAirplaneIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

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
    } catch (_) {
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
              content: `✅ Successfully processed ${urlToCheck}! Found ${status.documents_count} document chunks. I'm now ready to answer questions as this website's AI assistant.`,
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
      let finalSources = [];

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

  const clearChat = () => {
    setMessages([]);
    setCurrentAnswer('');
    setSources([]);
    setQuestion('');
  };

  const clearAll = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/website-rag/clear`, { method: 'POST' });
      setMessages([]);
      setCurrentAnswer('');
      setSources([]);
      setQuestion('');
      setUrl('');
      setProcessingStatus(null);
      setIsProcessing(false);
      setIsAsking(false);
    } catch (error) {
      console.error('Error clearing data:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isAsking || !question.trim()) return;
      askQuestion();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <GlobeAltIcon className="w-8 h-8 text-blue-600 mr-3" />
                Website Chatbot
              </h1>
              <p className="text-gray-600 mt-1">
                Chat with the website's AI assistant to learn about their services and offerings
              </p>
            </div>
            <button
              onClick={clearAll}
              className="flex items-center px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <TrashIcon className="w-4 h-4 mr-2" />
              Clear All
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* URL Input Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">1. Add Website URL</h2>
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isProcessing}
              />
            </div>
            <button
              onClick={processUrl}
              disabled={isProcessing || !url.trim() || !isValidUrl(url)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {isProcessing ? (
                <>
                  <ClockIcon className="w-5 h-5 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <GlobeAltIcon className="w-5 h-5 mr-2" />
                  Process URL
                </>
              )}
            </button>
          </div>
          
          {/* Processing Status */}
          {processingStatus && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  {processingStatus.url}
                </span>
                <div className="flex items-center">
                  {processingStatus.status === 'completed' && (
                    <CheckCircleIcon className="w-5 h-5 text-green-500 mr-2" />
                  )}
                  {processingStatus.status === 'error' && (
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
                  )}
                  {processingStatus.status === 'processing' && (
                    <ClockIcon className="w-5 h-5 text-blue-500 mr-2 animate-spin" />
                  )}
                  <span className="text-sm text-gray-600">
                    {processingStatus.status}
                  </span>
                </div>
              </div>
              
              {processingStatus.status === 'processing' && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${processingStatus.progress}%` }}
                  />
                </div>
              )}
              
              <p className="text-sm text-gray-600 mt-2">
                {processingStatus.message}
                {processingStatus.documents_count > 0 && (
                  <span className="ml-2 text-green-600">
                    ({processingStatus.documents_count} chunks)
                  </span>
                )}
              </p>
            </div>
          )}
        </div>

        {/* Chat Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col" style={{ height: '600px' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && !currentAnswer && (
              <div className="text-center text-gray-500 py-12">
                <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">Welcome to our Website Chatbot!</p>
                <p className="text-sm">Add a website URL above and I'll become their AI assistant to help answer your questions.</p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl px-4 py-3 rounded-lg ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : message.type === 'assistant'
                      ? 'bg-gray-100 text-gray-900'
                      : 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                  }`}
                >
                  {message.isTyping ? (
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-sm text-gray-500">AI is thinking...</span>
                    </div>
                  ) : (
                    <>
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <button
                            onClick={() => toggleSource(message.id)}
                            className="flex items-center text-xs font-medium text-gray-600 hover:text-gray-800 transition-colors"
                          >
                            <span className="mr-1">
                              {expandedSources.has(message.id) ? '▼' : '▶'}
                            </span>
                            Sources ({message.sources.length})
                          </button>
                          {expandedSources.has(message.id) && (
                            <div className="mt-2 space-y-2">
                              {message.sources.map((source, index) => (
                                <div key={index} className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                                  <div className="font-medium text-gray-700 mb-1">Source {index + 1}:</div>
                                  <div className="text-gray-600">{source.content}</div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                  
                  <div className="text-xs opacity-70 mt-2">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}


            <div ref={messagesEndRef} />
          </div>

          {/* Question Input */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex gap-4">
              <input
                ref={questionInputRef}
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about our services..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isAsking || !processingStatus || processingStatus.status !== 'completed'}
              />
              <button
                onClick={askQuestion}
                disabled={isAsking || !question.trim() || !processingStatus || processingStatus.status !== 'completed'}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                {isAsking ? (
                  <>
                    <ClockIcon className="w-5 h-5 mr-2 animate-spin" />
                    Asking...
                  </>
                ) : (
                  <>
                    <PaperAirplaneIcon className="w-5 h-5 mr-2" />
                    Ask
                  </>
                )}
              </button>
            </div>
            
            {(!processingStatus || processingStatus.status !== 'completed') && (
              <p className="text-sm text-gray-500 mt-2">
                Please process a URL first before asking questions.
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>
            This AI chatbot represents the website and can answer questions about their services and offerings.
            <br />
            Try asking questions like "What services do you offer?" or "How can I get started?"
          </p>
        </div>
      </div>
    </div>
  );
}