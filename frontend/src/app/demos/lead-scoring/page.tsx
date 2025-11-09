'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { 
  UserGroupIcon,
  DocumentArrowUpIcon,
  ChartBarIcon,
  EnvelopeIcon,
  CheckBadgeIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon,
  UserIcon,
  AcademicCapIcon,
  CogIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import FileUpload from '@/components/demos/FileUpload';

interface ProcessingStatus {
  session_id: string;
  status: string;
  message: string;
  total_leads: number;
}

interface ScoredLead {
  id: string;
  name: string;
  email: string;
  bio: string;
  skills: string;
  score: number;
  reason: string;
}

interface TopCandidatesResponse {
  session_id: string;
  top_candidates: ScoredLead[];
  all_candidates: ScoredLead[];
}

interface EmailResult {
  candidate_id: string;
  candidate_name: string;
  email_content: string;
  is_top_candidate: boolean;
}

export default function LeadScoringDemo() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [topCandidates, setTopCandidates] = useState<ScoredLead[]>([]);
  const [allCandidates, setAllCandidates] = useState<ScoredLead[]>([]);
  const [feedback, setFeedback] = useState('');
  const [isGeneratingEmails, setIsGeneratingEmails] = useState(false);
  const [emails, setEmails] = useState<EmailResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadLeads = async () => {
    if (!selectedFile) {
      alert('Please select a CSV file first');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setTopCandidates([]);
    setAllCandidates([]);
    setEmails([]);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (jobDescription.trim()) {
        formData.append('job_description', jobDescription.trim());
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/lead-scoring/upload-leads`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error('Failed to start processing');
      }

      const result = await response.json();
      setSessionId(result.session_id);
      setProcessingStatus(result);
      
      // Start polling for status updates
      pollProcessingStatus(result.session_id);
    } catch (error) {
      console.error('Error uploading leads:', error);
      setError('Failed to process leads. Please try again.');
      setIsProcessing(false);
    }
  };

  const pollProcessingStatus = async (sessionId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/lead-scoring/status/${sessionId}`);
        const status = await response.json();
        
        setProcessingStatus(status);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          // Automatically fetch top candidates
          fetchTopCandidates(sessionId);
        } else if (status.status === 'error') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          setError(status.message || 'Processing failed');
        }
      } catch (error) {
        console.error('Error polling status:', error);
        clearInterval(pollInterval);
        setIsProcessing(false);
        setError('Failed to check processing status');
      }
    }, 2000);
  };

  const fetchTopCandidates = async (sessionId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/lead-scoring/top-candidates/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch candidates');
      }

      const data: TopCandidatesResponse = await response.json();
      setTopCandidates(data.top_candidates);
      setAllCandidates(data.all_candidates);
    } catch (error) {
      console.error('Error fetching candidates:', error);
      setError('Failed to fetch candidates');
    }
  };

  const submitFeedback = async () => {
    if (!sessionId || !feedback.trim()) {
      alert('Please provide feedback');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/lead-scoring/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          feedback: feedback.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      const result = await response.json();
      setProcessingStatus(result);
      
      // Start polling again
      pollProcessingStatus(sessionId);
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setError('Failed to submit feedback');
      setIsProcessing(false);
    }
  };

  const generateEmails = async () => {
    if (!sessionId) {
      alert('No session found');
      return;
    }

    setIsGeneratingEmails(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/lead-scoring/generate-emails`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          proceed_with_top_3: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate emails');
      }

      const result = await response.json();
      setEmails(result.emails);
    } catch (error) {
      console.error('Error generating emails:', error);
      setError('Failed to generate emails');
    } finally {
      setIsGeneratingEmails(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    // Validate CSV file
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Please select a CSV file (.csv)');
      event.target.value = ''; // Clear the input
      return;
    }
    
    setSelectedFile(file);
    setError(null);
    setTopCandidates([]);
    setAllCandidates([]);
    setEmails([]);
    setProcessingStatus(null);
    setSessionId(null);
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
          <circle
            cx="50"
            cy="50"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="none"
            className="text-gray-200"
          />
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <UserGroupIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Lead Scoring & Email Generation
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Score candidates against job descriptions and generate personalized emails using AI-powered multi-crew workflows
          </p>
          <Link
            href="/challenges/lead-scoring"
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
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Upload Leads CSV</h2>
                <p className="text-sm sm:text-base text-gray-600">Get started with AI-powered lead scoring</p>
              </div>
            </div>

            <div className="space-y-4 sm:space-y-6">
              <FileUpload
                selectedFile={selectedFile}
                onFileSelect={handleFileSelect}
                onFileRemove={() => {
                  setSelectedFile(null);
                  setError(null);
                  setTopCandidates([]);
                  setAllCandidates([]);
                  setEmails([]);
                  setProcessingStatus(null);
                  setSessionId(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
                accept=".csv"
                disabled={isProcessing}
                placeholder="Drop your CSV file here"
                description="CSV format: id,name,email,bio,skills (max 10MB)"
              />

              <div>
                <label htmlFor="jobDescription" className="block text-sm font-semibold text-gray-700 mb-3">
                  Job Description (Optional)
                </label>
                <textarea
                  id="jobDescription"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description for targeted scoring..."
                  className="w-full px-4 py-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all duration-200"
                  rows={4}
                  disabled={isProcessing}
                />
                <p className="text-sm text-gray-500 mt-2">
                  💡 Including a job description helps provide more targeted scoring
                </p>
              </div>

              <ProcessingButton
                isLoading={isProcessing}
                onClick={uploadLeads}
                disabled={!selectedFile}
                icon={<ArrowTrendingUpIcon className="w-5 h-5 mr-3" />}
              >
                Score Leads
              </ProcessingButton>

              {processingStatus && (
                <StatusIndicator
                  status={processingStatus.status}
                  message={processingStatus.message}
                  progress={processingStatus.status === 'completed' ? 100 : processingStatus.status === 'error' ? 0 : 50}
                  documentsCount={processingStatus.total_leads}
                />
              )}
            </div>
          </div>

          {/* Top Candidates Section */}
          {topCandidates.length > 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center mr-4">
                  <SparklesIcon className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Top 3 Candidates</h2>
                  <p className="text-sm sm:text-base text-gray-600">Review and provide feedback to refine scoring</p>
                </div>
              </div>

              <div className="space-y-6 mb-6">
                {topCandidates.map((candidate, index) => (
                  <div key={candidate.id} className="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-500 text-white rounded-full font-bold mr-3">
                            {index + 1}
                          </span>
                          <h3 className="text-lg font-bold text-gray-900">{candidate.name}</h3>
                          <span className={`ml-4 px-3 py-1 rounded-full text-sm font-semibold ${getScoreColor(candidate.score)} bg-opacity-10`}>
                            Score: {candidate.score}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{candidate.email}</p>
                        <p className="text-sm text-gray-700 mb-2">{candidate.bio}</p>
                        <p className="text-sm text-gray-600"><strong>Skills:</strong> {candidate.skills}</p>
                      </div>
                      <CircularProgress score={candidate.score} size="w-20 h-20" strokeWidth={6} />
                    </div>
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-700"><strong>Reasoning:</strong> {candidate.reason}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Feedback Section */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Provide Feedback (Optional)</h3>
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="E.g., 'Focus more on React experience' or 'Prioritize candidates with AI experience'..."
                  className="w-full px-4 py-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all duration-200 mb-4"
                  rows={3}
                  disabled={isProcessing}
                />
                <button
                  onClick={submitFeedback}
                  disabled={isProcessing || !feedback.trim()}
                  className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? 'Re-scoring...' : 'Re-score with Feedback'}
                </button>
              </div>
            </div>
          )}

          {/* All Candidates Section */}
          {allCandidates.length > 0 && topCandidates.length === 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">All Candidates</h2>
                  <p className="text-sm sm:text-base text-gray-600">Sorted by score</p>
                </div>
                <button
                  onClick={generateEmails}
                  disabled={isGeneratingEmails}
                  className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isGeneratingEmails ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                      Generating...
                    </>
                  ) : (
                    <>
                      <EnvelopeIcon className="w-5 h-5 mr-2" />
                      Generate Emails
                    </>
                  )}
                </button>
              </div>

              <div className="space-y-4 max-h-96 overflow-y-auto">
                {allCandidates.map((candidate) => (
                  <div key={candidate.id} className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{candidate.name}</h3>
                        <p className="text-sm text-gray-600">{candidate.email}</p>
                      </div>
                      <div className="flex items-center">
                        <span className={`text-lg font-bold mr-2 ${getScoreColor(candidate.score)}`}>
                          {candidate.score}
                        </span>
                        <CircularProgress score={candidate.score} size="w-12 h-12" strokeWidth={4} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Generated Emails Section */}
          {emails.length > 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                  <EnvelopeIcon className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Generated Emails</h2>
                  <p className="text-sm sm:text-base text-gray-600">Personalized emails for all candidates</p>
                </div>
              </div>

              <div className="space-y-6">
                {emails.map((email) => (
                  <div key={email.candidate_id} className="border border-gray-200 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-gray-900">{email.candidate_name}</h3>
                      {email.is_top_candidate && (
                        <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                          <CheckBadgeIcon className="w-4 h-4 mr-1" />
                          Top Candidate
                        </span>
                      )}
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                        {email.email_content}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
              <AlertMessage type="error" message={error} />
            </div>
          )}

          {/* Empty State */}
          {!processingStatus && !topCandidates.length && !allCandidates.length && !error && (
            <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-200">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-2xl mb-6">
                  <DocumentArrowUpIcon className="w-8 h-8 text-gray-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Upload Your Leads CSV</h3>
                <p className="text-gray-600">Upload a CSV file with candidate data to get started with AI-powered lead scoring and email generation.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
