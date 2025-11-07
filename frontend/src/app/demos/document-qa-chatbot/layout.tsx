import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Document QA Chatbot | AI Bootcamp Demos",
  description: "Upload any document (PDF, Word, text) and get instant AI-powered analysis, key insights, and intelligent Q&A about your documents.",
};

export default function DocumentQAChatbotLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

