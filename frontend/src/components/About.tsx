export default function About() {
  return (
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
  );
}
