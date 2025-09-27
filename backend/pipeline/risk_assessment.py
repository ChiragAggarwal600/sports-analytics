"""
Risk Assessment Engine
Analyzes model outputs to identify PR risks and brand reputation threats
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
import aioredis
from collections import defaultdict, deque
import statistics
from enum import Enum

from config.settings import settings

        # settings imported above
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskCategory(Enum):
    """Risk category enumeration"""
    SENTIMENT = "sentiment"
    ENGAGEMENT = "engagement"
    REPUTATION = "reputation"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"

@dataclass
class RiskAlert:
    """Container for risk alerts"""
    id: str
    risk_level: RiskLevel
    risk_category: RiskCategory
    risk_score: float
    description: str
    affected_entities: List[str]
    contributing_factors: Dict[str, Any]
    recommended_actions: List[str]
    timestamp: datetime
    expires_at: datetime
    metadata: Dict[str, Any]

@dataclass
class RiskAssessment:
    """Container for comprehensive risk assessment"""
    overall_risk_score: float
    risk_level: RiskLevel
    active_alerts: List[RiskAlert]
    risk_trends: Dict[str, float]
    confidence_score: float
    assessment_timestamp: datetime
    next_assessment_due: datetime

class SentimentRiskAnalyzer:
    """Analyzes sentiment-based risks"""
    
    def __init__(self):
        self.sentiment_history = deque(maxlen=1000)
        self.negative_threshold = -0.3
        self.critical_threshold = -0.6
        self.volatility_threshold = 0.4
        
    async def analyze_sentiment_risks(self, predictions: List[Dict[str, Any]]) -> List[RiskAlert]:
        """Analyze sentiment predictions for risks"""
        alerts = []
        
        try:
            # Extract sentiment scores from predictions
            sentiment_scores = []
            for pred in predictions:
                if 'final_prediction' in pred:
                    # Convert prediction to sentiment score
                    sentiment_score = self._convert_prediction_to_sentiment(pred['final_prediction'])
                    sentiment_scores.append({
                        'score': sentiment_score,
                        'confidence': pred.get('ensemble_confidence', 0.5),
                        'timestamp': datetime.fromisoformat(pred.get('timestamp', datetime.now().isoformat()))
                    })
            
            if not sentiment_scores:
                return alerts
            
            # Update sentiment history
            for score_data in sentiment_scores:
                self.sentiment_history.append(score_data)
            
            # Analyze current sentiment
            current_scores = [s['score'] for s in sentiment_scores]
            avg_sentiment = statistics.mean(current_scores)
            
            # Critical negative sentiment alert
            if avg_sentiment <= self.critical_threshold:
                alerts.append(RiskAlert(
                    id=f"sentiment_critical_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    risk_level=RiskLevel.CRITICAL,
                    risk_category=RiskCategory.SENTIMENT,
                    risk_score=min(abs(avg_sentiment) * 100, 100),
                    description=f"Critical negative sentiment detected: {avg_sentiment:.2f}",
                    affected_entities=["brand_reputation", "public_perception"],
                    contributing_factors={
                        "average_sentiment": avg_sentiment,
                        "sample_size": len(current_scores),
                        "confidence": statistics.mean([s['confidence'] for s in sentiment_scores])
                    },
                    recommended_actions=[
                        "Immediate crisis communication response",
                        "Identify and address root causes",
                        "Monitor social media for escalation",
                        "Prepare public statement"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=6),
                    metadata={"analyzer": "sentiment", "threshold_breached": "critical"}
                ))
            
            # High negative sentiment alert
            elif avg_sentiment <= self.negative_threshold:
                risk_level = RiskLevel.HIGH if avg_sentiment <= -0.45 else RiskLevel.MEDIUM
                
                alerts.append(RiskAlert(
                    id=f"sentiment_negative_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    risk_level=risk_level,
                    risk_category=RiskCategory.SENTIMENT,
                    risk_score=abs(avg_sentiment) * 100,
                    description=f"Negative sentiment trend detected: {avg_sentiment:.2f}",
                    affected_entities=["brand_reputation"],
                    contributing_factors={
                        "average_sentiment": avg_sentiment,
                        "sample_size": len(current_scores)
                    },
                    recommended_actions=[
                        "Review recent communications",
                        "Identify sentiment drivers",
                        "Consider proactive messaging",
                        "Monitor sentiment trends"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=12),
                    metadata={"analyzer": "sentiment", "threshold_breached": "negative"}
                ))
            
            # Sentiment volatility alert
            volatility_alert = await self._analyze_sentiment_volatility()
            if volatility_alert:
                alerts.append(volatility_alert)
            
            # Sentiment momentum alert
            momentum_alert = await self._analyze_sentiment_momentum()
            if momentum_alert:
                alerts.append(momentum_alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment risks: {e}")
            return []
    
    def _convert_prediction_to_sentiment(self, prediction: Any) -> float:
        """Convert model prediction to sentiment score"""
        try:
            if isinstance(prediction, (int, float)):
                # Assume 0=negative, 1=neutral, 2=positive
                if prediction == 0:
                    return -0.7  # Negative
                elif prediction == 1:
                    return 0.0   # Neutral
                elif prediction == 2:
                    return 0.7   # Positive
                else:
                    # Continuous score
                    return max(-1.0, min(1.0, float(prediction)))
            return 0.0
        except Exception:
            return 0.0
    
    async def _analyze_sentiment_volatility(self) -> Optional[RiskAlert]:
        """Analyze sentiment volatility for risk"""
        try:
            if len(self.sentiment_history) < 10:
                return None
            
            # Get recent sentiment scores
            recent_scores = [s['score'] for s in list(self.sentiment_history)[-20:]]
            
            # Calculate volatility (standard deviation)
            volatility = statistics.stdev(recent_scores)
            
            if volatility > self.volatility_threshold:
                return RiskAlert(
                    id=f"sentiment_volatility_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    risk_level=RiskLevel.MEDIUM,
                    risk_category=RiskCategory.SENTIMENT,
                    risk_score=min(volatility * 100, 100),
                    description=f"High sentiment volatility detected: {volatility:.2f}",
                    affected_entities=["brand_stability", "message_consistency"],
                    contributing_factors={
                        "volatility_score": volatility,
                        "threshold": self.volatility_threshold,
                        "sample_size": len(recent_scores)
                    },
                    recommended_actions=[
                        "Review message consistency",
                        "Identify volatility drivers",
                        "Stabilize communication strategy",
                        "Monitor for trend patterns"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=8),
                    metadata={"analyzer": "sentiment_volatility"}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment volatility: {e}")
            return None
    
    async def _analyze_sentiment_momentum(self) -> Optional[RiskAlert]:
        """Analyze sentiment momentum for early warning"""
        try:
            if len(self.sentiment_history) < 20:
                return None
            
            # Get recent vs older sentiment
            recent_sentiment = [s['score'] for s in list(self.sentiment_history)[-10:]]
            older_sentiment = [s['score'] for s in list(self.sentiment_history)[-20:-10]]
            
            recent_avg = statistics.mean(recent_sentiment)
            older_avg = statistics.mean(older_sentiment)
            
            momentum = recent_avg - older_avg
            
            # Negative momentum alert
            if momentum < -0.2:
                risk_level = RiskLevel.HIGH if momentum < -0.4 else RiskLevel.MEDIUM
                
                return RiskAlert(
                    id=f"sentiment_momentum_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    risk_level=risk_level,
                    risk_category=RiskCategory.SENTIMENT,
                    risk_score=min(abs(momentum) * 100, 100),
                    description=f"Negative sentiment momentum detected: {momentum:.2f}",
                    affected_entities=["trend_analysis", "brand_trajectory"],
                    contributing_factors={
                        "momentum_score": momentum,
                        "recent_avg": recent_avg,
                        "older_avg": older_avg
                    },
                    recommended_actions=[
                        "Investigate momentum drivers",
                        "Implement countermeasures",
                        "Accelerate positive messaging",
                        "Monitor trend reversal"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=6),
                    metadata={"analyzer": "sentiment_momentum"}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment momentum: {e}")
            return None

class EngagementRiskAnalyzer:
    """Analyzes engagement-based risks"""
    
    def __init__(self):
        self.engagement_history = deque(maxlen=500)
        self.low_engagement_threshold = 0.1
        self.viral_threshold = 10.0
        self.anomaly_threshold = 2.0
        
    async def analyze_engagement_risks(self, social_data: List[Dict[str, Any]]) -> List[RiskAlert]:
        """Analyze engagement data for risks"""
        alerts = []
        
        try:
            if not social_data:
                return alerts
            
            # Extract engagement metrics
            engagement_metrics = []
            for item in social_data:
                engagement = (
                    item.get('like_count', 0) +
                    item.get('retweet_count', 0) +
                    item.get('reply_count', 0)
                )
                
                engagement_metrics.append({
                    'engagement': engagement,
                    'likes': item.get('like_count', 0),
                    'retweets': item.get('retweet_count', 0),
                    'replies': item.get('reply_count', 0),
                    'timestamp': datetime.fromisoformat(
                        item.get('created_at', item.get('timestamp', datetime.now().isoformat())).replace('Z', '+00:00')
                    )
                })
            
            # Update engagement history
            self.engagement_history.extend(engagement_metrics)
            
            # Analyze low engagement risk
            low_engagement_alert = await self._analyze_low_engagement(engagement_metrics)
            if low_engagement_alert:
                alerts.append(low_engagement_alert)
            
            # Analyze viral content risk
            viral_alert = await self._analyze_viral_content(engagement_metrics)
            if viral_alert:
                alerts.append(viral_alert)
            
            # Analyze engagement anomalies
            anomaly_alert = await self._analyze_engagement_anomalies(engagement_metrics)
            if anomaly_alert:
                alerts.append(anomaly_alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error analyzing engagement risks: {e}")
            return []
    
    async def _analyze_low_engagement(self, engagement_metrics: List[Dict[str, Any]]) -> Optional[RiskAlert]:
        """Analyze low engagement risk"""
        try:
            if not engagement_metrics:
                return None
            
            # Calculate average engagement
            avg_engagement = statistics.mean([m['engagement'] for m in engagement_metrics])
            
            # Get historical baseline
            if len(self.engagement_history) >= 50:
                historical_avg = statistics.mean([m['engagement'] for m in list(self.engagement_history)[-50:-len(engagement_metrics)]])
                
                # Compare current to historical
                engagement_ratio = avg_engagement / max(historical_avg, 1)
                
                if engagement_ratio < self.low_engagement_threshold:
                    return RiskAlert(
                        id=f"low_engagement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        risk_level=RiskLevel.MEDIUM,
                        risk_category=RiskCategory.ENGAGEMENT,
                        risk_score=min((1 - engagement_ratio) * 100, 100),
                        description=f"Significantly low engagement detected: {engagement_ratio:.2f}x historical average",
                        affected_entities=["audience_reach", "content_effectiveness"],
                        contributing_factors={
                            "current_avg": avg_engagement,
                            "historical_avg": historical_avg,
                            "ratio": engagement_ratio,
                            "sample_size": len(engagement_metrics)
                        },
                        recommended_actions=[
                            "Review content strategy",
                            "Analyze audience preferences", 
                            "Optimize posting timing",
                            "Consider content format changes"
                        ],
                        timestamp=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=24),
                        metadata={"analyzer": "low_engagement"}
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing low engagement: {e}")
            return None
    
    async def _analyze_viral_content(self, engagement_metrics: List[Dict[str, Any]]) -> Optional[RiskAlert]:
        """Analyze viral content risk"""
        try:
            # Check for unexpectedly high engagement
            for metric in engagement_metrics:
                engagement = metric['engagement']
                
                # Get historical baseline
                if len(self.engagement_history) >= 50:
                    historical_avg = statistics.mean([m['engagement'] for m in list(self.engagement_history)[-50:]])
                    
                    if engagement > historical_avg * self.viral_threshold:
                        return RiskAlert(
                            id=f"viral_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            risk_level=RiskLevel.HIGH,
                            risk_category=RiskCategory.REPUTATION,
                            risk_score=min((engagement / historical_avg) * 10, 100),
                            description=f"Viral content detected: {engagement / historical_avg:.1f}x normal engagement",
                            affected_entities=["content_control", "message_amplification"],
                            contributing_factors={
                                "engagement_level": engagement,
                                "historical_avg": historical_avg,
                                "viral_multiplier": engagement / historical_avg,
                                "content_type": "high_engagement"
                            },
                            recommended_actions=[
                                "Monitor content spread",
                                "Prepare for increased scrutiny",
                                "Review content appropriateness",
                                "Plan response strategy"
                            ],
                            timestamp=datetime.now(),
                            expires_at=datetime.now() + timedelta(hours=4),
                            metadata={"analyzer": "viral_content", "engagement_level": engagement}
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing viral content: {e}")
            return None
    
    async def _analyze_engagement_anomalies(self, engagement_metrics: List[Dict[str, Any]]) -> Optional[RiskAlert]:
        """Analyze engagement anomalies"""
        try:
            if len(self.engagement_history) < 30:
                return None
            
            # Get historical data for anomaly detection
            historical_engagement = [m['engagement'] for m in list(self.engagement_history)[-30:]]
            current_engagement = [m['engagement'] for m in engagement_metrics]
            
            # Calculate z-scores for anomaly detection
            historical_mean = statistics.mean(historical_engagement)
            historical_std = statistics.stdev(historical_engagement) if len(historical_engagement) > 1 else 1
            
            anomalies = []
            for engagement in current_engagement:
                z_score = abs((engagement - historical_mean) / historical_std)
                if z_score > self.anomaly_threshold:
                    anomalies.append({
                        'engagement': engagement,
                        'z_score': z_score
                    })
            
            if anomalies:
                max_anomaly = max(anomalies, key=lambda x: x['z_score'])
                
                return RiskAlert(
                    id=f"engagement_anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    risk_level=RiskLevel.MEDIUM,
                    risk_category=RiskCategory.ENGAGEMENT,
                    risk_score=min(max_anomaly['z_score'] * 20, 100),
                    description=f"Engagement anomaly detected: {len(anomalies)} anomalous posts",
                    affected_entities=["engagement_patterns", "audience_behavior"],
                    contributing_factors={
                        "anomaly_count": len(anomalies),
                        "max_z_score": max_anomaly['z_score'],
                        "threshold": self.anomaly_threshold,
                        "historical_mean": historical_mean
                    },
                    recommended_actions=[
                        "Investigate anomaly causes",
                        "Check for external factors",
                        "Verify data quality",
                        "Monitor for patterns"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=12),
                    metadata={"analyzer": "engagement_anomaly"}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing engagement anomalies: {e}")
            return None

class ReputationRiskAnalyzer:
    """Analyzes reputation-based risks from news and social mentions"""
    
    def __init__(self):
        self.reputation_keywords = {
            'scandal': ['scandal', 'controversy', 'corruption', 'fraud', 'investigation'],
            'legal': ['lawsuit', 'court', 'legal', 'sue', 'settlement', 'fine'],
            'performance': ['failure', 'loss', 'defeat', 'poor', 'worst', 'decline'],
            'integrity': ['cheat', 'dishonest', 'unethical', 'unfair', 'bias', 'fix']
        }
        
    async def analyze_reputation_risks(self, text_data: List[str]) -> List[RiskAlert]:
        """Analyze text data for reputation risks"""
        alerts = []
        
        try:
            if not text_data:
                return alerts
            
            # Analyze reputation keywords
            keyword_mentions = defaultdict(int)
            total_texts = len(text_data)
            
            for text in text_data:
                text_lower = text.lower()
                for category, keywords in self.reputation_keywords.items():
                    for keyword in keywords:
                        if keyword in text_lower:
                            keyword_mentions[category] += 1
            
            # Check for high-risk keyword mentions
            for category, count in keyword_mentions.items():
                mention_rate = count / total_texts
                
                if mention_rate > 0.1:  # 10% of texts contain risk keywords
                    risk_level = RiskLevel.CRITICAL if mention_rate > 0.3 else RiskLevel.HIGH
                    
                    alerts.append(RiskAlert(
                        id=f"reputation_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        risk_level=risk_level,
                        risk_category=RiskCategory.REPUTATION,
                        risk_score=min(mention_rate * 200, 100),
                        description=f"High frequency of {category}-related mentions: {mention_rate:.1%}",
                        affected_entities=["brand_reputation", "public_trust"],
                        contributing_factors={
                            "mention_rate": mention_rate,
                            "total_mentions": count,
                            "total_texts": total_texts,
                            "category": category
                        },
                        recommended_actions=[
                            f"Address {category} concerns immediately",
                            "Prepare official response",
                            "Monitor escalation",
                            "Engage legal/PR teams"
                        ],
                        timestamp=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=8),
                        metadata={"analyzer": "reputation", "category": category}
                    ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error analyzing reputation risks: {e}")
            return []

class RiskAssessmentEngine:
    """Main risk assessment engine coordinating all analyzers"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentRiskAnalyzer()
        self.engagement_analyzer = EngagementRiskAnalyzer()
        self.reputation_analyzer = ReputationRiskAnalyzer()
        
        self.redis_client = None
        self.active_alerts = {}
        self.risk_history = deque(maxlen=1000)
        
        # Risk scoring weights
        self.risk_weights = {
            RiskCategory.SENTIMENT: 0.25,
            RiskCategory.ENGAGEMENT: 0.20,
            RiskCategory.REPUTATION: 0.30,
            RiskCategory.FINANCIAL: 0.15,
            RiskCategory.REGULATORY: 0.10
        }
        
    async def initialize(self):
        """Initialize risk assessment engine"""
        try:
            # Initialize Redis client
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Load active alerts from storage
            await self._load_active_alerts()
            
            logger.info("Risk assessment engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize risk assessment engine: {e}")
            raise
    
    async def assess_risks(self) -> Dict[str, Any]:
        """Main risk assessment coordination"""
        assessment_start = datetime.now()
        
        try:
            # Get latest predictions and data
            predictions = await self._get_latest_predictions()
            social_data = await self._get_social_data()
            text_data = await self._get_text_data()
            
            # Run all risk analyzers
            all_alerts = []
            
            # Sentiment risk analysis
            if predictions:
                sentiment_alerts = await self.sentiment_analyzer.analyze_sentiment_risks(predictions)
                all_alerts.extend(sentiment_alerts)
            
            # Engagement risk analysis
            if social_data:
                engagement_alerts = await self.engagement_analyzer.analyze_engagement_risks(social_data)
                all_alerts.extend(engagement_alerts)
            
            # Reputation risk analysis
            if text_data:
                reputation_alerts = await self.reputation_analyzer.analyze_reputation_risks(text_data)
                all_alerts.extend(reputation_alerts)
            
            # Update active alerts
            await self._update_active_alerts(all_alerts)
            
            # Calculate overall risk assessment
            risk_assessment = await self._calculate_overall_risk()
            
            # Store assessment
            await self._store_risk_assessment(risk_assessment)
            
            processing_time = (datetime.now() - assessment_start).total_seconds()
            
            return {
                'overall_risk_score': risk_assessment.overall_risk_score,
                'risk_level': risk_assessment.risk_level.value,
                'active_alerts_count': len(risk_assessment.active_alerts),
                'new_alerts_count': len(all_alerts),
                'processing_time_seconds': processing_time,
                'confidence_score': risk_assessment.confidence_score,
                'timestamp': assessment_start.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            raise
    
    async def _get_latest_predictions(self) -> List[Dict[str, Any]]:
        """Get latest model predictions from Redis"""
        try:
            entries = await self.redis_client.xread(
                {'stream:predictions': '$'},
                count=100,
                block=1000
            )
            
            predictions = []
            for stream_entries in entries:
                for entry_id, entry_data in stream_entries[1]:
                    predictions.append(entry_data)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting latest predictions: {e}")
            return []
    
    async def _get_social_data(self) -> List[Dict[str, Any]]:
        """Get latest social media data from Redis"""
        try:
            entries = await self.redis_client.xread(
                {'stream:tweets': '$'},
                count=200,
                block=1000
            )
            
            social_data = []
            for stream_entries in entries:
                for entry_id, entry_data in stream_entries[1]:
                    try:
                        # Parse numeric fields
                        for field in ['like_count', 'retweet_count', 'reply_count']:
                            if field in entry_data:
                                entry_data[field] = int(entry_data[field])
                        social_data.append(entry_data)
                    except Exception:
                        continue
            
            return social_data
            
        except Exception as e:
            logger.error(f"Error getting social data: {e}")
            return []
    
    async def _get_text_data(self) -> List[str]:
        """Get text content for reputation analysis"""
        try:
            # Get from multiple sources
            text_data = []
            
            # From tweets
            social_entries = await self.redis_client.xread(
                {'stream:tweets': '$'},
                count=100,
                block=500
            )
            
            for stream_entries in social_entries:
                for entry_id, entry_data in stream_entries[1]:
                    if 'text' in entry_data:
                        text_data.append(entry_data['text'])
            
            # From news
            news_entries = await self.redis_client.xread(
                {'stream:news': '$'},
                count=50,
                block=500
            )
            
            for stream_entries in news_entries:
                for entry_id, entry_data in stream_entries[1]:
                    if 'title' in entry_data:
                        text_data.append(entry_data['title'])
                    if 'description' in entry_data:
                        text_data.append(entry_data['description'])
            
            return text_data
            
        except Exception as e:
            logger.error(f"Error getting text data: {e}")
            return []
    
    async def _update_active_alerts(self, new_alerts: List[RiskAlert]):
        """Update active alerts list"""
        try:
            current_time = datetime.now()
            
            # Remove expired alerts
            expired_ids = []
            for alert_id, alert in self.active_alerts.items():
                if alert.expires_at <= current_time:
                    expired_ids.append(alert_id)
            
            for alert_id in expired_ids:
                del self.active_alerts[alert_id]
            
            # Add new alerts
            for alert in new_alerts:
                self.active_alerts[alert.id] = alert
            
            # Store active alerts
            await self._store_active_alerts()
            
            logger.info(f"Updated active alerts: {len(new_alerts)} new, {len(expired_ids)} expired")
            
        except Exception as e:
            logger.error(f"Error updating active alerts: {e}")
    
    async def _calculate_overall_risk(self) -> RiskAssessment:
        """Calculate overall risk assessment"""
        try:
            if not self.active_alerts:
                return RiskAssessment(
                    overall_risk_score=0.0,
                    risk_level=RiskLevel.LOW,
                    active_alerts=[],
                    risk_trends={},
                    confidence_score=1.0,
                    assessment_timestamp=datetime.now(),
                    next_assessment_due=datetime.now() + timedelta(minutes=5)
                )
            
            # Calculate weighted risk score
            category_scores = defaultdict(list)
            
            for alert in self.active_alerts.values():
                category_scores[alert.risk_category].append(alert.risk_score)
            
            # Calculate category averages
            category_averages = {}
            for category, scores in category_scores.items():
                category_averages[category] = statistics.mean(scores)
            
            # Calculate overall weighted score
            overall_score = 0.0
            total_weight = 0.0
            
            for category, avg_score in category_averages.items():
                weight = self.risk_weights.get(category, 0.1)
                overall_score += avg_score * weight
                total_weight += weight
            
            if total_weight > 0:
                overall_score = overall_score / total_weight
            
            # Determine risk level
            if overall_score >= 80:
                risk_level = RiskLevel.CRITICAL
            elif overall_score >= 60:
                risk_level = RiskLevel.HIGH
            elif overall_score >= 30:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
            
            # Calculate confidence based on data availability
            confidence_score = min(len(self.active_alerts) / 10, 1.0)
            
            # Calculate risk trends
            risk_trends = await self._calculate_risk_trends()
            
            assessment = RiskAssessment(
                overall_risk_score=overall_score,
                risk_level=risk_level,
                active_alerts=list(self.active_alerts.values()),
                risk_trends=risk_trends,
                confidence_score=confidence_score,
                assessment_timestamp=datetime.now(),
                next_assessment_due=datetime.now() + timedelta(minutes=5)
            )
            
            # Add to history
            self.risk_history.append({
                'timestamp': datetime.now(),
                'overall_score': overall_score,
                'risk_level': risk_level.value,
                'alerts_count': len(self.active_alerts)
            })
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error calculating overall risk: {e}")
            return RiskAssessment(
                overall_risk_score=50.0,
                risk_level=RiskLevel.MEDIUM,
                active_alerts=[],
                risk_trends={},
                confidence_score=0.5,
                assessment_timestamp=datetime.now(),
                next_assessment_due=datetime.now() + timedelta(minutes=5)
            )
    
    async def _calculate_risk_trends(self) -> Dict[str, float]:
        """Calculate risk trends from history"""
        try:
            if len(self.risk_history) < 5:
                return {}
            
            # Get recent vs older risk scores
            recent_scores = [item['overall_score'] for item in list(self.risk_history)[-5:]]
            older_scores = [item['overall_score'] for item in list(self.risk_history)[-10:-5]] if len(self.risk_history) >= 10 else []
            
            trends = {}
            
            # Overall trend
            if older_scores:
                recent_avg = statistics.mean(recent_scores)
                older_avg = statistics.mean(older_scores)
                trends['overall_trend'] = recent_avg - older_avg
            
            # Alert count trend
            recent_alert_counts = [item['alerts_count'] for item in list(self.risk_history)[-5:]]
            older_alert_counts = [item['alerts_count'] for item in list(self.risk_history)[-10:-5]] if len(self.risk_history) >= 10 else []
            
            if older_alert_counts:
                recent_alert_avg = statistics.mean(recent_alert_counts)
                older_alert_avg = statistics.mean(older_alert_counts)
                trends['alert_trend'] = recent_alert_avg - older_alert_avg
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating risk trends: {e}")
            return {}
    
    async def _store_risk_assessment(self, assessment: RiskAssessment):
        """Store risk assessment in Redis"""
        try:
            assessment_data = {
                'overall_risk_score': assessment.overall_risk_score,
                'risk_level': assessment.risk_level.value,
                'active_alerts_count': len(assessment.active_alerts),
                'confidence_score': assessment.confidence_score,
                'risk_trends': json.dumps(assessment.risk_trends),
                'assessment_timestamp': assessment.assessment_timestamp.isoformat(),
                'next_assessment_due': assessment.next_assessment_due.isoformat()
            }
            
            # Store current assessment
            await self.redis_client.setex(
                'current_risk_assessment',
                timedelta(hours=1).total_seconds(),
                json.dumps(assessment_data)
            )
            
            # Store in assessment stream
            await self.redis_client.xadd(
                'stream:risk_assessments',
                assessment_data,
                maxlen=1000
            )
            
            logger.info(f"Stored risk assessment: {assessment.risk_level.value} ({assessment.overall_risk_score:.1f})")
            
        except Exception as e:
            logger.error(f"Error storing risk assessment: {e}")
    
    async def _load_active_alerts(self):
        """Load active alerts from storage"""
        try:
            alerts_data = await self.redis_client.get('active_alerts')
            if alerts_data:
                stored_alerts = json.loads(alerts_data)
                for alert_data in stored_alerts:
                    alert = RiskAlert(**alert_data)
                    if alert.expires_at > datetime.now():
                        self.active_alerts[alert.id] = alert
        except Exception as e:
            logger.error(f"Error loading active alerts: {e}")
    
    async def _store_active_alerts(self):
        """Store active alerts to Redis"""
        try:
            alerts_data = [asdict(alert) for alert in self.active_alerts.values()]
            await self.redis_client.setex(
                'active_alerts',
                timedelta(days=1).total_seconds(),
                json.dumps(alerts_data, default=str)
            )
        except Exception as e:
            logger.error(f"Error storing active alerts: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for risk assessment engine"""
        try:
            # Check Redis connection
            redis_status = "healthy"
            try:
                await self.redis_client.ping()
            except Exception:
                redis_status = "unhealthy"
            
            # Check analyzers
            analyzer_status = {
                'sentiment': 'healthy',
                'engagement': 'healthy',
                'reputation': 'healthy'
            }
            
            overall_status = "healthy" if redis_status == "healthy" else "degraded"
            
            return {
                'status': overall_status,
                'components': {
                    'redis': redis_status,
                    'analyzers': analyzer_status
                },
                'active_alerts': len(self.active_alerts),
                'risk_history_size': len(self.risk_history),
                'last_assessment': self.risk_history[-1] if self.risk_history else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def stop(self):
        """Stop risk assessment engine"""
        try:
            # Store final state
            await self._store_active_alerts()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Risk assessment engine stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping risk assessment engine: {e}")