import type { Metadata } from "next";

// Simple mapping of challenge slugs to titles (without React components)
const challengeTitleMap: Record<string, string> = {
  "bedtime-story-generator": "Bedtime Stories for Kids",
  "website-rag": "Website FAQ Chatbot",
  "document-qa-chatbot": "Document QA Chatbot",
  "cv-analyzer": "CV Analyzer & Improvement Suggester",
  "travel-support": "Travel Customer Support Assistant",
  "restaurant-booking": "Restaurant Booking Voice AI",
  "medical-office-triage": "Medical Office Triage Voice AI",
};

interface ChallengeLayoutProps {
  children: React.ReactNode;
  params: Promise<{
    slug: string;
  }>;
}

export async function generateMetadata(
  { params }: ChallengeLayoutProps
): Promise<Metadata> {
  const resolvedParams = await params;
  const demoTitle = challengeTitleMap[resolvedParams.slug];
  
  const title = demoTitle 
    ? `${demoTitle} Challenge | AI Bootcamp Demos`
    : "Challenge | AI Bootcamp Demos";
  
  const description = demoTitle
    ? `Complete learning objectives and hands-on exercises for ${demoTitle}`
    : "Complete learning objectives and hands-on exercises";

  return {
    title,
    description,
  };
}

export default function ChallengeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

