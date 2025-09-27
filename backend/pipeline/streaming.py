"""
Stream Processing Engine
Handles real-time data processing from Kafka streams with advanced analytics
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass
from confluent_kafka import Consumer, KafkaError
import aioredis
from collections import defaultdict, deque
import statistics

from config.settings import settings

        # settings imported above
logger = logging.getLogger(__name__)

@dataclass
class StreamMetrics:
    """Stream processing metrics"""
    topic: str
    messages_processed: int
    processing_time_avg: float
    errors: int
    last_processed: datetime
    throughput_per_second: float

class RealTimeAggregator:
    """Real-time data aggregation with sliding windows"""
    
    def __init__(self, window_size_minutes: int = 15):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.data_windows = defaultdict(deque)
        self.aggregations = {}
        
    def add_data_point(self, key: str, value: Any, timestamp: datetime = None):
        """Add a data point to the sliding window"""
        if timestamp is None:
            timestamp = datetime.now()
            
        # Add to window
        self.data_windows[key].append((timestamp, value))
        
        # Clean old data outside window
        cutoff_time = timestamp - self.window_size
        while (self.data_windows[key] and 
               self.data_windows[key][0][0] < cutoff_time):
            self.data_windows[key].popleft()
    
    def get_aggregation(self, key: str, agg_type: str = 'count') -> float:
        """Get aggregated value for a key"""
        if key not in self.data_windows or not self.data_windows[key]:
            return 0.0
            
        values = [item[1] for item in self.data_windows[key]]
        
        if agg_type == 'count':
            return len(values)
        elif agg_type == 'sum':
            return sum(values) if values else 0.0
        elif agg_type == 'avg':
            return statistics.mean(values) if values else 0.0
        elif agg_type == 'median':
            return statistics.median(values) if values else 0.0
        elif agg_type == 'max':
            return max(values) if values else 0.0
        elif agg_type == 'min':
            return min(values) if values else 0.0
        else:
            return 0.0

class SentimentStreamProcessor:
    """Process sentiment data from social media streams"""
    
    def __init__(self):
        self.sentiment_aggregator = RealTimeAggregator(window_size_minutes=30)
        self.keyword_tracker = defaultdict(list)
        self.anomaly_threshold = 2.0  # Standard deviations
        
    async def process_tweet(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual tweet for sentiment analysis"""
        try:
            # Extract features
            text = tweet_data.get('text', '')
            timestamp = datetime.fromisoformat(tweet_data.get('created_at', datetime.now().isoformat()))
            engagement = {
                'likes': tweet_data.get('like_count', 0),
                'retweets': tweet_data.get('retweet_count', 0),
                'replies': tweet_data.get('reply_count', 0)
            }
            
            # Basic sentiment scoring (to be replaced with ML model)
            sentiment_score = self._calculate_basic_sentiment(text)
            
            # Track sentiment trends
            self.sentiment_aggregator.add_data_point(
                'overall_sentiment', 
                sentiment_score, 
                timestamp
            )
            
            # Track engagement metrics
            total_engagement = sum(engagement.values())
            self.sentiment_aggregator.add_data_point(
                'engagement_score',
                total_engagement,
                timestamp
            )
            
            # Detect anomalies
            anomaly_detected = self._detect_sentiment_anomaly(sentiment_score, timestamp)
            
            processed_data = {
                'id': tweet_data.get('id'),
                'text': text,
                'sentiment_score': sentiment_score,
                'engagement': engagement,
                'total_engagement': total_engagement,
                'timestamp': timestamp.isoformat(),
                'anomaly_detected': anomaly_detected,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing tweet: {e}")
            return {}
    
    def _calculate_basic_sentiment(self, text: str) -> float:
        """Basic sentiment calculation (placeholder for ML model)"""
        # Simple keyword-based sentiment (to be replaced)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'win', 'victory']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'lose', 'defeat', 'disappointed']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def _detect_sentiment_anomaly(self, current_sentiment: float, timestamp: datetime) -> bool:
        """Detect sentiment anomalies using statistical methods"""
        try:
            # Get recent sentiment values
            recent_sentiments = [
                item[1] for item in self.sentiment_aggregator.data_windows['overall_sentiment']
                if timestamp - item[0] <= timedelta(hours=2)
            ]
            
            if len(recent_sentiments) < 10:  # Need minimum data points
                return False
            
            # Calculate z-score
            mean_sentiment = statistics.mean(recent_sentiments)
            std_sentiment = statistics.stdev(recent_sentiments)
            
            if std_sentiment == 0:
                return False
            
            z_score = abs((current_sentiment - mean_sentiment) / std_sentiment)
            
            return z_score > self.anomaly_threshold
            
        except Exception as e:
            logger.error(f"Error detecting sentiment anomaly: {e}")
            return False

class GameEventProcessor:
    """Process real-time game events and statistics"""
    
    def __init__(self):
        self.game_aggregator = RealTimeAggregator(window_size_minutes=180)  # 3-hour window
        self.active_games = {}
        
    async def process_game_event(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual game event"""
        try:
            game_id = game_data.get('id')
            sport = game_data.get('sport')
            timestamp = datetime.fromisoformat(
                game_data.get('collected_at', datetime.now().isoformat())
            )
            
            # Track game in active games
            if game_id not in self.active_games:
                self.active_games[game_id] = {
                    'start_time': timestamp,
                    'sport': sport,
                    'events': [],
                    'metrics': defaultdict(float)
                }
            
            # Process based on sport type
            processed_event = await self._process_sport_specific_event(game_data)
            
            # Add to game events
            self.active_games[game_id]['events'].append({
                'timestamp': timestamp.isoformat(),
                'data': processed_event
            })
            
            # Update aggregations
            self.game_aggregator.add_data_point(
                f"{sport}_game_count",
                1,
                timestamp
            )
            
            # Calculate momentum and trends
            momentum_score = self._calculate_game_momentum(game_id, game_data)
            
            return {
                'game_id': game_id,
                'sport': sport,
                'processed_event': processed_event,
                'momentum_score': momentum_score,
                'timestamp': timestamp.isoformat(),
                'processing_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing game event: {e}")
            return {}
    
    async def _process_sport_specific_event(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sport-specific game data"""
        sport = game_data.get('sport', '').lower()
        
        if sport == 'football':
            return self._process_football_event(game_data)
        elif sport == 'basketball':
            return self._process_basketball_event(game_data)
        elif sport == 'cricket':
            return self._process_cricket_event(game_data)
        else:
            return self._process_generic_event(game_data)
    
    def _process_football_event(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process football-specific events"""
        score = game_data.get('score', {})
        return {
            'home_score': score.get('fullTime', {}).get('homeTeam', 0),
            'away_score': score.get('fullTime', {}).get('awayTeam', 0),
            'status': game_data.get('status'),
            'venue': game_data.get('venue', {}).get('name', ''),
            'attendance': game_data.get('attendance', 0)
        }
    
    def _process_basketball_event(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process basketball-specific events"""
        return {
            'home_score': game_data.get('HomeTeamScore', 0),
            'away_score': game_data.get('AwayTeamScore', 0),
            'quarter': game_data.get('Quarter', 0),
            'time_remaining': game_data.get('TimeRemainingMinutes', 0),
            'status': game_data.get('Status')
        }
    
    def _process_cricket_event(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process cricket-specific events"""
        return {
            'team1_score': game_data.get('team1', {}).get('score', ''),
            'team2_score': game_data.get('team2', {}).get('score', ''),
            'overs': game_data.get('overs', 0),
            'status': game_data.get('matchStarted', False),
            'winner': game_data.get('winner_team', '')
        }
    
    def _process_generic_event(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process generic game events"""
        return {
            'home_team': game_data.get('home_team', ''),
            'away_team': game_data.get('away_team', ''),
            'status': game_data.get('status', ''),
            'date': game_data.get('date', ''),
            'venue': game_data.get('venue', '')
        }
    
    def _calculate_game_momentum(self, game_id: str, game_data: Dict[str, Any]) -> float:
        """Calculate game momentum score"""
        try:
            if game_id not in self.active_games:
                return 0.0
            
            events = self.active_games[game_id]['events']
            if len(events) < 2:
                return 0.0
            
            # Simple momentum calculation based on recent events
            # This would be more sophisticated in a real implementation
            recent_events = events[-5:]  # Last 5 events
            
            momentum = 0.0
            for i in range(1, len(recent_events)):
                # Compare current vs previous (simplified)
                momentum += 0.1  # Placeholder calculation
            
            return min(momentum, 1.0)  # Normalize to 0-1
            
        except Exception as e:
            logger.error(f"Error calculating game momentum: {e}")
            return 0.0

class StreamProcessor:
    """Main stream processing coordinator"""
    
    def __init__(self):
        self.consumers = {}
        self.processors = {
            'sentiment': SentimentStreamProcessor(),
            'game_events': GameEventProcessor()
        }
        self.redis_client = None
        self.processing_stats = defaultdict(lambda: StreamMetrics(
            topic='', messages_processed=0, processing_time_avg=0.0,
            errors=0, last_processed=datetime.now(), throughput_per_second=0.0
        ))
        self.is_running = False
        
    async def initialize(self):
        """Initialize stream processing components"""
        try:
            # Initialize Redis client
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize Kafka consumers
            topics_to_process = [
                f"{settings.KAFKA_TOPIC_PREFIX}tweets",
                f"{settings.KAFKA_TOPIC_PREFIX}games",
                f"{settings.KAFKA_TOPIC_PREFIX}news"
            ]
            
            for topic in topics_to_process:
                consumer = Consumer({
                    'bootstrap.servers': ','.join(settings.KAFKA_BOOTSTRAP_SERVERS),
                    'group.id': f'stream_processor_{topic}',
                    'auto.offset.reset': 'latest',
                    'enable.auto.commit': True,
                    'auto.commit.interval.ms': 5000,
                    'max.poll.interval.ms': 300000,
                    'session.timeout.ms': 30000
                })
                consumer.subscribe([topic])
                self.consumers[topic] = consumer
            
            logger.info(f"Stream processor initialized for topics: {topics_to_process}")
            
        except Exception as e:
            logger.error(f"Failed to initialize stream processor: {e}")
            raise
    
    async def process_streams(self) -> Dict[str, Any]:
        """Main stream processing loop"""
        if not self.consumers:
            return {'error': 'No consumers initialized'}
        
        processing_start = datetime.now()
        total_processed = 0
        
        try:
            # Process messages from all topics
            for topic, consumer in self.consumers.items():
                messages_processed = await self._process_topic_messages(topic, consumer)
                total_processed += messages_processed
                
                # Update stats
                stats = self.processing_stats[topic]
                stats.messages_processed += messages_processed
                stats.last_processed = datetime.now()
            
            processing_time = (datetime.now() - processing_start).total_seconds()
            
            # Calculate throughput
            if processing_time > 0:
                throughput = total_processed / processing_time
                for topic in self.consumers.keys():
                    self.processing_stats[topic].throughput_per_second = throughput / len(self.consumers)
            
            return {
                'total_processed': total_processed,
                'processing_time_seconds': processing_time,
                'throughput_per_second': total_processed / max(processing_time, 0.001),
                'topics_processed': len(self.consumers),
                'timestamp': processing_start.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")
            for topic in self.consumers.keys():
                self.processing_stats[topic].errors += 1
            raise
    
    async def _process_topic_messages(self, topic: str, consumer: Consumer, batch_size: int = 100) -> int:
        """Process messages from a specific topic"""
        messages_processed = 0
        
        try:
            # Poll for messages
            messages = consumer.consume(num_messages=batch_size, timeout=1.0)
            
            for msg in messages:
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue
                
                try:
                    # Parse message
                    message_data = json.loads(msg.value().decode('utf-8'))
                    
                    # Route to appropriate processor
                    processed_result = await self._route_message(topic, message_data)
                    
                    if processed_result:
                        # Store processed result
                        await self._store_processed_result(topic, processed_result)
                        messages_processed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process message from {topic}: {e}")
                    self.processing_stats[topic].errors += 1
            
            return messages_processed
            
        except Exception as e:
            logger.error(f"Failed to consume messages from {topic}: {e}")
            return 0
    
    async def _route_message(self, topic: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route message to appropriate processor"""
        try:
            if 'tweets' in topic:
                return await self.processors['sentiment'].process_tweet(message_data)
            elif 'games' in topic:
                return await self.processors['game_events'].process_game_event(message_data)
            elif 'news' in topic:
                # Process news articles (placeholder)
                return await self._process_news_article(message_data)
            else:
                logger.warning(f"No processor found for topic: {topic}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to route message from {topic}: {e}")
            return None
    
    async def _process_news_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process news articles (placeholder implementation)"""
        try:
            return {
                'title': article_data.get('title', ''),
                'content': article_data.get('content', ''),
                'source': article_data.get('source', ''),
                'published_at': article_data.get('published_at', ''),
                'sentiment_score': 0.0,  # Placeholder
                'relevance_score': 0.0,  # Placeholder
                'processing_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to process news article: {e}")
            return {}
    
    async def _store_processed_result(self, topic: str, result: Dict[str, Any]):
        """Store processed result in Redis"""
        try:
            # Create storage key
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            key = f"processed:{topic}:{timestamp}:{result.get('id', 'unknown')}"
            
            # Store with TTL
            await self.redis_client.setex(
                key,
                timedelta(hours=12).total_seconds(),  # 12-hour TTL
                json.dumps(result)
            )
            
            # Also store in aggregated streams for real-time dashboards
            stream_key = f"stream:{topic}"
            await self.redis_client.xadd(
                stream_key,
                result,
                maxlen=10000  # Keep last 10k entries
            )
            
        except Exception as e:
            logger.error(f"Failed to store processed result: {e}")
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time processing metrics"""
        try:
            metrics = {}
            
            # Get sentiment metrics
            sentiment_processor = self.processors['sentiment']
            metrics['sentiment'] = {
                'current_sentiment': sentiment_processor.sentiment_aggregator.get_aggregation('overall_sentiment', 'avg'),
                'sentiment_count_15min': sentiment_processor.sentiment_aggregator.get_aggregation('overall_sentiment', 'count'),
                'avg_engagement': sentiment_processor.sentiment_aggregator.get_aggregation('engagement_score', 'avg'),
                'anomalies_detected': 0  # Would track in real implementation
            }
            
            # Get game metrics
            game_processor = self.processors['game_events']
            metrics['games'] = {
                'active_games': len(game_processor.active_games),
                'total_game_events': sum(
                    len(game['events']) for game in game_processor.active_games.values()
                ),
                'sports_coverage': list(set(
                    game['sport'] for game in game_processor.active_games.values()
                ))
            }
            
            # Get processing stats
            metrics['processing'] = {}
            for topic, stats in self.processing_stats.items():
                metrics['processing'][topic] = {
                    'messages_processed': stats.messages_processed,
                    'errors': stats.errors,
                    'throughput_per_second': stats.throughput_per_second,
                    'last_processed': stats.last_processed.isoformat()
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {}
    
    async def reduce_batch_size(self):
        """Reduce batch size for graceful degradation"""
        # This would be implemented to reduce processing load
        logger.info("Reducing batch size for graceful degradation")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for stream processor"""
        try:
            # Check Redis connection
            redis_status = "healthy"
            try:
                await self.redis_client.ping()
            except Exception:
                redis_status = "unhealthy"
            
            # Check Kafka consumers
            kafka_status = "healthy"
            unhealthy_topics = []
            for topic, consumer in self.consumers.items():
                try:
                    # Check if consumer is still connected
                    metadata = consumer.list_topics(timeout=5)
                    if topic.split('_')[-1] not in str(metadata.topics):
                        unhealthy_topics.append(topic)
                except Exception:
                    unhealthy_topics.append(topic)
            
            if unhealthy_topics:
                kafka_status = "degraded"
                if len(unhealthy_topics) == len(self.consumers):
                    kafka_status = "unhealthy"
            
            # Overall status
            if redis_status == "unhealthy" or kafka_status == "unhealthy":
                overall_status = "critical"
            elif redis_status == "degraded" or kafka_status == "degraded":
                overall_status = "degraded"
            else:
                overall_status = "healthy"
            
            return {
                'status': overall_status,
                'components': {
                    'redis': redis_status,
                    'kafka': kafka_status,
                    'consumers': len(self.consumers),
                    'processors': len(self.processors)
                },
                'unhealthy_topics': unhealthy_topics,
                'processing_stats': {
                    topic: {
                        'messages_processed': stats.messages_processed,
                        'errors': stats.errors,
                        'throughput': stats.throughput_per_second
                    }
                    for topic, stats in self.processing_stats.items()
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def stop(self):
        """Stop stream processor"""
        try:
            self.is_running = False
            
            # Close Kafka consumers
            for topic, consumer in self.consumers.items():
                consumer.close()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Stream processor stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping stream processor: {e}")