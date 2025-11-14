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
    // Always fetch form structure to display the form
    fetchFormStructure();
  }, []);

  // Start auto-filling only if session_id is present
  useEffect(() => {
    if (formStructure && sessionId && !isFilling && !isComplete) {
      // Wait a bit for React to render the form, then start auto-filling
      const timer = setTimeout(() => {
        startFormFilling();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [formStructure, sessionId]);

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

    // Wait for form structure to be loaded and rendered
    if (!formStructure) {
      setCurrentMessage('Waiting for form to load...');
      // Retry after a short delay
      setTimeout(() => startFormFilling(), 500);
      return;
    }

    setIsFilling(true);
    setError(null);
    setCurrentMessage('Discovering form structure from HTML...');

    try {
      // Wait a bit for React to render the form
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Find the form element specifically
      const formElement = document.querySelector('form');
      let htmlContent = '';
      
      if (formElement) {
        // Get HTML from the form element
        htmlContent = formElement.outerHTML;
        setCurrentMessage('Form HTML extracted, sending to agent...');
        console.log('Extracted form HTML:', htmlContent.substring(0, 200));
      } else {
        // Fallback: find form container
        const formContainer = document.querySelector('[class*="bg-white"][class*="rounded-xl"]');
        if (formContainer) {
          htmlContent = formContainer.outerHTML;
          setCurrentMessage('Form container HTML extracted, sending to agent...');
        } else {
          // Last fallback: get all form-related elements
          const formElements = document.querySelectorAll('input, textarea, select, label');
          if (formElements.length > 0) {
            // Create a form wrapper with all form elements
            const formWrapper = document.createElement('form');
            formElements.forEach(el => {
              const clone = el.cloneNode(true);
              formWrapper.appendChild(clone);
            });
            htmlContent = formWrapper.outerHTML;
            setCurrentMessage('Form elements extracted, sending to agent...');
          } else {
            throw new Error('Could not find form element. Please ensure the form is visible.');
          }
        }
      }
      
      if (!htmlContent || htmlContent.length < 100) {
        throw new Error('Could not extract form HTML. Please ensure the form is visible.');
      }
      
      // Send HTML content to parse form structure dynamically
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/job-application-form-filling/fill-form-stream?session_id=${encodeURIComponent(sessionId)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            html_content: htmlContent
          }),
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

  // Handle manual field updates (when no session_id or manual mode)
  const handleFieldChange = (fieldName: string, value: string) => {
    if (sessionId && isFilling) {
      // Don't allow manual edits during auto-fill
      return;
    }
    
    setFilledFields(prev => {
      const updated = new Map(prev);
      const field = updated.get(fieldName);
      if (field) {
        updated.set(fieldName, { ...field, value });
      }
      return updated;
    });
  };

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
            {sessionId 
              ? 'Watch as AI automatically fills your application form'
              : 'Fill out the form manually or upload your resume to auto-fill'}
          </p>
          {!sessionId && (
            <div className="mt-4">
              <a
                href="/demos/job-application-form-filling"
                className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Upload Resume to Auto-Fill
              </a>
            </div>
          )}
        </div>

        {/* Status Bar - Only show when auto-filling */}
        {sessionId && (
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
                    className="bg-green-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6">
            <AlertMessage type="error" message={error} />
          </div>
        )}

        {/* Form */}
        {formStructure && (
          <form className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200 space-y-8">
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
                          ? 'bg-green-50 border-green-300 shadow-md scale-[1.02]'
                          : hasValue
                          ? 'bg-green-50 border-green-200'
                          : 'bg-white border-gray-200'
                      } border-2 rounded-lg p-4`}
                    >
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                        {isHighlighted && (
                          <SparklesIcon className="w-4 h-4 text-green-600 inline-block ml-2 animate-pulse" />
                        )}
                        {hasValue && !isHighlighted && (
                          <CheckCircleIcon className="w-4 h-4 text-green-600 inline-block ml-2" />
                        )}
                      </label>
                      {field.type === 'textarea' ? (
                        <textarea
                          name={field.name}
                          id={field.name}
                          value={field.value || ''}
                          readOnly={!!sessionId && (isFilling || isComplete)}
                          onChange={(e) => handleFieldChange(field.name, e.target.value)}
                          rows={field.name === 'work_experience' || field.name === 'education' ? 6 : 3}
                          className={`w-full px-4 py-3 border-0 rounded-lg focus:ring-2 focus:ring-green-500 resize-none transition-all duration-300 ${
                            hasValue
                              ? 'text-gray-900 bg-transparent'
                              : 'text-gray-400 bg-transparent'
                          } ${!sessionId || (!isFilling && !isComplete) ? 'cursor-text' : 'cursor-not-allowed'}`}
                          placeholder={sessionId ? (isFilling ? 'Filling...' : 'Waiting...') : `Enter ${field.label.toLowerCase()}`}
                        />
                      ) : (
                        <input
                          name={field.name}
                          id={field.name}
                          type={field.type}
                          value={field.value || ''}
                          readOnly={!!sessionId && (isFilling || isComplete)}
                          onChange={(e) => handleFieldChange(field.name, e.target.value)}
                          className={`w-full px-4 py-3 border-0 rounded-lg focus:ring-2 focus:ring-green-500 transition-all duration-300 ${
                            hasValue
                              ? 'text-gray-900 bg-transparent'
                              : 'text-gray-400 bg-transparent'
                          } ${!sessionId || (!isFilling && !isComplete) ? 'cursor-text' : 'cursor-not-allowed'}`}
                          placeholder={sessionId ? (isFilling ? 'Filling...' : 'Waiting...') : `Enter ${field.label.toLowerCase()}`}
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
                disabled={sessionId ? !isComplete : false}
                className={`w-full px-6 py-3 rounded-lg font-semibold transition-all ${
                  sessionId 
                    ? (isComplete
                        ? 'bg-green-600 text-white hover:bg-green-700 shadow-md hover:shadow-lg'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed')
                    : 'bg-green-600 text-white hover:bg-green-700 shadow-md hover:shadow-lg'
                }`}
              >
                {sessionId ? (
                  isComplete ? (
                    <>
                      <CheckCircleIcon className="w-5 h-5 inline-block mr-2" />
                      Submit Application
                    </>
                  ) : (
                    'Form Filling in Progress...'
                  )
                ) : (
                  <>
                    <CheckCircleIcon className="w-5 h-5 inline-block mr-2" />
                    Submit Application
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {!formStructure && !error && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
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

