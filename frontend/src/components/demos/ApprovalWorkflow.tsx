import { 
  ClipboardDocumentCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

interface ApprovalWorkflowProps {
  currentStep: 'analysis' | 'review' | 'decision';
  status?: 'pending' | 'approved' | 'rejected';
}

export default function ApprovalWorkflow({ currentStep, status }: ApprovalWorkflowProps) {
  const steps = [
    { id: 'analysis', label: 'AI Analysis', icon: ClipboardDocumentCheckIcon },
    { id: 'review', label: 'Human Review', icon: ClockIcon },
    { id: 'decision', label: 'Decision', icon: status === 'approved' ? CheckCircleIcon : status === 'rejected' ? XCircleIcon : ClockIcon },
  ];

  const getStepStatus = (stepId: string) => {
    const stepIndex = steps.findIndex(s => s.id === stepId);
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="card p-6">
      {steps.map((step, index) => {
        const stepStatus = getStepStatus(step.id);
        const Icon = step.icon;
        const isLast = index === steps.length - 1;

        return (
          <div key={step.id} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={`
                  w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-200
                  ${
                    stepStatus === 'completed'
                      ? 'bg-green-500 border-green-500 text-white'
                      : stepStatus === 'active'
                      ? 'bg-blue-500 border-blue-500 text-white'
                      : 'bg-gray-100 border-gray-300 text-gray-400'
                  }
                `}
              >
                <Icon className="w-6 h-6" />
              </div>
              <p
                className={`
                  mt-2 text-xs font-medium
                  ${
                    stepStatus === 'completed'
                      ? 'text-green-600'
                      : stepStatus === 'active'
                      ? 'text-blue-600 font-semibold'
                      : 'text-gray-400'
                  }
                `}
              >
                {step.label}
              </p>
            </div>
            {!isLast && (
              <div
                className={`
                  flex-1 h-0.5 mx-4 transition-all duration-200
                  ${
                    stepStatus === 'completed'
                      ? 'bg-green-500'
                      : 'bg-gray-200'
                  }
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

