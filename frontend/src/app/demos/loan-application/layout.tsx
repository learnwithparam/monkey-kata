import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Loan Application Assistant | AI Bootcamp Demos",
  description: "AI-powered loan application assistant with human-in-the-loop approval workflow for financial services.",
};

export default function LoanApplicationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

