import React from 'react';

interface SportSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const SportSelector: React.FC<SportSelectorProps> = ({ value, onChange }) => {
  const sports = [
    { value: 'all', label: 'All Sports', emoji: '🏆' },
    { value: 'cricket', label: 'Cricket', emoji: '🏏' },
    { value: 'football', label: 'Football', emoji: '⚽' },
    { value: 'basketball', label: 'Basketball', emoji: '🏀' },
    { value: 'tennis', label: 'Tennis', emoji: '🎾' },
  ];

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      {sports.map((sport) => (
        <option key={sport.value} value={sport.value}>
          {sport.emoji} {sport.label}
        </option>
      ))}
    </select>
  );
};

export default SportSelector;