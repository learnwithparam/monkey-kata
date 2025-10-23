import { ReactNode } from 'react';

interface WeekSectionProps {
  weekNumber: string;
  weekTitle: string;
  weekColor: string;
  children: ReactNode;
}

export default function WeekSection({ weekNumber, weekTitle, weekColor, children }: WeekSectionProps) {
  return (
    <div className="mb-16">
      <div className="flex items-center mb-8">
        <div className={`${weekColor} px-4 py-2 rounded-full font-semibold text-sm mr-4`}>
          {weekNumber}
        </div>
        <h3 className="text-2xl font-bold text-gray-900">{weekTitle}</h3>
      </div>
      
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );
}
