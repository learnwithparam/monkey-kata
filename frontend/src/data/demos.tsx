import { 
  BookOpenIcon,
  GlobeAltIcon,
  HeartIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ScaleIcon as LegalIcon,
  RocketLaunchIcon,
  MicrophoneIcon,
  ChartBarIcon,
  BuildingOfficeIcon,
  HandRaisedIcon,
  BeakerIcon,
  TruckIcon,
  PhoneIcon,
  EyeIcon,
  BriefcaseIcon,
  ChatBubbleLeftRightIcon,
  PhotoIcon,
  UserGroupIcon,
  ShoppingCartIcon,
} from '@heroicons/react/24/outline';

export interface Demo {
  icon: React.ReactNode;
  title: string;
  description: string;
  demoHref?: string;
  challengeHref?: string;
  apiSlug?: string; // Backend API folder name (e.g., 'travel_support_assistant')
  isComingSoon?: boolean;
}

// Utility to find demo by challenge slug
export function findDemoByChallengeSlug(slug: string): Demo | null {
  for (const week of weeksData) {
    for (const demo of week.demos) {
      if (demo.challengeHref === `/challenges/${slug}`) {
        return demo;
      }
    }
  }
  return null;
}

export interface WeekData {
  weekNumber: string;
  weekTitle: string;
  weekColor: string;
  demos: Demo[];
}

