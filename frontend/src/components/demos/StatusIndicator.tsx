import { 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

interface StatusIndicatorProps {
  status: string;
  message: string;
  progress?: number;
  documentsCount?: number;
}

export default function StatusIndicator({ status, message, progress, documentsCount }: StatusIndicatorProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-blue-500 animate-spin" />;
    }
  };

  return (
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          {message}
        </span>
        <div className="flex items-center">
          {getStatusIcon()}
          <span className="text-sm text-gray-600 ml-2">
            {status}
          </span>
        </div>
      </div>
      
      {status === 'processing' && progress !== undefined && (
        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {documentsCount && documentsCount > 0 && (
        <p className="text-sm text-gray-600">
          {message}
          <span className="ml-2 text-green-600">
            ({documentsCount} chunks)
          </span>
        </p>
      )}
    </div>
  );
}
