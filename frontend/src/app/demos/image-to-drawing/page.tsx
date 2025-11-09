'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  PhotoIcon,
  DocumentArrowUpIcon,
} from '@heroicons/react/24/outline';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';
import FileUpload from '@/components/demos/FileUpload';

export default function ImageToDrawingPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [originalImageUrl, setOriginalImageUrl] = useState<string | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
      
      if (!allowedTypes.includes(file.type)) {
        alert('Please select a JPG, PNG, or WebP image file');
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
      setGeneratedImageUrl(null);
      
      const url = URL.createObjectURL(file);
      setOriginalImageUrl(url);
    }
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setGeneratedImageUrl(null);
    if (originalImageUrl) {
      URL.revokeObjectURL(originalImageUrl);
      setOriginalImageUrl(null);
    }
  };

  const generateColoringPage = async () => {
    if (!selectedFile) {
      alert('Please select an image to convert');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setGeneratedImageUrl(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/image-to-drawing/convert`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error('Failed to generate coloring page');
      }

      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      setGeneratedImageUrl(imageUrl);
      
    } catch (error) {
      console.error('Error generating coloring page:', error);
      let errorMessage = 'Failed to generate coloring page. Please try again.';
      
      if (error instanceof Error) {
        const errorStr = error.message;
        // Check if it's a learning challenge error
        if (errorStr.includes('Learning Challenge')) {
          errorMessage = errorStr;
        } else if (errorStr.includes('NotImplementedError') || errorStr.includes('not yet implemented')) {
          errorMessage = errorStr;
        } else {
          errorMessage = error.message;
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    return () => {
      if (originalImageUrl) URL.revokeObjectURL(originalImageUrl);
      if (generatedImageUrl) URL.revokeObjectURL(generatedImageUrl);
    };
  }, [originalImageUrl, generatedImageUrl]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <PhotoIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Image to Coloring Book Converter
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Upload a photo and convert it into a coloring book page. Perfect for creating printable coloring worksheets!
          </p>
          <Link
            href="/challenges/image-to-drawing"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            View Learning Challenges
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
          <div className="space-y-4 sm:space-y-6">
            <div className="card p-4 sm:p-6 lg:p-8">
              <div className="flex items-center mb-8">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                  <DocumentArrowUpIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Upload Image</h2>
                  <p className="text-sm text-gray-600">JPG, PNG, or WebP files supported</p>
                </div>
              </div>

              <div className="space-y-4">
                <FileUpload
                  selectedFile={selectedFile}
                  onFileSelect={handleFileSelect}
                  onFileRemove={handleFileRemove}
                  disabled={isGenerating}
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  placeholder="Drop your image here"
                  description="Supports JPG, PNG, and WebP files (max 10MB)"
                />

                <ProcessingButton
                  isLoading={isGenerating}
                  onClick={generateColoringPage}
                  disabled={!selectedFile}
                  icon={<PhotoIcon className="w-5 h-5 mr-3" />}
                >
                  Create Coloring Page
                </ProcessingButton>

                {error && (
                  <div className="space-y-2">
                    <AlertMessage
                      type={error.includes('Learning Challenge') ? 'info' : 'error'}
                      message={error}
                    />
                    {error.includes('Learning Challenge') && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                        <p className="font-semibold mb-2">💡 Tip:</p>
                        <p>This is a learning opportunity! Check the README for guidance on implementing image generation for other providers.</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4 sm:space-y-6">
            <div className="card p-4 sm:p-6 lg:p-8">
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                  <PhotoIcon className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Result</h2>
                  <p className="text-sm text-gray-500">Your coloring page will appear here</p>
                </div>
              </div>

              <div className="space-y-6">
                {originalImageUrl && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Original Image</h3>
                    <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                      <img
                        src={originalImageUrl}
                        alt="Original"
                        className="w-full h-auto max-h-96 object-contain"
                      />
                    </div>
                  </div>
                )}

                {generatedImageUrl ? (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Coloring Page</h3>
                    <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                      <img
                        src={generatedImageUrl}
                        alt="Coloring Page"
                        className="w-full h-auto max-h-96 object-contain"
                      />
                    </div>
                    <div className="mt-4">
                      <a
                        href={generatedImageUrl}
                        download={
                          selectedFile
                            ? (() => {
                                const originalName = selectedFile.name;
                                const nameWithoutExt = originalName.includes('.')
                                  ? originalName.substring(0, originalName.lastIndexOf('.'))
                                  : originalName;
                                return `${nameWithoutExt}-colorbook.png`;
                              })()
                            : 'coloring_page.png'
                        }
                        className="block w-full bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md text-center"
                      >
                        Download Coloring Page
                      </a>
                    </div>
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center bg-gray-50">
                    <PhotoIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-gray-500">
                      {isGenerating 
                        ? 'Creating your coloring page...' 
                        : 'Upload an image and click "Create Coloring Page" to see the result here.'}
                    </p>
                    {isGenerating && (
                      <div className="mt-4">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            This demo uses basic image processing to convert photos into coloring book pages.
            <br />
            Perfect for creating printable coloring worksheets!
          </p>
        </div>
      </div>
    </div>
  );
}
