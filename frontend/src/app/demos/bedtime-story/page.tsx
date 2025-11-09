'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { BookOpenIcon } from '@heroicons/react/24/outline';
import CustomSelect from '@/components/CustomSelect';
import SubmitButton from '@/components/demos/SubmitButton';
import AlertMessage from '@/components/demos/AlertMessage';
import { normalizeSpacing } from '@/utils/textFormatting';

interface StoryRequest {
  character_name: string;
  character_age: number;
  story_theme: string;
  story_length: string;
}

interface StoryThemes {
  themes: string[];
}

export default function BedtimeStoryPage() {
  const [formData, setFormData] = useState<StoryRequest>({
    character_name: '',
    character_age: 5,
    story_theme: '',
    story_length: 'short'
  });
  
  const [story, setStory] = useState('');
  const [storyMetadata, setStoryMetadata] = useState<{title?: string; moral?: string} | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [themes, setThemes] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [isGeminiProvider, setIsGeminiProvider] = useState(false);

  // Load data on component mount
  useEffect(() => {
    fetchThemes();
    checkProvider();
  }, []);

  const checkProvider = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/bedtime-story/provider-info`);
      const data = await response.json();
      setIsGeminiProvider(data.provider_name === 'gemini');
    } catch (err) {
      console.error('Failed to check provider:', err);
    }
  };

  const fetchThemes = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/bedtime-story/themes`);
      const data: StoryThemes = await response.json();
      setThemes(data.themes);
    } catch (err) {
      console.error('Failed to fetch themes:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'character_age' ? parseInt(value) : value
    }));
  };

  const generateStory = async () => {
    if (!formData.character_name.trim() || !formData.story_theme.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    setIsGenerating(true);
    setStory('');
    setStoryMetadata(null);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/bedtime-story/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
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
              const data = JSON.parse(line.slice(6));

              // Handle connection status (ignore but don't break)
              if (data.status === 'connected') {
                // Connection established, continue processing
              }

              // Handle content streaming
              if (data.content) {
                setStory(prev => prev + data.content);
              }

              // Handle metadata
              if (data.metadata) {
                setStoryMetadata(data.metadata);
              }

              // Handle completion
              if (data.done) {
                setIsGenerating(false);
                return;
              }

              // Handle errors
              if (data.error) {
                throw new Error(data.error);
              }
            } catch (parseError) {
              console.error('Error parsing chunk:', parseError);
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate story');
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <BookOpenIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Bedtime Stories for Kids
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Create magical bedtime stories that adapt to your child&apos;s interests and age. Watch as AI brings their personalized adventure to life.
          </p>
            <Link
              href="/challenges/bedtime-story-generator"
              className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
            >
              View Learning Challenges
            </Link>
        </div>


        {/* Gemini Warning Banner */}
        {isGeminiProvider && (
          <div className="mb-6">
            <AlertMessage
              type="warning"
              message="Warning: Google Gemini is currently configured. This demo may not work properly due to Gemini's strict content safety filters. Please consider using a different provider (FireworksAI, OpenRouter, or OpenAI) for better results."
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 lg:gap-12">
          {/* Left Column - Form */}
          <div className="space-y-4 sm:space-y-6">
            <div className="card p-4 sm:p-6 lg:p-8">
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900">Story Settings</h2>
              </div>

              <div className="space-y-4 sm:space-y-6">
                {/* Character Name */}
                <div className="space-y-2">
                  <label htmlFor="character_name" className="block text-sm font-semibold text-gray-700">
                    Character Name *
                  </label>
                  <input
                    type="text"
                    id="character_name"
                    name="character_name"
                    value={formData.character_name}
                    onChange={handleInputChange}
                    placeholder="e.g., Emma, Alex, Luna"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                    disabled={isGenerating}
                  />
                </div>

                {/* Character Age & Theme Row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="character_age" className="block text-sm font-semibold text-gray-700">
                      Character Age *
                    </label>
                    <CustomSelect
                      id="character_age"
                      name="character_age"
                      value={formData.character_age.toString()}
                      onChange={(value) => setFormData(prev => ({ ...prev, character_age: parseInt(value) }))}
                      options={[3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(age => ({
                        value: age.toString(),
                        label: `${age} years old`
                      }))}
                      placeholder="Select age..."
                      disabled={isGenerating}
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="story_theme" className="block text-sm font-semibold text-gray-700">
                      Story Theme *
                    </label>
                    <CustomSelect
                      id="story_theme"
                      name="story_theme"
                      value={formData.story_theme}
                      onChange={(value) => setFormData(prev => ({ ...prev, story_theme: value }))}
                      options={themes.map(theme => ({
                        value: theme,
                        label: theme.charAt(0).toUpperCase() + theme.slice(1)
                      }))}
                      placeholder="Select theme..."
                      disabled={isGenerating}
                    />
                  </div>
                </div>

                {/* Story Length */}
                <div className="space-y-2">
                  <label htmlFor="story_length" className="block text-sm font-semibold text-gray-700">
                    Story Length
                  </label>
                  <CustomSelect
                    id="story_length"
                    name="story_length"
                    value={formData.story_length}
                    onChange={(value) => setFormData(prev => ({ ...prev, story_length: value }))}
                    options={[
                      { value: 'short', label: 'Short (2-3 paragraphs)' },
                      { value: 'medium', label: 'Medium (4-6 paragraphs)' },
                      { value: 'long', label: 'Long (7-10 paragraphs)' }
                    ]}
                    placeholder="Select length..."
                    disabled={isGenerating}
                  />
                </div>

                {/* Generate Button */}
                <SubmitButton
                  isLoading={isGenerating}
                  onClick={generateStory}
                  disabled={!formData.character_name.trim() || !formData.story_theme.trim()}
                >
                  <span className="flex items-center justify-center">
                    <span className="text-xl mr-3">✨</span>
                    Generate Story
                  </span>
                </SubmitButton>

                {/* Error Message */}
                {error && (
                  <AlertMessage
                    type="error"
                    message={error}
                  />
                )}
              </div>
            </div>

          </div>

          {/* Right Column - Story Display */}
          <div className="space-y-4 sm:space-y-6">
            <div className="card p-4 sm:p-6 lg:p-8 min-h-[500px] sm:min-h-[600px]">
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
                  <BookOpenIcon className="w-5 h-5 text-purple-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">Your Story</h2>
              </div>

                      {story ? (
                        <div className="space-y-6">
                          {storyMetadata && (
                            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                              {storyMetadata.title && (
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">{storyMetadata.title}</h3>
                              )}
                              {storyMetadata.moral && (
                                <p className="text-sm text-gray-600"><strong>Lesson:</strong> {storyMetadata.moral}</p>
                              )}
                            </div>
                          )}

                          <div className="prose prose-lg max-w-none">
                            <div
                              className="text-gray-800 leading-relaxed text-lg [&>p]:mb-4 [&>p:last-child]:mb-0"
                              dangerouslySetInnerHTML={{
                                __html: normalizeSpacing(story)
                                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                  .replace(/\*(.*?)\*/g, '<em>$1</em>')
                                  .replace(/\n\n+/g, '</p><p>')  // Handle multiple newlines
                                  .replace(/^\s*/, '<p>')       // Start with paragraph
                                  .replace(/\s*$/, '</p>')      // End with paragraph
                                  .replace(/<p><\/p>/g, '')     // Remove empty paragraphs
                              }}
                            />
                          </div>

                          {isGenerating && (
                            <div className="flex items-center p-4 bg-white rounded-lg border border-gray-200">
                              <div className="animate-pulse bg-green-500 h-3 w-3 rounded-full mr-3"></div>
                              <span className="text-sm text-gray-700 font-medium">AI is writing your story...</span>
                            </div>
                          )}
                        </div>
              ) : (
                <div className="flex items-center justify-center py-20 text-gray-500">
                  <div className="text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                      <BookOpenIcon className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-700 mb-3">Your story will appear here</h3>
                    <p className="text-gray-500 max-w-sm">Fill in the character details and click &quot;Generate Story&quot; to watch the magic happen</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}