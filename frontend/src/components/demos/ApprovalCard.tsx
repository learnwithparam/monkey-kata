import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  UserIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { Approval } from './ApprovalList';

interface ApprovalCardProps {
  approval: Approval;
  onSelect: (approval: Approval) => void;
  isSelected?: boolean;
}

export default function ApprovalCard({ approval, onSelect, isSelected }: ApprovalCardProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'approved':
        return {
          icon: CheckCircleIcon,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          label: 'Approved'
        };
      case 'rejected':
        return {
          icon: XCircleIcon,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          label: 'Rejected'
        };
      default:
        return {
          icon: ClockIcon,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          label: 'Pending Review'
        };
    }
  };

  const statusConfig = getStatusConfig(approval.status);
  const StatusIcon = statusConfig.icon;
  const riskLevel = approval.risk_score < 0.3 ? 'Low' : approval.risk_score < 0.6 ? 'Medium' : 'High';
  const riskColor = approval.risk_score < 0.3 ? 'text-green-600' : approval.risk_score < 0.6 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div
      onClick={() => onSelect(approval)}
      className={`
        relative p-5 rounded-xl border transition-all duration-200 cursor-pointer
        ${isSelected 
          ? 'border-blue-500 bg-blue-50 shadow-md' 
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
        }
      `}
    >
      {/* Status Badge */}
      <div className={`absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 rounded-full ${statusConfig.bgColor} ${statusConfig.borderColor} border`}>
        <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
        <span className={`text-xs font-semibold ${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </div>

      {/* Header */}
      <div className="pr-24 mb-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center border border-blue-200">
            <UserIcon className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">{approval.applicant_name}</h3>
            <p className="text-xs text-gray-500">Application #{approval.application_id}</p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <CurrencyDollarIcon className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-600">Loan Amount</span>
          </div>
          <p className="text-lg font-bold text-gray-900">
            ${approval.loan_amount.toLocaleString()}
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <ChartBarIcon className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-600">Risk Score</span>
          </div>
          <p className={`text-lg font-bold ${riskColor}`}>
            {approval.risk_score.toFixed(2)}
            <span className="text-xs font-normal text-gray-600 ml-1">({riskLevel})</span>
          </p>
        </div>
      </div>

      {/* Recommendation Preview */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs font-semibold text-blue-900 mb-1">AI Recommendation</p>
        <p className="text-sm text-blue-800 line-clamp-2">
          {approval.recommendation}
        </p>
      </div>

      {/* Timestamp */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Created {new Date(approval.created_at).toLocaleDateString()} at{' '}
          {new Date(approval.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}

