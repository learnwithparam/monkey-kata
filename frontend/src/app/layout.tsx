import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AI Bootcamp Demos | learnwithparam",
  description: "Interactive demos and examples from the AI Bootcamp for Software Engineers course",
  keywords: [
    "AI demos",
    "AI bootcamp",
    "software engineering demos", 
    "AI engineering examples",
    "LLM demos",
    "RAG systems",
    "AI agents",
    "voice AI",
    "learnwithparam",
    "Param Harrison"
  ],
  authors: [{ name: "Param Harrison", url: "https://learnwithparam.com" }],
  creator: "Param Harrison",
  publisher: "learnwithparam",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://learnwithparam.com/demos",
    siteName: "learnwithparam",
    title: "AI Bootcamp Demos | learnwithparam",
    description: "Interactive demos and examples from the AI Bootcamp for Software Engineers course",
  },
  twitter: {
    card: "summary_large_image",
    site: "@learnwithparam",
    creator: "@learnwithparam",
    title: "AI Bootcamp Demos | learnwithparam",
    description: "Interactive demos and examples from the AI Bootcamp for Software Engineers course",
  },
  alternates: {
    canonical: "https://learnwithparam.com/demos",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#000000" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="AI Bootcamp Demos" />
        <meta name="application-name" content="AI Bootcamp Demos" />
        <meta name="msapplication-TileColor" content="#000000" />
        
        {/* Essential SEO meta tags */}
        <meta name="author" content="Param Harrison" />
        <meta name="language" content="en" />
        <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
        
        {/* Performance optimizations */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://www.linkedin.com" />
        <link rel="dns-prefetch" href="https://x.com" />
      </head>
      <body
        className={`${inter.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}