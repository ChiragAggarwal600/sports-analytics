import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { toast } from 'react-hot-toast';
import { api } from '../services/api';
import SentimentTrendChart from '../components/Charts/SentimentTrendChart';
import SportSelector from '../components/Dashboard/SportSelector';

const SentimentAnalysis: React.FC = () => {
  const [selectedSport, setSelectedSport] = useState('all');
  const [textInput, setTextInput] = useState('');
  const [analysisResults, setAnalysisResults] = useState<any[]>([]);

  const { data: historicalData, isLoading } = useQuery(
    ['sentiment-history', selectedSport],
    () => api.getSentimentHistory(selectedSport, 30)
  );

  const analyzeMutation = useMutation(
    (texts: string[]) => api.analyzeSentiment(texts, selectedSport),
    {
      onSuccess: (data) => {
        setAnalysisResults(data.results);
        toast.success('Analysis completed!');
      },
      onError: () => {
        toast.error('Analysis failed');
      },
    }
  );

  const handleAnalyze = () => {
    const texts = textInput.split('\n').filter((t) => t.trim());
    if (texts.length > 0) {
      analyzeMutation.mutate(texts);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Sentiment Analysis</h1>
        <SportSelector value={selectedSport} onChange={setSelectedSport} />
      </div>

      {/* Historical Trends */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Historical Sentiment Trends</h2>
        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <SentimentTrendChart data={historicalData} />
        )}
      </div>

      {/* Real-time Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Analyze Text</h2>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Enter text to analyze (one per line)..."
            className="w-full h-40 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleAnalyze}
            disabled={analyzeMutation.isLoading}
            className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {analyzeMutation.isLoading ? 'Analyzing...' : 'Analyze Sentiment'}
          </button>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {analysisResults.map((result, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-3">
                <p className="text-sm text-gray-600 truncate">{result.text}</p>
                <div className="flex gap-4 mt-1">
                  <span className="text-xs">
                    Positive: {(result.positive * 100).toFixed(1)}%
                  </span>
                  <span className="text-xs">
                    Negative: {(result.negative * 100).toFixed(1)}%
                  </span>
                  <span className="text-xs font-semibold">
                    Overall: {result.overall}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SentimentAnalysis;