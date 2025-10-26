interface MessageBubbleProps {
  message: string;
  isUser: boolean;
  timestamp?: string;
}

export default function MessageBubble({ message, isUser, timestamp }: MessageBubbleProps) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[85%] sm:max-w-xs lg:max-w-md px-3 sm:px-4 py-2 sm:py-3 rounded-xl shadow-sm ${
        isUser 
          ? 'bg-blue-600 text-white rounded-br-md' 
          : 'bg-white text-gray-900 border border-gray-200 rounded-bl-md'
      }`}>
        <p className="text-sm sm:text-sm leading-relaxed break-words">{message}</p>
        {timestamp && (
          <p className={`text-xs mt-2 ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          }`}>
            {timestamp}
          </p>
        )}
      </div>
    </div>
  );
}
