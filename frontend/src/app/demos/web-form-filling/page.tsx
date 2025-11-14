'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { 
  DocumentTextIcon,
  GlobeAltIcon,
  CheckCircleIcon,
  SparklesIcon,
  ArrowPathIcon,
  PhoneIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline';
import { Room, RoomEvent } from 'livekit-client';
import { RoomAudioRenderer, RoomContext } from '@livekit/components-react';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import SubmitButton from '@/components/demos/SubmitButton';
import VoiceInterface from '@/components/demos/VoiceInterface';
import CustomSelect from '@/components/CustomSelect';

interface ConnectionDetails {
  server_url: string;
  room_name: string;
  participant_name: string;
  participant_token: string;
}

interface FormFillingRequest {
  url: string;
  form_data: Record<string, string>;
  auto_submit: boolean;
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
  steps?: Array<{
    timestamp: string;
    message: string;
    agent?: string;
    tool?: string;
    target?: string;
  }>;
}

interface B2BFormData {
  company_name: string;
  full_name: string;
  email: string;
  phone: string;
  company_size: string;
  job_title: string;
  use_case: string;
  message: string;
}

const COMPANY_SIZES = [
  { value: '1-10', label: '1-10 employees' },
  { value: '11-50', label: '11-50 employees' },
  { value: '51-200', label: '51-200 employees' },
  { value: '201-500', label: '201-500 employees' },
  { value: '500+', label: '500+ employees' },
];

