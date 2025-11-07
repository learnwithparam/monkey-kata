import { ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline';
import { Approval } from './ApprovalList';

interface ApprovalReviewPanelProps {
  approval: Approval | null;
  reviewNotes: string;
  onReviewNotesChange: (notes: string) => void;
  onReview: (decision: 'approve' | 'reject') => void;
  onRequestMoreInfo?: () => void;
  isReviewing: boolean;
}

export default function ApprovalReviewPanel({
  approval,
  reviewNotes,
  onReviewNotesChange,
  onReview,
  onRequestMoreInfo,
  isReviewing,
}: ApprovalReviewPanelProps) {
  if (!approval) {
    return (
      <div className="flex-1 flex items-center justify-center text-center py-12">
        <div className="max-w-sm">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-2xl mb-4">
            <ClipboardDocumentCheckIcon className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-sm font-medium text-gray-700 mb-1">
            No application selected
          </p>
          <p className="text-xs text-gray-500">
            Select an approval from the left to review details and make a decision
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Application Details</h3>
          <div className="bg-gray-50 rounded-lg p-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Applicant:</span>
              <span className="font-medium">{approval.applicant_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Loan Amount:</span>
              <span className="font-medium">${approval.loan_amount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Risk Score:</span>
              <span className="font-medium">{approval.risk_score.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className="font-medium">{approval.status}</span>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">AI Recommendation</h3>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-900">{approval.recommendation}</p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">AI Analysis</h3>
          <div className="bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
              {approval.ai_analysis}
            </pre>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Review Notes</h3>
          <textarea
            value={reviewNotes}
            onChange={(e) => onReviewNotesChange(e.target.value)}
            placeholder="Add your review notes..."
            className="w-full p-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={4}
          />
        </div>

        <div className="space-y-3 pt-4 border-t border-gray-200">
          {onRequestMoreInfo && approval.status === 'pending' && (
            <button
              onClick={onRequestMoreInfo}
              disabled={isReviewing}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Request More Information
            </button>
          )}
          {approval.status === 'needs_more_info' && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                <strong>More information requested.</strong> Use the chat interface to collect additional details from the applicant.
              </p>
            </div>
          )}
          <div className="flex space-x-3">
            <button
              onClick={() => onReview('approve')}
              disabled={isReviewing}
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isReviewing ? 'Processing...' : 'Approve'}
            </button>
            <button
              onClick={() => onReview('reject')}
              disabled={isReviewing}
              className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isReviewing ? 'Processing...' : 'Reject'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

