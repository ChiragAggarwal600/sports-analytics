import React from 'react';
import { ClockIcon, CurrencyDollarIcon, TrendingUpIcon } from '@heroicons/react/24/outline';

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
  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'text-green-600';
    if (confidence > 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{recommendation.action}</h3>
          <p className="text-sm text-gray-600 mt-1">{recommendation.description}</p>
        </div>
        <span className={`text-sm font-medium ${getConfidenceColor(recommendation.confidence)}`}>
          {(recommendation.confidence * 100).toFixed(0)}% confidence
        </span>
      </div>
      
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="flex items-center gap-2">
          <TrendingUpIcon className="h-4 w-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">Impact</p>
            <p className="text-sm font-medium">
              +{(recommendation.expectedImpact * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <ClockIcon className="h-4 w-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">Timing</p>
            <p className="text-sm font-medium">{recommendation.timing}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <CurrencyDollarIcon className="h-4 w-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">Cost</p>
            <p className="text-sm font-medium">{recommendation.cost}</p>
          </div>
        </div>
      </div>
      
      <button className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
        Execute Strategy
      </button>
    </div>
  );
};

export default PRRecommendationCard;