'use client';

import { useState, useEffect } from 'react';
import { 
  UserGroupIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  SparklesIcon,
  ArrowPathIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';

interface InfluencerProfile {
  username: string;
  profile_url: string;
  follower_count?: number;
  bio?: string;
  content_focus?: string;
  has_own_platform?: boolean;
  collaboration_potential?: string;
  location?: string;
}

interface DiscoveryRequest {
  min_followers: number;
  max_followers?: number;
  content_keywords: string[];
  location: string;
  count: number;
}

interface DiscoveryResponse {
  session_id: string;
  status: string;
  message: string;
  criteria: DiscoveryRequest;
}

interface DiscoveryResult {
  session_id: string;
  status: string;
  influencers: InfluencerProfile[];
  total_found: number;
  completed_at?: string;
  error?: string;
}

export default function InfluencerDiscoveryDemo() {
  const [minFollowers, setMinFollowers] = useState<number | ''>('');
  const [maxFollowers, setMaxFollowers] = useState<number | ''>('');
  const [contentKeywords, setContentKeywords] = useState('');
  const [location, setLocation] = useState('');
  const [count, setCount] = useState<number | ''>('');
  
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [influencers, setInfluencers] = useState<InfluencerProfile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [isComplete, setIsComplete] = useState(false);

  const startDiscovery = async () => {
    // Validate inputs
    if (minFollowers === '' || minFollowers < 1000) {
      setError('Minimum followers must be at least 1,000');
      return;
    }
    
    if (maxFollowers !== '' && maxFollowers < minFollowers) {
      setError('Maximum followers must be greater than minimum followers');
      return;
    }
    
    if (count === '' || count < 1 || count > 10) {
      setError('Count must be between 1 and 10');
      return;
    }

    if (!location.trim()) {
      setError('Please enter a location');
      return;
    }

    const keywordsList = contentKeywords
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0);

    if (keywordsList.length === 0) {
      setError('Please enter at least one content keyword');
      return;
    }

    setIsDiscovering(true);
    setError(null);
    setInfluencers([]);
    setProgressMessages([]);
    setIsComplete(false);

    try {
      const request: DiscoveryRequest = {
        min_followers: minFollowers as number,
        max_followers: maxFollowers === '' ? undefined : (maxFollowers as number),
        content_keywords: keywordsList,
        location: location.trim(),
        count: count as number,
      };

      // Start discovery
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/influencer-discovery/start-discovery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to start discovery');
      }

      const data: DiscoveryResponse = await response.json();
      setSessionId(data.session_id);
      setProgressMessages([data.message]);

      // Start streaming progress
      streamDiscoveryProgress(data.session_id);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start discovery');
      setIsDiscovering(false);
    }
  };

  const streamDiscoveryProgress = async (sessionId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/influencer-discovery/stream/${sessionId}`
      );

      if (!response.ok) {
        throw new Error('Failed to stream progress');
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

              const data = JSON.parse(jsonStr);

              if (data.message) {
                setProgressMessages(prev => [...prev, data.message]);
              }

              if (data.status === 'completed') {
                setInfluencers(data.influencers || []);
                setIsComplete(true);
                setIsDiscovering(false);
                return;
              }

              if (data.status === 'error') {
                setError(data.error || 'Discovery failed');
                setIsDiscovering(false);
                return;
              }
            } catch (parseErr) {
              console.warn('Failed to parse progress data:', parseErr);
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stream progress');
      setIsDiscovering(false);
    }
  };

  const resetForm = () => {
    setMinFollowers('');
    setMaxFollowers('');
    setContentKeywords('');
    setLocation('');
    setCount('');
    setSessionId(null);
    setInfluencers([]);
    setError(null);
    setProgressMessages([]);
    setIsComplete(false);
    setIsDiscovering(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center">
              <UserGroupIcon className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
            Influencer Discovery Agent
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Use AI to find Indian Instagram influencers who can collaborate with your platform.
            The agent searches the web, analyzes profiles, and finds the perfect matches.
          </p>
        </div>

        {/* Discovery Form */}
        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200 mb-6">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
              <MagnifyingGlassIcon className="w-6 h-6 text-gray-600" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Discovery Criteria</h2>
              <p className="text-sm sm:text-base text-gray-600">Set your requirements for finding influencers</p>
            </div>
          </div>

          <div className="space-y-6">
            {/* Minimum Followers */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Minimum Followers <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={minFollowers}
                onChange={(e) => setMinFollowers(e.target.value === '' ? '' : parseInt(e.target.value) || '')}
                min={1000}
                placeholder="e.g., 10000"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                disabled={isDiscovering}
              />
              <p className="text-xs text-gray-500 mt-1">Minimum number of followers required (at least 1,000)</p>
            </div>

            {/* Maximum Followers */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Maximum Followers <span className="text-gray-400">(Optional)</span>
              </label>
              <input
                type="number"
                value={maxFollowers}
                onChange={(e) => setMaxFollowers(e.target.value === '' ? '' : parseInt(e.target.value) || '')}
                min={minFollowers !== '' ? minFollowers : undefined}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="e.g., 100000 (leave empty for no limit)"
                disabled={isDiscovering}
              />
              <p className="text-xs text-gray-500 mt-1">Maximum number of followers (leave empty for no limit)</p>
            </div>

            {/* Content Keywords */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Content Keywords <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={contentKeywords}
                onChange={(e) => setContentKeywords(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="e.g., AI, tech, technology, machine learning"
                disabled={isDiscovering}
              />
              <p className="text-xs text-gray-500 mt-1">Comma-separated keywords describing the content focus</p>
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Location <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="e.g., India, United States, UK"
                disabled={isDiscovering}
              />
              <p className="text-xs text-gray-500 mt-1">Target location for influencer search</p>
            </div>

            {/* Count */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Number of Influencers <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={count}
                onChange={(e) => setCount(e.target.value === '' ? '' : parseInt(e.target.value) || '')}
                min={1}
                max={10}
                placeholder="e.g., 5"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                disabled={isDiscovering}
              />
              <p className="text-xs text-gray-500 mt-1">Number of influencers to find (1-10)</p>
            </div>

            {/* Error Message */}
            {error && (
              <AlertMessage
                type="error"
                message={error}
                onClose={() => setError(null)}
              />
            )}

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <ProcessingButton
                onClick={startDiscovery}
                isLoading={isDiscovering}
                disabled={isDiscovering}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDiscovering ? 'Discovering Influencers...' : (
                  <>
                    <SparklesIcon className="w-5 h-5 mr-2 inline" />
                    Start Discovery
                  </>
                )}
              </ProcessingButton>
              <button
                onClick={resetForm}
                className="px-6 py-3 bg-gray-100 text-gray-700 font-semibold rounded-lg hover:bg-gray-200 transition-colors"
                disabled={isDiscovering}
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Progress Messages */}
        {progressMessages.length > 0 && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-6">
            <div className="flex items-center mb-4">
              <ArrowPathIcon className={`w-5 h-5 text-green-600 mr-2 ${isDiscovering ? 'animate-spin' : ''}`} />
              <h3 className="text-lg font-semibold text-gray-900">Discovery Progress</h3>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {progressMessages.map((msg, idx) => (
                <div key={idx} className="text-sm text-gray-600 p-2 bg-gray-50 rounded">
                  {msg}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {isComplete && influencers.length > 0 && (
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                  <CheckCircleIcon className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
                    Found {influencers.length} Influencer{influencers.length !== 1 ? 's' : ''}
                  </h2>
                  <p className="text-sm sm:text-base text-gray-600">Matching your criteria</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              {influencers.map((influencer, idx) => (
                <div
                  key={idx}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          @{influencer.username}
                        </h3>
                        {influencer.follower_count && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            {influencer.follower_count.toLocaleString()} followers
                          </span>
                        )}
                      </div>
                      
                      {influencer.bio && (
                        <p className="text-sm text-gray-600 mb-2">{influencer.bio}</p>
                      )}
                      
                      {influencer.content_focus && (
                        <p className="text-xs text-gray-500 mb-2">
                          <span className="font-medium">Focus:</span> {influencer.content_focus}
                        </p>
                      )}
                      
                      {influencer.collaboration_potential && (
                        <p className="text-xs text-green-700 mb-2">
                          <span className="font-medium">Potential:</span> {influencer.collaboration_potential}
                        </p>
                      )}
                      
                      {influencer.location && (
                        <p className="text-xs text-gray-500">
                          <span className="font-medium">Location:</span> {influencer.location}
                        </p>
                      )}
                    </div>
                    
                    <a
                      href={influencer.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors inline-flex items-center"
                    >
                      <LinkIcon className="w-4 h-4 mr-1" />
                      View Profile
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {isComplete && influencers.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
            <p className="text-yellow-800">
              No influencers found matching your criteria. Try adjusting your search parameters.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

