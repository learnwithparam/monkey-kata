'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  MagnifyingGlassIcon,
  ChartBarIcon,
  DocumentTextIcon,
  SparklesIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import StructuredAnalysisReport from '@/components/demos/StructuredAnalysisReport';

interface AnalysisRequest {
  company_name: string;
  competitors: string[];
  focus_areas?: string[];
}


interface AnalysisResult {
  session_id: string;
  status: string;
  company_name: string;
  competitors: string[];
  report?: string;
  error?: string;
  steps?: Array<{
    timestamp: string;
    message: string;
    agent?: string;
    tool?: string;
    target?: string;
  }>;
}

interface AnalysisResponse {
  session_id: string;
  status: string;
  message: string;
  company_name: string;
  competitors: string[];
  steps?: Array<{
    timestamp: string;
    message: string;
    agent?: string;
    tool?: string;
    target?: string;
  }>;
}

export default function CompetitorAnalysisDemo() {
  const [companyName, setCompanyName] = useState('');
  const [competitors, setCompetitors] = useState('');
  const [focusAreas, setFocusAreas] = useState('pricing, features, market position');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startAnalysis = async () => {
    if (!companyName.trim()) {
      setError('Please enter a company name');
      return;
    }

    const competitorsList = competitors
      .split(',')
      .map(c => c.trim())
      .filter(c => c.length > 0);

    if (competitorsList.length === 0) {
      setError('Please enter at least one competitor');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setAnalysisResult(null);
    setAnalysisStatus({
      session_id: '',
      status: 'processing',
      message: 'Starting analysis...',
      company_name: companyName.trim(),
      competitors: competitorsList
    });

    try {
      const request: AnalysisRequest = {
        company_name: companyName.trim(),
        competitors: competitorsList,
        focus_areas: focusAreas
          .split(',')
          .map(f => f.trim())
          .filter(f => f.length > 0)
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/competitor-analysis/start-analysis-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to start analysis');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder('utf-8');
      let sessionId = '';
      const steps: Array<{ timestamp: string; message: string }> = [];

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
                // Connection established
                setAnalysisStatus(prev => prev ? {
                  ...prev,
                  message: data.message || 'Starting analysis...',
                  status: 'processing'
                } : null);
                continue;
              }

              if (data.step) {
                // Real-time step update - add to steps array
                const newSteps = [...steps, data.step];
                steps.length = 0; // Clear array
                steps.push(...newSteps); // Add all steps back
                
                setAnalysisResult(prev => ({
                  ...prev || {
                    session_id: sessionId || '',
                    status: 'processing',
                    company_name: companyName.trim(),
                    competitors: competitorsList,
                  },
                  steps: newSteps
                }));
                setAnalysisStatus(prev => prev ? {
                  ...prev,
                  message: data.step.message,
                  status: 'researching'
                } : null);
              }

              if (data.done) {
                setIsProcessing(false);
                if (data.report) {
                  setAnalysisResult(prev => ({
                    ...prev || {
                      session_id: sessionId || '',
                      status: 'completed',
                      company_name: companyName.trim(),
                      competitors: competitorsList,
                    },
                    report: data.report,
                    status: 'completed',
                    steps: steps
                  }));
                  setAnalysisStatus(prev => prev ? {
                    ...prev,
                    status: 'completed',
                    message: '✅ Analysis complete! Report generated successfully.'
                  } : null);
                } else if (data.error) {
                  setError(data.error);
                  setAnalysisStatus(prev => prev ? {
                    ...prev,
                    status: 'error',
                    message: `❌ Error: ${data.error}`
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
      console.error('Error starting analysis:', error);
      setError(error instanceof Error ? error.message : 'Failed to start analysis. Please try again.');
      setIsProcessing(false);
    }
  };


  const resetForm = () => {
    setCompanyName('');
    setCompetitors('');
    setFocusAreas('pricing, features, market position');
    setSessionId(null);
    setAnalysisStatus(null);
    setAnalysisResult(null);
    setIsProcessing(false);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <MagnifyingGlassIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Competitor Analysis Research Agent
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Multi-agent system that researches competitors and analyzes market positioning
          </p>
          <Link
            href="/challenges/competitor-analysis"
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
                  <SparklesIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Analysis Configuration</h2>
                  <p className="text-sm sm:text-base text-gray-600">Configure your competitor analysis</p>
                </div>
              </div>

            <div className="space-y-4 sm:space-y-6">
              {/* Company Name */}
              <div>
                <label htmlFor="company-name" className="block text-sm font-medium text-gray-700 mb-2">
                  Your Company Name *
                </label>
                <input
                  id="company-name"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g., TechCorp"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isProcessing}
                />
              </div>

              {/* Competitors */}
              <div>
                <label htmlFor="competitors" className="block text-sm font-medium text-gray-700 mb-2">
                  Competitors (comma-separated) *
                </label>
                <input
                  id="competitors"
                  type="text"
                  value={competitors}
                  onChange={(e) => setCompetitors(e.target.value)}
                  placeholder="e.g., Competitor A, Competitor B, Competitor C"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isProcessing}
                />
                <p className="text-xs text-gray-500 mt-1">Enter competitor names separated by commas</p>
              </div>

              {/* Focus Areas */}
              <div>
                <label htmlFor="focus-areas" className="block text-sm font-medium text-gray-700 mb-2">
                  Focus Areas (comma-separated)
                </label>
                <input
                  id="focus-areas"
                  type="text"
                  value={focusAreas}
                  onChange={(e) => setFocusAreas(e.target.value)}
                  placeholder="e.g., pricing, features, market position"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isProcessing}
                />
                <p className="text-xs text-gray-500 mt-1">What aspects to focus on in the analysis</p>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <ProcessingButton
                  onClick={startAnalysis}
                  isProcessing={isProcessing}
                  disabled={!companyName.trim() || !competitors.trim()}
                  className="flex-1"
                >
                  {isProcessing ? 'Analyzing...' : 'Start Analysis'}
                </ProcessingButton>
                {(analysisResult || error) && (
                  <button
                    onClick={resetForm}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    <ArrowPathIcon className="h-5 w-5 inline mr-2" />
                    Reset
                  </button>
                )}
              </div>
            </div>
            </div>

            {/* Status & Results */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <ChartBarIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Analysis Status</h2>
                  <p className="text-sm sm:text-base text-gray-600">Track your analysis progress</p>
                </div>
              </div>

            {!analysisStatus && !analysisResult && (
              <div className="text-center py-12 text-gray-500">
                <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p>Enter company and competitor information to start analysis</p>
              </div>
            )}

            {analysisStatus && (
              <div className="mb-6">
                <StatusIndicator
                  status={analysisStatus.status}
                  message={analysisStatus.message}
                />
                
                {/* Agent Workflow Steps */}
                {(analysisResult?.steps && analysisResult.steps.length > 0) && (
                  <div className="mt-6 space-y-3">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                      <SparklesIcon className="h-4 w-4 text-blue-600 mr-2" />
                      Multi-Agent Workflow
                    </h3>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {analysisResult.steps.map((step, index) => {
                        const getStatusColor = () => {
                          if (step.tool === 'agent_complete') return 'bg-green-500';
                          if (step.tool === 'agent_invoke') return 'bg-blue-500 animate-pulse';
                          if (step.tool === 'search_web' || step.tool === 'scrape_website') return 'bg-purple-500 animate-pulse';
                          return 'bg-gray-400';
                        };

                        const getAgentColor = (agent: string | undefined) => {
                          if (!agent) return 'bg-gray-200 text-gray-700';
                          if (agent.includes('Research')) return 'bg-blue-100 text-blue-700';
                          if (agent.includes('Analysis')) return 'bg-purple-100 text-purple-700';
                          if (agent.includes('Report')) return 'bg-green-100 text-green-700';
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
                                  {step.tool && step.tool !== 'agent_invoke' && step.tool !== 'agent_complete' && (
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
                
                {analysisStatus.status === 'processing' || analysisStatus.status === 'researching' ? (
                  <div className="mt-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      {analysisStatus.message || (analysisStatus.status === 'researching' 
                        ? 'Research Agent gathering information...'
                        : 'Initializing analysis...')}
                    </div>
                  </div>
                ) : null}
              </div>
            )}


            {analysisResult && analysisResult.error && (
              <div className="mt-6">
                <AlertMessage type="error" message={analysisResult.error} />
              </div>
            )}
            </div>
          </div>
        </div>

        {/* Full-Width Report Section at Bottom */}
        {analysisResult && analysisResult.report && (
          <div className="mt-12 -mx-4 sm:-mx-6 lg:-mx-8">
            <StructuredAnalysisReport
              report={analysisResult.report}
              companyName={analysisResult.company_name}
              competitors={analysisResult.competitors}
            />
          </div>
        )}
      </div>
    </div>
  );
}

