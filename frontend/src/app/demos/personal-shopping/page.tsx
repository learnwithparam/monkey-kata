'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ShoppingBagIcon,
  SparklesIcon,
  MagnifyingGlassIcon,
  HeartIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import StatusIndicator from '@/components/demos/StatusIndicator';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';

interface ShoppingRequest {
  user_query: string;
  user_id?: string;
  budget?: string;
  preferences?: Record<string, any>;
}

interface ShoppingResponse {
  session_id: string;
  status: string;
  message: string;
  user_query: string;
}

interface ShoppingResult {
  session_id: string;
  status: string;
  user_query: string;
  search_results?: string;
  comparison?: string;
  recommendations?: string;
  user_preferences?: Record<string, any>;
  error?: string;
}

export default function PersonalShoppingDemo() {
  const [userQuery, setUserQuery] = useState('');
  const [budget, setBudget] = useState('');
  const [userId, setUserId] = useState('default');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [shoppingStatus, setShoppingStatus] = useState<ShoppingResponse | null>(null);
  const [shoppingResult, setShoppingResult] = useState<ShoppingResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userPreferences, setUserPreferences] = useState<Record<string, any>>({});

  const getRecommendations = async () => {
    if (!userQuery.trim()) {
      setError('Please enter a product query');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setShoppingResult(null);

    try {
      const request: ShoppingRequest = {
        user_query: userQuery.trim(),
        user_id: userId,
        budget: budget.trim() || undefined,
        preferences: Object.keys(userPreferences).length > 0 ? userPreferences : undefined
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/personal-shopping/get-recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to get recommendations');
      }

      const result: ShoppingResponse = await response.json();
      setSessionId(result.session_id);
      setShoppingStatus(result);
      
      // Start polling for status updates
      pollStatus(result.session_id);
    } catch (error) {
      console.error('Error getting recommendations:', error);
      setError(error instanceof Error ? error.message : 'Failed to get recommendations. Please try again.');
      setIsProcessing(false);
    }
  };

  const pollStatus = async (sessionId: string) => {
    const maxAttempts = 90;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/personal-shopping/status/${sessionId}`);
        
        if (!response.ok) {
          throw new Error('Failed to get status');
        }

        const status: ShoppingResponse = await response.json();
        setShoppingStatus(status);

        if (status.status === 'completed' || status.status === 'success') {
          // Get the final result
          const resultResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/personal-shopping/result/${sessionId}`);
          if (resultResponse.ok) {
            const result: ShoppingResult = await resultResponse.json();
            setShoppingResult(result);
            if (result.user_preferences) {
              setUserPreferences(result.user_preferences);
            }
          }
          setIsProcessing(false);
          return;
        }

        if (status.status === 'error') {
          setIsProcessing(false);
          setError(status.message || 'Recommendation generation failed');
          return;
        }

        attempts++;
        if (attempts < maxAttempts && (status.status === 'processing' || status.status === 'searching')) {
          setTimeout(poll, 2000);
        } else {
          setIsProcessing(false);
          setError('Recommendation generation timed out. Please try again.');
        }
      } catch (error) {
        console.error('Error polling status:', error);
        setIsProcessing(false);
        setError('Failed to check recommendation status');
      }
    };

    poll();
  };

  const loadPreferences = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/personal-shopping/preferences/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setUserPreferences(data.preferences || {});
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  useEffect(() => {
    loadPreferences();
  }, [userId]);

  const resetForm = () => {
    setUserQuery('');
    setBudget('');
    setSessionId(null);
    setShoppingStatus(null);
    setShoppingResult(null);
    setIsProcessing(false);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <ShoppingBagIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Personal Shopping Assistant
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            AI agent for personalized product recommendations
          </p>
          <Link
            href="/challenges/personal-shopping"
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
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Product Search</h2>
                  <p className="text-sm sm:text-base text-gray-600">Search for products with AI assistance</p>
                </div>
              </div>

            <div className="space-y-4 sm:space-y-6">
              {/* User ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  User ID (for memory)
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  disabled={isProcessing}
                />
                <p className="text-xs text-gray-500 mt-1">Used to remember your preferences</p>
              </div>

              {/* Product Query */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  What are you looking for? *
                </label>
                <input
                  type="text"
                  value={userQuery}
                  onChange={(e) => setUserQuery(e.target.value)}
                  placeholder="e.g., wireless headphones, gaming laptop, running shoes"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  disabled={isProcessing}
                />
              </div>

              {/* Budget */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Budget (optional)
                </label>
                <input
                  type="text"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="e.g., under $100, $200-$300"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  disabled={isProcessing}
                />
              </div>

              {/* User Preferences Display */}
              {Object.keys(userPreferences).length > 0 && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                    <HeartIcon className="h-4 w-4 text-blue-600 mr-2" />
                    Your Preferences
                  </h3>
                  <div className="text-sm text-gray-700 space-y-1">
                    {Object.entries(userPreferences).map(([key, value]) => (
                      <div key={key}>
                        <span className="font-medium">{key}:</span> {String(value)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4">
                <ProcessingButton
                  onClick={getRecommendations}
                  isProcessing={isProcessing}
                  disabled={!userQuery.trim()}
                  className="flex-1"
                >
                  {isProcessing ? 'Searching...' : 'Get Recommendations'}
                </ProcessingButton>
                {(shoppingResult || error) && (
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

            {/* Results Display */}
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <MagnifyingGlassIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Recommendations</h2>
                  <p className="text-sm sm:text-base text-gray-600">View personalized recommendations</p>
                </div>
              </div>

            {!shoppingStatus && !shoppingResult && (
              <div className="text-center py-12 text-gray-500">
                <ShoppingBagIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p>Enter a product query to get personalized recommendations</p>
              </div>
            )}

            {shoppingStatus && (
              <div className="mb-6">
                <StatusIndicator
                  status={shoppingStatus.status}
                  message={shoppingStatus.message}
                />
                {(shoppingStatus.status === 'processing' || shoppingStatus.status === 'searching') && (
                  <div className="mt-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      {shoppingStatus.status === 'searching' 
                        ? 'Product Search Agent finding products...'
                        : 'Shopping Assistant working...'}
                    </div>
                  </div>
                )}
              </div>
            )}

            {shoppingResult && shoppingResult.recommendations && (
              <div className="mt-6 space-y-4">
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                    <SparklesIcon className="h-5 w-5 text-green-600 mr-2" />
                    Personalized Recommendations
                  </h3>
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans bg-white p-4 rounded border">
                      {shoppingResult.recommendations}
                    </pre>
                  </div>
                </div>

                {shoppingResult.comparison && (
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Product Comparison</h3>
                    <div className="text-sm text-gray-700 whitespace-pre-wrap bg-white p-3 rounded border max-h-48 overflow-y-auto">
                      {shoppingResult.comparison.substring(0, 1000)}
                      {shoppingResult.comparison.length > 1000 && '...'}
                    </div>
                  </div>
                )}
              </div>
            )}

            {shoppingResult && shoppingResult.error && (
              <div className="mt-6">
                <AlertMessage type="error" message={shoppingResult.error} />
              </div>
            )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

