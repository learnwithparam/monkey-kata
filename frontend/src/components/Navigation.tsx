'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
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
  );
}
