import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Website Chatbot | AI Bootcamp Demos",
  description: "Transform any website into an intelligent assistant. Simply add a URL and start having meaningful conversations about their services and offerings.",
};

export default function WebsiteRAGLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

