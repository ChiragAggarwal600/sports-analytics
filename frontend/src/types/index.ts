export interface Sport {
  id: string;
  name: string;
  description: string;
}

export interface SentimentData {
  text: string;
  positive: number;
  negative: number;
  neutral: number;
  overall: 'positive' | 'negative' | 'neutral';
}

export interface EngagementData {
  date: string;
  sport: string;
  engagement_score: number;
  confidence?: number;
  factors: {
    timing: string;
    sentiment: string;
    competition: string;
    content_quality: string;
  };
}

export interface PRRecommendation {
  action: string;
  description: string;
  confidence: number;
  expected_impact: number;
  timing: string;
  cost: string;
  alternative_actions?: PRRecommendation[];
}

export interface DashboardData {
  metrics: {
    sentiment: number;
    sentimentChange: number;
    engagement: number;
    engagementChange: number;
    mentions: number;
    mentionsChange: number;
    riskLevel: string;
  };
  sentimentTrends: {
    dates: string[];
    positive: number[];
    negative: number[];
    neutral: number[];
  };
  engagementData: {
    heatmap: number[][];
  };
  recommendations: PRRecommendation[];
  riskAssessment: {
    overall: number;
    factors: Record<string, number>;
  };
  sportComparison: {
    sentiment: number[];
    engagement: number[];
  };
}

export interface Campaign {
  id: string;
  name: string;
  sport: string;
  strategy: string;
  startDate: string;
  endDate: string;
  budget: number;
  targetSentiment: number;
  targetEngagement: number;
  status: 'planned' | 'active' | 'completed';
}