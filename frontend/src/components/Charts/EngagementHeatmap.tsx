import React from 'react';

interface EngagementHeatmapProps {
  data: any;
}

const EngagementHeatmap: React.FC<EngagementHeatmapProps> = ({ data }) => {
  if (!data) {
    return <div>No data available</div>;
  }

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const getColor = (value: number) => {
    if (value > 0.8) return 'bg-green-600';
    if (value > 0.6) return 'bg-green-500';
    if (value > 0.4) return 'bg-yellow-500';
    if (value > 0.2) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        <div className="grid grid-cols-25 gap-1">
          <div></div>
          {hours.map((hour) => (
            <div key={hour} className="text-xs text-center text-gray-600">
              {hour}
            </div>
          ))}
          
          {days.map((day, dayIndex) => (
            <React.Fragment key={day}>
              <div className="text-xs text-gray-600 flex items-center">{day}</div>
              {hours.map((hour) => {
                const value = data?.heatmap?.[dayIndex]?.[hour] || Math.random();
                return (
                  <div
                    key={`${day}-${hour}`}
                    className={`h-8 w-full ${getColor(value)} opacity-75 hover:opacity-100 transition-opacity cursor-pointer`}
                    title={`${day} ${hour}:00 - ${(value * 100).toFixed(0)}%`}
                  />
                );
              })}
            </React.Fragment>
          ))}
        </div>
        
        {/* Legend */}
        <div className="mt-4 flex items-center gap-4 text-xs">
          <span>Low</span>
          <div className="flex gap-1">
            <div className="h-4 w-8 bg-red-500"></div>
            <div className="h-4 w-8 bg-orange-500"></div>
            <div className="h-4 w-8 bg-yellow-500"></div>
            <div className="h-4 w-8 bg-green-500"></div>
            <div className="h-4 w-8 bg-green-600"></div>
          </div>
          <span>High</span>
        </div>
      </div>
    </div>
  );
};

export default EngagementHeatmap;