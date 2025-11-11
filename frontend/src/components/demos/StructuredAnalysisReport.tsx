'use client';

import { 
  ChartBarIcon,
  BuildingOfficeIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

interface CompetitorData {
  name: string;
  positioning: string;
  strengths: string[];
  weaknesses: string[];
  pricing: string;
  key_features: string[];
}

interface StructuredReport {
  executive_summary: string;
  market_positioning: {
    your_company: string;
    competitors: CompetitorData[];
  };
  competitive_advantages: string[];
  competitive_disadvantages: string[];
  market_opportunities: string[];
  market_threats: string[];
  strategic_recommendations: string[];
  key_insights: string[];
}

interface StructuredAnalysisReportProps {
  report: string;
  companyName: string;
  competitors: string[];
}

export default function StructuredAnalysisReport({ report, companyName, competitors }: StructuredAnalysisReportProps) {
  // Parse JSON report
  let structuredData: StructuredReport | null = null;
  try {
    structuredData = JSON.parse(report);
  } catch (e) {
    // If parsing fails, show error
    return (
      <div className="w-full bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
            <div className="text-center text-gray-600">
              <p>Unable to parse report data. Please try again.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!structuredData) return null;

  return (
    <div className="w-full bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <ChartBarIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Competitive Analysis Report
          </h1>
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-gray-600 mb-8">
            <div className="flex items-center gap-2">
              <BuildingOfficeIcon className="h-5 w-5 text-gray-600" />
              <span className="font-semibold">Company:</span> {companyName}
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">Competitors:</span> {competitors.join(', ')}
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        {structuredData.executive_summary && (
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                <ChartBarIcon className="w-6 h-6 text-gray-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Executive Summary</h2>
                <p className="text-sm sm:text-base text-gray-600">Key findings at a glance</p>
              </div>
            </div>
            <p className="text-gray-700 leading-relaxed">{structuredData.executive_summary}</p>
          </div>
        )}

        {/* Market Positioning */}
        {structuredData.market_positioning && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mr-4">
                  <BuildingOfficeIcon className="w-6 h-6 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Market Positioning</h2>
                  <p className="text-sm sm:text-base text-gray-600">How companies position themselves</p>
                </div>
              </div>

              {/* Your Company */}
              {structuredData.market_positioning.your_company && (
                <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h3 className="font-semibold text-gray-900 mb-2">{companyName}</h3>
                  <p className="text-gray-700">{structuredData.market_positioning.your_company}</p>
                </div>
              )}

              {/* Competitors */}
              {structuredData.market_positioning.competitors && structuredData.market_positioning.competitors.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {structuredData.market_positioning.competitors.map((competitor, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                      <h3 className="font-bold text-lg text-gray-900 mb-3">{competitor.name}</h3>
                      <p className="text-sm text-gray-700 mb-4">{competitor.positioning}</p>
                      
                      {competitor.pricing && (
                        <div className="mb-4">
                          <span className="text-xs font-semibold text-gray-600 uppercase">Pricing:</span>
                          <p className="text-sm text-gray-700 mt-1">{competitor.pricing}</p>
                        </div>
                      )}

                      {competitor.strengths && competitor.strengths.length > 0 && (
                        <div className="mb-4">
                          <span className="text-xs font-semibold text-green-700 uppercase">Strengths:</span>
                          <ul className="mt-2 space-y-1">
                            {competitor.strengths.map((strength, i) => (
                              <li key={i} className="text-sm text-gray-700 flex items-start">
                                <CheckCircleIcon className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                                {strength}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {competitor.weaknesses && competitor.weaknesses.length > 0 && (
                        <div>
                          <span className="text-xs font-semibold text-red-700 uppercase">Weaknesses:</span>
                          <ul className="mt-2 space-y-1">
                            {competitor.weaknesses.map((weakness, i) => (
                              <li key={i} className="text-sm text-gray-700 flex items-start">
                                <XCircleIcon className="w-4 h-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                                {weakness}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Competitive Advantages & Disadvantages */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Advantages */}
          {structuredData.competitive_advantages && structuredData.competitive_advantages.length > 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                  <ArrowTrendingUpIcon className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Competitive Advantages</h3>
                  <p className="text-sm text-gray-600">Your strengths</p>
                </div>
              </div>
              <div className="space-y-3">
                {structuredData.competitive_advantages.map((advantage, index) => (
                  <div key={index} className="flex items-start p-3 bg-green-50 rounded-lg border border-green-200">
                    <CheckCircleIcon className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{advantage}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Disadvantages */}
          {structuredData.competitive_disadvantages && structuredData.competitive_disadvantages.length > 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mr-4">
                  <ArrowTrendingDownIcon className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Areas of Concern</h3>
                  <p className="text-sm text-gray-600">Areas to improve</p>
                </div>
              </div>
              <div className="space-y-3">
                {structuredData.competitive_disadvantages.map((disadvantage, index) => (
                  <div key={index} className="flex items-start p-3 bg-red-50 rounded-lg border border-red-200">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{disadvantage}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Market Opportunities & Threats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Opportunities */}
          {structuredData.market_opportunities && structuredData.market_opportunities.length > 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                  <LightBulbIcon className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Market Opportunities</h3>
                  <p className="text-sm text-gray-600">Growth potential</p>
                </div>
              </div>
              <div className="space-y-3">
                {structuredData.market_opportunities.map((opportunity, index) => (
                  <div key={index} className="flex items-start p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <LightBulbIcon className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{opportunity}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Threats */}
          {structuredData.market_threats && structuredData.market_threats.length > 0 && (
            <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mr-4">
                  <ExclamationTriangleIcon className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Market Threats</h3>
                  <p className="text-sm text-gray-600">Risks to watch</p>
                </div>
              </div>
              <div className="space-y-3">
                {structuredData.market_threats.map((threat, index) => (
                  <div key={index} className="flex items-start p-3 bg-orange-50 rounded-lg border border-orange-200">
                    <ExclamationTriangleIcon className="w-5 h-5 text-orange-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{threat}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Strategic Recommendations */}
        {structuredData.strategic_recommendations && structuredData.strategic_recommendations.length > 0 && (
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center mr-4">
                <LightBulbIcon className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Strategic Recommendations</h2>
                <p className="text-sm sm:text-base text-gray-600">Actionable next steps</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {structuredData.strategic_recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    <span className="text-white font-bold text-sm">{index + 1}</span>
                  </div>
                  <span className="text-gray-700 font-medium">{recommendation}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Insights */}
        {structuredData.key_insights && structuredData.key_insights.length > 0 && (
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mr-4">
                <ChartBarIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Key Insights</h2>
                <p className="text-sm sm:text-base text-gray-600">Important takeaways</p>
              </div>
            </div>
            <div className="space-y-3">
              {structuredData.key_insights.map((insight, index) => (
                <div key={index} className="flex items-start p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <ChartBarIcon className="w-5 h-5 text-purple-600 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{insight}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>Report generated by AI Multi-Agent System</p>
          <p className="mt-2">Generated on {new Date().toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}</p>
        </div>
      </div>
    </div>
  );
}

