'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { ClipboardDocumentCheckIcon, ChatBubbleLeftRightIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import ChatInput from '@/components/demos/ChatInput';
import AlertMessage from '@/components/demos/AlertMessage';
import ChatMessages from '@/components/demos/ChatMessages';
import ApprovalList from '@/components/demos/ApprovalList';
import ApprovalReviewPanel from '@/components/demos/ApprovalReviewPanel';
import LoanApplicationForm, { LoanApplicationData } from '@/components/demos/LoanApplicationForm';
import { Approval } from '@/components/demos/ApprovalList';
import { useStreamingChat, useApprovals } from '@/hooks';

export default function LoanApplicationPage() {
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [showChat, setShowChat] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [chatApplicationId, setChatApplicationId] = useState<string | null>(null);
  
  const apiBaseUrl = `${process.env.NEXT_PUBLIC_API_URL}/loan-application`;
  
  // Use approvals hook
  const { pendingApprovals, reviewApproval, fetchApprovals, isReviewing } = useApprovals({
    apiBaseUrl,
    refreshInterval: 5000,
  });

  // Use streaming chat hook
  const {
    message,
    setMessage,
    messages,
    isAsking,
    currentAnswer,
    expandedToolCalls,
    toggleToolCall,
    askQuestion,
    handleKeyPress,
    addMessage,
  } = useStreamingChat({
    apiEndpoint: `${apiBaseUrl}/chat/stream`,
    sessionId,
    applicationId: chatApplicationId || undefined,
    onApprovalCreated: () => {
      setTimeout(fetchApprovals, 1000);
    },
  });

  const [analysisMessages, setAnalysisMessages] = useState<typeof messages>([]);

  const handleFormSubmit = useCallback(async (formData: LoanApplicationData) => {
    setIsSubmitting(true);
    setShowForm(false);
    setShowChat(true);
    setSelectedApproval(null);
    setMessage('');
    
    // Clear and initialize analysis messages
    const initialMessages: typeof messages = [];
    
    // Add initial message
    initialMessages.push({
      id: `system-${Date.now()}`,
      type: 'system',
      content: `Analyzing loan application for ${formData.applicant_name}...`,
      timestamp: new Date(),
    });

    setAnalysisMessages(initialMessages);

    try {
      const response = await fetch(`${apiBaseUrl}/analyze/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to start analysis');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let done = false;
      let finalAnswer = '';
      let finalToolCalls: Array<{tool_name: string; arguments: Record<string, unknown>; result: string; timestamp: string}> = [];
      let approvalData: {approval_id?: string; application_id?: string; recommendation?: string; risk_score?: number} | null = null;

      // Add typing indicator
      const typingMessageId = `typing-${Date.now()}`;
      initialMessages.push({
        id: typingMessageId,
        type: 'assistant',
        content: '',
        isTyping: true,
        timestamp: new Date(),
      });
      setAnalysisMessages([...initialMessages]);

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
                setAnalysisMessages(prev => [...prev, {
                  id: `error-${Date.now()}`,
                  type: 'system',
                  content: `❌ Error: ${data.error}`,
                  timestamp: new Date(),
                }]);
                setIsSubmitting(false);
                return;
              }

              if (data.tool_calls) {
                finalToolCalls = data.tool_calls;
                setAnalysisMessages(prev => {
                  const updated = [...prev];
                  const typingMessage = updated.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.tool_calls = data.tool_calls;
                  }
                  return updated;
                });
              }
              
              if (data.content) {
                finalAnswer += data.content;
                setAnalysisMessages(prev => {
                  const updated = [...prev];
                  const typingMessage = updated.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.content = finalAnswer;
                    typingMessage.isTyping = false;
                  }
                  return updated;
                });
              }
              
              if (data.done) {
                const finalContent = data.response || finalAnswer;
                approvalData = data.approval;
                
                setAnalysisMessages(prev => {
                  const updated = [...prev];
                  const typingMessage = updated.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.content = finalContent;
                    typingMessage.tool_calls = data.tool_calls || finalToolCalls;
                    typingMessage.isTyping = false;
                  }
                  return updated;
                });
                
                setIsSubmitting(false);
                
                if (approvalData?.application_id) {
                  await fetchApprovals();
                  const appId = approvalData.application_id;
                  setAnalysisMessages(prev => [...prev, {
                    id: `complete-${Date.now()}`,
                    type: 'system',
                    content: `✅ Analysis complete. Application ${appId} is ready for review.`,
                    timestamp: new Date(),
                  }]);
                }
              }
            } catch (e) {
              console.error('Error parsing streaming data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error submitting application:', error);
      setAnalysisMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        type: 'system',
        content: `❌ Error: ${error instanceof Error ? error.message : 'Failed to analyze application'}`,
        timestamp: new Date(),
      }]);
      setIsSubmitting(false);
    }
  }, [apiBaseUrl, fetchApprovals, setMessage]);

  const handleRequestMoreInfo = useCallback(async () => {
    if (!selectedApproval) return;

    try {
      const response = await fetch(`${apiBaseUrl}/approvals/${selectedApproval.approval_id}/request-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(null),
      });

      if (!response.ok) {
        throw new Error('Failed to request more information');
      }

      await fetchApprovals();
      setChatApplicationId(selectedApproval.application_id);
      setShowChat(true);
      setMessage(`I need more information about your loan application ${selectedApproval.application_id}. Can you provide additional details?`);
    } catch (error) {
      console.error('Error requesting more info:', error);
      addMessage({
        type: 'system',
        content: `❌ Error: ${error instanceof Error ? error.message : 'Failed to request more information'}`,
      });
    }
  }, [selectedApproval, apiBaseUrl, fetchApprovals, setMessage, addMessage]);

  const handleReview = useCallback(async (decision: 'approve' | 'reject') => {
    if (!selectedApproval) return;

    try {
      await reviewApproval(selectedApproval.approval_id, decision, reviewNotes);
      
      setSelectedApproval(null);
      setReviewNotes('');
      setShowChat(false);
      setChatApplicationId(null);
      
      addMessage({
        type: 'system',
        content: `✅ Application ${decision === 'approve' ? 'approved' : 'rejected'} successfully.`,
      });
    } catch (error) {
      console.error('Error reviewing approval:', error);
      addMessage({
        type: 'system',
        content: `❌ Error: ${error instanceof Error ? error.message : 'Failed to review approval'}`,
      });
    }
  }, [selectedApproval, reviewNotes, reviewApproval, addMessage]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'needs_more_info':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <ClipboardDocumentCheckIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Loan Application Assistant
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Agentic AI workflow demonstration. Submit loan applications via form, and watch the AI agent perform multi-step analysis automatically using tools to calculate metrics, assess risk, and generate comprehensive reports.
          </p>
          <Link
            href="/challenges/loan-application-assistant"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md inline-block"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
          {/* Left Column - Form or Pending Approvals */}
          <div className="lg:col-span-1">
            {showForm ? (
              <div className="card p-4 sm:p-6 lg:p-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                      <PlusIcon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">New Application</h2>
                      <p className="text-sm text-gray-500">Submit loan application</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowForm(false)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Close form"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
                <LoanApplicationForm
                  onSubmit={handleFormSubmit}
                  isLoading={isSubmitting}
                />
              </div>
            ) : (
              <div className="card p-4 sm:p-6 lg:p-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                      <ClipboardDocumentCheckIcon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">Pending Reviews</h2>
                      <p className="text-sm text-gray-500">Applications awaiting decision</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setShowForm(true);
                      setSelectedApproval(null);
                      setShowChat(false);
                      setChatApplicationId(null);
                    }}
                    className="bg-white text-gray-900 font-semibold py-2 px-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2 text-sm"
                  >
                    <PlusIcon className="w-4 h-4" />
                    New Application
                  </button>
                </div>
                <ApprovalList
                  approvals={pendingApprovals}
                  selectedApproval={selectedApproval}
                  onSelectApproval={(approval) => {
                    setSelectedApproval(approval);
                    setShowChat(approval.status === 'needs_more_info');
                    setChatApplicationId(approval.status === 'needs_more_info' ? approval.application_id : null);
                  }}
                  getStatusColor={getStatusColor}
                />
              </div>
            )}
          </div>

          {/* Right Column - Review Panel or Chat */}
          <div className="lg:col-span-1">
            {showChat ? (
              <div className="card p-4 sm:p-6 lg:p-8 h-[700px] flex flex-col">
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                      <ChatBubbleLeftRightIcon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">Collect Information</h2>
                      <p className="text-sm text-gray-500">
                        {chatApplicationId ? `Application ${chatApplicationId}` : 'Chat with applicant'}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setShowChat(false);
                      setChatApplicationId(null);
                      if (selectedApproval && pendingApprovals.length > 0) {
                        const updated = pendingApprovals.find(a => a.approval_id === selectedApproval.approval_id);
                        if (updated) setSelectedApproval(updated);
                      }
                    }}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Close chat"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex-1 overflow-hidden flex flex-col">
                  <ChatMessages
                    messages={showChat && analysisMessages.length > 0 ? analysisMessages : messages}
                    currentAnswer={currentAnswer}
                    emptyState={{
                      icon: <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />,
                      title: 'AI Agent Analysis',
                      description: 'Submit a loan application using the form to see the AI agent perform multi-step analysis using tools.'
                    }}
                    onToggleToolCall={toggleToolCall}
                    expandedToolCalls={expandedToolCalls}
                  />
                  <div className="border-t border-gray-200 pt-4 mt-auto">
                    <div className="space-y-3">
                      {(isAsking || isSubmitting) && (
                        <AlertMessage
                          type="info"
                          message={isSubmitting ? "AI agent is analyzing the application..." : "Processing your request..."}
                        />
                      )}
                      <ChatInput
                        value={message}
                        onChange={setMessage}
                        onSend={askQuestion}
                        onKeyPress={handleKeyPress}
                        disabled={isAsking || isSubmitting}
                        isLoading={isAsking || isSubmitting}
                        placeholder={isSubmitting ? "Analysis in progress..." : (chatApplicationId ? "Ask for more information about the application..." : "Enter your message...")}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="card p-4 sm:p-6 lg:p-8 h-[700px] flex flex-col overflow-hidden">
                <ApprovalReviewPanel
                  approval={selectedApproval}
                  reviewNotes={reviewNotes}
                  onReviewNotesChange={setReviewNotes}
                  onReview={handleReview}
                  onRequestMoreInfo={handleRequestMoreInfo}
                  isReviewing={isReviewing}
                />
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 py-8">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">How it works</h3>
                <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                  <li>Submit a loan application using the form (applicant details, income, credit score, etc.)</li>
                  <li>AI agent automatically performs multi-step analysis using tools</li>
                  <li>Agent calculates debt-to-income ratio, assesses credit risk, and generates detailed analysis</li>
                  <li>Analysis results are displayed in real-time on the right side</li>
                  <li>Agent creates a review request for final human decision</li>
                  <li>Application appears in pending reviews queue for human escalation</li>
                </ol>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Agentic AI Workflows</h3>
                <p className="text-sm text-gray-600 leading-relaxed mb-3">
                  This demonstrates <strong className="text-gray-900">agentic AI workflows</strong> where an AI agent autonomously performs 
                  complex multi-step analysis using tools. The agent orchestrates multiple analysis steps, calculates metrics, 
                  and presents findings for human review.
                </p>
                <p className="text-sm text-gray-600 leading-relaxed">
                  The agent uses function calling to execute analysis tools in sequence, showing each step of the process 
                  and creating structured outputs ready for human decision-making.
                </p>
              </div>
            </div>
            <div className="text-center text-sm text-gray-500 pt-4 border-t border-gray-200">
              <p>
                This loan application assistant demonstrates agentic AI workflows with AutoGen, showing how agents perform multi-step analysis using tools.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
