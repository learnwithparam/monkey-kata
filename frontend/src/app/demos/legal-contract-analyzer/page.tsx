'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { 
  ScaleIcon,
  DocumentTextIcon,
  CheckBadgeIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  DocumentArrowUpIcon,
  ShieldExclamationIcon,
  KeyIcon,
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
  document_id: string;
  status: string;
  progress: number;
  message: string;
  pages_count: number;
  error?: string;
}

interface RiskAnalysis {
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
  clause: string;
  recommendation: string;
}

interface KeyTerm {
  term: string;
  definition: string;
  importance: 'low' | 'medium' | 'high';
  clause: string;
}

export default function LegalContractAnalyzerDemo() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const [riskAnalysis, setRiskAnalysis] = useState<RiskAnalysis[]>([]);
  const [keyTerms, setKeyTerms] = useState<KeyTerm[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const questionInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'> & { id?: string }) => {
    const newMessage: Message = {
      ...message,
      id: message.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check file type
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
      ];
      
      if (!allowedTypes.includes(file.type)) {
        alert('Please select a PDF, Word document, or text file');
        return;
      }
      
      // Check file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const processDocument = async () => {
    if (!selectedFile) {
      alert('Please select a document to analyze');
      return;
    }

    setIsProcessing(true);
    addMessage({
      type: 'system',
      content: `Starting to process document: ${selectedFile.name}`,
    });

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('chunk_size', '500');
      formData.append('chunk_overlap', '50');

      console.log('Sending document to process:', selectedFile.name);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-contract-analyzer/upload-document`, {
        method: 'POST',
        body: formData,
      });

      console.log('Upload response:', response.status, response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error('Failed to start processing');
      }

      const result = await response.json();
      console.log('Upload result:', result);
      
      // Start polling for status
      pollProcessingStatus(result.document_id);
      
    } catch (error) {
      console.error('Error processing document:', error);
      addMessage({
        type: 'system',
        content: `Error processing document: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
      setIsProcessing(false);
    }
  };

  const pollProcessingStatus = async (documentId: string) => {
    console.log('Starting to poll status for:', documentId);
    const pollInterval = setInterval(async () => {
      try {
        console.log('Polling status for:', documentId);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-contract-analyzer/status/${documentId}`);
        console.log('Status response:', response.status, response.ok);
        
        if (response.ok) {
          const status: ProcessingStatus = await response.json();
          console.log('Status data:', status);
          setProcessingStatus(status);
          
          if (status.status === 'completed') {
            console.log('Processing completed!');
            addMessage({
              type: 'system',
              content: `Successfully processed document! Found ${status.pages_count} pages. I'm now ready to analyze risks and key terms.`,
            });
            
            // Get comprehensive agentic analysis
            await fetchAgenticAnalysis(documentId);
            
            setIsProcessing(false);
            clearInterval(pollInterval);
          } else if (status.status === 'error') {
            console.log('Processing error:', status.error);
            addMessage({
              type: 'system',
              content: `❌ Error processing document: ${status.error || 'Unknown error'}`,
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

  const fetchAgenticAnalysis = async (documentId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-contract-analyzer/agentic-analysis/${documentId}`);
      if (response.ok) {
        const analysis = await response.json();
        
        // Check if it's a legal document
        if (!analysis.is_legal_document) {
          addMessage({
            type: 'system',
            content: '⚠️ This document does not appear to be a legal document. Please upload a contract, agreement, or other legal document for analysis.',
          });
          return;
        }
        
        // Set the analysis results
        setRiskAnalysis(analysis.risk_analysis || []);
        setKeyTerms(analysis.key_terms || []);
        
        // Add the comprehensive report as a system message
        if (analysis.final_report) {
          addMessage({
            type: 'system',
            content: `📋 **Comprehensive Legal Analysis Report**\n\n${analysis.final_report}`,
          });
        }
      }
    } catch (error) {
      console.error('Error fetching agentic analysis:', error);
    }
  };

  const askQuestion = async () => {
    if (!question.trim() || !processingStatus) {
      alert('Please enter a question and make sure a document is processed');
      return;
    }

    if (!processingStatus || processingStatus.status !== 'completed') {
      alert('Please wait for the document to finish processing');
      return;
    }

    // Store the question and clear input immediately
    const userQuestion = question;
    setQuestion(''); // Clear input immediately
    setIsAsking(true);
    setCurrentAnswer('');

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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-contract-analyzer/ask/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          document_id: processingStatus.document_id,
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


  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isAsking || !question.trim()) return;
      askQuestion();
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <ScaleIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Legal Contract Analyzer
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Upload legal documents and instantly identify potential risks, key terms, and get AI-powered analysis of complex legal language.
          </p>
          <Link
            href="/challenges/legal-contract-analyzer"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Document Upload */}
          <div className="space-y-6">
            <div className="card p-6 lg:p-8">
              <div className="flex items-center mb-8">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                  <DocumentArrowUpIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Upload Legal Document</h2>
                  <p className="text-sm text-gray-600">PDF, Word, or text files supported</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="file" className="block text-sm font-semibold text-gray-700 mb-2">
                    Legal Document *
                  </label>
                  
                  {/* Drag and Drop Area */}
                  <div 
                    className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                      selectedFile 
                        ? 'border-blue-300 bg-blue-50' 
                        : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                    }`}
                    onDragOver={(e) => {
                      e.preventDefault();
                      e.currentTarget.classList.add('border-blue-400', 'bg-blue-50');
                    }}
                    onDragLeave={(e) => {
                      e.preventDefault();
                      e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50');
                    }}
                    onDrop={(e) => {
                      e.preventDefault();
                      e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50');
                      const files = e.dataTransfer.files;
                      if (files.length > 0) {
                        handleFileSelect({ target: { files } } as React.ChangeEvent<HTMLInputElement>);
                      }
                    }}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      id="file"
                      accept=".pdf,.doc,.docx,.txt"
                      onChange={handleFileSelect}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      disabled={isProcessing}
                    />
                    
                    {selectedFile ? (
                      <div className="space-y-2">
                        <DocumentTextIcon className="w-8 h-8 text-gray-600 mx-auto" />
                        <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                        <p className="text-xs text-gray-700">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                        <button
                          type="button"
                          onClick={() => setSelectedFile(null)}
                          className="text-xs text-blue-600 hover:text-blue-800 underline"
                        >
                          Remove file
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <DocumentArrowUpIcon className="w-8 h-8 text-gray-400 mx-auto" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Drop your legal document here
                          </p>
                          <p className="text-xs text-gray-500">
                            or click to browse files
                          </p>
                        </div>
                        <p className="text-xs text-gray-400">
                          Supports PDF, Word, and text files (max 10MB)
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <ProcessingButton
                  isLoading={isProcessing}
                  onClick={processDocument}
                  disabled={!selectedFile}
                >
                  <span className="flex items-center justify-center">
                    Analyze Document
                  </span>
                </ProcessingButton>

                {/* Processing Status */}
                {processingStatus && (
                  <StatusIndicator
                    status={processingStatus.status}
                    message={processingStatus.message}
                    progress={processingStatus.progress}
                    documentsCount={processingStatus.pages_count}
                  />
                )}
              </div>
            </div>

            {/* Risk Analysis */}
            {riskAnalysis.length > 0 && (
              <div className="card p-6 lg:p-8">
                <div className="flex items-center mb-6">
                  <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center mr-4">
                    <ShieldExclamationIcon className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Risk Analysis</h2>
                    <p className="text-sm text-gray-600">Potential risks identified in the document</p>
                  </div>
                </div>
                <div className="space-y-4">
                  {riskAnalysis.map((risk, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(risk.risk_level)}`}>
                          {risk.risk_level.toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-500">{risk.category}</span>
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-2">{risk.description}</h3>
                      <p className="text-sm text-gray-600 mb-2">{risk.clause}</p>
                      <p className="text-sm text-blue-600 font-medium">{risk.recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Terms */}
            {keyTerms.length > 0 && (
              <div className="card p-6 lg:p-8">
                <div className="flex items-center mb-6">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                    <KeyIcon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Key Terms</h2>
                    <p className="text-sm text-gray-600">Important legal terms and definitions</p>
                  </div>
                </div>
                <div className="space-y-4">
                  {keyTerms.map((term, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">{term.term}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImportanceColor(term.importance)}`}>
                          {term.importance.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{term.definition}</p>
                      <p className="text-xs text-gray-500">{term.clause}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
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
                    <h2 className="text-xl font-bold text-gray-900">Ask About Your Document</h2>
                    <p className="text-sm text-gray-500">Get AI-powered analysis of your legal document</p>
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
                  <p className="text-lg font-medium">Welcome to Legal Contract Analyzer!</p>
                  <p className="text-sm">Upload a legal document above and I&apos;ll analyze it for risks, key terms, and answer your questions.</p>
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
                              <span className="text-sm text-gray-500">AI is analyzing...</span>
                          </div>
                          ) : (
                            <>
                              {message.type === 'system' && (
                                <div className="flex items-start space-x-2 mb-3">
                                  {message.content.includes('Successfully') || message.content.includes('completed') ? (
                                    <CheckBadgeIcon className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                                  ) : message.content.includes('Error') || message.content.includes('Failed') || message.content.includes('⚠️') ? (
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
                    placeholder="Ask me about risks, terms, or any legal questions..."
                  />
                  
                  {(!processingStatus || processingStatus.status !== 'completed') && (
                    <AlertMessage
                      type="warning"
                      message="Please upload and process a document first before asking questions."
                    />
                  )}
                  
                  {isAsking && (
                    <AlertMessage
                      type="info"
                      message="AI is analyzing your document and will respond shortly..."
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
            This AI analyzer can identify potential risks, extract key terms, and answer questions about your legal documents.
            <br />
            Try asking questions like &quot;What are the main risks in this contract?&quot; or &quot;Explain the termination clause&quot;
          </p>
        </div>
      </div>
    </div>
  );
}
