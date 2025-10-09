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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/bedtime-story/health`);
      const data = await response.json();
      setProviderInfo(data);
    } catch (err) {
      console.error('Failed to fetch provider info:', err);
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
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4 flex items-center justify-center">
              <BookOpenIcon className="w-10 h-10 text-purple-600 mr-3" />
              Bedtime Story Generator
            </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-4">
            Create magical bedtime stories with AI. Perfect for teaching streaming responses, 
            prompt engineering, and real-time UI updates.
          </p>
          
          {/* Provider Status */}
          {providerInfo && (
            <div className="inline-flex items-center px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-blue-800">
                  Powered by: <strong>{providerInfo.llm_provider}</strong>
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Story Settings</h2>
            
            <div className="space-y-6">
              {/* Character Name */}
              <div>
                <label htmlFor="character_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Character Name *
                </label>
                <input
                  type="text"
                  id="character_name"
                  name="character_name"
                  value={formData.character_name}
                  onChange={handleInputChange}
                  placeholder="e.g., Emma, Alex, Luna"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={isGenerating}
                />
              </div>

              {/* Character Age */}
              <div>
                <label htmlFor="character_age" className="block text-sm font-medium text-gray-700 mb-2">
                  Character Age *
                </label>
                <select
                  id="character_age"
                  name="character_age"
                  value={formData.character_age}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={isGenerating}
                >
                  {[3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(age => (
                    <option key={age} value={age}>{age} years old</option>
                  ))}
                </select>
              </div>

              {/* Story Theme */}
              <div>
                <label htmlFor="story_theme" className="block text-sm font-medium text-gray-700 mb-2">
                  Story Theme *
                </label>
                <select
                  id="story_theme"
                  name="story_theme"
                  value={formData.story_theme}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                <label htmlFor="story_length" className="block text-sm font-medium text-gray-700 mb-2">
                  Story Length
                </label>
                <select
                  id="story_length"
                  name="story_length"
                  value={formData.story_length}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
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
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Story Display */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Story</h2>
            
            <div 
              ref={storyRef}
              className="bg-gray-50 rounded-lg p-6 min-h-[400px] max-h-[600px] overflow-y-auto"
            >
              {story ? (
                <div className="prose prose-lg max-w-none">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {story}
                  </p>
                  {isGenerating && (
                    <div className="flex items-center mt-4">
                      <div className="animate-pulse bg-purple-500 h-2 w-2 rounded-full mr-2"></div>
                      <span className="text-sm text-gray-500">AI is writing...</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <div className="text-center">
                    <div className="text-6xl mb-4">📖</div>
                    <p className="text-lg">Your magical story will appear here...</p>
                    <p className="text-sm mt-2">Fill in the form and click "Generate Story"</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Learning Notes */}
        <div className="mt-12 bg-blue-50 rounded-xl p-6">
          <h3 className="text-xl font-bold text-blue-900 mb-4">🎓 What You're Learning</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-blue-800 mb-2">Backend Concepts:</h4>
              <ul className="text-blue-700 space-y-1 text-sm">
                <li>• Streaming responses with FastAPI</li>
                <li>• Prompt engineering techniques</li>
                <li>• Error handling and validation</li>
                <li>• Async/await patterns</li>
                <li>• Multi-provider LLM integration</li>
                <li>• Factory pattern for providers</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-blue-800 mb-2">Frontend Concepts:</h4>
              <ul className="text-blue-700 space-y-1 text-sm">
                <li>• Real-time UI updates</li>
                <li>• Stream processing</li>
                <li>• Form validation</li>
                <li>• Loading states</li>
                <li>• Error handling</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
