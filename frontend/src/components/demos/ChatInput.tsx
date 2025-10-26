import { PaperAirplaneIcon, ClockIcon } from '@heroicons/react/24/outline';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
  disabled: boolean;
  isLoading: boolean;
  placeholder?: string;
}

export default function ChatInput({ 
  value, 
  onChange, 
  onSend, 
  onKeyPress, 
  disabled, 
  isLoading, 
  placeholder = "Ask me anything about our services..." 
}: ChatInputProps) {
  return (
    <div className="relative">
      <div className="flex items-center space-x-2 sm:space-x-3 bg-white border border-gray-200 rounded-xl px-3 sm:px-4 py-2 sm:py-3 shadow-sm hover:shadow-md transition-all duration-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
        <div className="flex-shrink-0">
          <div className="w-7 h-7 sm:w-8 sm:h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-blue-600 text-xs sm:text-sm font-semibold">U</span>
          </div>
        </div>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder={placeholder}
          className="flex-1 bg-transparent border-none outline-none text-gray-900 placeholder-gray-500 text-sm sm:text-sm min-w-0"
          disabled={disabled}
        />
        <button
          onClick={onSend}
          disabled={isLoading || !value.trim() || disabled}
          className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
        >
          {isLoading ? (
            <ClockIcon className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
          ) : (
            <PaperAirplaneIcon className="w-4 h-4 sm:w-5 sm:h-5" />
          )}
        </button>
      </div>
    </div>
  );
}
