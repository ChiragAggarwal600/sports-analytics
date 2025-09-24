import React, { useState } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface SportSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const SportSelector: React.FC<SportSelectorProps> = ({ value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const sports = [
    { value: 'all', label: 'All Sports', emoji: '🏆', gradient: 'from-purple-500 to-pink-500' },
    { value: 'cricket', label: 'Cricket', emoji: '🏏', gradient: 'from-green-500 to-emerald-500' },
    { value: 'football', label: 'Football', emoji: '⚽', gradient: 'from-blue-500 to-cyan-500' },
    { value: 'basketball', label: 'Basketball', emoji: '🏀', gradient: 'from-orange-500 to-red-500' },
    { value: 'tennis', label: 'Tennis', emoji: '🎾', gradient: 'from-yellow-500 to-orange-500' },
  ];

  const selectedSport = sports.find(sport => sport.value === value) || sports[0];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-6 py-3 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all duration-300 shadow-lg hover:shadow-xl font-medium text-gray-700 min-w-48"
      >
        <div className={`w-8 h-8 rounded-xl bg-gradient-to-br ${selectedSport.gradient} flex items-center justify-center text-white shadow-lg`}>
          <span className="text-sm">{selectedSport.emoji}</span>
        </div>
        <div className="flex-1 text-left">
          <span className="font-semibold">{selectedSport.label}</span>
        </div>
        <ChevronDownIcon className={`w-5 h-5 text-gray-400 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute top-full left-0 mt-2 w-full bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200/50 z-20 overflow-hidden">
            {sports.map((sport) => (
              <button
                key={sport.value}
                onClick={() => {
                  onChange(sport.value);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50/80 transition-all duration-200 ${
                  sport.value === value ? 'bg-blue-50/50 border-l-4 border-blue-500' : ''
                }`}
              >
                <div className={`w-8 h-8 rounded-xl bg-gradient-to-br ${sport.gradient} flex items-center justify-center text-white shadow-md`}>
                  <span className="text-sm">{sport.emoji}</span>
                </div>
                <div className="flex-1 text-left">
                  <span className={`font-medium ${sport.value === value ? 'text-blue-700' : 'text-gray-700'}`}>
                    {sport.label}
                  </span>
                </div>
                {sport.value === value && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default SportSelector;