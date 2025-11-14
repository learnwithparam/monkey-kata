'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  BriefcaseIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import FileUpload from '@/components/demos/FileUpload';

interface ResumeData {
  name: string;
  email: string;
  phone?: string;
  address?: string;
  work_experience: Array<{
    company: string;
    role: string;
    start_date: string;
    end_date?: string;
    description: string;
  }>;
  education: Array<{
    degree: string;
    institution: string;
    graduation_date?: string;
    gpa?: string;
  }>;
  skills: string[];
  summary?: string;
}

interface ResumeUploadResponse {
  session_id: string;
  resume_data: ResumeData;
  status: string;
  message: string;
}

export default function JobApplicationFormFillingDemo() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isFilling, setIsFilling] = useState(false);
  const [parsedResume, setParsedResume] = useState<ResumeData | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [parsingStatus, setParsingStatus] = useState<string>('');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Please upload a PDF file');
        return;
      }
      setSelectedFile(file);
      setError(null);
      setParsedResume(null);
      setSessionId(null);
    }
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setParsedResume(null);
    setSessionId(null);
    setError(null);
    setParsingStatus('');
  };

  const uploadAndParseResume = async () => {
    if (!selectedFile) {
      setError('Please select a PDF file');
      return;
    }

    setIsParsing(true);
    setError(null);
    setParsingStatus('Uploading resume...');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/job-application-form-filling/upload-resume`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to upload and parse resume');
      }

      const result: ResumeUploadResponse = await response.json();
      setParsedResume(result.resume_data);
      setSessionId(result.session_id);
      setParsingStatus('Resume parsed successfully!');
      
    } catch (error) {
      console.error('Error uploading resume:', error);
      setError(error instanceof Error ? error.message : 'Failed to upload and parse resume. Please try again.');
      setParsingStatus('');
    } finally {
      setIsParsing(false);
    }
  };

  const startFormFilling = () => {
    if (!sessionId) {
      setError('Please upload and parse a resume first');
      return;
    }

    // Open form page in new tab
    const formUrl = `/demos/job-application-form-filling/form?session_id=${sessionId}`;
    window.open(formUrl, '_blank');
    setIsFilling(true);
  };

  const resetForm = () => {
    setSelectedFile(null);
    setParsedResume(null);
    setSessionId(null);
    setError(null);
    setParsingStatus('');
    setIsParsing(false);
    setIsFilling(false);
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
            Job Application Form Auto-Fill
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Upload your resume and watch AI automatically fill your job application form
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/challenges/job-application-form-filling"
              className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
            >
              View Learning Challenges
            </Link>
            <a
              href="/demos/job-application-form-filling/job-listing"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-sm hover:shadow-md inline-block"
            >
              View Job Listing
            </a>
          </div>
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
            {/* Resume Upload Section */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <DocumentTextIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Upload Resume</h2>
                  <p className="text-sm sm:text-base text-gray-600">Upload your PDF resume</p>
                </div>
              </div>

              <div className="space-y-4 sm:space-y-6">
                <FileUpload
                  selectedFile={selectedFile}
                  onFileSelect={handleFileSelect}
                  onFileRemove={handleFileRemove}
                  accept=".pdf"
                  disabled={isParsing}
                  placeholder="Drop your resume PDF here"
                  description="PDF files only (max 10MB)"
                />

                <ProcessingButton
                  onClick={uploadAndParseResume}
                  isProcessing={isParsing}
                  disabled={!selectedFile}
                  className="w-full"
                >
                  {isParsing ? 'Parsing Resume...' : 'Upload & Parse Resume'}
                </ProcessingButton>

                {parsingStatus && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">{parsingStatus}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Parsed Resume Preview */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <SparklesIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Parsed Resume</h2>
                  <p className="text-sm sm:text-base text-gray-600">Extracted information</p>
                </div>
              </div>

              {!parsedResume && (
                <div className="text-center py-12 text-gray-500">
                  <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p>Upload and parse a resume to see extracted information</p>
                </div>
              )}

              {parsedResume && (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Personal Information</h3>
                    <div className="text-sm text-gray-600 space-y-1">
                      <p><span className="font-medium">Name:</span> {parsedResume.name}</p>
                      <p><span className="font-medium">Email:</span> {parsedResume.email}</p>
                      {parsedResume.phone && (
                        <p><span className="font-medium">Phone:</span> {parsedResume.phone}</p>
                      )}
                      {parsedResume.address && (
                        <p><span className="font-medium">Address:</span> {parsedResume.address}</p>
                      )}
                    </div>
                  </div>

                  {parsedResume.work_experience.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Work Experience</h3>
                      <div className="text-sm text-gray-600 space-y-2">
                        {parsedResume.work_experience.slice(0, 2).map((exp, idx) => (
                          <div key={idx} className="border-l-2 border-blue-200 pl-3">
                            <p className="font-medium">{exp.role} at {exp.company}</p>
                            <p className="text-xs text-gray-500">{exp.start_date} - {exp.end_date || 'Present'}</p>
                          </div>
                        ))}
                        {parsedResume.work_experience.length > 2 && (
                          <p className="text-xs text-gray-500">+{parsedResume.work_experience.length - 2} more</p>
                        )}
                      </div>
                    </div>
                  )}

                  {parsedResume.education.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Education</h3>
                      <div className="text-sm text-gray-600 space-y-1">
                        {parsedResume.education.map((edu, idx) => (
                          <p key={idx}>{edu.degree} from {edu.institution}</p>
                        ))}
                      </div>
                    </div>
                  )}

                  {parsedResume.skills.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Skills</h3>
                      <div className="flex flex-wrap gap-2">
                        {parsedResume.skills.slice(0, 8).map((skill, idx) => (
                          <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            {skill}
                          </span>
                        ))}
                        {parsedResume.skills.length > 8 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            +{parsedResume.skills.length - 8} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Start Form Filling Section */}
          {parsedResume && sessionId && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                    <CheckCircleIcon className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Ready to Fill Form</h2>
                    <p className="text-sm sm:text-base text-gray-600">Resume parsed successfully</p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <p className="text-gray-600">
                  Click the button below to open the application form in a new tab. 
                  Watch as AI automatically fills the form with your resume information.
                </p>
                <div className="flex gap-4">
                  <ProcessingButton
                    onClick={startFormFilling}
                    isProcessing={isFilling}
                    disabled={!sessionId}
                    className="flex-1"
                  >
                    {isFilling ? 'Opening Form...' : (
                      <>
                        Start Form Filling
                        <ArrowRightIcon className="w-5 h-5 ml-2" />
                      </>
                    )}
                  </ProcessingButton>
                  <button
                    onClick={resetForm}
                    className="px-6 py-3 bg-gray-100 text-gray-700 font-semibold rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Reset
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

