import React from 'react';
import { Line } from 'react-chartjs-2';
import { format } from 'date-fns';

interface SentimentTrendChartProps {
  data: any;
}

const SentimentTrendChart: React.FC<SentimentTrendChartProps> = ({ data }) => {
  if (!data) {
    return <div>No data available</div>;
  }

  const chartData = {
    labels: data.dates?.map((d: string) => format(new Date(d), 'MMM dd')) || [],
    datasets: [
      {
        label: 'Positive',
        data: data.positive || [],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Neutral',
        data: data.neutral || [],
        borderColor: 'rgb(156, 163, 175)',
        backgroundColor: 'rgba(156, 163, 175, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Negative',
        data: data.negative || [],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 1,
      },
    },
  };

  return (
    <div className="h-64">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default SentimentTrendChart;