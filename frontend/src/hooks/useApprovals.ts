import { useState, useEffect, useCallback } from 'react';

// Generic approval type for use across different demos
export interface Approval {
  approval_id: string;
  application_id: string;
  applicant_name?: string;
  status: string;
  recommendation?: string;
  risk_score?: number;
  loan_amount?: number;
  ai_analysis?: string;
  created_at?: string;
  reviewed_at?: string;
  reviewer_feedback?: string;
  [key: string]: unknown; // Allow additional properties for different demo types
}

interface UseApprovalsOptions {
  apiBaseUrl: string;
  refreshInterval?: number; // Set to 0 to disable automatic polling
}

export function useApprovals({ apiBaseUrl, refreshInterval = 5000 }: UseApprovalsOptions) {
  const [pendingApprovals, setPendingApprovals] = useState<Approval[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchApprovals = useCallback(async () => {
    if (!apiBaseUrl) {
      setError('API base URL is not configured');
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${apiBaseUrl}/approvals`);
      if (response.ok) {
        const data = await response.json();
        setPendingApprovals(data.approvals || []);
      } else {
        const errorText = await response.text().catch(() => 'Unknown error');
        setError(`Failed to fetch approvals: ${response.status} ${errorText}`);
      }
    } catch (err) {
      console.error('Error fetching approvals:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch approvals');
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    if (!apiBaseUrl) {
      return;
    }
    
    // Only set up periodic refresh if refreshInterval > 0
    // Don't fetch on mount - let components fetch manually when needed
    if (refreshInterval && refreshInterval > 0) {
      // Fetch once on mount, then set up interval
      fetchApprovals();
      const interval = setInterval(fetchApprovals, refreshInterval);
      return () => clearInterval(interval);
    }
    // If refreshInterval is 0, don't fetch automatically at all
  }, [apiBaseUrl, fetchApprovals, refreshInterval]);

  const reviewApproval = useCallback(async (
    approvalId: string,
    decision: 'approve' | 'reject',
    notes?: string
  ) => {
    setIsReviewing(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/approvals/${approvalId}/review`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            approval_id: approvalId,
            decision,
            reviewer_notes: notes,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to review approval');
      }

      // Refresh approvals after review
      await fetchApprovals();
      return true;
    } catch (err) {
      console.error('Error reviewing approval:', err);
      throw err;
    } finally {
      setIsReviewing(false);
    }
  }, [apiBaseUrl, fetchApprovals]);

  return {
    pendingApprovals,
    isLoading,
    isReviewing,
    error,
    fetchApprovals,
    reviewApproval,
  };
}

