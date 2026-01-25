'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  ScaleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  DocumentTextIcon,
  CommandLineIcon,
  ListBulletIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import CustomSelect from '@/components/CustomSelect';
import ThinkingBlock from '@/components/demos/ThinkingBlock';
import LiveLogViewer from '@/components/demos/LiveLogViewer';

interface CaseIntakeRequest {
  client_name: string;
  client_email: string;
  client_phone?: string;
  case_type: string;
  case_description: string;
  urgency: string;
  additional_info?: string;
}

interface StepData {
  timestamp: string;
  message: string;
  agent?: string;
  tool?: string;
  target?: string;
  category?: string;
}

interface LogEntry {
  timestamp: string;
  content: string;
  type: string;
}

interface CaseIntakeResponse {
  case_id: string;
  status: string;
  message: string;
  steps?: StepData[];
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
  const [workflowSteps, setWorkflowSteps] = useState<StepData[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [activeTab, setActiveTab] = useState<'workflow' | 'logs'>('workflow');

  // Helper to read stream
  const readStream = async (response: Response) => {
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || 'Request failed');
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder('utf-8');
    const newSteps: StepData[] = []; // Accumulate steps for this run

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;
            
            let data;
            try {
              data = JSON.parse(jsonStr);
            } catch (parseErr) {
              console.warn('Failed to parse JSON line:', jsonStr.substring(0, 100));
              continue;
            }

            if (data.status === 'connected') {
              if (data.case_id) setCaseId(data.case_id);
              setCaseStatus(prev => ({
                case_id: data.case_id || prev?.case_id || '',
                status: 'processing',
                message: data.message || 'Processing...',
                steps: prev?.steps,
                needs_more_info: false, // Reset flags on new run
                is_complete: false
              }));
              continue;
            }

            // Handle Logs
            if (data.type === 'log') {
              setLogs(prev => [...prev, {
                timestamp: data.timestamp,
                content: data.content,
                type: 'log'
              }]);
              // Auto-switch to logs if it's the first log and user hasn't explicitly chosen
              continue;
            }

            // Handle Workflow Steps
            if (data.step) {
              // If step is actually a log (backend sometimes wraps logs in step_queue without type)
              // Check if it has the log structure or if we should treat it as a step
              if (data.step.type === 'log') {
                   setLogs(prev => [...prev, {
                    timestamp: data.step.timestamp,
                    content: data.step.content,
                    type: 'log'
                  }]);
                  continue;
              }

              // It's a real workflow step
              setWorkflowSteps(prev => {
                const combined = [...prev, data.step];
                // Update status message with latest step
                setCaseStatus(current => current ? {
                  ...current,
                  message: data.step.message,
                  steps: combined
                } : null);
                return combined;
              });
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
                  steps: workflowSteps, // Use current state (approx)
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
  };

  const submitCase = async () => {
    if (!caseData.client_name || !caseData.client_email || !caseData.case_type || !caseData.case_description) {
      setError('Please fill in all required fields');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setWorkflowSteps([]);
    setLogs([]);
    setAdditionalInfo('');
    setActiveTab('logs'); // Switch to logs on start to show activity

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/submit-case-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(caseData),
      });
      await readStream(response);
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
    setActiveTab('logs'); // Switch to logs to show resumption

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-case-intake/provide-additional-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          additional_info: additionalInfo
        }),
      });
      
      // Clear previous result specific flags but keep history
      setCaseStatus(prev => prev ? { ...prev, needs_more_info: false, is_complete: false, message: 'Resuming analysis...' } : null);
      
      await readStream(response);
      setAdditionalInfo('');
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
    setLogs([]);
    setActiveTab('workflow');
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
                  isLoading={isProcessing}
                  disabled={!caseData.client_name || !caseData.client_email || !caseData.case_type || !caseData.case_description}
                  className="w-full"
                >
                  {isProcessing ? 'Processing...' : 'Submit Case'}
                </ProcessingButton>
              </div>
            </div>

            {/* Status & Results */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-6 sm:mb-8">
                <div className="flex items-center">
                    <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                        <ScaleIcon className="w-6 h-6 text-gray-600" />
                    </div>
                    <div>
                        <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Case Status</h2>
                        <p className="text-sm sm:text-base text-gray-600">Track your case intake progress</p>
                    </div>
                </div>
                
                {/* View Switcher */}
                {caseStatus && (
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        <button 
                            onClick={() => setActiveTab('workflow')}
                            className={`p-2 rounded-md transition-all ${activeTab === 'workflow' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                            title="Workflow View"
                        >
                            <ListBulletIcon className="w-5 h-5" />
                        </button>
                        <button 
                            onClick={() => setActiveTab('logs')}
                            className={`p-2 rounded-md transition-all ${activeTab === 'logs' ? 'bg-white shadow-sm text-green-600' : 'text-gray-500 hover:text-gray-700'}`}
                            title="Live Logs View"
                        >
                            <CommandLineIcon className="w-5 h-5" />
                        </button>
                    </div>
                )}
              </div>

              {!caseStatus && !isProcessing && logs.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p>Enter case information to start intake</p>
                </div>
              )}

              {(caseStatus || isProcessing || logs.length > 0) && (
                <div className="mb-6">
                  {caseStatus && (
                    <StatusIndicator
                        status={caseStatus.status}
                        message={caseStatus.message}
                    />
                  )}
                  
                  <div className="mt-6">
                      {/* Tabs Content */}
                      <div className={activeTab === 'workflow' ? 'block' : 'hidden'}>
                          <ThinkingBlock
                            events={workflowSteps.map(step => ({
                              category: step.category || (
                                step.tool === 'agent_complete' || step.tool === 'workflow_complete' ? 'complete' :
                                step.tool === 'agent_invoke' ? 'agent' :
                                step.tool === 'agent_processing' ? 'processing' :
                                step.tool === 'crew_execution' ? 'processing' :
                                step.tool === 'data_parsing' ? 'analysis' :
                                'processing'
                              ),
                              content: step.message,
                              timestamp: step.timestamp,
                              agent: step.agent,
                              tool: step.tool,
                              target: step.target,
                            }))}
                            title="Multi-Agent Workflow"
                            maxHeight="400px"
                            autoScroll={true}
                            collapsible={false}
                            defaultExpanded={true}
                          />
                      </div>
                      
                      <div className={activeTab === 'logs' ? 'block' : 'hidden'}>
                          <LiveLogViewer 
                            logs={logs}
                            isVisible={true}
                          />
                      </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Verdict Card - Show when processing is done or needs more info */}
          {caseStatus && !isProcessing && (caseStatus.status !== 'processing' || caseStatus.needs_more_info || caseStatus.is_complete) && (
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
                  {/* Show Risk Assessment if available */}
                  {caseStatus.risk_assessment && (
                    <div className="mt-4">
                        <h4 className="font-semibold text-gray-900 mb-1">Risk Assessment:</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-line">{caseStatus.risk_assessment}</p>
                    </div>
                  )}
                  {/* Show Recommended Action if available */}
                  {caseStatus.recommended_action && (
                    <div className="mt-4">
                        <h4 className="font-semibold text-gray-900 mb-1">Recommendation:</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-line">{caseStatus.recommended_action}</p>
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
                      isLoading={isProcessing}
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