export const weeksData: WeekData[] = [
  {
    weekNumber: "Week 1",
    weekTitle: "AI Foundation — LLMs, Prompts & RAG",
    weekColor: "bg-purple-100 text-purple-800",
    demos: [
      {
        icon: <BookOpenIcon className="w-8 h-8 text-purple-600 mr-4" />,
        title: "Bedtime Stories for Kids",
        description: "AI-powered bedtime stories that adapt to your child's interests and age",
        demoHref: "/demos/bedtime-story",
        challengeHref: "/challenges/bedtime-story-generator",
        apiSlug: "bedtime_story_generator"
      },
      {
        icon: <GlobeAltIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Website FAQ Chatbot",
        description: "Ask questions about any website and get instant, accurate answers from the content",
        demoHref: "/demos/website-rag",
        challengeHref: "/challenges/website-rag",
        apiSlug: "website_rag"
      },
      {
        icon: <DocumentTextIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Document QA Chatbot",
        description: "Upload any document and get instant AI-powered analysis, key insights, and intelligent Q&A",
        demoHref: "/demos/document-qa-chatbot",
        challengeHref: "/challenges/document-qa-chatbot",
        apiSlug: "document_qa_chatbot"
      },
      {
        icon: <BriefcaseIcon className="w-8 h-8 text-indigo-600 mr-4" />,
        title: "CV Analyzer & Improvement Suggester",
        description: "AI-powered CV analysis with personalized improvement suggestions to land your dream job",
        demoHref: "/demos/cv-analyzer",
        challengeHref: "/challenges/cv-analyzer",
        apiSlug: "cv_analyzer"
      }
    ]
  },
  {
    weekNumber: "Week 2",
    weekTitle: "Building Reliable Conversational Systems",
    weekColor: "bg-blue-100 text-blue-800",
    demos: [
      {
        icon: <ChatBubbleLeftRightIcon className="w-8 h-8 text-purple-600 mr-4" />,
        title: "Travel Customer Support Assistant",
        description: "Travel support assistant (like Booking.com) with function calling - helps with booking lookups, hotel reservations, flight status, and taxi bookings",
        demoHref: "/demos/travel-support",
        challengeHref: "/challenges/travel-support",
        apiSlug: "travel_support_assistant"
      },
      {
        icon: <PhoneIcon className="w-8 h-8 text-orange-600 mr-4" />,
        title: "Restaurant Booking Voice AI",
        description: "Take food orders naturally through voice conversation with AI-powered restaurant assistant",
        demoHref: "/demos/restaurant-booking",
        challengeHref: "/challenges/restaurant-booking",
        apiSlug: "restaurant_booking"
      },
      {
        icon: <HeartIcon className="w-8 h-8 text-red-600 mr-4" />,
        title: "Medical Office Triage Voice AI",
        description: "Multi-agent voice AI system that routes patients to specialized departments with context preservation",
        demoHref: "/demos/medical-office-triage",
        challengeHref: "/challenges/medical-office-triage",
        apiSlug: "medical_office_triage"
      },
      {
        icon: <PhotoIcon className="w-8 h-8 text-pink-600 mr-4" />,
        title: "Image to Coloring Book Converter",
        description: "Upload a photo and convert it into a printable coloring book page with simple image processing",
        demoHref: "/demos/image-to-drawing",
        challengeHref: "/challenges/image-to-drawing",
        apiSlug: "image_to_drawing"
      }
    ]
  },
  {
    weekNumber: "Week 3",
    weekTitle: "AI Agents & Workflows",
    weekColor: "bg-green-100 text-green-800",
    demos: [
      {
        icon: <UserGroupIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "Lead Scoring & Email Generation",
        description: "Score candidates against job descriptions and generate personalized emails using AI-powered multi-crew workflows",
        demoHref: "/demos/lead-scoring",
        challengeHref: "/challenges/lead-scoring",
        apiSlug: "lead_scoring"
      },
      {
        icon: <MagnifyingGlassIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "Competitor Analysis Research Agent",
        description: "Research competitors and analyze market positioning using multi-agent workflows",
        demoHref: "/demos/competitor-analysis",
        challengeHref: "/challenges/competitor-analysis",
        apiSlug: "competitor_analysis"
      },
      {
        icon: <LegalIcon className="w-8 h-8 text-red-600 mr-4" />,
        title: "Legal Case Intake Workflow",
        description: "Client intake with AI-powered case assessment and human lawyer review",
        demoHref: "/demos/legal-case-intake",
        challengeHref: "/challenges/legal-case-intake",
        apiSlug: "legal_case_intake"
      },
      {
        icon: <BriefcaseIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "Job Application Form Auto-Fill",
        description: "Upload your resume and watch AI automatically fill your job application form in real-time",
        demoHref: "/demos/job-application-form-filling",
        challengeHref: "/challenges/job-application-form-filling",
        apiSlug: "job_application_form_filling"
      },
    ]
  },
  {
    weekNumber: "Week 4",
    weekTitle: "Prototype to Production",
    weekColor: "bg-orange-100 text-orange-800",
    demos: [
      {
        icon: <RocketLaunchIcon className="w-8 h-8 text-orange-600 mr-4" />,
        title: "RAG Performance Optimizer",
        description: "Boost RAG system performance with advanced optimization techniques",
        isComingSoon: true
      },
      {
        icon: <MicrophoneIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Voice Agent Optimizer",
        description: "Enhance voice AI systems with advanced performance tuning and optimization",
        isComingSoon: true
      },
      {
        icon: <ChartBarIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "AI System Scaler",
        description: "Scale AI agent systems to handle millions of users with enterprise-grade architecture",
        isComingSoon: true
      }
    ]
  },
  {
    weekNumber: "Week 5",
    weekTitle: "AI System Design & Architecture",
    weekColor: "bg-indigo-100 text-indigo-800",
    demos: [
      {
        icon: <BuildingOfficeIcon className="w-8 h-8 text-indigo-600 mr-4" />,
        title: "Enterprise Architecture",
        description: "Microservices and event-driven patterns",
        isComingSoon: true
      },
      {
        icon: <HandRaisedIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Agent-to-Agent Communication",
        description: "MCP and inter-agent protocols",
        isComingSoon: true
      },
      {
        icon: <BeakerIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "AI Testing & Validation",
        description: "Testing methodologies and frameworks",
        isComingSoon: true
      }
    ]
  },
  {
    weekNumber: "Week 6",
    weekTitle: "Capstone Project & Demo Day",
    weekColor: "bg-yellow-100 text-yellow-800",
    demos: [
      {
        icon: <TruckIcon className="w-8 h-8 text-yellow-600 mr-4" />,
        title: "Drive-Thru Order Assistant",
        description: "Revolutionary voice AI that takes fast-food orders with natural conversation. Integrates voice, agents, and real-time processing.",
        isComingSoon: true
      },
      {
        icon: <PhoneIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Smart Call Center",
        description: "Transform customer support with AI that handles calls naturally and efficiently. Combines voice AI, RAG, and human-in-the-loop patterns.",
        isComingSoon: true
      },
      {
        icon: <EyeIcon className="w-8 h-8 text-purple-600 mr-4" />,
        title: "Financial Document Analyzer",
        description: "AI that reads and analyzes financial reports, charts, and documents with computer vision. Multi-modal system combining vision and LLMs.",
        isComingSoon: true
      }
    ]
  }
];
