'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import { 
  BriefcaseIcon,
  DocumentTextIcon,
  CheckBadgeIcon,
  DocumentArrowUpIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon,
  UserIcon,
  AcademicCapIcon,
  CogIcon,
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

  const CircularProgress = ({ score, size = 'w-24 h-24', strokeWidth = 8 }: { score: number; size?: string; strokeWidth?: number }) => {
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (score / 100) * circumference;
    
    return (
      <div className={`${size} relative`}>
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="none"
            className="text-gray-200"
          />
          {/* Progress circle */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={`transition-all duration-1000 ease-out ${getScoreColor(score)}`}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-lg font-bold ${getScoreColor(score)}`}>
            {score}
          </span>
        </div>
      </div>
    );
  };

  const ScoreCard = ({ title, score, icon: Icon, color }: { title: string; score: number; icon: React.ComponentType<{ className?: string }>; color: string }) => (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <h3 className="text-sm font-semibold text-gray-900 ml-3">{title}</h3>
        </div>
        <CircularProgress score={score} size="w-16 h-16" strokeWidth={6} />
      </div>
      <div className="text-right">
        <span className={`text-2xl font-bold ${getScoreColor(score)}`}>{score}</span>
        <span className="text-sm text-gray-500 ml-1">/100</span>
      </div>
    </div>
  );

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
            Transform your CV with AI-powered analysis and personalized improvement suggestions to land your dream job
          </p>
          <Link
            href="/challenges/cv-analyzer"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">
          {/* Upload Section */}
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center mb-6 sm:mb-8">
              <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                <DocumentArrowUpIcon className="w-6 h-6 text-gray-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Upload Your CV</h2>
                <p className="text-sm sm:text-base text-gray-600">Get started with comprehensive AI analysis</p>
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
                <label htmlFor="jobDescription" className="block text-sm font-semibold text-gray-700 mb-3">
                  Job Description (Optional)
                </label>
                <textarea
                  id="jobDescription"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description for targeted analysis..."
                  className="w-full px-4 py-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all duration-200"
                  rows={4}
                  disabled={isProcessing}
                />
                <p className="text-sm text-gray-500 mt-2">
                  💡 Including a job description helps provide more targeted suggestions
                </p>
              </div>

              <ProcessingButton
                isLoading={isProcessing}
                onClick={processDocument}
                disabled={!selectedFile}
                icon={<ArrowTrendingUpIcon className="w-5 h-5 mr-3" />}
              >
                Analyze CV
              </ProcessingButton>

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

          {/* Analysis Results */}
          {analysisResult && (
            <div className="space-y-8">
              {/* Overall Score Hero */}
              <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
                <div className="text-center">
                  <h2 className="text-3xl font-bold mb-4 text-gray-900">Your CV Analysis Results</h2>
                  <div className="flex justify-center mb-6">
                    <CircularProgress score={analysisResult.overall_score} size="w-32 h-32" strokeWidth={12} />
                  </div>
                  <div className="text-center">
                    <div className="text-5xl font-bold mb-2 text-gray-900">{analysisResult.overall_score}</div>
                    <div className="text-xl text-gray-600">Overall Score</div>
                    <div className="mt-4">
                      {analysisResult.overall_score >= 80 && (
                        <span className="inline-flex items-center px-4 py-2 bg-green-100 rounded-full text-green-800">
                          <CheckBadgeIcon className="w-5 h-5 mr-2" />
                          Excellent CV!
                        </span>
                      )}
                      {analysisResult.overall_score >= 60 && analysisResult.overall_score < 80 && (
                        <span className="inline-flex items-center px-4 py-2 bg-yellow-100 rounded-full text-yellow-800">
                          <ArrowTrendingUpIcon className="w-5 h-5 mr-2" />
                          Good, with room for improvement
                        </span>
                      )}
                      {analysisResult.overall_score < 60 && (
                        <span className="inline-flex items-center px-4 py-2 bg-red-100 rounded-full text-red-800">
                          <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                          Needs significant improvement
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Detailed Scores Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <ScoreCard
                  title="Keyword Match"
                  score={analysisResult.keyword_match_score}
                  icon={CogIcon}
                  color="bg-blue-500"
                />
                <ScoreCard
                  title="Experience Relevance"
                  score={analysisResult.experience_relevance}
                  icon={UserIcon}
                  color="bg-green-500"
                />
                <ScoreCard
                  title="Skills Alignment"
                  score={analysisResult.skills_alignment}
                  icon={AcademicCapIcon}
                  color="bg-purple-500"
                />
                <ScoreCard
                  title="Format & Presentation"
                  score={analysisResult.format_score}
                  icon={ChartBarIcon}
                  color="bg-orange-500"
                />
              </div>

              {/* Strengths & Weaknesses */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Strengths */}
                <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
                  <div className="flex items-center mb-6">
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                      <CheckBadgeIcon className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Strengths</h3>
                      <p className="text-gray-600">What&apos;s working well</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    {analysisResult.strengths.map((strength, index) => (
                      <div key={index} className="flex items-start p-4 bg-green-50 rounded-xl border border-green-200">
                        <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                          <CheckBadgeIcon className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-gray-700">{strength}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Weaknesses */}
                <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
                  <div className="flex items-center mb-6">
                    <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mr-4">
                      <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Areas for Improvement</h3>
                      <p className="text-gray-600">Focus areas to enhance</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    {analysisResult.weaknesses.map((weakness, index) => (
                      <div key={index} className="flex items-start p-4 bg-red-50 rounded-xl border border-red-200">
                        <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                          <ExclamationTriangleIcon className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-gray-700">{weakness}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Improvement Suggestions */}
              <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center mr-4">
                    <LightBulbIcon className="w-6 h-6 text-yellow-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Actionable Suggestions</h3>
                    <p className="text-gray-600">Step-by-step improvements</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysisResult.improvement_suggestions.map((suggestion, index) => (
                    <div key={index} className="flex items-start p-4 bg-yellow-50 rounded-xl border border-yellow-200">
                      <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                        <span className="text-white font-bold text-sm">{index + 1}</span>
                      </div>
                      <span className="text-gray-700 font-medium">{suggestion}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Loading State */}
          {isAnalyzing && (
            <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-200">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-2xl mb-6">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Analyzing Your CV</h3>
                <p className="text-gray-600">Our AI agents are working hard to provide you with comprehensive insights...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {analysisError && (
            <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
              <AlertMessage type="error" message={analysisError} />
            </div>
          )}

          {/* Ready State */}
          {!analysisResult && !isAnalyzing && !analysisError && processingStatus?.status === 'completed' && (
            <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-200">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-2xl mb-6">
                  <CheckBadgeIcon className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready for Analysis</h3>
                <p className="text-gray-600 mb-6">Your CV has been processed successfully.</p>
                <button
                  onClick={() => runCVAnalysis()}
                  className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  <ArrowTrendingUpIcon className="w-5 h-5 mr-2" />
                  Run CV Analysis
                </button>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!analysisResult && !isAnalyzing && !analysisError && !processingStatus && (
            <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-200">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-2xl mb-6">
                  <DocumentTextIcon className="w-8 h-8 text-gray-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Upload Your CV</h3>
                <p className="text-gray-600">Upload your CV to get started with comprehensive analysis and improvement suggestions.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}