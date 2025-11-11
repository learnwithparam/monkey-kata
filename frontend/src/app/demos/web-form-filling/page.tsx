'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  DocumentTextIcon,
  GlobeAltIcon,
  CheckCircleIcon,
  SparklesIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';

interface FormFillingRequest {
  url: string;
  form_data: Record<string, string>;
  auto_submit: boolean;
}

interface FormFillingResponse {
  session_id: string;
  status: string;
  message: string;
  url: string;
}

interface FormFillingResult {
  session_id: string;
  status: string;
  url: string;
  form_data: Record<string, string>;
  navigation?: string;
  form_detection?: string;
  form_filling?: string;
  form_submission?: string;
  submitted: boolean;
  error?: string;
}

export default function WebFormFillingDemo() {
  const [url, setUrl] = useState('');
  const [formFields, setFormFields] = useState<Array<{key: string, value: string}>>([{key: '', value: ''}]);
  const [autoSubmit, setAutoSubmit] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [fillingStatus, setFillingStatus] = useState<FormFillingResponse | null>(null);
  const [fillingResult, setFillingResult] = useState<FormFillingResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addFormField = () => {
    setFormFields([...formFields, {key: '', value: ''}]);
  };

  const removeFormField = (index: number) => {
    setFormFields(formFields.filter((_, i) => i !== index));
  };

  const updateFormField = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...formFields];
    updated[index][field] = value;
    setFormFields(updated);
  };

  const startFormFilling = async () => {
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setError('URL must start with http:// or https://');
      return;
    }

    const formData: Record<string, string> = {};
    formFields.forEach(field => {
      if (field.key.trim() && field.value.trim()) {
        formData[field.key.trim()] = field.value.trim();
      }
    });

    if (Object.keys(formData).length === 0) {
      setError('Please enter at least one form field');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setFillingResult(null);

    try {
      const request: FormFillingRequest = {
        url: url.trim(),
        form_data: formData,
        auto_submit: autoSubmit
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/web-form-filling/fill-form`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to start form filling');
      }

      const result: FormFillingResponse = await response.json();
      setSessionId(result.session_id);
      setFillingStatus(result);
      
      // Start polling for status updates
      pollStatus(result.session_id);
    } catch (error) {
      console.error('Error starting form filling:', error);
      setError(error instanceof Error ? error.message : 'Failed to start form filling. Please try again.');
      setIsProcessing(false);
    }
  };

  const pollStatus = async (sessionId: string) => {
    const maxAttempts = 60; // 1 minute max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/web-form-filling/status/${sessionId}`);
        
        if (!response.ok) {
          throw new Error('Failed to get status');
        }

        const status: FormFillingResponse = await response.json();
        setFillingStatus(status);

        if (status.status === 'completed' || status.status === 'success') {
          // Get the final result
          const resultResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/web-form-filling/result/${sessionId}`);
          if (resultResponse.ok) {
            const result: FormFillingResult = await resultResponse.json();
            setFillingResult(result);
          }
          setIsProcessing(false);
          return;
        }

        if (status.status === 'error') {
          setIsProcessing(false);
          setError(status.message || 'Form filling failed');
          return;
        }

        attempts++;
        if (attempts < maxAttempts && status.status === 'processing') {
          setTimeout(poll, 2000); // Poll every 2 seconds
        } else {
          setIsProcessing(false);
          setError('Form filling timed out. Please try again.');
        }
      } catch (error) {
        console.error('Error polling status:', error);
        setIsProcessing(false);
        setError('Failed to check form filling status');
      }
    };

    poll();
  };

  const resetForm = () => {
    setUrl('');
    setFormFields([{key: '', value: ''}]);
    setAutoSubmit(false);
    setSessionId(null);
    setFillingStatus(null);
    setFillingResult(null);
    setIsProcessing(false);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <DocumentTextIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Web Form Filling AI Bot
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            AI agent that navigates websites and fills forms automatically
          </p>
          <Link
            href="/challenges/web-form-filling"
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
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Form Configuration</h2>
                  <p className="text-sm sm:text-base text-gray-600">Configure form URL and fields</p>
                </div>
              </div>

            <div className="space-y-4 sm:space-y-6">
              {/* URL */}
              <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                  Form URL *
                </label>
                <input
                  id="url"
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/contact"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isProcessing}
                />
                <p className="text-xs text-gray-500 mt-1">Enter the full URL of the webpage with the form</p>
              </div>

              {/* Form Fields */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Form Fields *
                </label>
                <div className="space-y-3">
                  {formFields.map((field, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={field.key}
                        onChange={(e) => updateFormField(index, 'key', e.target.value)}
                        placeholder="Field name/id/label"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={isProcessing}
                      />
                      <input
                        type="text"
                        value={field.value}
                        onChange={(e) => updateFormField(index, 'value', e.target.value)}
                        placeholder="Value"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={isProcessing}
                      />
                      {formFields.length > 1 && (
                        <button
                          onClick={() => removeFormField(index)}
                          className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                          disabled={isProcessing}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  onClick={addFormField}
                  className="mt-2 text-sm text-blue-600 hover:text-blue-800"
                  disabled={isProcessing}
                >
                  + Add Field
                </button>
                <p className="text-xs text-gray-500 mt-1">Match fields by id, name, or label text</p>
              </div>

              {/* Auto Submit */}
              <div className="flex items-center">
                <input
                  id="auto-submit"
                  type="checkbox"
                  checked={autoSubmit}
                  onChange={(e) => setAutoSubmit(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  disabled={isProcessing}
                />
                <label htmlFor="auto-submit" className="ml-2 block text-sm text-gray-700">
                  Automatically submit form after filling
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <ProcessingButton
                  onClick={startFormFilling}
                  isProcessing={isProcessing}
                  disabled={!url.trim() || formFields.every(f => !f.key.trim() || !f.value.trim())}
                  className="flex-1"
                >
                  {isProcessing ? 'Filling Form...' : 'Start Form Filling'}
                </ProcessingButton>
                {(fillingResult || error) && (
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
                  <GlobeAltIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Filling Status</h2>
                  <p className="text-sm sm:text-base text-gray-600">Track form filling progress</p>
                </div>
              </div>

            {!fillingStatus && !fillingResult && (
              <div className="text-center py-12 text-gray-500">
                <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p>Enter form URL and fields to start filling</p>
              </div>
            )}

            {fillingStatus && (
              <div className="mb-6">
                <StatusIndicator
                  status={fillingStatus.status}
                  message={fillingStatus.message}
                />
                {fillingStatus.status === 'processing' && (
                  <div className="mt-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      Form Filling Agent working...
                    </div>
                  </div>
                )}
              </div>
            )}

            {fillingResult && fillingResult.status === 'success' && (
              <div className="mt-6 space-y-4">
                <div className="flex items-center text-green-600">
                  <CheckCircleIcon className="h-5 w-5 mr-2" />
                  <span className="font-semibold">Form Filling Completed</span>
                </div>
                
                {fillingResult.form_detection && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Form Detection:</h3>
                    <div className="bg-gray-50 rounded p-3 text-xs text-gray-700 font-mono overflow-x-auto">
                      {fillingResult.form_detection.substring(0, 500)}
                      {fillingResult.form_detection.length > 500 && '...'}
                    </div>
                  </div>
                )}

                {fillingResult.form_filling && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Filling Results:</h3>
                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 whitespace-pre-wrap">
                      {fillingResult.form_filling}
                    </div>
                  </div>
                )}

                {fillingResult.submitted && fillingResult.form_submission && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Submission:</h3>
                    <div className="bg-green-50 rounded p-3 text-sm text-green-700">
                      {fillingResult.form_submission}
                    </div>
                  </div>
                )}
              </div>
            )}

            {fillingResult && fillingResult.error && (
              <div className="mt-6">
                <AlertMessage type="error" message={fillingResult.error} />
              </div>
            )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

