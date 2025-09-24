import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { ChartBarIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { format } from 'date-fns';

import SentimentTrendChart from '../components/Charts/SentimentTrendChart';
import EngagementHeatmap from '../components/Charts/EngagementHeatmap';
import PRRecommendationCard from '../components/Cards/PRRecommendationCard';
import RiskMeter from '../components/Dashboard/RiskMeter';
import SportSelector from '../components/Dashboard/SportSelector';
import { api } from '../services/api';
import { DashboardData } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const Dashboard: React.FC = () => {
  const [selectedSport, setSelectedSport] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('7d');

  const { data: dashboardData, isLoading, error } = useQuery(
    ['dashboard', selectedSport, timeRange],
    () => api.getDashboardData(selectedSport, timeRange),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600">Error loading dashboard data</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-6 bg-white/60 backdrop-blur-sm rounded-3xl p-8 border border-gray-200/50 shadow-xl">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-indigo-800 bg-clip-text text-transparent">
            Sports PR Analytics
          </h1>
          <p className="text-gray-600 mt-2 text-lg">Real-time insights across all sports campaigns</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative">
            <SportSelector value={selectedSport} onChange={setSelectedSport} />
          </div>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-6 py-3 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all duration-300 shadow-lg font-medium text-gray-700"
          >
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Overall Sentiment"
          value={dashboardData?.metrics.sentiment.toFixed(2) || '0'}
          change={dashboardData?.metrics.sentimentChange || 0}
          color="blue"
        />
        <MetricCard
          title="Engagement Rate"
          value={`${(dashboardData?.metrics.engagement * 100).toFixed(1)}%`}
          change={dashboardData?.metrics.engagementChange || 0}
          color="green"
        />
        <MetricCard
          title="Brand Mentions"
          value={dashboardData?.metrics.mentions || '0'}
          change={dashboardData?.metrics.mentionsChange || 0}
          color="purple"
        />
        <MetricCard
          title="Risk Level"
          value={dashboardData?.metrics.riskLevel || 'Low'}
          change={0}
          color="red"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <div className="bg-white/80 backdrop-blur-sm p-8 rounded-3xl shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-500">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-lg">
              <ChatBubbleLeftRightIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Sentiment Trends</h2>
              <p className="text-gray-600">Real-time sentiment analysis</p>
            </div>
          </div>
          <div className="relative">
            <SentimentTrendChart data={dashboardData?.sentimentTrends} />
          </div>
        </div>
        <div className="bg-white/80 backdrop-blur-sm p-8 rounded-3xl shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-500">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-lg">
              <ChartBarIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Engagement Heatmap</h2>
              <p className="text-gray-600">Audience interaction patterns</p>
            </div>
          </div>
          <div className="relative">
            <EngagementHeatmap data={dashboardData?.engagementData} />
          </div>
        </div>
      </div>

      {/* PR Recommendations and Risk Assessment */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">PR Recommendations</h2>
          <div className="space-y-4">
            {dashboardData?.recommendations.map((rec, index) => (
              <PRRecommendationCard key={index} recommendation={rec} />
            ))}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Risk Assessment</h2>
          <RiskMeter level={dashboardData?.riskAssessment.overall || 0} />
          <div className="mt-4 bg-white p-4 rounded-lg shadow">
            <h3 className="font-semibold mb-2">Risk Factors</h3>
            <div className="space-y-2">
              {Object.entries(dashboardData?.riskAssessment.factors || {}).map(
                ([factor, level]) => (
                  <div key={factor} className="flex justify-between">
                    <span className="text-sm text-gray-600">{factor}</span>
                    <span
                      className={`text-sm font-medium ${
                        level > 0.5 ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {(level * 100).toFixed(0)}%
                    </span>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sport Performance Comparison */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Cross-Sport Performance</h2>
        <div className="h-64">
          <Bar
            data={{
              labels: ['Cricket', 'Football', 'Basketball', 'Tennis'],
              datasets: [
                {
                  label: 'Sentiment',
                  data: dashboardData?.sportComparison.sentiment || [],
                  backgroundColor: 'rgba(59, 130, 246, 0.5)',
                },
                {
                  label: 'Engagement',
                  data: dashboardData?.sportComparison.engagement || [],
                  backgroundColor: 'rgba(16, 185, 129, 0.5)',
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true,
                  max: 1,
                },
              },
            }}
          />
        </div>
      </div>
    </div>
  );
};

type ColorKey = 'blue' | 'green' | 'purple' | 'red';

const MetricCard: React.FC<{
  title: string;
  value: string;
  change: number;
  color: ColorKey;
}> = ({ title, value, change, color }) => {
  const colorClasses: Record<ColorKey, { bg: string; text: string; gradient: string; shadow: string }> = {
    blue: { 
      bg: 'from-blue-50 to-blue-100', 
      text: 'text-blue-800', 
      gradient: 'from-blue-500 to-blue-600',
      shadow: 'shadow-blue-500/20'
    },
    green: { 
      bg: 'from-green-50 to-green-100', 
      text: 'text-green-800', 
      gradient: 'from-green-500 to-green-600',
      shadow: 'shadow-green-500/20'
    },
    purple: { 
      bg: 'from-purple-50 to-purple-100', 
      text: 'text-purple-800', 
      gradient: 'from-purple-500 to-purple-600',
      shadow: 'shadow-purple-500/20'
    },
    red: { 
      bg: 'from-red-50 to-red-100', 
      text: 'text-red-800', 
      gradient: 'from-red-500 to-red-600',
      shadow: 'shadow-red-500/20'
    },
  };

  const colorConfig = colorClasses[color];

  return (
    <div className={`relative bg-white/80 backdrop-blur-sm p-8 rounded-3xl shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 overflow-hidden group ${colorConfig.shadow}`}>
      {/* Background Gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${colorConfig.bg} opacity-50 group-hover:opacity-70 transition-opacity duration-500`}></div>
      
      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 mb-2 uppercase tracking-wider">{title}</p>
            <p className="text-4xl font-bold text-gray-900 mb-1">{value}</p>
          </div>
          <div className={`px-4 py-2 rounded-2xl text-sm font-bold shadow-lg ${colorConfig.text} bg-gradient-to-r ${colorConfig.bg} border border-white/50`}>
            {change > 0 ? '+' : ''}
            {change.toFixed(1)}%
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200/50 rounded-full h-2 mb-3">
          <div 
            className={`h-2 rounded-full bg-gradient-to-r ${colorConfig.gradient} transition-all duration-1000 ease-out`}
            style={{ width: `${Math.min(Math.abs(change) * 10, 100)}%` }}
          ></div>
        </div>
        
        {/* Trend Indicator */}
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${change > 0 ? 'bg-green-500 animate-pulse' : change < 0 ? 'bg-red-500 animate-pulse' : 'bg-gray-400'}`}></div>
          <span className="text-xs font-medium text-gray-600">
            {change > 0 ? 'Trending Up' : change < 0 ? 'Trending Down' : 'Stable'}
          </span>
        </div>
      </div>
      
      {/* Decorative Elements */}
      <div className="absolute -top-10 -right-10 w-20 h-20 bg-white/10 rounded-full blur-xl"></div>
      <div className="absolute -bottom-5 -left-5 w-15 h-15 bg-white/10 rounded-full blur-lg"></div>
    </div>
  );
};

export default Dashboard;