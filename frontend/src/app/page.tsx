'use client';

import { useState } from 'react';
import Link from 'next/link';
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

export default function Home() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white/95 backdrop-blur-sm sticky top-0 z-50 border-b border-gray-200" role="navigation" aria-label="Main navigation">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16 sm:h-18">
            {/* Logo */}
            <div className="flex-shrink-0">
              <Link href="/" className="text-xl sm:text-2xl md:text-3xl font-bold hover:opacity-80 transition-colors" aria-label="AI Bootcamp Demos - Home">
                <span className="text-brand-purple">learnwith</span><span className="text-brand-teal">param</span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex flex-1 justify-center">
              <nav className="flex items-center space-x-4 xl:space-x-6">
                <Link href="#demos" className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors">
                  Demos
                </Link>
                <Link href="#about" className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors">
                  About
                </Link>
                <Link href="https://learnwithparam.com" className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors">
                  Bootcamp
                </Link>
              </nav>
            </div>

            {/* CTA Button - Desktop Only */}
            <div className="hidden lg:flex items-center">
              <Link 
                href="https://learnwithparam.com?utm_source=demos&utm_medium=ai-bootcamp&utm_campaign=demo-site" 
                className="btn-primary text-sm hover:scale-105 inline-block"
                aria-label="Enroll in AI Bootcamp"
              >
                Enroll Now
              </Link>
            </div>
              
            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="lg:hidden p-2 rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-brand-purple"
              aria-expanded={isMenuOpen}
              aria-label="Toggle navigation menu"
            >
              <span className="sr-only">Open main menu</span>
              <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>

          {/* Mobile menu */}
          {isMenuOpen && (
            <div className="lg:hidden">
              <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t border-gray-200">
                <Link 
                  href="#demos" 
                  className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Demos
                </Link>
                <Link 
                  href="#about" 
                  className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                  onClick={() => setIsMenuOpen(false)}
                >
                  About
                </Link>
                <Link 
                  href="https://learnwithparam.com" 
                  className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Bootcamp
                </Link>
                <div className="pt-4 border-t border-gray-200">
                  <Link 
                    href="https://learnwithparam.com?utm_source=demos&utm_medium=ai-bootcamp&utm_campaign=demo-site" 
                    className="btn-primary text-base hover:scale-105 w-full text-center block"
                    aria-label="Enroll in AI Bootcamp"
                  >
                    Enroll Now
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </nav>

      <main>

        {/* Demos Section */}
        <section id="demos" className="py-12 sm:py-16 md:py-24 bg-white">
          <div className="max-w-4xl mx-auto container-padding">
            <div className="text-center mb-8 sm:mb-12 md:mb-16">
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 sm:mb-6 md:mb-8 leading-tight px-2">
                AI Bootcamp for Software Engineers
              </h1>
              <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed px-2">
                Hands-on demonstrations from each week of the <strong>AI Bootcamp for Software Engineers</strong>
              </p>
            </div>

            {/* Week 1: AI Foundation */}
            <div className="mb-16">
              <div className="flex items-center mb-8">
                <div className="bg-purple-100 text-purple-800 px-4 py-2 rounded-full font-semibold text-sm mr-4">
                  Week 1
                </div>
                <h3 className="text-2xl font-bold text-gray-900">AI Foundation — LLMs, Prompts & RAG</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
                  <div className="flex items-center">
                    <BookOpenIcon className="w-8 h-8 text-purple-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Bedtime Story Generator</h4>
                      <p className="text-sm text-gray-600">Interactive story creation with streaming responses</p>
                    </div>
                  </div>
                  <Link 
                    href="/demos/bedtime-story" 
                    className="btn-accent px-4 py-2 text-sm"
                  >
                    Try Demo
                  </Link>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <ScaleIcon className="w-8 h-8 text-orange-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Legal Document Analysis</h4>
                      <p className="text-sm text-gray-600">Extract key terms and risks from contracts</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <GlobeAltIcon className="w-8 h-8 text-blue-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Web Page Q&A</h4>
                      <p className="text-sm text-gray-600">Q&A system for any webpage content</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <SpeakerWaveIcon className="w-8 h-8 text-green-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Customer Support KB</h4>
                      <p className="text-sm text-gray-600">Q&A system with vector search</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>
              </div>
            </div>

            {/* Week 2: Conversational Systems */}
            <div className="mb-16">
              <div className="flex items-center mb-8">
                <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full font-semibold text-sm mr-4">
                  Week 2
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Building Reliable Conversational Systems</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <TagIcon className="w-8 h-8 text-blue-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Lead Qualifier Bot</h4>
                      <p className="text-sm text-gray-600">Chat-based lead qualification system</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <CakeIcon className="w-8 h-8 text-orange-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Restaurant Voice Assistant</h4>
                      <p className="text-sm text-gray-600">Voice system for food ordering</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <HeartIcon className="w-8 h-8 text-red-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Healthcare Triage</h4>
                      <p className="text-sm text-gray-600">Voice system for patient intake</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>
              </div>
            </div>

            {/* Week 3: AI Agents & Workflows */}
            <div className="mb-16">
              <div className="flex items-center mb-8">
                <div className="bg-green-100 text-green-800 px-4 py-2 rounded-full font-semibold text-sm mr-4">
                  Week 3
                </div>
                <h3 className="text-2xl font-bold text-gray-900">AI Agents & Workflows</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <MagnifyingGlassIcon className="w-8 h-8 text-green-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Competitor Analysis Agent</h4>
                      <p className="text-sm text-gray-600">Agent that researches competitors</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <DocumentTextIcon className="w-8 h-8 text-blue-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Web Form Filling Bot</h4>
                      <p className="text-sm text-gray-600">Agent that fills forms automatically</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <LegalIcon className="w-8 h-8 text-red-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Legal Case Intake</h4>
                      <p className="text-sm text-gray-600">Chat system with human lawyer review</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <ShoppingBagIcon className="w-8 h-8 text-purple-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Personal Shopping Assistant</h4>
                      <p className="text-sm text-gray-600">AI agent for product recommendations</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>
              </div>
            </div>

            {/* Week 4: Production Optimization */}
            <div className="mb-16">
              <div className="flex items-center mb-8">
                <div className="bg-orange-100 text-orange-800 px-4 py-2 rounded-full font-semibold text-sm mr-4">
                  Week 4
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Prototype to Production</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <RocketLaunchIcon className="w-8 h-8 text-orange-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">RAG Optimization</h4>
                      <p className="text-sm text-gray-600">Optimize Customer Support RAG for production</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <MicrophoneIcon className="w-8 h-8 text-blue-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Voice Agent Enhancement</h4>
                      <p className="text-sm text-gray-600">Optimize voice systems for production</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <ChartBarIcon className="w-8 h-8 text-green-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Agent System Scalability</h4>
                      <p className="text-sm text-gray-600">Scale agent systems for production</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>
              </div>
            </div>

            {/* Week 5: System Design */}
            <div className="mb-16">
              <div className="flex items-center mb-8">
                <div className="bg-indigo-100 text-indigo-800 px-4 py-2 rounded-full font-semibold text-sm mr-4">
                  Week 5
                </div>
                <h3 className="text-2xl font-bold text-gray-900">AI System Design & Architecture</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <BuildingOfficeIcon className="w-8 h-8 text-indigo-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Enterprise Architecture</h4>
                      <p className="text-sm text-gray-600">Microservices and event-driven patterns</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <HandRaisedIcon className="w-8 h-8 text-blue-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Agent-to-Agent Communication</h4>
                      <p className="text-sm text-gray-600">MCP and inter-agent protocols</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <BeakerIcon className="w-8 h-8 text-green-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">AI Testing & Validation</h4>
                      <p className="text-sm text-gray-600">Testing methodologies and frameworks</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>
              </div>
            </div>

            {/* Week 6: Capstone */}
            <div className="mb-16">
              <div className="flex items-center mb-8">
                <div className="bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full font-semibold text-sm mr-4">
                  Week 6
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Capstone Project & Demo Day</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <TruckIcon className="w-8 h-8 text-yellow-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Drive-Thru Voice Agent</h4>
                      <p className="text-sm text-gray-600">Fast-food ordering with speech recognition</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <PhoneIcon className="w-8 h-8 text-blue-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">IVR Agent</h4>
                      <p className="text-sm text-gray-600">Inbound support calls with natural conversation</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 opacity-60">
                  <div className="flex items-center">
                    <EyeIcon className="w-8 h-8 text-purple-600 mr-4" />
                    <div>
                      <h4 className="font-semibold text-gray-900">Vision AI Agent</h4>
                      <p className="text-sm text-gray-600">Multimodal assistant for financial reports</p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">Coming Soon</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* About Section */}
        <section id="about" className="py-12 sm:py-16 md:py-24 bg-gray-50">
          <div className="max-w-4xl mx-auto container-padding">
            <div className="text-center mb-8 sm:mb-12">
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 sm:mb-6 md:mb-8 leading-tight px-2">
                About the AI Bootcamp
              </h2>
              <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed px-2">
                The <strong>AI Bootcamp for Software Engineers</strong> is a 6-week, cohort-based program designed for engineers who want to upskill in AI engineering. Unlike other AI courses, you won&apos;t learn passively – you&apos;ll build real AI applications, create lifelong connections, and leave with a new perspective for what is possible with AI.
              </p>
            </div>

            <div className="text-center">
              <a
                href="https://learnwithparam.com?utm_source=demos&utm_medium=ai-bootcamp&utm_campaign=demo-site" 
                className="bg-gray-900 hover:bg-gray-800 text-white font-bold py-4 px-8 sm:py-5 sm:px-12 rounded-xl text-lg sm:text-xl transition-all duration-200 shadow-xl hover:shadow-2xl transform hover:scale-105 inline-block"
                aria-label="Enroll in AI Bootcamp for Software Engineers"
              >
                Join the AI Bootcamp
              </a>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto container-padding text-center">
          <p className="text-gray-600 text-sm">
            © 2025 Secret SaaS OÜ. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}