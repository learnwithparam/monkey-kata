'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import { 
  ScaleIcon,
  DocumentTextIcon,
  CheckBadgeIcon,
  InformationCircleIcon,
  DocumentArrowUpIcon,
  ShieldExclamationIcon,
  ChartBarIcon,
  ClipboardDocumentListIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import FileUpload from '@/components/demos/FileUpload';

interface ProcessingStatus {
  document_id: string;
  status: string;
  progress: number;
  message: string;
  pages_count: number;
  error?: string;
}

interface LegalInsights {
  executive_summary: string;
  risk_overview: {
    total_risks: number;
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
    critical_areas: string[];
  };
  compliance_score: number;
  key_insights: string[];
  action_items: string[];
  recommendations: string[];
}

export default function LegalContractAnalyzerDemo() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [insights, setInsights] = useState<LegalInsights | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processDocument = async () => {
    if (!selectedFile) {
      alert('Please select a file first');
      return;
    }

    setIsProcessing(true);
    setAnalysisError(null);
    setInsights(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-contract-analyzer/upload-document`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error('Failed to start processing');
      }

      const result = await response.json();
      setProcessingStatus(result);
      
      // Start polling for status updates
      pollProcessingStatus(result.document_id);
    } catch (error) {
      console.error('Error processing document:', error);
      setAnalysisError('Failed to process document. Please try again.');
      setIsProcessing(false);
    }
  };

  const pollProcessingStatus = async (documentId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-contract-analyzer/status/${documentId}`);
        const status = await response.json();
        
        setProcessingStatus(status);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          // Automatically run analysis when processing is complete
          runComprehensiveAnalysis(status);
        } else if (status.status === 'error') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          setAnalysisError(status.error || 'Processing failed');
        }
      } catch (error) {
        console.error('Error polling status:', error);
        clearInterval(pollInterval);
        setIsProcessing(false);
        setAnalysisError('Failed to check processing status');
      }
    }, 2000);
  };

  const runComprehensiveAnalysis = async (status?: ProcessingStatus) => {
    const currentStatus = status || processingStatus;
    
    if (!currentStatus || currentStatus.status !== 'completed') {
      setAnalysisError('Please wait for the document to finish processing');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setInsights(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/legal-contract-analyzer/agentic-analysis/${currentStatus.document_id}`);
      
      if (!response.ok) {
        throw new Error('Failed to analyze document');
      }

      const analysis = await response.json();
      
      // Check if it's not a legal document
      if (analysis.error && analysis.error.includes('not a legal document')) {
        setAnalysisError('This document does not appear to be a legal document. Please upload a contract, agreement, or other legal document for analysis.');
        return;
      }

      setInsights(analysis);
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysisError('Failed to analyze document. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setAnalysisError(null);
      setInsights(null);
      setProcessingStatus(null);
    }
  };

  const getComplianceColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getComplianceBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
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
            Upload any legal document and get comprehensive AI-powered analysis with risk assessment, compliance scoring, and actionable insights.
          </p>
          <Link
            href="/challenges/legal-contract-analyzer"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content - Single Column */}
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Document Upload Section */}
          <div className="card p-6 lg:p-8">
            <div className="flex items-center mb-6 sm:mb-8">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                <DocumentArrowUpIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Upload Legal Document</h2>
                <p className="text-sm text-gray-600">Upload PDF, Word, or text files for comprehensive analysis</p>
              </div>
            </div>

            <div className="space-y-4 sm:space-y-6">
              <FileUpload
                selectedFile={selectedFile}
                onFileSelect={handleFileSelect}
                onFileRemove={() => {
                  setSelectedFile(null);
                  setAnalysisError(null);
                  setInsights(null);
                  setProcessingStatus(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
                disabled={isProcessing}
                placeholder="Drop your legal document here"
                description="Supports PDF, Word, and text files (max 10MB)"
              />

              <ProcessingButton
                isLoading={isProcessing}
                onClick={processDocument}
                disabled={!selectedFile}
              >
                <span className="flex items-center justify-center">
                  Process Document
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

          {/* Analysis Results Section */}
          <div className="card p-6 lg:p-8">
            <div className="flex items-center justify-between mb-6 sm:mb-8">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                  <ChartBarIcon className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Analysis Results</h2>
                  <p className="text-sm text-gray-500">Comprehensive legal document insights</p>
                </div>
              </div>
              {insights && (
                <div className="flex items-center space-x-2 bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-medium">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>Analysis Complete</span>
                </div>
              )}
            </div>

            {/* Analysis Content */}
            <div className="space-y-6">
              {analysisError && (
                <AlertMessage type="error" message={analysisError} />
              )}

              {isAnalyzing && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Running comprehensive legal analysis...</p>
                  </div>
                </div>
              )}

                {insights && (
                  <div className="space-y-6">
                    {/* Executive Summary */}
                    <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                        <InformationCircleIcon className="w-5 h-5 text-blue-600 mr-2" />
                        Executive Summary
                      </h3>
                      <p className="text-gray-700 leading-relaxed">{insights.executive_summary || 'No summary available'}</p>
                    </div>

                    {/* Risk Overview & Compliance Score */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                      {/* Risk Overview */}
                      <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                          <ShieldExclamationIcon className="w-5 h-5 text-red-600 mr-2" />
                          Risk Overview
                        </h3>
                        <div className="space-y-2 sm:space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Total Risks</span>
                            <span className="font-semibold text-gray-900">{insights.risk_overview?.total_risks || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-red-600">High Risk</span>
                            <span className="font-semibold text-red-600">{insights.risk_overview?.high_risk_count || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-yellow-600">Medium Risk</span>
                            <span className="font-semibold text-yellow-600">{insights.risk_overview?.medium_risk_count || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-green-600">Low Risk</span>
                            <span className="font-semibold text-green-600">{insights.risk_overview?.low_risk_count || 0}</span>
                          </div>
                          {insights.risk_overview?.critical_areas && insights.risk_overview.critical_areas.length > 0 && (
                            <div className="mt-3 sm:mt-4">
                              <p className="text-sm font-medium text-gray-700 mb-2">Critical Areas:</p>
                              <div className="flex flex-wrap gap-1 sm:gap-2">
                                {insights.risk_overview.critical_areas.map((area, index) => (
                                  <span key={index} className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                                    {area}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Compliance Score */}
                      <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                          <CheckBadgeIcon className="w-5 h-5 text-green-600 mr-2" />
                          Compliance Score
                        </h3>
                        <div className="text-center">
                          <div className={`inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 rounded-full ${getComplianceBgColor(insights.compliance_score || 0)} mb-3 sm:mb-4`}>
                            <span className={`text-xl sm:text-2xl font-bold ${getComplianceColor(insights.compliance_score || 0)}`}>
                              {insights.compliance_score || 0}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">out of 100</p>
                        </div>
                      </div>
                    </div>

                    {/* Key Insights */}
                    <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                        <LightBulbIcon className="w-5 h-5 text-yellow-600 mr-2" />
                        Key Insights
                      </h3>
                      <ul className="space-y-2 sm:space-y-3">
                        {(insights.key_insights || []).map((insight, index) => (
                          <li key={index} className="flex items-start">
                            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span className="text-gray-700 text-sm sm:text-base">{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Action Items */}
                    <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                        <ClipboardDocumentListIcon className="w-5 h-5 text-orange-600 mr-2" />
                        Action Items
                      </h3>
                      <ul className="space-y-2 sm:space-y-3">
                        {(insights.action_items || []).map((item, index) => (
                          <li key={index} className="flex items-start">
                            <div className="w-2 h-2 bg-orange-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span className="text-gray-700 text-sm sm:text-base">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Recommendations */}
                    <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                        <ChartBarIcon className="w-5 h-5 text-green-600 mr-2" />
                        Recommendations
                      </h3>
                      <ul className="space-y-2 sm:space-y-3">
                        {(insights.recommendations || []).map((recommendation, index) => (
                          <li key={index} className="flex items-start">
                            <div className="w-2 h-2 bg-green-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span className="text-gray-700 text-sm sm:text-base">{recommendation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

              {!insights && !isAnalyzing && !analysisError && processingStatus?.status === 'completed' && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <ScaleIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready for Analysis</h3>
                    <p className="text-gray-600 mb-4">Your document has been processed successfully.</p>
                    <button
                      onClick={() => runComprehensiveAnalysis()}
                      className="bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Run Comprehensive Analysis
                    </button>
                  </div>
                </div>
              )}

              {!insights && !isAnalyzing && !analysisError && !processingStatus && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload a Document</h3>
                    <p className="text-gray-600">Upload a legal document to get started with comprehensive analysis.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}