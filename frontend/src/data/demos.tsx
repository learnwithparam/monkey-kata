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
  learnings: string[];
}

// Utility to find demo by challenge slug
export function findDemoByChallengeSlug(slug: string): Demo | null {
  for (const category of categoriesData) {
    for (const demo of category.demos) {
      if (demo.challengeHref === `/challenges/${slug}`) {
        return demo;
      }
    }
  }
  return null;
}

export interface CategoryData {
  title: string;
  color: string;
  demos: Demo[];
}

export const categoriesData: CategoryData[] = [
  {
    title: "LLM & Prompt Engineering",
    color: "bg-purple-100 text-purple-800",
    demos: [
      {
        icon: <BookOpenIcon className="w-8 h-8 text-purple-600 mr-4" />,
        title: "Bedtime Stories for Kids",
        description: "AI-powered bedtime stories that adapt to your child's interests and age",
        demoHref: "/demos/bedtime-story",
        challengeHref: "/challenges/bedtime-story-generator",
        apiSlug: "bedtime_story_generator",
        learnings: [
          "Learn to stream LLM responses in real-time for better user experience",
          "Master temperature and max_tokens to control creativity and output length",
          "Build effective prompts using proven patterns and structures",
          "Handle streaming responses and update UI in real-time"
        ]
      },
      {
        icon: <DocumentTextIcon className="w-8 h-8 text-emerald-600 mr-4" />,
        title: "Invoice Parser",
        description: "Vision-enabled extraction of structured data from invoices. Supports Images (all providers) and PDFs (Gemini only) with Pydantic validation",
        demoHref: "/demos/invoice-parser",
        challengeHref: "/challenges/invoice-parser",
        apiSlug: "invoice_parser",
        learnings: [
          "Use vision-enabled LLMs to extract structured data from images and PDFs",
          "Enforce type-safe structured outputs with Pydantic validation",
          "Classify documents without training data using zero-shot learning",
          "Automatically detect document types and intents"
        ]
      },
      {
        icon: <BriefcaseIcon className="w-8 h-8 text-indigo-600 mr-4" />,
        title: "CV Analyzer",
        description: "Production-ready CV analysis with multi-agent orchestration and prompt chaining for deep insights",
        demoHref: "/demos/cv-analyzer",
        challengeHref: "/challenges/cv-analyzer",
        apiSlug: "cv_analyzer",
        learnings: [
          "Use LlamaIndex for document processing and vector operations",
          "Build complex multi-agent workflows with LangGraph orchestration",
          "Implement section-aware chunking strategies for CV documents",
          "Create embeddings that preserve CV section context"
        ]
      }
    ]
  },
  {
    title: "Image Generation",
    color: "bg-pink-100 text-pink-800",
    demos: [
      {
        icon: <PhotoIcon className="w-8 h-8 text-pink-600 mr-4" />,
        title: "Image to Coloring Book Converter",
        description: "Upload a photo and convert it into a printable coloring book page with simple image processing",
        demoHref: "/demos/image-to-drawing",
        challengeHref: "/challenges/image-to-drawing",
        apiSlug: "image_to_drawing",
        learnings: [
          "Transform images using image-to-image generation models",
          "Implement provider pattern for multi-model support",
          "Optimize images with pre and post-processing techniques",
          "Handle async workflows with polling patterns"
        ]
      }
    ]
  },
  {
    title: "RAG",
    color: "bg-blue-100 text-blue-800",
    demos: [
      {
        icon: <GlobeAltIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Website FAQ Chatbot",
        description: "Ask questions about any website and get instant, accurate answers from the content",
        demoHref: "/demos/website-rag",
        challengeHref: "/challenges/website-rag",
        apiSlug: "website_rag",
        learnings: [
          "Build RAG systems with ChromaDB vector database",
          "Use RecursiveCharacterTextSplitter for intelligent text chunking",
          "Combine keyword and semantic search with hybrid retrieval",
          "Improve search accuracy with Cross-Encoder reranking",
          "Engineer effective RAG prompts for accurate answers"
        ]
      },
      {
        icon: <DocumentTextIcon className="w-8 h-8 text-blue-600 mr-4" />,
        title: "Document QA Chatbot",
        description: "Upload any document and get instant AI-powered analysis, key insights, and intelligent Q&A",
        demoHref: "/demos/document-qa-chatbot",
        challengeHref: "/challenges/document-qa-chatbot",
        apiSlug: "document_qa_chatbot",
        learnings: [
          "Store and query embeddings with Qdrant vector database",
          "Generate embeddings using Sentence Transformers models",
          "Split documents intelligently with RecursiveCharacterTextSplitter",
          "Refine search results using Cross-Encoder reranking",
          "Design chunking strategies for optimal retrieval"
        ]
      }
    ]
  },
  {
    title: "Agentic RAG",
    color: "bg-indigo-100 text-indigo-800",
    demos: [
      {
        icon: <ChatBubbleLeftRightIcon className="w-8 h-8 text-purple-600 mr-4" />,
        title: "Travel Customer Support Assistant",
        description: "Travel support assistant (like Booking.com) with function calling - helps with booking lookups, hotel reservations, flight status, and taxi bookings",
        demoHref: "/demos/travel-support",
        challengeHref: "/challenges/travel-support",
        apiSlug: "travel_support_assistant",
        learnings: [
          "Build multi-agent systems with AutoGen GroupChat orchestration",
          "Enable agents to call functions and tools dynamically",
          "Manage conversation state across agent interactions"
        ]
      }
    ]
  },
  {
    title: "Voice Agents",
    color: "bg-orange-100 text-orange-800",
    demos: [
      {
        icon: <PhoneIcon className="w-8 h-8 text-orange-600 mr-4" />,
        title: "Restaurant Booking Voice AI",
        description: "Take food orders naturally through voice conversation with AI-powered restaurant assistant",
        demoHref: "/demos/restaurant-booking",
        challengeHref: "/challenges/restaurant-booking",
        apiSlug: "restaurant_booking",
        learnings: [
          "Build real-time voice AI systems with LiveKit",
          "Integrate speech-to-text and text-to-speech with Deepgram",
          "Design voice agent architecture for conversational AI",
          "Enable voice agents to call tools and functions"
        ]
      },
      {
        icon: <HeartIcon className="w-8 h-8 text-red-600 mr-4" />,
        title: "Medical Office Triage Voice AI",
        description: "Multi-agent voice AI system that routes patients to specialized departments with context preservation",
        demoHref: "/demos/medical-office-triage",
        challengeHref: "/challenges/medical-office-triage",
        apiSlug: "medical_office_triage",
        learnings: [
          "Build multi-agent voice systems with LiveKit",
          "Transfer conversations between specialized agents seamlessly",
          "Preserve context when routing between different agents"
        ]
      }
    ]
  },
  {
    title: "AI Workflows",
    color: "bg-green-100 text-green-800",
    demos: [
      {
        icon: <LegalIcon className="w-8 h-8 text-red-600 mr-4" />,
        title: "Legal Case Intake Workflow",
        description: "Client intake with AI-powered case assessment and human lawyer review",
        demoHref: "/demos/legal-case-intake",
        challengeHref: "/challenges/legal-case-intake",
        apiSlug: "legal_case_intake",
        learnings: [
          "Orchestrate multi-agent workflows with CrewAI",
          "Integrate human review and approval in AI workflows",
          "Design sequential and parallel agent coordination"
        ]
      },
      {
        icon: <BriefcaseIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "Job Application Form Auto-Fill",
        description: "Upload your resume and watch AI automatically fill your job application form in real-time",
        demoHref: "/demos/job-application-form-filling",
        challengeHref: "/challenges/job-application-form-filling",
        apiSlug: "job_application_form_filling",
        learnings: [
          "Parse documents with LlamaIndex for structured extraction",
          "Build agents that discover form structures autonomously",
          "Map data semantically to form fields without hardcoding",
          "Adapt to any form structure dynamically",
          "Stream form filling progress in real-time"
        ]
      }
    ]
  },
  {
    title: "AI Agents",
    color: "bg-red-100 text-red-800",
    demos: [
      {
        icon: <UserGroupIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "Lead Scoring & Email Generation",
        description: "Score candidates against job descriptions and generate personalized emails using AI-powered multi-crew workflows",
        demoHref: "/demos/lead-scoring",
        challengeHref: "/challenges/lead-scoring",
        apiSlug: "lead_scoring",
        learnings: [
          "Coordinate multiple CrewAI crews for complex workflows",
          "Process multiple candidates in parallel for speed",
          "Integrate human feedback to refine AI outputs"
        ]
      },
      {
        icon: <MagnifyingGlassIcon className="w-8 h-8 text-green-600 mr-4" />,
        title: "Competitor Analysis Research Agent",
        description: "Research competitors and analyze market positioning using multi-agent workflows",
        demoHref: "/demos/competitor-analysis",
        challengeHref: "/challenges/competitor-analysis",
        apiSlug: "competitor_analysis",
        learnings: [
          "Build research agents with LangChain Agent Executors",
          "Coordinate multiple specialized agents for complex tasks",
          "Enable agents to use tools like web search and scraping"
        ]
      }
    ]
  }
];
