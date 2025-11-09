export default function Hero() {
  return (
    <div className="relative text-center mb-12 sm:mb-16 md:mb-20 lg:mb-24">
      {/* Subtle background decoration */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-purple-50 rounded-full blur-3xl opacity-40"></div>
      </div>
      
      {/* Badge */}
      <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 sm:mb-8 rounded-full bg-purple-100 border border-purple-200/50">
        <span className="text-xs sm:text-sm font-semibold text-purple-600">
          Interactive Learning Platform
        </span>
      </div>

      {/* Main heading */}
      <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 sm:mb-8 leading-tight px-2">
        <span className="block mb-2">AI Bootcamp for</span>
        <span className="block text-purple-600">
          Software Engineers
        </span>
      </h1>
      
      {/* Subtitle */}
      <p className="text-lg sm:text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto leading-relaxed px-2 mb-8 sm:mb-10">
        Hands-on demonstrations from each week of the <strong className="text-gray-900">AI Bootcamp for Software Engineers</strong>
      </p>

      {/* Decorative line */}
      <div className="flex items-center justify-center gap-4 max-w-md mx-auto">
        <div className="h-px flex-1 bg-gray-300"></div>
        <div className="w-2 h-2 rounded-full bg-purple-500"></div>
        <div className="h-px flex-1 bg-gray-300"></div>
      </div>
    </div>
  );
}
