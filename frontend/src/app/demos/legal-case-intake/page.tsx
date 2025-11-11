'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ScaleIcon,
  DocumentTextIcon,
  UserIcon,
  CheckCircleIcon,
  XCircleIcon,
  SparklesIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import CustomSelect from '@/components/CustomSelect';

interface CaseIntakeRequest {
  client_name: string;
  client_email: string;
  client_phone?: string;
  case_type: string;
  case_description: string;
  urgency: string;
  additional_info?: string;
}

interface CaseIntakeResponse {
  case_id: string;
  status: string;
  message: string;
  steps?: Array<{
    timestamp: string;
    message: string;
    agent?: string;
    tool?: string;
    target?: string;
  }>;
}

interface CaseReview {
  case_id: string;
  status: string;
  intake_data: CaseIntakeRequest;
  intake_summary: string;
  risk_assessment: string;
  recommended_action: string;
  lawyer_notes?: string;
  lawyer_decision?: string;
}

export default function LegalCaseIntakeDemo() {
  const [caseData, setCaseData] = useState<CaseIntakeRequest>({
    client_name: '',
    client_email: '',
    client_phone: '',
    case_type: '',
    case_description: '',
    urgency: 'normal',
    additional_info: ''
  });
  const [caseId, setCaseId] = useState<string | null>(null);
  const [caseStatus, setCaseStatus] = useState<CaseIntakeResponse | null>(null);
  const [caseReview, setCaseReview] = useState<CaseReview | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lawyerNotes, setLawyerNotes] = useState('');
  const [lawyerDecision, setLawyerDecision] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'submit' | 'review'>('submit');
  const [workflowSteps, setWorkflowSteps] = useState<Array<{
    timestamp: string;
    message: string;
    agent?: string;
    tool?: string;
    target?: string;
  }>>([]);

  const submitCase = async () => {
    if (!caseData.client_name || !caseData.client_email || !caseData.case_type || !caseData.case_description) {
      setError('Please fill in all required fields');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setCaseReview(null);
    setWorkflowSteps([]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/submit-case-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(caseData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to submit case');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder('utf-8');
      const steps: Array<{ timestamp: string; message: string; agent?: string; tool?: string; target?: string }> = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.status === 'connected') {
                if (data.case_id) {
                  setCaseId(data.case_id);
                }
                setCaseStatus({
                  case_id: data.case_id || '',
                  status: 'processing',
                  message: data.message || 'Starting case intake processing...'
                });
                continue;
              }

              if (data.step) {
                // Real-time step update
                const newSteps = [...steps, data.step];
                steps.length = 0;
                steps.push(...newSteps);
                
                setWorkflowSteps(newSteps);
                setCaseStatus(prev => prev ? {
                  ...prev,
                  message: data.step.message,
                  status: 'processing',
                  steps: newSteps
                } : null);
              }

              if (data.done) {
                setIsProcessing(false);
                if (data.result) {
                  // Update status first
                  setCaseStatus(prev => {
                    const updatedStatus = prev ? {
                      ...prev,
                      status: 'pending_lawyer',
                      message: 'Case processed. Awaiting lawyer review.',
                      steps: steps
                    } : null;
                    
                    // Get case for review using case_id from status
                    if (updatedStatus && updatedStatus.case_id) {
                      fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/review/${updatedStatus.case_id}`)
                        .then(reviewResponse => {
                          if (reviewResponse.ok) {
                            return reviewResponse.json();
                          }
                          return null;
                        })
                        .then(review => {
                          if (review) {
                            setCaseReview(review);
                            setViewMode('review');
                            setCaseId(updatedStatus.case_id);
                          }
                        })
                        .catch(err => {
                          console.error('Error fetching review:', err);
                        });
                    }
                    
                    return updatedStatus;
                  });
                } else if (data.error) {
                  setError(data.error);
                  setCaseStatus(prev => prev ? {
                    ...prev,
                    status: 'error',
                    message: `Error: ${data.error}`
                  } : null);
                }
                return;
              }

              if (data.error) {
                setError(data.error);
                setIsProcessing(false);
                return;
              }
            } catch (parseError) {
              console.error('Error parsing chunk:', parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error submitting case:', error);
      setError(error instanceof Error ? error.message : 'Failed to submit case. Please try again.');
      setIsProcessing(false);
    }
  };

  const pollStatus = async (caseId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/status/${caseId}`);
        
        if (!response.ok) {
          throw new Error('Failed to get status');
        }

        const status: CaseIntakeResponse = await response.json();
        setCaseStatus(status);

        if (status.status === 'pending_lawyer') {
          // Get case for review
          const reviewResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/review/${caseId}`);
          if (reviewResponse.ok) {
            const review: CaseReview = await reviewResponse.json();
            setCaseReview(review);
            setViewMode('review');
          }
          setIsProcessing(false);
          return;
        }

        if (status.status === 'error') {
          setIsProcessing(false);
          setError(status.message || 'Case processing failed');
          return;
        }

        attempts++;
        if (attempts < maxAttempts && status.status === 'processing') {
          setTimeout(poll, 2000);
        } else {
          setIsProcessing(false);
          setError('Case processing timed out. Please try again.');
        }
      } catch (error) {
        console.error('Error polling status:', error);
        setIsProcessing(false);
        setError('Failed to check case status');
      }
    };

    poll();
  };

  const submitLawyerReview = async () => {
    if (!caseId || !lawyerDecision) {
      setError('Please select a decision');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/review/${caseId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          case_id: caseId,
          lawyer_notes: lawyerNotes,
          lawyer_decision: lawyerDecision
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to submit review');
      }

      const review: CaseReview = await response.json();
      setCaseReview(review);
      setCaseStatus({ case_id: caseId, status: review.status, message: `Case ${review.status}` });
      setIsProcessing(false);
    } catch (error) {
      console.error('Error submitting review:', error);
      setError(error instanceof Error ? error.message : 'Failed to submit review');
      setIsProcessing(false);
    }
  };

  const resetForm = () => {
    setCaseData({
      client_name: '',
      client_email: '',
      client_phone: '',
      case_type: '',
      case_description: '',
      urgency: 'normal',
      additional_info: ''
    });
    setCaseId(null);
    setCaseStatus(null);
    setCaseReview(null);
    setIsProcessing(false);
    setLawyerNotes('');
    setLawyerDecision('');
    setError(null);
    setViewMode('submit');
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
            Legal Case Intake Workflow
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Multi-agent system with human lawyer review
          </p>
          <Link
            href="/challenges/legal-case-intake"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6">
            <AlertMessage type="error" message={error} />
          </div>
        )}

        {/* Main Content */}
        <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">
        {viewMode === 'submit' ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
            {/* Case Submission Form */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <UserIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Case Information</h2>
                  <p className="text-sm sm:text-base text-gray-600">Submit a new case for intake</p>
                </div>
              </div>

              <div className="space-y-4 sm:space-y-6">
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Client Name *
                  </label>
                  <input
                    type="text"
                    value={caseData.client_name}
                    onChange={(e) => setCaseData({...caseData, client_name: e.target.value})}
                    placeholder="e.g., John Doe"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isProcessing}
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Client Email *
                  </label>
                  <input
                    type="email"
                    value={caseData.client_email}
                    onChange={(e) => setCaseData({...caseData, client_email: e.target.value})}
                    placeholder="e.g., john.doe@example.com"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isProcessing}
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Client Phone
                  </label>
                  <input
                    type="tel"
                    value={caseData.client_phone}
                    onChange={(e) => setCaseData({...caseData, client_phone: e.target.value})}
                    placeholder="e.g., +1 (555) 123-4567"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isProcessing}
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Case Type *
                  </label>
                  <input
                    type="text"
                    value={caseData.case_type}
                    onChange={(e) => setCaseData({...caseData, case_type: e.target.value})}
                    placeholder="e.g., Personal Injury, Contract Dispute"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isProcessing}
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Case Description *
                  </label>
                  <textarea
                    value={caseData.case_description}
                    onChange={(e) => setCaseData({...caseData, case_description: e.target.value})}
                    rows={5}
                    placeholder="Provide a detailed description of the case..."
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed resize-y"
                    disabled={isProcessing}
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    Urgency
                  </label>
                  <CustomSelect
                    id="urgency"
                    name="urgency"
                    value={caseData.urgency}
                    onChange={(value) => setCaseData({...caseData, urgency: value})}
                    options={[
                      { value: 'low', label: 'Low' },
                      { value: 'normal', label: 'Normal' },
                      { value: 'high', label: 'High' },
                      { value: 'urgent', label: 'Urgent' }
                    ]}
                    placeholder="Select urgency level..."
                    disabled={isProcessing}
                  />
                </div>

                <ProcessingButton
                  onClick={submitCase}
                  isProcessing={isProcessing}
                  disabled={!caseData.client_name || !caseData.client_email || !caseData.case_type || !caseData.case_description}
                  className="w-full"
                >
                  {isProcessing ? 'Processing...' : 'Submit Case'}
                </ProcessingButton>
              </div>
            </div>

            {/* Status Display */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <DocumentTextIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Case Status</h2>
                  <p className="text-sm sm:text-base text-gray-600">Track case processing status</p>
                </div>
              </div>

              {!caseStatus && (
                <div className="text-center py-12 text-gray-500">
                  <ScaleIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p>Submit a case to see status</p>
                </div>
              )}

              {caseStatus && (
                <div className="mb-6">
                  <StatusIndicator
                    status={caseStatus.status}
                    message={caseStatus.message}
                  />
                  
                  {/* Multi-Agent Workflow Steps */}
                  {(workflowSteps.length > 0 || (caseStatus.steps && caseStatus.steps.length > 0)) && (
                    <div className="mt-6 space-y-3">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                        <SparklesIcon className="h-4 w-4 text-blue-600 mr-2" />
                        Multi-Agent Workflow
                      </h3>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {(workflowSteps.length > 0 ? workflowSteps : caseStatus.steps || []).map((step, index) => {
                          const getStatusColor = () => {
                            if (step.tool === 'agent_complete' || step.tool === 'workflow_complete') return 'bg-green-500';
                            if (step.tool === 'agent_invoke') return 'bg-blue-500 animate-pulse';
                            if (step.tool === 'agent_processing' || step.tool === 'crew_execution' || step.tool === 'data_parsing') return 'bg-purple-500 animate-pulse';
                            return 'bg-gray-400';
                          };

                          const getAgentColor = (agent: string | undefined) => {
                            if (!agent) return 'bg-gray-200 text-gray-700';
                            if (agent.includes('Intake')) return 'bg-blue-100 text-blue-700';
                            if (agent.includes('Review')) return 'bg-purple-100 text-purple-700';
                            if (agent.includes('Workflow') || agent.includes('Orchestrator')) return 'bg-green-100 text-green-700';
                            return 'bg-gray-100 text-gray-700';
                          };

                          return (
                            <div
                              key={index}
                              className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-all"
                            >
                              <div className="flex-shrink-0 mt-0.5">
                                <div className={`w-3 h-3 ${getStatusColor()} rounded-full`}></div>
                              </div>
                              <div className="flex-1 min-w-0">
                                {step.agent && (
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className={`text-xs font-semibold px-2 py-1 rounded ${getAgentColor(step.agent)}`}>
                                      {step.agent}
                                    </span>
                                    {step.tool && step.tool !== 'agent_invoke' && step.tool !== 'agent_complete' && step.tool !== 'workflow_complete' && (
                                      <span className="text-xs text-gray-600 font-mono bg-gray-100 px-2 py-1 rounded">
                                        {step.tool}
                                      </span>
                                    )}
                                  </div>
                                )}
                                <p className="text-sm font-medium text-gray-900 break-words">
                                  {step.message}
                                </p>
                                {step.target && (
                                  <p className="text-xs text-gray-600 mt-1 font-mono bg-gray-50 px-2 py-1 rounded inline-block">
                                    {step.target}
                                  </p>
                                )}
                                <p className="text-xs text-gray-500 mt-2">
                                  {new Date(step.timestamp).toLocaleTimeString()}
                                </p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {caseStatus.status === 'processing' && (
                    <div className="mt-4">
                      <div className="flex items-center text-sm text-gray-600">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                        Intake and Review agents processing case...
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Lawyer Review View */
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center mb-6 sm:mb-8">
              <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                <ScaleIcon className="w-6 h-6 text-gray-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Lawyer Review</h2>
                <p className="text-sm sm:text-base text-gray-600">Review and make decisions on cases</p>
              </div>
            </div>

            {caseReview && (
              <div className="space-y-6">
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Case Summary</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-line">{caseReview.intake_summary}</p>
                </div>

                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Risk Assessment</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-line">{caseReview.risk_assessment}</p>
                </div>

                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">AI Recommendation</h3>
                  <p className="text-sm text-gray-700">{caseReview.recommended_action}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Notes
                  </label>
                  <textarea
                    value={lawyerNotes}
                    onChange={(e) => setLawyerNotes(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Add your review notes..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Decision *
                  </label>
                  <div className="flex gap-4">
                    <button
                      onClick={() => setLawyerDecision('approve')}
                      className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                        lawyerDecision === 'approve'
                          ? 'bg-green-100 border-green-500 text-green-700'
                          : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <CheckCircleIcon className="h-5 w-5 inline mr-2" />
                      Approve
                    </button>
                    <button
                      onClick={() => setLawyerDecision('reject')}
                      className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                        lawyerDecision === 'reject'
                          ? 'bg-red-100 border-red-500 text-red-700'
                          : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <XCircleIcon className="h-5 w-5 inline mr-2" />
                      Reject
                    </button>
                    <button
                      onClick={() => setLawyerDecision('request_info')}
                      className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                        lawyerDecision === 'request_info'
                          ? 'bg-yellow-100 border-yellow-500 text-yellow-700'
                          : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      Request Info
                    </button>
                  </div>
                </div>

                <div className="flex gap-4">
                  <ProcessingButton
                    onClick={submitLawyerReview}
                    isProcessing={isProcessing}
                    disabled={!lawyerDecision}
                    className="flex-1"
                  >
                    Submit Review
                  </ProcessingButton>
                  <button
                    onClick={resetForm}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                  >
                    <ArrowPathIcon className="h-5 w-5 inline mr-2" />
                    New Case
                  </button>
                </div>

                {caseReview.lawyer_decision && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Final Decision</h3>
                    <p className="text-sm text-gray-700">
                      Status: <span className="font-semibold">{caseReview.status}</span>
                    </p>
                    {caseReview.lawyer_notes && (
                      <p className="text-sm text-gray-700 mt-2 whitespace-pre-line">{caseReview.lawyer_notes}</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        </div>
      </div>
    </div>
  );
}

