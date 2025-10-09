'use client';

import { useState, useRef, useEffect } from 'react';
import { BookOpenIcon } from '@heroicons/react/24/outline';

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
  const [isGenerating, setIsGenerating] = useState(false);
  const [themes, setThemes] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [providerInfo, setProviderInfo] = useState<any>(null);
  const storyRef = useRef<HTMLDivElement>(null);

  // Load themes and provider info on component mount
  useEffect(() => {
    fetchThemes();
    fetchProviderInfo();
  }, []);

  const fetchThemes = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/bedtime-story/themes`);
      const data: StoryThemes = await response.json();
      setThemes(data.themes);
    } catch (err) {
      console.error('Failed to fetch themes:', err);
    }
  };

  const fetchProviderInfo = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      console.log('API URL:', apiUrl);
      const fullUrl = `${apiUrl}/bedtime-story/health`;
      console.log('Full URL:', fullUrl);
      
      const response = await fetch(fullUrl);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Provider info data:', data);
      setProviderInfo(data);
    } catch (err) {
      console.error('Failed to fetch provider info:', err);
      console.error('Error details:', {
        message: err.message,
        name: err.name,
        stack: err.stack
      });
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
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.content) {
                setStory(prev => prev + data.content);
                // Auto-scroll to bottom
                setTimeout(() => {
                  if (storyRef.current) {
                    storyRef.current.scrollTop = storyRef.current.scrollHeight;
                  }
                }, 100);
              } else if (data.done) {
                setIsGenerating(false);
                return;
              } else if (data.error) {
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
      <div className="max-w-7xl mx-auto container-padding section-padding">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-display text-gray-900 mb-6 flex items-center justify-center">
            <BookOpenIcon className="w-12 h-12 text-brand-purple mr-4" />
            Bedtime Story Generator
          </h1>
          <p className="text-body max-w-3xl mx-auto mb-8">
            Create personalized bedtime stories with AI. Enter character details and watch as your story comes to life in real-time.
          </p>
          
          {/* Provider Status */}
          {providerInfo && (
            <div className="inline-flex items-center px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-green-800">
                  Powered by: <strong>{providerInfo.llm_provider}</strong>
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="card p-8">
            <h2 className="text-headline text-gray-900 mb-8">Story Settings</h2>
            
            <div className="space-y-8">
              {/* Character Name */}
              <div>
                <label htmlFor="character_name" className="block text-sm font-semibold text-gray-900 mb-3">
                  Character Name *
                </label>
                <input
                  type="text"
                  id="character_name"
                  name="character_name"
                  value={formData.character_name}
                  onChange={handleInputChange}
                  placeholder="e.g., Emma, Alex, Luna"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus-ring text-gray-900 placeholder-gray-500"
                  disabled={isGenerating}
                />
              </div>

              {/* Character Age */}
              <div>
                <label htmlFor="character_age" className="block text-sm font-semibold text-gray-900 mb-3">
                  Character Age *
                </label>
                <select
                  id="character_age"
                  name="character_age"
                  value={formData.character_age}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus-ring text-gray-900 placeholder-gray-500"
                  disabled={isGenerating}
                >
                  {[3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(age => (
                    <option key={age} value={age}>{age} years old</option>
                  ))}
                </select>
              </div>

              {/* Story Theme */}
              <div>
                <label htmlFor="story_theme" className="block text-sm font-semibold text-gray-900 mb-3">
                  Story Theme *
                </label>
                <select
                  id="story_theme"
                  name="story_theme"
                  value={formData.story_theme}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus-ring text-gray-900 placeholder-gray-500"
                  disabled={isGenerating}
                >
                  <option value="">Select a theme...</option>
                  {themes.map(theme => (
                    <option key={theme} value={theme}>
                      {theme.charAt(0).toUpperCase() + theme.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Story Length */}
              <div>
                <label htmlFor="story_length" className="block text-sm font-semibold text-gray-900 mb-3">
                  Story Length
                </label>
                <select
                  id="story_length"
                  name="story_length"
                  value={formData.story_length}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus-ring text-gray-900 placeholder-gray-500"
                  disabled={isGenerating}
                >
                  <option value="short">Short (2-3 paragraphs)</option>
                  <option value="medium">Medium (4-6 paragraphs)</option>
                  <option value="long">Long (7-10 paragraphs)</option>
                </select>
              </div>

              {/* Generate Button */}
              <button
                onClick={generateStory}
                disabled={isGenerating || !formData.character_name.trim() || !formData.story_theme.trim()}
                className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Generating Story...
                  </span>
                ) : (
                  '✨ Generate Story'
                )}
              </button>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Story Display */}
          <div className="card p-8">
            <h2 className="text-headline text-gray-900 mb-8">Your Story</h2>
            
            <div 
              ref={storyRef}
              className="bg-gray-50 rounded-lg p-6 min-h-[500px]"
            >
              {story ? (
                <div className="prose prose-lg max-w-none">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap text-lg">
                    {story}
                  </p>
                  {isGenerating && (
                    <div className="flex items-center mt-4">
                      <div className="animate-pulse bg-brand-purple h-2 w-2 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-500">AI is writing...</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <div className="text-center">
                    <BookOpenIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-lg text-gray-600 mb-2">Your story will appear here</p>
                    <p className="text-sm text-gray-500">Fill in the details and click "Generate Story"</p>
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
