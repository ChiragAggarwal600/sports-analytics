import React from 'react';

interface RiskMeterProps {
  level: number; // 0-1
}

const RiskMeter: React.FC<RiskMeterProps> = ({ level }) => {
  const rotation = level * 180 - 90; // Convert to degrees
  
  const getRiskLabel = (level: number) => {
    if (level < 0.3) return 'Low';
    if (level < 0.6) return 'Medium';
    if (level < 0.8) return 'High';
    return 'Critical';
  };
  
  const getRiskColor = (level: number) => {
    if (level < 0.3) return 'text-green-600';
    if (level < 0.6) return 'text-yellow-600';
    if (level < 0.8) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="relative w-48 h-24 mx-auto">
        {/* Meter arc */}
        <svg className="absolute inset-0" viewBox="0 0 200 100">
          <path
            d="M 20 80 A 70 70 0 0 1 180 80"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="20"
          />
          <path
            d="M 20 80 A 70 70 0 0 1 180 80"
            fill="none"
            stroke="url(#gradient)"
            strokeWidth="20"
            strokeDasharray={`${level * 220} 220`}
          />
          
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22c55e" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>
          
          {/* Needle */}
          <line
            x1="100"
            y1="80"
            x2="100"
            y2="20"
            stroke="#1f2937"
            strokeWidth="3"
            transform={`rotate(${rotation} 100 80)`}
          />
          
          <circle cx="100" cy="80" r="5" fill="#1f2937" />
        </svg>
      </div>
      
      <div className="text-center mt-4">
        <p className={`text-2xl font-bold ${getRiskColor(level)}`}>
          {getRiskLabel(level)}
        </p>
        <p className="text-sm text-gray-600 mt-1">
          Risk Level: {(level * 100).toFixed(0)}%
        </p>
      </div>
    </div>
  );
};

export default RiskMeter;