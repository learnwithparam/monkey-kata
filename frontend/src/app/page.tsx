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

      <main>
        {/* Demos Section */}
        <section id="demos" className="py-12 sm:py-16 md:py-24 bg-white">
          <div className="max-w-4xl mx-auto container-padding">
            <Hero />

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
        </section>

        <About />
      </main>

      <Footer />
    </div>
  );
}