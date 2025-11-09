import { ReactNode } from 'react';

interface WeekSectionProps {
  weekNumber: string;
  weekTitle: string;
  weekColor: string;
  children: ReactNode;
}

export default function WeekSection({ weekNumber, weekTitle, weekColor, children }: WeekSectionProps) {
  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center mb-8 sm:mb-10 gap-3 sm:gap-4">
        <div className={`${weekColor} px-4 py-2 rounded-full font-semibold text-xs sm:text-sm self-start shadow-sm border border-opacity-20`}>
          {weekNumber}
        </div>
        <h3 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 leading-tight">{weekTitle}</h3>
      </div>
      
      <div className="space-y-4 sm:space-y-5">
        {children}
      </div>
    </div>
  );
}
