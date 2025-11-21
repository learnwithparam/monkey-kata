export default function Hero() {
  return (
    <div className="relative text-center mb-12 sm:mb-16 md:mb-20">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-[0.02] -z-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}></div>
      </div>
      
      {/* Brand badge */}
      <div className="inline-flex items-center gap-2 px-4 py-2 mb-6 rounded-full bg-emerald-100/80 backdrop-blur-sm border border-emerald-200/50">
        <span className="text-sm font-medium text-emerald-700">Interactive Learning Platform</span>
      </div>

      {/* Main heading */}
      <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6 leading-tight px-2">
        <span className="block mb-2">AI Bootcamp for</span>
        <span className="block bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
          Software Engineers
        </span>
      </h1>
      
      {/* Subtitle */}
      <p className="text-base sm:text-lg md:text-xl text-gray-700 max-w-3xl mx-auto leading-relaxed px-2 mb-8">
        Hands-on demonstrations from each week of the <strong className="text-gray-900">AI Bootcamp for Software Engineers</strong>
      </p>

      {/* Decorative line */}
      <div className="flex items-center justify-center gap-4 max-w-md mx-auto">
        <div className="h-px flex-1 bg-gray-300"></div>
        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
        <div className="h-px flex-1 bg-gray-300"></div>
      </div>
    </div>
  );
}
