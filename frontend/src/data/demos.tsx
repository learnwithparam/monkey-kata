import { 
  BookOpenIcon,
  ScaleIcon,
  GlobeAltIcon,
  SpeakerWaveIcon,
  TagIcon,
  CakeIcon,
  HeartIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ScaleIcon as LegalIcon,
  ShoppingBagIcon,
  RocketLaunchIcon,
  MicrophoneIcon,
  ChartBarIcon,
  BuildingOfficeIcon,
  HandRaisedIcon,
  BeakerIcon,
  TruckIcon,
  PhoneIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

export interface Demo {
  icon: React.ReactNode;
  title: string;
  description: string;
  demoHref?: string;
  challengeHref?: string;
  isComingSoon?: boolean;
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
        challengeHref: "/challenges/bedtime-story-generator"
      },
      {
        icon: <GlobeAltIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Website FAQ Chatbot",
        description: "Ask questions about any website and get instant, accurate answers from the content",
        demoHref: "/demos/website-rag",
        challengeHref: "/challenges/website-rag"
      },
      {
        icon: <ScaleIcon className="w-8 h-8 text-orange-600 mr-4" />,
        title: "Legal Contract Analyzer",
        description: "Instantly identify potential risks and key terms in legal documents",
        isComingSoon: true
      },
      {
        icon: <SpeakerWaveIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "24/7 Customer Support Bot with Human Escalation",
        description: "Intelligent customer support that finds answers instantly from your knowledge base",
        isComingSoon: true
      }
    ]
  },
  {
    weekNumber: "Week 2",
    weekTitle: "Building Reliable Conversational Systems",
    weekColor: "bg-blue-100 text-blue-800",
    demos: [
      {
        icon: <TagIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Sales Lead Qualifier",
        description: "Automatically qualify and score leads through intelligent conversation",
        isComingSoon: true
      },
      {
        icon: <CakeIcon className="w-8 h-8 text-orange-600 mr-4" />,
        title: "Voice Order Assistant",
        description: "Take food orders naturally through voice conversation with AI",
        isComingSoon: true
      },
      {
        icon: <HeartIcon className="w-8 h-8 text-red-600 mr-4" />,
        title: "Medical Triage Assistant",
        description: "Intelligent patient intake that prioritizes cases and gathers symptoms",
        isComingSoon: true
      }
    ]
  },
  {
    weekNumber: "Week 3",
    weekTitle: "AI Agents & Workflows",
    weekColor: "bg-green-100 text-green-800",
    demos: [
      {
        icon: <MagnifyingGlassIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "Market Intelligence Agent",
        description: "Automatically research competitors and analyze market positioning",
        isComingSoon: true
      },
      {
        icon: <DocumentTextIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Auto Form Filler",
        description: "Intelligent agent that navigates websites and fills forms automatically",
        isComingSoon: true
      },
      {
        icon: <LegalIcon className="w-8 h-8 text-red-600 mr-4" />,
        title: "Legal Case Intake System",
        description: "Streamline client intake with AI-powered case assessment and lawyer handoff",
        isComingSoon: true
      },
      {
        icon: <ShoppingBagIcon className="w-8 h-8 text-purple-600 mr-4" />,
        title: "Personal Shopping Assistant",
        description: "AI-powered shopping companion that finds perfect products based on your preferences",
        isComingSoon: true
      }
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
        description: "Revolutionary voice AI that takes fast-food orders with natural conversation",
        isComingSoon: true
      },
      {
        icon: <PhoneIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Smart Call Center",
        description: "Transform customer support with AI that handles calls naturally and efficiently",
        isComingSoon: true
      },
      {
        icon: <EyeIcon className="w-8 h-8 text-purple-600 mr-4" />,
        title: "Financial Document Analyzer",
        description: "AI that reads and analyzes financial reports, charts, and documents with computer vision",
        isComingSoon: true
      }
    ]
  }
];
