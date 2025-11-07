'use client';

import CustomSelect from './CustomSelect';

interface StoryRequest {
  character_name: string;
  character_age: number;
  story_theme: string;
  story_length: string;
  prompt_technique: string;
  template_name?: string;
}

interface PromptTechnique {
  id: string;
  name: string;
  description: string;
  use_case: string;
}

interface PromptTemplate {
  name: string;
  label?: string;
  description: string;
  variables: string[];
  use_case: string;
}

interface StoryFormProps {
  formData: StoryRequest;
  setFormData: React.Dispatch<React.SetStateAction<StoryRequest>>;
  themes: string[];
  promptTechniques: PromptTechnique[];
  promptTemplates: PromptTemplate[];
  isGenerating: boolean;
  showAdvanced: boolean;
  setShowAdvanced: React.Dispatch<React.SetStateAction<boolean>>;
  error: string;
  onGenerate: () => void;
}

export default function StoryForm({
  formData,
  setFormData,
  themes,
  promptTechniques,
  promptTemplates,
  isGenerating,
  showAdvanced,
  setShowAdvanced,
  error,
  onGenerate
}: StoryFormProps) {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTechniqueChange = (technique: string) => {
    setFormData(prev => ({
      ...prev,
      prompt_technique: technique,
      template_name: undefined
    }));
  };

  const handleTemplateChange = (template: string) => {
    setFormData(prev => ({
      ...prev,
      template_name: template === '' ? undefined : template
    }));
  };

  return (
    <div className="card p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Story Settings</h2>
      
      <div className="space-y-6">
        {/* Character Name */}
        <div className="space-y-2">
          <label htmlFor="character_name" className="block text-sm font-medium text-gray-700">
            Character Name *
          </label>
          <input
            type="text"
            id="character_name"
            name="character_name"
            value={formData.character_name}
            onChange={handleInputChange}
            placeholder="e.g., Emma, Alex, Luna"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
            disabled={isGenerating}
          />
        </div>

        {/* Character Age */}
        <div className="space-y-2">
          <label htmlFor="character_age" className="block text-sm font-medium text-gray-700">
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

        {/* Story Theme */}
        <div className="space-y-2">
          <label htmlFor="story_theme" className="block text-sm font-medium text-gray-700">
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
            placeholder="Select a theme..."
            disabled={isGenerating}
          />
        </div>

        {/* Story Length */}
        <div className="space-y-2">
          <label htmlFor="story_length" className="block text-sm font-medium text-gray-700">
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

        {/* Advanced Options Toggle */}
        <div className="pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full p-3 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 group"
            disabled={isGenerating}
          >
            <span className="flex items-center text-sm font-medium text-gray-700 group-hover:text-gray-900">
              <svg 
                className={`w-4 h-4 mr-2 transition-transform duration-200 ${showAdvanced ? 'rotate-90' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Advanced Options
            </span>
            <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded-md border">
              {showAdvanced ? 'Hide' : 'Show'}
            </span>
          </button>
        </div>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="space-y-4 pt-4">
            {/* Prompt Technique */}
            <div className="space-y-2">
              <label htmlFor="prompt_technique" className="block text-sm font-medium text-gray-700">
                Prompt Engineering Technique
              </label>
              <CustomSelect
                id="prompt_technique"
                name="prompt_technique"
                value={formData.prompt_technique}
                onChange={handleTechniqueChange}
                options={promptTechniques.map(technique => ({
                  value: technique.id,
                  label: technique.name
                }))}
                placeholder="Select technique..."
                disabled={isGenerating}
              />
              {promptTechniques.find(t => t.id === formData.prompt_technique) && (
                <p className="text-xs text-gray-500 mt-1">
                  {promptTechniques.find(t => t.id === formData.prompt_technique)?.description}
                </p>
              )}
            </div>

            {/* Prompt Template (only for template-based technique) */}
            {formData.prompt_technique === 'template_based' && (
              <div className="space-y-2">
                <label htmlFor="template_name" className="block text-sm font-medium text-gray-700">
                  Prompt Template
                </label>
                <CustomSelect
                  id="template_name"
                  name="template_name"
                  value={formData.template_name || ''}
                  onChange={handleTemplateChange}
                  options={promptTemplates.map(template => ({
                    value: template.name,
                    label: template.label || template.name
                  }))}
                  placeholder="Select a template (optional)..."
                  disabled={isGenerating}
                />
                {formData.template_name && promptTemplates.find(t => t.name === formData.template_name) && (
                  <p className="text-xs text-gray-500 mt-1">
                    {promptTemplates.find(t => t.name === formData.template_name)?.description}
                  </p>
                )}
              </div>
            )}

            {/* Technique Explanation */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <h4 className="text-xs font-medium text-gray-700 mb-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                About {promptTechniques.find(t => t.id === formData.prompt_technique)?.name}
              </h4>
              <p className="text-xs text-gray-600 leading-relaxed">
                {promptTechniques.find(t => t.id === formData.prompt_technique)?.use_case}
              </p>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={onGenerate}
          disabled={isGenerating || !formData.character_name.trim() || !formData.story_theme.trim()}
          className="w-full btn-accent disabled:opacity-50 disabled:cursor-not-allowed"
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
            <span className="flex items-center justify-center">
              <span className="text-lg mr-2">✨</span>
              Generate Story
            </span>
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
  );
}
