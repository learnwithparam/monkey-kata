'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import { 
  BriefcaseIcon,
  DocumentTextIcon,
  CheckBadgeIcon,
  InformationCircleIcon,
  DocumentArrowUpIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ClipboardDocumentListIcon,
  LightBulbIcon,
  StarIcon,
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

interface CVAnalysisResult {
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
  keyword_match_score: number;
  experience_relevance: number;
  skills_alignment: number;
  format_score: number;
}

export default function CVAnalyzerDemo() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResult, setAnalysisResult] = useState<CVAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processDocument = async () => {
    if (!selectedFile) {
      alert('Please select a CV file first');
      return;
    }

    setIsProcessing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (jobDescription.trim()) {
        formData.append('job_description', jobDescription.trim());
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/cv-analyzer/upload-cv`, {
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
      setAnalysisError('Failed to process CV. Please try again.');
      setIsProcessing(false);
    }
  };

  const pollProcessingStatus = async (documentId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/cv-analyzer/status/${documentId}`);
        const status = await response.json();
        
        setProcessingStatus(status);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          // Automatically run analysis when processing is complete
          runCVAnalysis(status);
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

  const runCVAnalysis = async (status?: ProcessingStatus) => {
    const currentStatus = status || processingStatus;
    
    if (!currentStatus || currentStatus.status !== 'completed') {
      setAnalysisError('Please wait for the CV to finish processing');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/cv-analyzer/analyze/${currentStatus.document_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_description: jobDescription.trim() || null
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to analyze CV');
      }

      const analysis = await response.json();
      setAnalysisResult(analysis);
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysisError('Failed to analyze CV. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setAnalysisError(null);
      setAnalysisResult(null);
      setProcessingStatus(null);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
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
            <BriefcaseIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            CV Analyzer & Improvement Suggester
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Upload your CV and get AI-powered analysis with personalized improvement suggestions to land your dream job.
          </p>
          <Link
            href="/challenges/cv-analyzer"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content - Single Column */}
        <div className="max-w-4xl mx-auto space-y-8">
          {/* CV Upload Section */}
          <div className="card p-6 lg:p-8">
            <div className="flex items-center mb-6 sm:mb-8">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                <DocumentArrowUpIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Upload Your CV</h2>
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
                  setAnalysisResult(null);
                  setProcessingStatus(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
                disabled={isProcessing}
                placeholder="Drop your CV here"
                description="Supports PDF, Word, and text files (max 10MB)"
              />

              <div>
                <label htmlFor="jobDescription" className="block text-sm font-semibold text-gray-700 mb-2">
                  Job Description (Optional)
                </label>
                <textarea
                  id="jobDescription"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description for targeted analysis..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={4}
                  disabled={isProcessing}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Including a job description helps provide more targeted suggestions
                </p>
              </div>

              <ProcessingButton
                isLoading={isProcessing}
                onClick={processDocument}
                disabled={!selectedFile}
              >
                <span className="flex items-center justify-center">
                  Analyze CV
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
                  <p className="text-sm text-gray-500">Comprehensive CV analysis and improvement suggestions</p>
                </div>
              </div>
              {analysisResult && (
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
                    <p className="text-gray-600">Running comprehensive CV analysis...</p>
                  </div>
                </div>
              )}

              {analysisResult && (
                <div className="space-y-6">
                  {/* Overall Score */}
                  <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                      <StarIcon className="w-5 h-5 text-yellow-600 mr-2" />
                      Overall CV Score
                    </h3>
                    <div className="text-center">
                      <div className={`inline-flex items-center justify-center w-20 h-20 sm:w-24 sm:h-24 rounded-full ${getScoreBgColor(analysisResult.overall_score)} mb-3 sm:mb-4`}>
                        <span className={`text-2xl sm:text-3xl font-bold ${getScoreColor(analysisResult.overall_score)}`}>
                          {analysisResult.overall_score}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">out of 100</p>
                    </div>
                  </div>

                  {/* Detailed Scores */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                    <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                        <CheckBadgeIcon className="w-5 h-5 text-green-600 mr-2" />
                        Detailed Scores
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Keyword Match</span>
                          <span className={`font-semibold ${getScoreColor(analysisResult.keyword_match_score)}`}>
                            {analysisResult.keyword_match_score}/100
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Experience Relevance</span>
                          <span className={`font-semibold ${getScoreColor(analysisResult.experience_relevance)}`}>
                            {analysisResult.experience_relevance}/100
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Skills Alignment</span>
                          <span className={`font-semibold ${getScoreColor(analysisResult.skills_alignment)}`}>
                            {analysisResult.skills_alignment}/100
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Format & Presentation</span>
                          <span className={`font-semibold ${getScoreColor(analysisResult.format_score)}`}>
                            {analysisResult.format_score}/100
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Strengths */}
                    <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                        <CheckBadgeIcon className="w-5 h-5 text-green-600 mr-2" />
                        Strengths
                      </h3>
                      <ul className="space-y-2 sm:space-y-3">
                        {(analysisResult.strengths || []).map((strength, index) => (
                          <li key={index} className="flex items-start">
                            <div className="w-2 h-2 bg-green-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span className="text-gray-700 text-sm sm:text-base">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Weaknesses */}
                  <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                      <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mr-2" />
                      Areas for Improvement
                    </h3>
                    <ul className="space-y-2 sm:space-y-3">
                      {(analysisResult.weaknesses || []).map((weakness, index) => (
                        <li key={index} className="flex items-start">
                          <div className="w-2 h-2 bg-red-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <span className="text-gray-700 text-sm sm:text-base">{weakness}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Improvement Suggestions */}
                  <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center">
                      <LightBulbIcon className="w-5 h-5 text-yellow-600 mr-2" />
                      Actionable Suggestions
                    </h3>
                    <ul className="space-y-2 sm:space-y-3">
                      {(analysisResult.improvement_suggestions || []).map((suggestion, index) => (
                        <li key={index} className="flex items-start">
                          <div className="w-2 h-2 bg-yellow-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <span className="text-gray-700 text-sm sm:text-base">{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {!analysisResult && !isAnalyzing && !analysisError && processingStatus?.status === 'completed' && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <BriefcaseIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready for Analysis</h3>
                    <p className="text-gray-600 mb-4">Your CV has been processed successfully.</p>
                    <button
                      onClick={() => runCVAnalysis()}
                      className="bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Run CV Analysis
                    </button>
                  </div>
                </div>
              )}

              {!analysisResult && !isAnalyzing && !analysisError && !processingStatus && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Your CV</h3>
                    <p className="text-gray-600">Upload your CV to get started with comprehensive analysis and improvement suggestions.</p>
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
