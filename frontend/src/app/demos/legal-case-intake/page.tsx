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

  const submitCase = async () => {
    if (!caseData.client_name || !caseData.client_email || !caseData.case_type || !caseData.case_description) {
      setError('Please fill in all required fields');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setCaseReview(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/submit-case`, {
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

      const result: CaseIntakeResponse = await response.json();
      setCaseId(result.case_id);
      setCaseStatus(result);
      
      // Start polling for status updates
      pollStatus(result.case_id);
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Client Name *
                  </label>
                  <input
                    type="text"
                    value={caseData.client_name}
                    onChange={(e) => setCaseData({...caseData, client_name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Client Email *
                  </label>
                  <input
                    type="email"
                    value={caseData.client_email}
                    onChange={(e) => setCaseData({...caseData, client_email: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Client Phone
                  </label>
                  <input
                    type="tel"
                    value={caseData.client_phone}
                    onChange={(e) => setCaseData({...caseData, client_phone: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Case Type *
                  </label>
                  <input
                    type="text"
                    value={caseData.case_type}
                    onChange={(e) => setCaseData({...caseData, case_type: e.target.value})}
                    placeholder="e.g., Personal Injury, Contract Dispute"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Case Description *
                  </label>
                  <textarea
                    value={caseData.case_description}
                    onChange={(e) => setCaseData({...caseData, case_description: e.target.value})}
                    rows={5}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Urgency
                  </label>
                  <select
                    value={caseData.urgency}
                    onChange={(e) => setCaseData({...caseData, urgency: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={isProcessing}
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
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
                <div>
                  <StatusIndicator
                    status={caseStatus.status}
                    message={caseStatus.message}
                  />
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

