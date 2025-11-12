'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  ScaleIcon,
  CheckCircleIcon,
  SparklesIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  DocumentTextIcon,
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
  needs_more_info?: boolean;
  missing_info?: string[];
  is_complete?: boolean;
  intake_summary?: string;
  risk_assessment?: string;
  recommended_action?: string;
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
  const [isProcessing, setIsProcessing] = useState(false);
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [error, setError] = useState<string | null>(null);
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
    setWorkflowSteps([]);
    setAdditionalInfo('');

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
              // Safely parse JSON, handle malformed JSON from streaming
              const jsonStr = line.slice(6).trim();
              if (!jsonStr) continue; // Skip empty lines
              
              let data;
              try {
                data = JSON.parse(jsonStr);
              } catch (parseErr) {
                // If JSON parsing fails, skip this line (likely incomplete or malformed)
                console.warn('Failed to parse JSON line:', jsonStr.substring(0, 100));
                continue;
              }

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
                  setCaseStatus({
                    case_id: caseId || '',
                    status: data.status,
                    message: data.result.is_complete ? 'Case intake complete! All information collected.' : 
                             data.result.needs_more_info ? 'Additional information needed.' : 
                             'Case processed. Ready for review.',
                    steps: steps,
                    needs_more_info: data.result.needs_more_info,
                    missing_info: data.result.missing_info,
                    is_complete: data.result.is_complete,
                    intake_summary: data.result.intake_summary,
                    risk_assessment: data.result.risk_assessment,
                    recommended_action: data.result.recommended_action
                  });
                } else if (data.error) {
                  setError(data.error);
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

  const submitAdditionalInfo = async () => {
    if (!caseId || !additionalInfo.trim()) {
      setError('Please provide the additional information');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/provide-additional-info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          case_id: caseId,
          additional_info: additionalInfo
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to submit additional information');
      }

      const result: CaseIntakeResponse = await response.json();
      setCaseStatus(result);
      setWorkflowSteps(result.steps || []);
      setAdditionalInfo('');
      setIsProcessing(false);
    } catch (error) {
      console.error('Error submitting additional info:', error);
      setError(error instanceof Error ? error.message : 'Failed to submit additional information.');
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
    setIsProcessing(false);
    setAdditionalInfo('');
    setError(null);
    setWorkflowSteps([]);
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
            Multi-agent system with iterative human-in-the-loop data gathering
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
            {/* Input Form */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <ScaleIcon className="w-6 h-6 text-gray-600" />
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

            {/* Status & Results */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <ScaleIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Case Status</h2>
                  <p className="text-sm sm:text-base text-gray-600">Track your case intake progress</p>
                </div>
              </div>

              {!caseStatus && (
                <div className="text-center py-12 text-gray-500">
                  <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p>Enter case information to start intake</p>
                </div>
              )}

              {caseStatus && (
                <div className="mb-6">
                  <StatusIndicator
                    status={caseStatus.status}
                    message={caseStatus.message}
                  />
                  
                  {/* Multi-Agent Workflow Steps */}
                  {workflowSteps.length > 0 && (
                    <div className="mt-6 space-y-3">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                        <SparklesIcon className="h-4 w-4 text-blue-600 mr-2" />
                        Multi-Agent Workflow
                      </h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {workflowSteps.map((step, index) => {
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
                </div>
              )}
            </div>
          </div>

          {/* Verdict Card - Show when processing is done or needs more info */}
          {caseStatus && !isProcessing && (caseStatus.status !== 'processing' || caseStatus.needs_more_info) && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-start gap-4 mb-6">
                {caseStatus.is_complete ? (
                  <div className="flex-shrink-0 w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                    <CheckCircleIcon className="w-6 h-6 text-green-600" />
                  </div>
                ) : caseStatus.needs_more_info ? (
                  <div className="flex-shrink-0 w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                    <InformationCircleIcon className="w-6 h-6 text-yellow-600" />
                  </div>
                ) : (
                  <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <ExclamationCircleIcon className="w-6 h-6 text-blue-600" />
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {caseStatus.is_complete ? 'Case Intake Complete!' : 
                     caseStatus.needs_more_info ? 'Additional Information Needed' : 
                     'Case Analysis Complete'}
                  </h3>
                  {caseStatus.intake_summary && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-700 whitespace-pre-line">{caseStatus.intake_summary}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Missing Information Form */}
              {caseStatus.needs_more_info && (
                <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <h4 className="text-sm font-semibold text-yellow-900 mb-3">Please provide the following information:</h4>
                  {caseStatus.missing_info && caseStatus.missing_info.length > 0 ? (
                    <ul className="list-disc list-inside space-y-1 mb-4 text-sm text-yellow-800">
                      {caseStatus.missing_info.map((info, idx) => (
                        <li key={idx}>{info}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mb-4 text-sm text-yellow-800">
                      The AI agent has requested additional information to complete the case intake. Please provide the details below.
                    </p>
                  )}
                  <div className="space-y-3">
                    <textarea
                      value={additionalInfo}
                      onChange={(e) => setAdditionalInfo(e.target.value)}
                      rows={4}
                      placeholder={caseStatus.missing_info && caseStatus.missing_info.length > 0 
                        ? "Provide the additional information requested above..."
                        : "Provide the additional information requested by the AI agent..."}
                      className="w-full px-4 py-3 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 text-gray-900 placeholder-gray-400 bg-white"
                      disabled={isProcessing}
                    />
                    <ProcessingButton
                      onClick={submitAdditionalInfo}
                      isProcessing={isProcessing}
                      disabled={!additionalInfo.trim()}
                      className="w-full"
                    >
                      {isProcessing ? 'Processing...' : 'Submit Additional Information'}
                    </ProcessingButton>
                  </div>
                </div>
              )}

              {/* Complete Status */}
              {caseStatus.is_complete && (
                <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-3 mb-4">
                    <CheckCircleIcon className="w-6 h-6 text-green-600" />
                    <h4 className="text-lg font-semibold text-green-900">All Requirements Satisfied</h4>
                  </div>
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-green-800">
                      <CheckCircleIcon className="w-5 h-5 text-green-600" />
                      <span>Case information validated</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-800">
                      <CheckCircleIcon className="w-5 h-5 text-green-600" />
                      <span>Risk assessment completed</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-800">
                      <CheckCircleIcon className="w-5 h-5 text-green-600" />
                      <span>All required information collected</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-green-200">
                    <p className="text-sm font-semibold text-green-900 mb-2">Case Status: Approved</p>
                    <p className="text-sm text-green-800">The case has been successfully intaken and is ready for further processing.</p>
                  </div>
                  <button
                    onClick={resetForm}
                    className="mt-4 w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Start New Case
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
