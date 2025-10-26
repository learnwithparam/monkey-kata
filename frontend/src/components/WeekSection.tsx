import { ReactNode } from 'react';

interface WeekSectionProps {
  weekNumber: string;
  weekTitle: string;
  weekColor: string;
  children: ReactNode;
}

export default function WeekSection({ weekNumber, weekTitle, weekColor, children }: WeekSectionProps) {
  return (
    <div className="mb-12 sm:mb-16">
      <div className="flex flex-col sm:flex-row sm:items-center mb-6 sm:mb-8">
        <div className={`${weekColor} px-3 sm:px-4 py-1 sm:py-2 rounded-full font-semibold text-xs sm:text-sm mr-0 sm:mr-4 mb-2 sm:mb-0 self-start`}>
          {weekNumber}
        </div>
        <h3 className="text-xl sm:text-2xl font-bold text-gray-900">{weekTitle}</h3>
      </div>
      
      <div className="space-y-3 sm:space-y-4">
        {children}
      </div>
    </div>
  );
}
