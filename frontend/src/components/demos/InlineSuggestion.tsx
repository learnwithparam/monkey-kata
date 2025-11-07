import { 
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

interface InlineSuggestionProps {
  type: 'recommendation' | 'warning' | 'info';
  content: string;
  riskScore?: number;
  onAccept?: () => void;
  onReject?: () => void;
}

export default function InlineSuggestion({
  type,
  content,
  riskScore,
  onAccept,
  onReject,
}: InlineSuggestionProps) {
  const getConfig = () => {
    switch (type) {
      case 'recommendation':
        if (riskScore && riskScore < 0.3) {
          return {
            icon: CheckCircleIcon,
            bgColor: 'bg-green-50',
            borderColor: 'border-green-300',
            iconColor: 'text-green-600',
            textColor: 'text-green-900',
            title: 'AI Recommendation: Approve',
            badge: 'Low Risk'
          };
        } else if (riskScore && riskScore < 0.6) {
          return {
            icon: ExclamationTriangleIcon,
            bgColor: 'bg-yellow-50',
            borderColor: 'border-yellow-300',
            iconColor: 'text-yellow-600',
            textColor: 'text-yellow-900',
            title: 'AI Recommendation: Review Carefully',
            badge: 'Medium Risk'
          };
        } else {
          return {
            icon: XCircleIcon,
            bgColor: 'bg-red-50',
            borderColor: 'border-red-300',
            iconColor: 'text-red-600',
            textColor: 'text-red-900',
            title: 'AI Recommendation: Reject',
            badge: 'High Risk'
          };
        }
      case 'warning':
        return {
          icon: ExclamationTriangleIcon,
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-300',
          iconColor: 'text-yellow-600',
          textColor: 'text-yellow-900',
          title: 'Warning',
          badge: null
        };
      default:
        return {
          icon: LightBulbIcon,
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-300',
          iconColor: 'text-blue-600',
          textColor: 'text-blue-900',
          title: 'Information',
          badge: null
        };
    }
  };

  const config = getConfig();
  const Icon = config.icon;

  return (
    <div className={`${config.bgColor} ${config.borderColor} border-2 rounded-lg p-4 relative`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`${config.iconColor} bg-white rounded-lg p-2 border-2 ${config.borderColor}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h4 className={`font-semibold ${config.textColor}`}>
              {config.title}
            </h4>
            {config.badge && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${config.iconColor} bg-white/50 mt-1 inline-block`}>
                {config.badge}
              </span>
            )}
          </div>
        </div>
        {onAccept && onReject && (
          <div className="flex gap-2">
            <button
              onClick={onAccept}
              className="p-1.5 rounded hover:bg-white/50 transition-colors"
              title="Accept suggestion"
            >
              <CheckCircleIcon className="w-4 h-4 text-green-600" />
            </button>
            <button
              onClick={onReject}
              className="p-1.5 rounded hover:bg-white/50 transition-colors"
              title="Dismiss suggestion"
            >
              <XCircleIcon className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className={`${config.textColor} text-sm leading-relaxed pl-12`}>
        {content}
      </div>

    </div>
  );
}

