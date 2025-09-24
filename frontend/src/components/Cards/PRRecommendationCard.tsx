import React from 'react';
import { ClockIcon, CurrencyDollarIcon, ArrowTrendingUpIcon, CheckCircleIcon, SparklesIcon } from '@heroicons/react/24/outline';

interface PRRecommendationProps {
  recommendation: {
    action: string;
    description: string;
    confidence: number;
    expectedImpact: number;
    timing: string;
    cost: string;
  };
}

const PRRecommendationCard: React.FC<PRRecommendationProps> = ({ recommendation }) => {
  const getConfidenceConfig = (confidence: number) => {
    if (confidence > 0.8) return {
      color: 'text-green-600',
      bg: 'from-green-50 to-green-100',
      border: 'border-green-200',
      shadow: 'shadow-green-500/10',
      icon: 'text-green-600'
    };
    if (confidence > 0.5) return {
      color: 'text-amber-600',
      bg: 'from-amber-50 to-amber-100',
      border: 'border-amber-200',
      shadow: 'shadow-amber-500/10',
      icon: 'text-amber-600'
    };
    return {
      color: 'text-red-600',
      bg: 'from-red-50 to-red-100',
      border: 'border-red-200',
      shadow: 'shadow-red-500/10',
      icon: 'text-red-600'
    };
  };

  const confidenceConfig = getConfidenceConfig(recommendation.confidence);

  return (
    <div className={`relative bg-white/90 backdrop-blur-sm rounded-3xl p-8 border ${confidenceConfig.border} ${confidenceConfig.shadow} shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 overflow-hidden group`}>
      {/* Background Gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${confidenceConfig.bg} opacity-30 group-hover:opacity-50 transition-opacity duration-500`}></div>
      
      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1 pr-4">
            <div className="flex items-center gap-3 mb-3">
              <div className={`p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-lg`}>
                <SparklesIcon className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">{recommendation.action}</h3>
            </div>
            <p className="text-gray-600 leading-relaxed">{recommendation.description}</p>
          </div>
          <div className={`px-4 py-2 rounded-2xl text-sm font-bold ${confidenceConfig.color} bg-gradient-to-r ${confidenceConfig.bg} border ${confidenceConfig.border} shadow-lg flex items-center gap-2`}>
            <CheckCircleIcon className={`w-4 h-4 ${confidenceConfig.icon}`} />
            {(recommendation.confidence * 100).toFixed(0)}% confidence
          </div>
        </div>
        
        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="text-center p-4 bg-white/60 rounded-2xl border border-gray-200/50 shadow-sm">
            <div className="flex justify-center mb-2">
              <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg">
                <ArrowTrendingUpIcon className="h-5 w-5 text-white" />
              </div>
            </div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Expected Impact</p>
            <p className="text-lg font-bold text-green-600">
              +{(recommendation.expectedImpact * 100).toFixed(0)}%
            </p>
          </div>
          
          <div className="text-center p-4 bg-white/60 rounded-2xl border border-gray-200/50 shadow-sm">
            <div className="flex justify-center mb-2">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
                <ClockIcon className="h-5 w-5 text-white" />
              </div>
            </div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Timeline</p>
            <p className="text-lg font-bold text-blue-600">{recommendation.timing}</p>
          </div>
          
          <div className="text-center p-4 bg-white/60 rounded-2xl border border-gray-200/50 shadow-sm">
            <div className="flex justify-center mb-2">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
                <CurrencyDollarIcon className="h-5 w-5 text-white" />
              </div>
            </div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Investment</p>
            <p className="text-lg font-bold text-purple-600">{recommendation.cost}</p>
          </div>
        </div>
        
        {/* Action Button */}
        <button className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 flex items-center justify-center gap-3">
          <SparklesIcon className="w-5 h-5" />
          Execute Strategy
          <div className="w-2 h-2 bg-white/80 rounded-full animate-pulse"></div>
        </button>
      </div>
      
      {/* Decorative Elements */}
      <div className="absolute -top-8 -right-8 w-16 h-16 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-xl"></div>
      <div className="absolute -bottom-6 -left-6 w-12 h-12 bg-gradient-to-br from-green-400/20 to-blue-400/20 rounded-full blur-lg"></div>
    </div>
  );
};

export default PRRecommendationCard;