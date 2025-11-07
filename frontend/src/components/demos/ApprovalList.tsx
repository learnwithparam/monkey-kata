import { ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline';

export interface Approval {
  approval_id: string;
  application_id: string;
  applicant_name: string;
  loan_amount: number;
  recommendation: string;
  risk_score: number;
  status: 'pending' | 'approved' | 'rejected' | 'needs_revision' | 'needs_more_info';
  ai_analysis: string;
  created_at: string;
  reviewed_at?: string;
  reviewer_notes?: string;
}

interface ApprovalListProps {
  approvals: Approval[];
  selectedApproval: Approval | null;
  onSelectApproval: (approval: Approval) => void;
  getStatusColor: (status: string) => string;
}

export default function ApprovalList({
  approvals,
  selectedApproval,
  onSelectApproval,
  getStatusColor,
}: ApprovalListProps) {
  return (
    <div className="space-y-3 max-h-[600px] overflow-y-auto">
      {approvals.length > 0 ? (
        approvals.map((approval) => (
          <div
            key={approval.approval_id}
            onClick={() => onSelectApproval(approval)}
            className={`p-4 border rounded-lg cursor-pointer transition-all ${
              selectedApproval?.approval_id === approval.approval_id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 text-sm">
                  {approval.applicant_name}
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  ${approval.loan_amount.toLocaleString()}
                </p>
              </div>
              <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(approval.status)}`}>
                {approval.status}
              </div>
            </div>
            <div className="mt-2 pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-600">
                Risk: {approval.risk_score.toFixed(2)} | {approval.recommendation.split(' - ')[0]}
              </p>
            </div>
          </div>
        ))
      ) : (
        <div className="text-center py-8 text-gray-400 text-sm">
          <ClipboardDocumentCheckIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No pending approvals</p>
        </div>
      )}
    </div>
  );
}

