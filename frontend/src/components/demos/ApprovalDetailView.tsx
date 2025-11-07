import { 
  CheckCircleIcon,
  XCircleIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  UserIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { Approval } from './ApprovalList';
import InlineSuggestion from './InlineSuggestion';

interface ApprovalDetailViewProps {
  approval: Approval;
  reviewNotes: string;
  onReviewNotesChange: (notes: string) => void;
  onApprove: () => void;
  onReject: () => void;
  isReviewing: boolean;
}

export default function ApprovalDetailView({
  approval,
  reviewNotes,
  onReviewNotesChange,
  onApprove,
  onReject,
  isReviewing,
}: ApprovalDetailViewProps) {
  const riskLevel = approval.risk_score < 0.3 ? 'Low' : approval.risk_score < 0.6 ? 'Medium' : 'High';
  const riskBadgeClass = approval.risk_score < 0.3 
    ? 'bg-green-50 border-green-200 text-green-700' 
    : approval.risk_score < 0.6 
    ? 'bg-yellow-50 border-yellow-200 text-yellow-700' 
    : 'bg-red-50 border-red-200 text-red-700';

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center border border-blue-200">
              <UserIcon className="w-7 h-7 text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{approval.applicant_name}</h2>
              <p className="text-sm text-gray-500">Application #{approval.application_id}</p>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-lg border ${riskBadgeClass}`}>
            <span className="text-sm font-semibold">{riskLevel} Risk</span>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {/* Application Summary */}
        <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <DocumentTextIcon className="w-5 h-5" />
            Application Summary
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <CurrencyDollarIcon className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-600">Loan Amount</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                ${approval.loan_amount.toLocaleString()}
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <ChartBarIcon className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-600">Risk Score</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {approval.risk_score.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        {/* AI Analysis with Inline Suggestions */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <ChartBarIcon className="w-5 h-5" />
            AI Analysis & Recommendations
          </h3>
          
          <InlineSuggestion
            type="recommendation"
            content={approval.recommendation}
            riskScore={approval.risk_score}
          />

          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-3">
              <ClockIcon className="w-5 h-5 text-gray-400" />
              <span className="text-sm font-semibold text-gray-700">Detailed Analysis</span>
            </div>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-x-auto">
              {approval.ai_analysis}
            </pre>
          </div>
        </div>

        {/* Review Section */}
        <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Your Review</h3>
          <textarea
            value={reviewNotes}
            onChange={(e) => onReviewNotesChange(e.target.value)}
            placeholder="Add your review notes, concerns, or additional context..."
            className="w-full p-4 border-2 border-blue-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white resize-none"
            rows={5}
          />
          <p className="text-xs text-blue-700 mt-2">
            Your notes will be saved with the decision for audit purposes.
          </p>
        </div>
      </div>

      {/* Action Buttons - Fixed at Bottom */}
      <div className="border-t border-gray-200 pt-4 mt-6 flex gap-3">
        <button
          onClick={onReject}
          disabled={isReviewing}
          className="flex-1 flex items-center justify-center gap-2 bg-red-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
        >
          <XCircleIcon className="w-5 h-5" />
          {isReviewing ? 'Processing...' : 'Reject Application'}
        </button>
        <button
          onClick={onApprove}
          disabled={isReviewing}
          className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
        >
          <CheckCircleIcon className="w-5 h-5" />
          {isReviewing ? 'Processing...' : 'Approve Application'}
        </button>
      </div>
    </div>
  );
}

