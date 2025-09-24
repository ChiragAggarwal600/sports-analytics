import axios, { AxiosInstance } from 'axios';
import { toast } from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.detail || 'An error occurred';
        toast.error(message);
        return Promise.reject(error);
      }
    );
  }

  // Dashboard
  async getDashboardData(sport: string, timeRange: string) {
    const response = await this.client.get('/dashboard', {
      params: { sport, time_range: timeRange },
    });
    return response.data;
  }

  // Sentiment Analysis
  async analyzeSentiment(texts: string[], sport?: string) {
    const response = await this.client.post('/sentiment/predict', {
      texts,
      sport: sport || 'general',
    });
    return response.data;
  }

  async getSentimentHistory(sport: string, days: number = 7) {
    const response = await this.client.get('/sentiment/history', {
      params: { sport, days },
    });
    return response.data;
  }

  // Engagement Prediction
  async predictEngagement(sport: string, data: any) {
    const response = await this.client.post('/engagement/predict', {
      sport,
      data,
      include_confidence: true,
    });
    return response.data;
  }

  async getEngagementHistory(sport: string, startDate: string, endDate: string) {
    const response = await this.client.post('/engagement/historical', {
      sport,
      start_date: startDate,
      end_date: endDate,
      granularity: 'daily',
    });
    return response.data;
  }

  // PR Strategy
  async getPRRecommendation(params: {
    sport: string;
    current_sentiment: number;
    current_engagement: number;
    budget_remaining: number;
    crisis_level: number;
  }) {
    const response = await this.client.post('/pr-strategy/recommend', params);
    return response.data;
  }

  async simulatePRCampaign(
    strategy: string,
    duration: number,
    sport: string,
    initialSentiment: number,
    initialEngagement: number
  ) {
    const response = await this.client.post('/pr-strategy/simulate', {
      strategy,
      duration_days: duration,
      sport,
      initial_sentiment: initialSentiment,
      initial_engagement: initialEngagement,
    });
    return response.data;
  }

  // Real-time data
  subscribeToRealTimeUpdates(callback: (data: any) => void) {
    // WebSocket connection for real-time updates
    const ws = new WebSocket(`ws://localhost:8000/ws`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback(data);
    };

    return () => ws.close();
  }
}

export const api = new ApiService();