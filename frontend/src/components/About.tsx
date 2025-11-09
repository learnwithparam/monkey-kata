export default function About() {
  return (
    <section id="about" className="relative py-16 sm:py-20 md:py-28 bg-gray-50 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-100/30 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-teal-100/30 rounded-full blur-3xl"></div>
      </div>

      <div className="max-w-4xl mx-auto container-padding relative">
        <div className="text-center mb-10 sm:mb-12 md:mb-16">
          <div className="inline-block mb-4 sm:mb-6">
            <span className="text-xs sm:text-sm font-semibold text-purple-600 uppercase tracking-wider">
              Learn by Building
            </span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 sm:mb-8 leading-tight px-2">
            About the AI Bootcamp
          </h2>
          <p className="text-lg sm:text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto leading-relaxed px-2">
            The <strong className="text-gray-900">AI Bootcamp for Software Engineers</strong> is a 6-week, cohort-based program designed for engineers who want to upskill in AI engineering. Unlike other AI courses, you won&apos;t learn passively – you&apos;ll build real AI applications, create lifelong connections, and leave with a new perspective for what is possible with AI.
          </p>
        </div>

        <div className="text-center">
          <a
            href="https://learnwithparam.com?utm_source=demos&utm_medium=ai-bootcamp&utm_campaign=demo-site" 
            className="inline-flex items-center justify-center bg-gray-900 hover:bg-gray-800 text-white font-semibold py-4 px-8 sm:py-5 sm:px-12 rounded-xl text-lg sm:text-xl transition-all duration-300 shadow-lg hover:shadow-2xl transform hover:scale-105"
            aria-label="Enroll in AI Bootcamp for Software Engineers"
          >
            Join the AI Bootcamp
          </a>
        </div>
      </div>
    </section>
  );
}
