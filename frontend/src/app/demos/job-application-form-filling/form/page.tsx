'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { 
  DocumentTextIcon,
  CheckCircleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import AlertMessage from '@/components/demos/AlertMessage';

interface FormField {
  name: string;
  label: string;
  type: string;
  section: string;
  value?: string;
  required?: boolean;
}

interface FormStructure {
  sections: string[];
  fields: FormField[];
}

function FormPageContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  
  const [formStructure, setFormStructure] = useState<FormStructure | null>(null);
  const [filledFields, setFilledFields] = useState<Map<string, FormField>>(new Map());
  const [isFilling, setIsFilling] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentMessage, setCurrentMessage] = useState('');
  const [highlightedField, setHighlightedField] = useState<string | null>(null);
  const fieldRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  useEffect(() => {
    if (!sessionId) {
      setError('No session ID provided. Please start from the main demo page.');
      return;
    }

    // Fetch form structure
    fetchFormStructure();
    
    // Start form filling
    startFormFilling();
  }, [sessionId]);

  const fetchFormStructure = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/job-application-form-filling/form-structure`);
      if (!response.ok) {
        throw new Error('Failed to fetch form structure');
      }
      const data = await response.json();
      setFormStructure(data);
      
      // Initialize empty fields
      const fieldsMap = new Map<string, FormField>();
      data.fields.forEach((field: FormField) => {
        fieldsMap.set(field.name, { ...field, value: '' });
      });
      setFilledFields(fieldsMap);
    } catch (error) {
      console.error('Error fetching form structure:', error);
      setError(error instanceof Error ? error.message : 'Failed to load form structure');
    }
  };

  const startFormFilling = async () => {
    if (!sessionId) return;

    setIsFilling(true);
    setError(null);
    setCurrentMessage('Connecting to form filling agent...');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/job-application-form-filling/fill-form-stream?session_id=${encodeURIComponent(sessionId)}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to start form filling');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder('utf-8');

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
                setCurrentMessage(data.message || 'Starting form filling...');
                continue;
              }

              if (data.field) {
                // Update field value
                setFilledFields(prev => {
                  const newMap = new Map(prev);
                  const field = newMap.get(data.field.name);
                  if (field) {
                    newMap.set(data.field.name, {
                      ...field,
                      value: data.field.value
                    });
                  }
                  return newMap;
                });

                // Highlight field being filled
                setHighlightedField(data.field.name);
                setCurrentMessage(`Filling ${data.field.label}...`);
                setProgress(data.progress || 0);

                // Scroll to field
                setTimeout(() => {
                  const fieldElement = fieldRefs.current.get(data.field.name);
                  if (fieldElement) {
                    fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }
                }, 100);

                // Remove highlight after animation
                setTimeout(() => {
                  setHighlightedField(null);
                }, 1500);
              }

              if (data.done) {
                setIsComplete(true);
                setIsFilling(false);
                setCurrentMessage('Form filled successfully!');
                setProgress(1);
                setHighlightedField(null);
              }

              if (data.error) {
                setError(data.error);
                setIsFilling(false);
              }
            } catch (parseError) {
              console.error('Error parsing chunk:', parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error filling form:', error);
      setError(error instanceof Error ? error.message : 'Failed to fill form. Please try again.');
      setIsFilling(false);
    }
  };

  const getFieldsBySection = (section: string): FormField[] => {
    if (!formStructure) return [];
    return formStructure.fields
      .filter(field => field.section === section)
      .map(field => filledFields.get(field.name) || field);
  };

  if (!sessionId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertMessage type="error" message="No session ID provided. Please start from the main demo page." />
          <a
            href="/demos/job-application-form-filling"
            className="mt-4 inline-block text-blue-600 hover:text-blue-700"
          >
            Go to main demo page
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <DocumentTextIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Job Application Form
          </h1>
          <p className="text-lg text-gray-600">
            Watch as AI automatically fills your application form
          </p>
        </div>

        {/* Status Bar */}
        <div className="mb-6">
          <StatusIndicator
            status={isComplete ? 'completed' : isFilling ? 'processing' : 'idle'}
            message={currentMessage || (isComplete ? 'Form filled successfully!' : 'Waiting to start...')}
          />
          {isFilling && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Progress</span>
                <span className="text-sm font-semibold text-gray-900">{Math.round(progress * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress * 100}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6">
            <AlertMessage type="error" message={error} />
          </div>
        )}

        {/* Form */}
        {formStructure && (
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200 space-y-8">
            {formStructure.sections.map((section) => (
              <div key={section} className="space-y-4">
                <h2 className="text-xl font-bold text-gray-900 border-b border-gray-200 pb-2">
                  {section}
                </h2>
                {getFieldsBySection(section).map((field) => {
                  const isHighlighted = highlightedField === field.name;
                  const hasValue = field.value && field.value.trim().length > 0;
                  
                  return (
                    <div
                      key={field.name}
                      ref={(el) => {
                        if (el) {
                          fieldRefs.current.set(field.name, el);
                        }
                      }}
                      className={`transition-all duration-500 ${
                        isHighlighted
                          ? 'bg-blue-50 border-blue-300 shadow-md scale-[1.02]'
                          : hasValue
                          ? 'bg-green-50 border-green-200'
                          : 'bg-white border-gray-200'
                      } border-2 rounded-lg p-4`}
                    >
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                        {isHighlighted && (
                          <SparklesIcon className="w-4 h-4 text-blue-600 inline-block ml-2 animate-pulse" />
                        )}
                        {hasValue && !isHighlighted && (
                          <CheckCircleIcon className="w-4 h-4 text-green-600 inline-block ml-2" />
                        )}
                      </label>
                      {field.type === 'textarea' ? (
                        <textarea
                          value={field.value || ''}
                          readOnly
                          rows={field.name === 'work_experience' || field.name === 'education' ? 6 : 3}
                          className={`w-full px-4 py-3 border-0 rounded-lg focus:ring-0 resize-none transition-all duration-300 ${
                            hasValue
                              ? 'text-gray-900 bg-transparent'
                              : 'text-gray-400 bg-transparent'
                          }`}
                          placeholder={isFilling ? 'Filling...' : 'Waiting...'}
                        />
                      ) : (
                        <input
                          type={field.type}
                          value={field.value || ''}
                          readOnly
                          className={`w-full px-4 py-3 border-0 rounded-lg focus:ring-0 transition-all duration-300 ${
                            hasValue
                              ? 'text-gray-900 bg-transparent'
                              : 'text-gray-400 bg-transparent'
                          }`}
                          placeholder={isFilling ? 'Filling...' : 'Waiting...'}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            ))}

            {/* Submit Button */}
            <div className="pt-6 border-t border-gray-200">
              <button
                disabled={!isComplete}
                className={`w-full px-6 py-3 rounded-lg font-semibold transition-all ${
                  isComplete
                    ? 'bg-green-600 text-white hover:bg-green-700 shadow-md hover:shadow-lg'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {isComplete ? (
                  <>
                    <CheckCircleIcon className="w-5 h-5 inline-block mr-2" />
                    Submit Application
                  </>
                ) : (
                  'Form Filling in Progress...'
                )}
              </button>
            </div>
          </div>
        )}

        {!formStructure && !error && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading form structure...</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function FormPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    }>
      <FormPageContent />
    </Suspense>
  );
}

