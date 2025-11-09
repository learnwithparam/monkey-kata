import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '30-Day Meal Prep Agent | AI Bootcamp Demos',
  description: 'Create personalized 30-day meal plans with human-in-the-loop approval. Download your final plan as PDF.',
};

export default function MealPrepLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