export default function WebFormFillingDemo() {
  const [url, setUrl] = useState('');
  const [formData, setFormData] = useState<B2BFormData>({
    company_name: '',
    full_name: '',
    email: '',
    phone: '',
    company_size: '',
    job_title: '',
    use_case: '',
    message: '',
  });
  const [autoSubmit, setAutoSubmit] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [fillingStatus, setFillingStatus] = useState<{status: string, message: string} | null>(null);
  const [fillingResult, setFillingResult] = useState<FormFillingResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workflowSteps, setWorkflowSteps] = useState<Array<{timestamp: string, message: string, agent?: string, tool?: string, target?: string}>>([]);
  
  // Voice connection state
  const [connectionDetails, setConnectionDetails] = useState<ConnectionDetails | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const room = useMemo(() => new Room(), []);

  useEffect(() => {
    const onDisconnected = () => {
      setIsConnected(false);
      setConnectionDetails(null);
    };
    
    const onMediaDevicesError = (err: Error) => {
      setError(`Media device error: ${err.message}`);
    };

    room.on(RoomEvent.Disconnected, onDisconnected);
    room.on(RoomEvent.MediaDevicesError, onMediaDevicesError);

    return () => {
      room.off(RoomEvent.Disconnected, onDisconnected);
      room.off(RoomEvent.MediaDevicesError, onMediaDevicesError);
      room.disconnect();
    };
  }, [room]);

  useEffect(() => {
    if (isConnected && connectionDetails && room.state === 'disconnected') {
      room.localParticipant.setMicrophoneEnabled(true);
      room.connect(connectionDetails.server_url, connectionDetails.participant_token)
        .then(() => {
          setIsConnected(true);
        })
        .catch((err) => {
          setError(`Connection failed: ${err.message}`);
          setIsConnected(false);
        });
    }
  }, [isConnected, connectionDetails, room]);

  // Poll for voice-collected form data
  useEffect(() => {
    if (!isConnected || !connectionDetails) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/web-form-filling/voice-data/${connectionDetails.room_name}`
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.form_data && Object.keys(data.form_data).length > 0) {
            // Map API field names to form field names
            const fieldMapping: Record<string, keyof B2BFormData> = {
              company_name: 'company_name',
              full_name: 'full_name',
              email: 'email',
              phone: 'phone',
              company_size: 'company_size',
              job_title: 'job_title',
              use_case: 'use_case',
              message: 'message',
            };

            // Update form fields with collected data (only if field is empty or update if new data is provided)
            setFormData(prev => {
              const updated = { ...prev };
              Object.entries(data.form_data).forEach(([key, value]) => {
                const formField = fieldMapping[key];
                if (formField && value && typeof value === 'string') {
                  // Only update if current field is empty or if new value is different
                  if (!prev[formField] || prev[formField] !== value) {
                    updated[formField] = value;
                  }
                }
              });
              return updated;
            });
          }
        }
      } catch (err) {
        // Silently ignore errors (data might not be available yet)
        console.debug('Polling for voice data:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [isConnected, connectionDetails]);

  const connectToVoiceAgent = async () => {
    setIsConnecting(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/web-form-filling/connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const details: ConnectionDetails = await response.json();
      setConnectionDetails(details);
      setIsConnected(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to voice agent');
      setIsConnected(false);
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnect = () => {
    room.disconnect();
    setIsConnected(false);
    setConnectionDetails(null);
  };

  const updateFormField = (field: keyof B2BFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const convertFormDataToDict = (): Record<string, string> => {
    const dict: Record<string, string> = {};
    Object.entries(formData).forEach(([key, value]) => {
      if (value.trim()) {
        dict[key] = value.trim();
      }
    });
    return dict;
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

    const dataDict = convertFormDataToDict();
    if (Object.keys(dataDict).length === 0) {
      setError('Please collect form data via voice or enter it manually');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setFillingResult(null);
    setWorkflowSteps([]);
    setFillingStatus({
      status: 'processing',
      message: 'Starting form filling workflow...'
    });

    try {
      const request: FormFillingRequest = {
        url: url.trim(),
        form_data: dataDict,
        auto_submit: autoSubmit
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/web-form-filling/fill-form-stream`, {
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

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder('utf-8');
      const steps: Array<{timestamp: string, message: string, agent?: string, tool?: string, target?: string}> = [];

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
              } catch {
                console.warn('Failed to parse JSON line:', jsonStr.substring(0, 100));
                continue;
              }

              if (data.step) {
                const newSteps = [...steps, data.step];
                steps.length = 0;
                steps.push(...newSteps);
                
                setWorkflowSteps(newSteps);
                setFillingStatus(prev => prev ? {
                  ...prev,
                  message: data.step.message,
                  status: 'processing'
                } : null);
              }

              if (data.done) {
                setIsProcessing(false);
                if (data.result) {
                  setFillingResult({
                    session_id: sessionId || '',
                    status: data.status,
                    url: data.result.url,
                    form_data: data.result.form_data,
                    navigation: data.result.navigation,
                    form_detection: data.result.form_detection,
                    form_filling: data.result.form_filling,
                    form_submission: data.result.form_submission,
                    submitted: data.result.submitted,
                    steps: steps
                  });
                  setFillingStatus({
                    status: data.status,
                    message: data.status === 'success' ? 'Form filling completed successfully!' : 'Form filling failed'
                  });
                } else if (data.error) {
                  setError(data.error);
                  setFillingStatus({
                    status: 'error',
                    message: `Error: ${data.error}`
                  });
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
      console.error('Error starting form filling:', error);
      setError(error instanceof Error ? error.message : 'Failed to start form filling. Please try again.');
      setIsProcessing(false);
    }
  };

  const resetForm = () => {
    setUrl('');
    setFormData({
      company_name: '',
      full_name: '',
      email: '',
      phone: '',
      company_size: '',
      job_title: '',
      use_case: '',
      message: '',
    });
    setAutoSubmit(false);
    setSessionId(null);
    setFillingStatus(null);
    setFillingResult(null);
    setIsProcessing(false);
    setError(null);
    setWorkflowSteps([]);
  };

  const isFormValid = () => {
    return formData.company_name.trim() && 
           formData.full_name.trim() && 
           formData.email.trim() && 
           formData.phone.trim() && 
           formData.company_size.trim();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <BuildingOfficeIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            B2B Demo Booking Form Filling
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Collect B2B demo booking data via voice conversation, then automatically fill forms with browser automation
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

        {/* Main Content - Voice Collector Left, Form Right */}
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8 mb-8">
            {/* Left Side: Voice Collector */}
            <div className="lg:col-span-1">
              <div className="card p-4 sm:p-6 lg:p-8 sticky top-8">
                <div className="flex items-center mb-6">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
                    <PhoneIcon className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Voice Collection</h2>
                    <p className="text-sm text-gray-600">Speak with CrispDream CRM</p>
                  </div>
                </div>

                {!isConnected ? (
                  <div>
                    <SubmitButton
                      isLoading={isConnecting}
                      onClick={connectToVoiceAgent}
                      disabled={isConnecting}
                      className="w-full btn-accent disabled:opacity-50 disabled:cursor-not-allowed py-4 text-lg font-semibold flex items-center justify-center"
                    >
                      <PhoneIcon className="w-5 h-5 mr-2" />
                      Call to Collect Data
                    </SubmitButton>
                    <p className="text-xs text-gray-500 mt-3 text-center">
                      Click to start a conversation with our sales team
                    </p>
                  </div>
                ) : (
                  <RoomContext.Provider value={room}>
                    <RoomAudioRenderer />
                    <VoiceInterface 
                      onDisconnect={disconnect}
                      examples={[
                        "I'm looking for a CRM solution",
                        "We need help with customer management",
                        "I want to see how CrispDream can help my team",
                        "We're interested in automating our sales process"
                      ]}
                    />
                    {Object.values(formData).some(v => v.trim()) && (
                      <div className="mt-4 text-xs text-green-600 bg-green-50 p-3 rounded-lg border border-green-200">
                        <div className="font-semibold mb-1">✓ Data Collected</div>
                        <div className="text-gray-700">
                          Form fields are being populated from your conversation
                        </div>
                      </div>
                    )}
                  </RoomContext.Provider>
                )}
              </div>
            </div>

            {/* Right Side: Form */}
            <div className="lg:col-span-2">
              <div className="card p-4 sm:p-6 lg:p-8">
                <div className="flex items-center mb-6">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                    <SparklesIcon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Book a Demo</h2>
                    <p className="text-sm text-gray-600">CrispDream CRM Demo Booking Form</p>
                  </div>
                </div>

                {/* Form Fields */}
                <div className="space-y-4 sm:space-y-6">
                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Company Name *
                    </label>
                    <input
                      type="text"
                      value={formData.company_name}
                      onChange={(e) => updateFormField('company_name', e.target.value)}
                      placeholder="Acme Corp"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      value={formData.full_name}
                      onChange={(e) => updateFormField('full_name', e.target.value)}
                      placeholder="John Doe"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Email *
                    </label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => updateFormField('email', e.target.value)}
                      placeholder="john@acme.com"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Phone *
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => updateFormField('phone', e.target.value)}
                      placeholder="+1 (555) 123-4567"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Company Size *
                    </label>
                    <CustomSelect
                      id="company-size"
                      name="company_size"
                      value={formData.company_size}
                      onChange={(value: string) => updateFormField('company_size', value)}
                      options={COMPANY_SIZES}
                      placeholder="Select company size"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Job Title
                    </label>
                    <input
                      type="text"
                      value={formData.job_title}
                      onChange={(e) => updateFormField('job_title', e.target.value)}
                      placeholder="CEO, CTO, etc."
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Use Case
                    </label>
                    <input
                      type="text"
                      value={formData.use_case}
                      onChange={(e) => updateFormField('use_case', e.target.value)}
                      placeholder="What are you interested in?"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Message
                    </label>
                    <textarea
                      value={formData.message}
                      onChange={(e) => updateFormField('message', e.target.value)}
                      placeholder="Additional information..."
                      rows={3}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">
                      Form URL *
                    </label>
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com/book-demo"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                      disabled={isProcessing}
                    />
                  </div>

                  <div className="space-y-2">
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
                        Auto submit after filling
                      </label>
                    </div>
                  </div>

                  <ProcessingButton
                    onClick={startFormFilling}
                    isLoading={isProcessing}
                    disabled={!url.trim() || !isFormValid()}
                  >
                    {isProcessing ? 'Filling Form...' : 'Fill Form'}
                  </ProcessingButton>

                  {(fillingResult || error) && (
                    <button
                      onClick={resetForm}
                      className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      <ArrowPathIcon className="h-5 w-5 inline mr-2" />
                      Reset
                    </button>
                  )}
                </div>
              </div>
            </div>

          </div>

          {/* Status Section - Below Form */}
          {(fillingStatus || fillingResult || workflowSteps.length > 0) && (
            <div className="mt-8">
              <div className="card p-4 sm:p-6 lg:p-8">
                <div className="flex items-center mb-6">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                    <GlobeAltIcon className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Filling Status</h2>
                    <p className="text-sm text-gray-600">Track form filling progress</p>
                  </div>
                </div>

                {fillingStatus && (
                  <div className="mb-6">
                    <StatusIndicator
                      status={fillingStatus.status}
                      message={fillingStatus.message}
                    />
                  </div>
                )}

                {/* Workflow Steps */}
                {workflowSteps.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-900 mb-3">Agent Steps</h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {workflowSteps.map((step, index) => (
                        <div key={index} className="text-xs bg-gray-50 p-3 rounded-lg border border-gray-200">
                          <div className="flex items-start justify-between mb-1">
                            <span className="font-medium text-gray-900">{step.message}</span>
                            {step.agent && (
                              <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                                {step.agent}
                              </span>
                            )}
                          </div>
                          {step.tool && (
                            <div className="text-gray-600 mt-1">
                              <span className="font-medium">Tool:</span> {step.tool}
                              {step.target && <span className="ml-2">→ {step.target.substring(0, 50)}</span>}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {fillingResult && fillingResult.status === 'success' && (
                  <div className="mt-6 space-y-4">
                    <div className="flex items-center text-green-600">
                      <CheckCircleIcon className="h-5 w-5 mr-2" />
                      <span className="font-semibold">Form Filling Completed</span>
                    </div>
                    
                    {fillingResult.form_filling && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-900 mb-2">Filling Results:</h3>
                        <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap border border-gray-200">
                          {fillingResult.form_filling}
                        </div>
                      </div>
                    )}

                    {fillingResult.submitted && fillingResult.form_submission && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-900 mb-2">Submission:</h3>
                        <div className="bg-green-50 rounded-lg p-3 text-sm text-green-700 border border-green-200">
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
          )}
        </div>
      </div>
    </div>
  );
}
