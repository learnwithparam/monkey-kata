'use client';

import { useState } from 'react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface InlineApprovalProps {
  approvalId: string;
  stepName: string;
  stepNumber: number;
  content: Record<string, unknown>;
  onApprove: (approvalId: string, feedback?: string) => Promise<void>;
  onReject: (approvalId: string, feedback?: string) => Promise<void>;
  isReviewing?: boolean;
}

export default function InlineApproval({
  approvalId,
  stepName,
  stepNumber,
  content,
  onApprove,
  onReject,
  isReviewing = false,
}: InlineApprovalProps) {
  const [feedback, setFeedback] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);

  const getStepName = (stepNum: number) => {
    switch (stepNum) {
      case 1:
        return 'Preferences & Setup';
      case 2:
        return 'Meal Plan Generation';
      case 3:
        return 'Final 30-Day Plan';
      default:
        return `Step ${stepNum}`;
    }
  };

  const handleApprove = async () => {
    await onApprove(approvalId, feedback || undefined);
    setFeedback('');
    setShowFeedback(false);
  };

  const handleReject = async () => {
    await onReject(approvalId, feedback || undefined);
    setFeedback('');
    setShowFeedback(false);
  };

  return (
    <div className="mt-4 pt-4 border-t border-gray-200">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded-full">
                {stepNumber}
              </span>
              <h4 className="text-sm font-semibold text-gray-900">
                {getStepName(stepNumber)}
              </h4>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {stepName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </p>
          </div>
        </div>

        {(stepNumber === 2 || stepNumber === 3) && content.meals && (
          <div className="mb-3 p-3 bg-white rounded-lg border border-gray-200">
            <p className="text-xs font-semibold text-gray-700 mb-2">
              {stepNumber === 3 ? '30-Day Meal Plan Summary:' : 'Meal Plan Summary:'}
            </p>
            <div className="text-xs text-gray-600 space-y-1">
              <p>• {Array.isArray(content.meals) ? content.meals.length : 0} meals selected</p>
              {content.nutrition_summary && typeof content.nutrition_summary === 'object' && (
                <>
                  <p>• {content.nutrition_summary.calories || 0} calories/day</p>
                  <p>• {content.nutrition_summary.protein || 0}g protein/day</p>
                </>
              )}
              {content.shopping_list && Array.isArray(content.shopping_list) && (
                <p>• {content.shopping_list.length} items in shopping list</p>
              )}
            </div>
          </div>
        )}

        {showFeedback && (
          <div className="mb-3">
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Add feedback or modification requests..."
              className="w-full p-2.5 border border-gray-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={3}
            />
          </div>
        )}

        <div className="flex items-center gap-2">
          <button
            onClick={handleApprove}
            disabled={isReviewing}
            className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <CheckCircleIcon className="w-4 h-4" />
            {isReviewing ? 'Processing...' : 'Approve'}
          </button>
          <button
            onClick={handleReject}
            disabled={isReviewing}
            className="flex-1 flex items-center justify-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <XCircleIcon className="w-4 h-4" />
            {isReviewing ? 'Processing...' : 'Reject'}
          </button>
          <button
            onClick={() => setShowFeedback(!showFeedback)}
            className="px-3 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {showFeedback ? 'Hide' : 'Feedback'}
          </button>
        </div>
      </div>
    </div>
  );
}

