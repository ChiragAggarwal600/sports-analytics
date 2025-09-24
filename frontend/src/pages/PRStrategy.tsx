import React, { useState } from 'react';
import { useMutation } from 'react-query';
import { toast } from 'react-hot-toast';
import { api } from '../services/api';
import PRRecommendationCard from '../components/Cards/PRRecommendationCard';
import RiskMeter from '../components/Dashboard/RiskMeter';

const PRStrategy: React.FC = () => {
  const [formData, setFormData] = useState({
    sport: 'cricket',
    current_sentiment: 0.5,
    current_engagement: 0.5,
    budget_remaining: 1.0,
    crisis_level: 0,
  });

  const [recommendation, setRecommendation] = useState<any>(null);
  const [simulationResults, setSimulationResults] = useState<any>(null);

  const recommendMutation = useMutation(
    () => api.getPRRecommendation(formData),
    {
      onSuccess: (data) => {
        setRecommendation(data);
        toast.success('Strategy recommendation generated!');
      },
      onError: () => {
        toast.error('Failed to generate recommendation');
      },
    }
  );

  const simulateMutation = useMutation(
    (params: any) => api.simulatePRCampaign(
      params.strategy,
      params.duration,
      formData.sport,
      formData.current_sentiment,
      formData.current_engagement
    ),
    {
      onSuccess: (data) => {
        setSimulationResults(data);
        toast.success('Simulation completed!');
      },
    }
  );

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">PR Strategy Optimizer</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Current Situation</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sport
              </label>
              <select
                value={formData.sport}
                onChange={(e) => setFormData({ ...formData, sport: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="cricket">Cricket</option>
                <option value="football">Football</option>
                <option value="basketball">Basketball</option>
                <option value="tennis">Tennis</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Sentiment: {(formData.current_sentiment * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={formData.current_sentiment * 100}
                onChange={(e) => setFormData({
                  ...formData,
                  current_sentiment: Number(e.target.value) / 100
                })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Engagement: {(formData.current_engagement * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={formData.current_engagement * 100}
                onChange={(e) => setFormData({
                  ...formData,
                  current_engagement: Number(e.target.value) / 100
                })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Budget Remaining: {(formData.budget_remaining * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={formData.budget_remaining * 100}
                onChange={(e) => setFormData({
                  ...formData,
                  budget_remaining: Number(e.target.value) / 100
                })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Crisis Level: {(formData.crisis_level * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={formData.crisis_level * 100}
                onChange={(e) => setFormData({
                  ...formData,
                  crisis_level: Number(e.target.value) / 100
                })}
                className="w-full"
              />
            </div>

            <button
              onClick={() => recommendMutation.mutate()}
              disabled={recommendMutation.isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {recommendMutation.isLoading ? 'Generating...' : 'Get Recommendation'}
            </button>
          </div>
        </div>

        {/* Recommendation */}
        <div className="lg:col-span-2 space-y-6">
          {recommendation && (
            <>
              <PRRecommendationCard
                recommendation={{
                  action: recommendation.recommended_action.action,
                  description: recommendation.recommended_action.description,
                  confidence: recommendation.recommended_action.confidence,
                  expectedImpact: recommendation.expected_outcomes.sentiment_change,
                  timing: recommendation.timing_recommendation.recommended_time,
                  cost: `$${(recommendation.expected_outcomes.cost_efficiency * 10000).toFixed(0)}`,
                }}
              />

              <RiskMeter level={recommendation.risk_assessment.overall_risk} />

              {/* Alternative Strategies */}
              {recommendation.alternative_strategies?.length > 0 && (
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold mb-4">Alternative Strategies</h3>
                  <div className="space-y-3">
                    {recommendation.alternative_strategies.map((alt: any, index: number) => (
                      <div key={index} className="border-l-4 border-gray-300 pl-4">
                        <p className="font-medium">{alt.action}</p>
                        <p className="text-sm text-gray-600">{alt.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Campaign Simulator */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Campaign Simulator</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <select
            id="strategy"
            className="px-3 py-2 border border-gray-300 rounded-lg"
          >
            <option value="aggressive">Aggressive</option>
            <option value="moderate">Moderate</option>
            <option value="conservative">Conservative</option>
          </select>
          
          <input
            type="number"
            id="duration"
            placeholder="Duration (days)"
            defaultValue={7}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          />
          
          <button
            onClick={() => {
              const strategy = (document.getElementById('strategy') as HTMLSelectElement).value;
              const duration = Number((document.getElementById('duration') as HTMLInputElement).value);
              simulateMutation.mutate({ strategy, duration });
            }}
            className="bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
          >
            Run Simulation
          </button>
        </div>

        {simulationResults && (
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Simulation Results</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Final Sentiment</p>
                <p className="text-lg font-semibold">
                  {(simulationResults.summary.final_sentiment * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Final Engagement</p>
                <p className="text-lg font-semibold">
                  {(simulationResults.summary.final_engagement * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Cost</p>
                <p className="text-lg font-semibold">
                  ${(simulationResults.summary.total_cost * 10000).toFixed(0)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">ROI</p>
                <p className="text-lg font-semibold">
                  {((simulationResults.summary.sentiment_improvement + 
                     simulationResults.summary.engagement_improvement) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PRStrategy;