'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import { 
  MapPinIcon,
  GlobeAltIcon,
  BuildingOfficeIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  UserGroupIcon,
  SunIcon,
  SparklesIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import AlertMessage from '@/components/demos/AlertMessage';

interface StepProgress {
  step: string;
  message: string;
  agent?: string;
  timestamp: number;
}

interface TravelPlanResult {
  selected_city?: string;
  city_reasoning?: string;
  local_insights?: string;
  itinerary?: string;
  budget_breakdown?: string;
  packing_suggestions?: string;
  full_output?: string;
}

export default function TravelPlannerDemo() {
  const [destination, setDestination] = useState('');
  const [interests, setInterests] = useState('');
  const [budget, setBudget] = useState('');
  const [duration, setDuration] = useState('');
  const [season, setSeason] = useState('');
  const [travelers, setTravelers] = useState('');
  
  const [isPlanning, setIsPlanning] = useState(false);
  const [progressSteps, setProgressSteps] = useState<StepProgress[]>([]);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [travelPlan, setTravelPlan] = useState<TravelPlanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [planContent, setPlanContent] = useState('');
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const startTravelPlanning = async () => {
    if (!interests.trim() || !budget.trim() || !duration.trim()) {
      setError('Please fill in at least Interests, Budget, and Duration');
      return;
    }

    setIsPlanning(true);
    setError(null);
    setProgressSteps([]);
    setTravelPlan(null);
    setPlanContent('');
    setCurrentAgent(null);

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/travel-planner/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          destination: destination.trim() || null,
          interests: interests.trim(),
          budget: budget.trim(),
          duration: duration.trim(),
          season: season.trim() || null,
          travelers: travelers.trim() || null,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error('Failed to start travel planning');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response stream available');
      }

      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              // Handle errors
              if (data.error) {
                setError(data.error);
                setIsPlanning(false);
                return;
              }

              // Handle step progress
              if (data.step && data.message) {
                const stepProgress: StepProgress = {
                  step: data.step,
                  message: data.message,
                  agent: data.agent || undefined,
                  timestamp: Date.now(),
                };
                
                setProgressSteps(prev => [...prev, stepProgress]);
                
                if (data.agent) {
                  setCurrentAgent(data.agent);
                }
              }

              // Handle final result
              if (data.result) {
                setTravelPlan(data.result);
                if (data.result.full_output) {
                  setPlanContent(data.result.full_output);
                }
              }

              // Handle completion
              if (data.done) {
                setIsPlanning(false);
                setCurrentAgent(null);
                return;
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        console.error('Error in travel planning:', err);
        setError(err instanceof Error ? err.message : 'Failed to plan your trip');
      }
      setIsPlanning(false);
    }
  };

  const cancelPlanning = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsPlanning(false);
    setCurrentAgent(null);
  };

  const resetForm = () => {
    setDestination('');
    setInterests('');
    setBudget('');
    setDuration('');
    setSeason('');
    setTravelers('');
    setProgressSteps([]);
    setTravelPlan(null);
    setPlanContent('');
    setError(null);
    setCurrentAgent(null);
  };

  const getStepIcon = (step: string) => {
    if (step === 'completed') {
      return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
    }
    if (step === 'error') {
      return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
    }
    return <ClockIcon className="w-5 h-5 text-blue-500 animate-spin" />;
  };

  const getAgentIcon = (agent: string) => {
    if (agent?.includes('City Selection')) {
      return <MapPinIcon className="w-6 h-6" />;
    }
    if (agent?.includes('Local Expert')) {
      return <GlobeAltIcon className="w-6 h-6" />;
    }
    if (agent?.includes('Travel Concierge')) {
      return <BuildingOfficeIcon className="w-6 h-6" />;
    }
    return <SparklesIcon className="w-6 h-6" />;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <MapPinIcon className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            AI Travel Planner
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Plan your perfect trip with AI-powered multi-agent collaboration. Watch as specialized agents work together to create your dream itinerary.
          </p>
          <Link
            href="/challenges/travel-planner"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">
          {/* Input Form */}
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center mb-6 sm:mb-8">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                <PaperAirplaneIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Plan Your Trip</h2>
                <p className="text-sm sm:text-base text-gray-600">Tell us about your travel preferences</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Destination */}
              <div>
                <label htmlFor="destination" className="block text-sm font-semibold text-gray-700 mb-2">
                  Destination (Optional)
                </label>
                <input
                  id="destination"
                  type="text"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g., Paris, Tokyo, or leave blank"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  disabled={isPlanning}
                />
              </div>

              {/* Interests */}
              <div>
                <label htmlFor="interests" className="block text-sm font-semibold text-gray-700 mb-2">
                  Interests <span className="text-red-500">*</span>
                </label>
                <input
                  id="interests"
                  type="text"
                  value={interests}
                  onChange={(e) => setInterests(e.target.value)}
                  placeholder="e.g., Museums, Food, Nightlife, Nature"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  disabled={isPlanning}
                  required
                />
              </div>

              {/* Budget */}
              <div>
                <label htmlFor="budget" className="block text-sm font-semibold text-gray-700 mb-2">
                  <CurrencyDollarIcon className="w-4 h-4 inline mr-1" />
                  Budget <span className="text-red-500">*</span>
                </label>
                <input
                  id="budget"
                  type="text"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="e.g., $2000, Budget-friendly"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  disabled={isPlanning}
                  required
                />
              </div>

              {/* Duration */}
              <div>
                <label htmlFor="duration" className="block text-sm font-semibold text-gray-700 mb-2">
                  <CalendarIcon className="w-4 h-4 inline mr-1" />
                  Duration <span className="text-red-500">*</span>
                </label>
                <input
                  id="duration"
                  type="text"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  placeholder="e.g., 5 days, 2 weeks"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  disabled={isPlanning}
                  required
                />
              </div>

              {/* Season */}
              <div>
                <label htmlFor="season" className="block text-sm font-semibold text-gray-700 mb-2">
                  <SunIcon className="w-4 h-4 inline mr-1" />
                  Season (Optional)
                </label>
                <input
                  id="season"
                  type="text"
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  placeholder="e.g., Summer, Winter, Spring"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  disabled={isPlanning}
                />
              </div>

              {/* Travelers */}
              <div>
                <label htmlFor="travelers" className="block text-sm font-semibold text-gray-700 mb-2">
                  <UserGroupIcon className="w-4 h-4 inline mr-1" />
                  Travelers (Optional)
                </label>
                <input
                  id="travelers"
                  type="text"
                  value={travelers}
                  onChange={(e) => setTravelers(e.target.value)}
                  placeholder="e.g., 2 adults, Solo traveler"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  disabled={isPlanning}
                />
              </div>
            </div>

            <div className="mt-6 flex gap-4">
              <button
                onClick={startTravelPlanning}
                disabled={isPlanning || !interests.trim() || !budget.trim() || !duration.trim()}
                className="flex-1 bg-blue-600 text-white font-semibold py-3 px-6 rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md flex items-center justify-center"
              >
                {isPlanning ? (
                  <>
                    <ClockIcon className="w-5 h-5 mr-2 animate-spin" />
                    Planning Your Trip...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-5 h-5 mr-2" />
                    Plan My Trip
                  </>
                )}
              </button>
              
              {isPlanning && (
                <button
                  onClick={cancelPlanning}
                  className="bg-gray-200 text-gray-700 font-semibold py-3 px-6 rounded-xl hover:bg-gray-300 transition-all duration-200"
                >
                  Cancel
                </button>
              )}

              {travelPlan && !isPlanning && (
                <button
                  onClick={resetForm}
                  className="bg-gray-200 text-gray-700 font-semibold py-3 px-6 rounded-xl hover:bg-gray-300 transition-all duration-200"
                >
                  New Trip
                </button>
              )}
            </div>
          </div>

          {/* Progress Steps */}
          {progressSteps.length > 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Planning Progress</h3>
              <div className="space-y-4">
                {progressSteps.map((step, index) => (
                  <div
                    key={index}
                    className={`flex items-start p-4 rounded-lg border ${
                      step.step === 'completed' 
                        ? 'bg-green-50 border-green-200' 
                        : step.step === 'error'
                        ? 'bg-red-50 border-red-200'
                        : 'bg-blue-50 border-blue-200'
                    }`}
                  >
                    <div className="flex-shrink-0 mr-4">
                      {getStepIcon(step.step)}
                    </div>
                    <div className="flex-1">
                      {step.agent && (
                        <div className="flex items-center mb-2">
                          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-2">
                            {getAgentIcon(step.agent)}
                          </div>
                          <span className="font-semibold text-gray-900">{step.agent}</span>
                        </div>
                      )}
                      <p className="text-gray-700">{step.message}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Current Agent Status */}
              {currentAgent && isPlanning && (
                <div className="mt-6 p-4 bg-blue-100 rounded-lg border border-blue-200">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center mr-3">
                      {getAgentIcon(currentAgent)}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{currentAgent}</p>
                      <p className="text-sm text-gray-600">Working on your request...</p>
                    </div>
                    <div className="ml-auto">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Travel Plan Results */}
          {travelPlan && (
            <div className="space-y-6">
              {travelPlan.selected_city && (
                <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                      <MapPinIcon className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Selected Destination</h3>
                      <p className="text-gray-600">{travelPlan.selected_city}</p>
                    </div>
                  </div>
                  {travelPlan.city_reasoning && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <p className="text-gray-700">{travelPlan.city_reasoning}</p>
                    </div>
                  )}
                </div>
              )}

              {planContent && (
                <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Complete Travel Plan</h3>
                  <div className="prose prose-lg max-w-none">
                    <div 
                      className="text-gray-800 leading-relaxed whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{ 
                        __html: planContent
                          .replace(/\n/g, '<br>')
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
              <AlertMessage type="error" message={error} />
            </div>
          )}

          {/* Empty State */}
          {!travelPlan && !isPlanning && !error && progressSteps.length === 0 && (
            <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-200">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-2xl mb-6">
                  <MapPinIcon className="w-8 h-8 text-gray-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready to Plan Your Trip</h3>
                <p className="text-gray-600">Fill in the form above and watch as our AI agents collaborate to create your perfect travel plan.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

