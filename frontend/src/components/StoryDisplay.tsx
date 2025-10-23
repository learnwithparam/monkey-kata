'use client';

import { BookOpenIcon } from '@heroicons/react/24/outline';

interface StoryDisplayProps {
  story: string;
  storyMetadata: { title?: string; moral?: string; tags?: string[] } | null;
  isGenerating: boolean;
  generationLogs: string[];
}

export default function StoryDisplay({
  story,
  storyMetadata,
  isGenerating,
  generationLogs
}: StoryDisplayProps) {
  return (
    <>
      {/* Generation Logs */}
      {generationLogs.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Generation Progress</h3>
          <div className="space-y-2">
            {generationLogs.map((log, index) => (
              <div key={index} className="flex items-center text-sm text-gray-600">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                {log}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Story Display */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Your Story</h2>

        {story ? (
          <div className="space-y-6">
            {storyMetadata && (
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{storyMetadata.title}</h3>
                {storyMetadata.moral && (
                  <p className="text-sm text-gray-600 mb-2"><strong>Lesson:</strong> {storyMetadata.moral}</p>
                )}
                {storyMetadata.tags && storyMetadata.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {storyMetadata.tags.map((tag: string, index: number) => (
                      <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            <div className="prose prose-lg max-w-none">
              <div 
                className="text-gray-800 leading-relaxed text-lg"
                dangerouslySetInnerHTML={{ 
                  __html: story
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/\n\n/g, '</p><p>')
                    .replace(/^/, '<p>')
                    .replace(/$/, '</p>')
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
          <div className="flex items-center justify-center py-16 text-gray-500">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <BookOpenIcon className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Your story will appear here</h3>
              <p className="text-gray-500">Fill in the details and click &quot;Generate Story&quot; to begin</p>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
