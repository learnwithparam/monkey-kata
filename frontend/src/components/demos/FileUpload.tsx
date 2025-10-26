'use client';

import { useRef } from 'react';
import { DocumentArrowUpIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface FileUploadProps {
  selectedFile: File | null;
  onFileSelect: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onFileRemove: () => void;
  accept?: string;
  disabled?: boolean;
  placeholder?: string;
  description?: string;
}

export default function FileUpload({
  selectedFile,
  onFileSelect,
  onFileRemove,
  accept = ".pdf,.doc,.docx,.txt",
  disabled = false,
  placeholder = "Drop your document here",
  description = "Supports PDF, Word, and text files (max 10MB)"
}: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.add('border-blue-400', 'bg-blue-50');
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelect({ target: { files } } as React.ChangeEvent<HTMLInputElement>);
    }
  };

  return (
    <div>
      <label htmlFor="file" className="block text-sm font-semibold text-gray-700 mb-2">
        Document *
      </label>
      
      {/* Drag and Drop Area */}
      <div 
        className={`relative border-2 border-dashed rounded-lg p-4 sm:p-6 text-center transition-colors ${
          selectedFile 
            ? 'border-gray-300 bg-gray-50' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          id="file"
          accept={accept}
          onChange={onFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={disabled}
        />
        
        <div className="space-y-2">
          <DocumentArrowUpIcon className="w-6 h-6 sm:w-8 sm:h-8 text-gray-400 mx-auto" />
          <div>
            <p className="text-sm font-medium text-gray-900">
              {placeholder}
            </p>
            <p className="text-xs text-gray-500">
              or click to browse files
            </p>
          </div>
          <p className="text-xs text-gray-400">
            {description}
          </p>
        </div>
      </div>

      {/* Selected File Display */}
      {selectedFile && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm mt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={onFileRemove}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={disabled}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
