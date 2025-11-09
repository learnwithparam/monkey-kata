'use client';

import { useState, useCallback, useEffect } from 'react';
import Link from 'next/link';
import { 
  ChatBubbleLeftRightIcon, 
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline';
import ChatInput from '@/components/demos/ChatInput';
import AlertMessage from '@/components/demos/AlertMessage';
import ChatMessages from '@/components/demos/ChatMessages';
import { useStreamingChat, useApprovals } from '@/hooks';

interface MealPrepApproval {
  approval_id: string;
  step_name: string;
  step_number: number;
  content: Record<string, unknown>;
  status: 'pending' | 'approved' | 'rejected' | 'needs_revision';
  created_at: string;
  reviewed_at?: string;
  feedback?: string;
}

export default function MealPrepPage() {
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [selectedApproval, setSelectedApproval] = useState<MealPrepApproval | null>(null);
  const [reviewFeedback, setReviewFeedback] = useState('');
  const [currentStep, setCurrentStep] = useState(1);
  const [planId, setPlanId] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  
  const apiBaseUrl = `${process.env.NEXT_PUBLIC_API_URL}/meal-prep`;
  
  // Use approvals hook
  const { pendingApprovals, reviewApproval, fetchApprovals, isReviewing } = useApprovals({
    apiBaseUrl,
    refreshInterval: 3000,
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
    onApprovalCreated: (approvalId) => {
      setTimeout(() => {
        fetchApprovals();
        const approval = pendingApprovals.find(a => a.approval_id === approvalId);
        if (approval) {
          setSelectedApproval(approval as unknown as MealPrepApproval);
          setCurrentStep((approval as unknown as MealPrepApproval).step_number);
        }
      }, 500);
    },
  });

  // Update selected approval when pending approvals change
  useEffect(() => {
    if (pendingApprovals.length > 0 && !selectedApproval) {
      const latest = pendingApprovals[0] as unknown as MealPrepApproval;
      setSelectedApproval(latest);
      setCurrentStep(latest.step_number);
    }
  }, [pendingApprovals, selectedApproval]);

  const handleReview = useCallback(async (decision: 'approve' | 'reject') => {
    if (!selectedApproval) return;

    try {
      const response = await fetch(`${apiBaseUrl}/approvals/${selectedApproval.approval_id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approval_id: selectedApproval.approval_id,
          decision,
          feedback: reviewFeedback || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to review approval');
      }

      const result = await response.json();
      
      // If final plan was approved, extract plan_id
      if (decision === 'approve' && selectedApproval.step_name === 'final_plan') {
        const content = result.content as { plan_id?: string };
        if (content?.plan_id) {
          setPlanId(content.plan_id);
        }
      }

      setSelectedApproval(null);
      setReviewFeedback('');
      await fetchApprovals();
      
      addMessage({
        type: 'system',
        content: `✅ Step ${selectedApproval.step_number} ${decision === 'approve' ? 'approved' : 'rejected'}. ${decision === 'reject' ? 'Please provide feedback or ask the agent to modify.' : 'Continuing to next step...'}`,
      });

      if (decision === 'reject') {
        setMessage('Please modify the previous step based on my feedback.');
      }
    } catch (error) {
      console.error('Error reviewing approval:', error);
      addMessage({
        type: 'system',
        content: `❌ Error: ${error instanceof Error ? error.message : 'Failed to review approval'}`,
      });
    }
  }, [selectedApproval, reviewFeedback, apiBaseUrl, fetchApprovals, addMessage, setMessage]);

  const handleDownloadPDF = useCallback(async () => {
    if (!planId) return;

    setIsDownloading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/plans/${planId}/pdf`);
      if (!response.ok) {
        throw new Error('Failed to download PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `meal-plan-${planId.substring(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      addMessage({
        type: 'system',
        content: `❌ Error: ${error instanceof Error ? error.message : 'Failed to download PDF'}`,
      });
    } finally {
      setIsDownloading(false);
    }
  }, [planId, apiBaseUrl, addMessage]);

  const getStepName = (stepNumber: number) => {
    switch (stepNumber) {
      case 1:
        return 'Collecting Preferences';
      case 2:
        return 'Generating Meal Suggestions';
      case 3:
        return 'Calculating Nutrition';
      case 4:
        return 'Creating Shopping List';
      case 5:
        return 'Final Plan Review';
      default:
        return `Step ${stepNumber}`;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'needs_revision':
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
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            30-Day Meal Prep Agent
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Your personalized healthy eating assistant. Create a customized 30-day meal plan through 
            conversational interaction with human-in-the-loop approval at each step. Download your final plan as PDF.
          </p>
          <Link
            href="/challenges/meal-prep-agent"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md inline-block"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Step Indicator */}
        {currentStep > 0 && (
          <div className="mb-6">
            <div className="card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-1">
                    Current Step: {getStepName(currentStep)}
                  </h3>
                  <div className="flex items-center space-x-2">
                    {[1, 2, 3, 4, 5].map((step) => (
                      <div
                        key={step}
                        className={`flex items-center ${
                          step < currentStep
                            ? 'text-green-600'
                            : step === currentStep
                            ? 'text-blue-600 font-semibold'
                            : 'text-gray-400'
                        }`}
                      >
                        {step < currentStep ? (
                          <CheckCircleIcon className="w-5 h-5" />
                        ) : step === currentStep ? (
                          <div className="w-5 h-5 rounded-full border-2 border-blue-600 bg-blue-100" />
                        ) : (
                          <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                        )}
                        {step < 5 && (
                          <div
                            className={`w-8 h-0.5 ${
                              step < currentStep ? 'bg-green-600' : 'bg-gray-300'
                            }`}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                {planId && (
                  <button
                    onClick={handleDownloadPDF}
                    disabled={isDownloading}
                    className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <DocumentArrowDownIcon className="w-5 h-5" />
                    {isDownloading ? 'Downloading...' : 'Download PDF'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          {/* Left Column - Pending Approvals */}
          <div className="lg:col-span-1">
            <div className="card p-4 sm:p-6 lg:p-8">
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                  <CheckCircleIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Pending Approvals</h2>
                  <p className="text-sm text-gray-500">Review and approve steps</p>
                </div>
              </div>

              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {pendingApprovals.length > 0 ? (
                  pendingApprovals.map((approval) => {
                    const mealApproval = approval as unknown as MealPrepApproval;
                    return (
                      <div
                        key={approval.approval_id}
                        onClick={() => setSelectedApproval(mealApproval)}
                        className={`p-4 border rounded-lg cursor-pointer transition-all ${
                          selectedApproval?.approval_id === approval.approval_id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 text-sm">
                              Step {mealApproval.step_number}: {getStepName(mealApproval.step_number)}
                            </h3>
                            <p className="text-xs text-gray-600 mt-1">
                              {mealApproval.step_name.replace(/_/g, ' ')}
                            </p>
                          </div>
                          <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(approval.status)}`}>
                            {approval.status}
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <p className="text-xs text-gray-600">
                            Created: {new Date(mealApproval.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center py-8 text-gray-400 text-sm">
                    <CheckCircleIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No pending approvals</p>
                    <p className="text-xs mt-1">Start chatting to begin meal planning</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Chat and Approval Panel */}
          <div className="lg:col-span-2">
            {selectedApproval && selectedApproval.status === 'pending' ? (
              <div className="card p-4 sm:p-6 lg:p-8 h-[700px] flex flex-col">
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                      <CheckCircleIcon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">
                        Step {selectedApproval.step_number}: {getStepName(selectedApproval.step_number)}
                      </h2>
                      <p className="text-sm text-gray-500">Review and approve this step</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedApproval(null)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Close approval"
                  >
                    <XCircleIcon className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto mb-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Step Content</h3>
                      <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                          {JSON.stringify(selectedApproval.content, null, 2)}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Feedback (Optional)</h3>
                      <textarea
                        value={reviewFeedback}
                        onChange={(e) => setReviewFeedback(e.target.value)}
                        placeholder="Add your feedback or modification requests..."
                        className="w-full p-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        rows={4}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <div className="flex space-x-3">
                    <button
                      onClick={() => handleReview('approve')}
                      disabled={isReviewing}
                      className="flex-1 bg-green-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                    >
                      <CheckCircleIcon className="w-5 h-5" />
                      {isReviewing ? 'Processing...' : 'Approve'}
                    </button>
                    <button
                      onClick={() => handleReview('reject')}
                      disabled={isReviewing}
                      className="flex-1 bg-red-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                    >
                      <XCircleIcon className="w-5 h-5" />
                      {isReviewing ? 'Processing...' : 'Reject'}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="card p-4 sm:p-6 lg:p-8 h-[700px] flex flex-col">
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                      <ChatBubbleLeftRightIcon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">Meal Prep Assistant</h2>
                      <p className="text-sm text-gray-500">Conversational meal planning</p>
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
                    title: 'Welcome to Meal Prep Assistant!',
                    description: 'I\'ll help you create a personalized 30-day meal plan. Let\'s start by discussing your dietary preferences, restrictions, and goals. You can approve or modify each step as we go!'
                  }}
                  onToggleToolCall={toggleToolCall}
                  expandedToolCalls={expandedToolCalls}
                />

                <div className="border-t border-gray-200 pt-4 mt-auto">
                  <div className="space-y-3">
                    {isAsking && (
                      <AlertMessage
                        type="info"
                        message="Agent is processing your request..."
                      />
                    )}
                    
                    {selectedApproval && selectedApproval.status === 'pending' && (
                      <AlertMessage
                        type="warning"
                        message={`Step ${selectedApproval.step_number} is awaiting your approval. Please review it in the left panel.`}
                      />
                    )}
                    
                    <ChatInput
                      value={message}
                      onChange={setMessage}
                      onSend={askQuestion}
                      onKeyPress={handleKeyPress}
                      disabled={isAsking}
                      isLoading={isAsking}
                      placeholder="Tell me about your dietary preferences, restrictions, or goals..."
                    />
                  </div>
                </div>
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
                  <li>Start a conversation about your dietary preferences and goals</li>
                  <li>Agent collects information step-by-step and requests approval at each stage</li>
                  <li>Review and approve or reject each step with optional feedback</li>
                  <li>Agent generates meal suggestions, calculates nutrition, and creates shopping lists</li>
                  <li>Approve the final meal plan and download as PDF</li>
                  <li>You can interrupt, modify, or redo any step at any time</li>
                </ol>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Human-in-the-Loop</h3>
                <p className="text-sm text-gray-600 leading-relaxed mb-3">
                  This demonstrates <strong className="text-gray-900">human-in-the-loop AI workflows</strong> where 
                  an AI agent assists with meal planning but requires human approval at each critical step. 
                  You maintain full control and can interrupt, modify, or restart any part of the process.
                </p>
                <p className="text-sm text-gray-600 leading-relaxed">
                  The agent uses function calling to generate meal suggestions, calculate nutrition, 
                  and create shopping lists, but you decide what gets approved and what needs modification.
                </p>
              </div>
            </div>
            <div className="text-center text-sm text-gray-500 pt-4 border-t border-gray-200">
              <p>
                This meal prep assistant demonstrates human-in-the-loop workflows with AutoGen, showing how agents 
                can assist with meal planning while maintaining human oversight and control.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

