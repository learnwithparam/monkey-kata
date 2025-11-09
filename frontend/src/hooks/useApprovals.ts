import { useState, useEffect, useCallback } from 'react';
import { Approval } from '@/components/demos/ApprovalList';

interface UseApprovalsOptions {
  apiBaseUrl: string;
  refreshInterval?: number;
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
    
    // Fetch on mount
    fetchApprovals();
    
    // Set up periodic refresh
    const interval = setInterval(fetchApprovals, refreshInterval);
    return () => clearInterval(interval);
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

