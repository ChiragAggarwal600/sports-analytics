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
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">PR Analytics Dashboard</h1>
        <div className="flex gap-4">
          <SportSelector value={selectedSport} onChange={setSelectedSport} />
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Sentiment Trends</h2>
          <SentimentTrendChart data={dashboardData?.sentimentTrends} />
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Engagement Heatmap</h2>
          <EngagementHeatmap data={dashboardData?.engagementData} />
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

const MetricCard: React.FC<{
  title: string;
  value: string;
  change: number;
  color: string;
}> = ({ title, value, change, color }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    purple: 'bg-purple-100 text-purple-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <div
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            colorClasses[color]
          }`}
        >
          {change > 0 ? '+' : ''}
          {change.toFixed(1)}%
        </div>
      </div>
    </div>
  );
};

export default Dashboard;