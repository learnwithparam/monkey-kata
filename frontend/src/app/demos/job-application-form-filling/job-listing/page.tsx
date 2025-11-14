'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  BriefcaseIcon,
  MapPinIcon,
  CheckCircleIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';

interface JobListing {
  job_title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  benefits: string[];
  application_instructions?: string;
}

export default function JobListingPage() {
  const [jobListing, setJobListing] = useState<JobListing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchJobListing();
  }, []);

  const fetchJobListing = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/job-application-form-filling/job-listing`);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`Failed to fetch job listing: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      setJobListing(data);
    } catch (error) {
      console.error('Error fetching job listing:', error);
      setError(error instanceof Error ? error.message : 'Failed to load job listing. Please ensure the API server is running.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading job listing...</p>
        </div>
      </div>
    );
  }

  if (error || !jobListing) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Job listing not found'}</p>
          <Link
            href="/demos/job-application-form-filling"
            className="text-blue-600 hover:text-blue-700"
          >
            Go back to demo
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-6">
            <Link
              href="/demos/job-application-form-filling"
              className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span className="font-medium">Back to Demo</span>
            </Link>
          </div>
        </div>

        {/* Job Listing Card */}
        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
          {/* Job Header */}
          <div className="mb-8">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                <BriefcaseIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
                  {jobListing.job_title}
                </h1>
                <p className="text-xl text-gray-600 mt-1">{jobListing.company}</p>
              </div>
            </div>
            <div className="flex items-center text-gray-600 mt-4">
              <MapPinIcon className="w-5 h-5 mr-2" />
              <span>{jobListing.location}</span>
            </div>
          </div>

          {/* Job Description */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Job Description</h2>
            <div className="text-gray-700 whitespace-pre-line">
              {jobListing.description}
            </div>
          </div>

          {/* Requirements */}
          {jobListing.requirements.length > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Requirements</h2>
              <ul className="space-y-2">
                {jobListing.requirements.map((req, idx) => (
                  <li key={idx} className="flex items-start">
                    <CheckCircleIcon className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{req}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Benefits */}
          {jobListing.benefits.length > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Benefits</h2>
              <ul className="space-y-2">
                {jobListing.benefits.map((benefit, idx) => (
                  <li key={idx} className="flex items-start">
                    <CheckCircleIcon className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Application Instructions */}
          {jobListing.application_instructions && (
            <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">Application Instructions</h3>
              <p className="text-sm text-blue-800">{jobListing.application_instructions}</p>
            </div>
          )}

          {/* CTA */}
          <div className="pt-6 border-t border-gray-200">
            <Link
              href="/demos/job-application-form-filling/form"
              className="inline-flex items-center justify-center w-full sm:w-auto px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md"
            >
              Start Application
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

