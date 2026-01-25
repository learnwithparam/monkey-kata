import { ReactNode } from 'react';

interface CategorySectionProps {
  title: string;
  children: ReactNode;
}

export default function WeekSection({ title, children }: CategorySectionProps) {
  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center mb-8 sm:mb-10 gap-3 sm:gap-4">
        <h3 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 leading-tight">{title}</h3>
      </div>
      
      <div className="space-y-4 sm:space-y-5">
        {children}
      </div>
    </div>
  );
}
