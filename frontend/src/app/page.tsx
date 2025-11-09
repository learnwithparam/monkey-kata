import React from 'react';
import Navigation from '@/components/Navigation';
import Hero from '@/components/Hero';
import WeekSection from '@/components/WeekSection';
import DemoCard from '@/components/DemoCard';
import About from '@/components/About';
import Footer from '@/components/Footer';
import { weeksData } from '../../src/data/demos';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      <main className="relative">
        {/* Subtle background pattern */}
        <div className="fixed inset-0 -z-10 pointer-events-none">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-20"></div>
        </div>

        {/* Demos Section */}
        <section id="demos" className="relative py-12 sm:py-16 md:py-20 lg:py-28 bg-white">
          <div className="max-w-5xl mx-auto container-padding">
            <Hero />

            <div className="space-y-16 sm:space-y-20 md:space-y-24">
              {weeksData.map((week: { weekNumber: string; weekTitle: string; weekColor: string; demos: { icon: React.ReactNode; title: string; description: string; demoHref?: string; challengeHref?: string; isComingSoon?: boolean }[] }, index: number) => (
                <WeekSection
                  key={index}
                  weekNumber={week.weekNumber}
                  weekTitle={week.weekTitle}
                  weekColor={week.weekColor}
                >
                  {week.demos.map((demo: { icon: React.ReactNode; title: string; description: string; demoHref?: string; challengeHref?: string; isComingSoon?: boolean }, demoIndex: number) => (
                    <DemoCard
                      key={demoIndex}
                      icon={demo.icon}
                      title={demo.title}
                      description={demo.description}
                      demoHref={demo.demoHref}
                      challengeHref={demo.challengeHref}
                      isComingSoon={demo.isComingSoon}
                    />
                  ))}
                </WeekSection>
              ))}
            </div>
          </div>
        </section>

        <About />
      </main>

      <Footer />
    </div>
  );
}