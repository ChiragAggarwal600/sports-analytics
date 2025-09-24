import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Line, Bar } from 'react-chartjs-2';
import { format, subDays } from 'date-fns';
import { api } from '../services/api';
import SportSelector from '../components/Dashboard/SportSelector';
import EngagementHeatmap from '../components/Charts/EngagementHeatmap';

const EngagementMetrics: React.FC = () => {
  const [selectedSport, setSelectedSport] = useState('all');
  const [dateRange, setDateRange] = useState({
    start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd'),
  });

  const { data: engagementData, isLoading } = useQuery(
    ['engagement', selectedSport, dateRange],
    () => api.getEngagementHistory(selectedSport, dateRange.start, dateRange.end)
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Engagement Metrics</h1>
        <div className="flex gap-4">
          <SportSelector value={selectedSport} onChange={setSelectedSport} />
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          />
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          title="Avg Engagement"
          value={engagementData?.avgEngagement || '0%'}
          trend={engagementData?.trend || 'stable'}
        />
        <MetricCard
          title="Peak Engagement"
          value={engagementData?.peakEngagement || '0%'}
          trend="up"
        />
        <MetricCard
          title="Total Interactions"
          value={engagementData?.totalInteractions || '0'}
          trend="up"
        />
        <MetricCard
          title="Engagement Rate"
          value={engagementData?.engagementRate || '0%'}
          trend={engagementData?.rateTrend || 'stable'}
        />
      </div>

      {/* Engagement Heatmap */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Engagement Heatmap (Time of Day)</h2>
        <EngagementHeatmap data={engagementData} />
      </div>

      {/* Engagement Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Daily Engagement Trend</h2>
          {isLoading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="h-64">
              <Line
                data={{
                  labels: engagementData?.data?.map((d: any) => 
                    format(new Date(d.date), 'MMM dd')
                  ) || [],
                  datasets: [{
                    label: 'Engagement',
                    data: engagementData?.data?.map((d: any) => d.engagement * 100) || [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                  }],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: {
                      beginAtZero: true,
                      max: 100,
                    },
                  },
                }}
              />
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Platform Comparison</h2>
          <div className="h-64">
            <Bar
              data={{
                labels: ['Twitter', 'Instagram', 'Facebook', 'LinkedIn'],
                datasets: [{
                  label: 'Engagement Rate',
                  data: [65, 78, 45, 32],
                  backgroundColor: [
                    'rgba(29, 161, 242, 0.6)',
                    'rgba(225, 48, 108, 0.6)',
                    'rgba(24, 119, 242, 0.6)',
                    'rgba(0, 119, 181, 0.6)',
                  ],
                }],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{
  title: string;
  value: string;
  trend: string;
}> = ({ title, value, trend }) => {
  const getTrendIcon = () => {
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-600';
    if (trend === 'down') return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <p className="text-sm text-gray-600">{title}</p>
      <div className="flex items-baseline gap-2 mt-2">
        <p className="text-2xl font-bold">{value}</p>
        <span className={`text-lg ${getTrendColor()}`}>{getTrendIcon()}</span>
      </div>
    </div>
  );
};

export default EngagementMetrics;