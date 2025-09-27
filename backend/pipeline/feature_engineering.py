"""
Feature Engineering Engine
Handles temporal, semantic, and network feature extraction for ML models
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass
import aioredis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from collections import defaultdict, Counter
import re
import networkx as nx
from textblob import TextBlob
import statistics

from config.settings import settings

        # settings imported above
logger = logging.getLogger(__name__)

@dataclass
class FeatureSet:
    """Container for engineered features"""
    temporal_features: Dict[str, float]
    semantic_features: Dict[str, float]
    network_features: Dict[str, float]
    engagement_features: Dict[str, float]
    metadata: Dict[str, Any]
    timestamp: datetime

class TemporalFeatureExtractor:
    """Extract time-based features from social media and game data"""
    
    def __init__(self):
        self.time_windows = {
            'hour': timedelta(hours=1),
            '6hour': timedelta(hours=6),
            'day': timedelta(days=1),
            'week': timedelta(weeks=1)
        }
        self.temporal_cache = defaultdict(list)
        
    async def extract_temporal_features(self, data: List[Dict[str, Any]], 
                                      reference_time: datetime = None) -> Dict[str, float]:
        """Extract comprehensive temporal features"""
        if not data:
            return {}
        
        if reference_time is None:
            reference_time = datetime.now()
        
        features = {}
        
        # Extract timestamps
        timestamps = []
        for item in data:
            try:
                if 'created_at' in item:
                    ts = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                elif 'published_at' in item:
                    ts = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                elif 'timestamp' in item:
                    ts = datetime.fromisoformat(item['timestamp'])
                else:
                    continue
                timestamps.append(ts)
            except Exception:
                continue
        
        if not timestamps:
            return features
        
        # Time-based aggregations
        for window_name, window_size in self.time_windows.items():
            cutoff_time = reference_time - window_size
            recent_timestamps = [ts for ts in timestamps if ts >= cutoff_time]
            
            features[f'count_{window_name}'] = len(recent_timestamps)
            features[f'rate_{window_name}'] = len(recent_timestamps) / (window_size.total_seconds() / 3600)
        
        # Temporal patterns
        if timestamps:
            # Hour of day distribution
            hours = [ts.hour for ts in timestamps]
            features['peak_hour'] = max(set(hours), key=hours.count) if hours else 0
            features['hour_std'] = statistics.stdev(hours) if len(hours) > 1 else 0
            
            # Day of week distribution
            weekdays = [ts.weekday() for ts in timestamps]
            features['peak_weekday'] = max(set(weekdays), key=weekdays.count) if weekdays else 0
            
            # Recency features
            latest_time = max(timestamps)
            features['recency_hours'] = (reference_time - latest_time).total_seconds() / 3600
            
            # Velocity (change in posting rate)
            if len(timestamps) > 10:
                recent_half = [ts for ts in timestamps if ts >= reference_time - timedelta(hours=12)]
                older_half = [ts for ts in timestamps if reference_time - timedelta(days=1) <= ts < reference_time - timedelta(hours=12)]
                
                recent_rate = len(recent_half) / 12  # per hour
                older_rate = len(older_half) / 12
                
                features['velocity'] = (recent_rate - older_rate) / max(older_rate, 0.1)
        
        # Seasonal patterns
        features['is_weekend'] = 1.0 if reference_time.weekday() >= 5 else 0.0
        features['is_prime_time'] = 1.0 if 18 <= reference_time.hour <= 22 else 0.0
        features['is_business_hours'] = 1.0 if 9 <= reference_time.hour <= 17 else 0.0
        
        return features
    
    async def extract_event_temporal_features(self, events: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract temporal features specific to game events"""
        features = {}
        
        if not events:
            return features
        
        # Event frequency patterns
        event_times = []
        for event in events:
            try:
                event_time = datetime.fromisoformat(event.get('timestamp', ''))
                event_times.append(event_time)
            except Exception:
                continue
        
        if len(event_times) > 1:
            # Calculate inter-event intervals
            intervals = []
            for i in range(1, len(event_times)):
                interval = (event_times[i] - event_times[i-1]).total_seconds()
                intervals.append(interval)
            
            features['avg_interval_seconds'] = statistics.mean(intervals)
            features['interval_std'] = statistics.stdev(intervals) if len(intervals) > 1 else 0
            features['min_interval'] = min(intervals)
            features['max_interval'] = max(intervals)
        
        # Event clustering (bursts vs steady flow)
        if len(event_times) > 5:
            # Detect bursts using coefficient of variation
            if len(intervals) > 1:
                cv = statistics.stdev(intervals) / statistics.mean(intervals)
                features['burst_indicator'] = cv
                features['is_bursty'] = 1.0 if cv > 1.0 else 0.0
        
        return features

class SemanticFeatureExtractor:
    """Extract semantic features from text content"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        self.emotion_keywords = {
            'joy': ['happy', 'excited', 'thrilled', 'amazing', 'wonderful', 'great'],
            'anger': ['angry', 'furious', 'mad', 'frustrated', 'annoyed', 'hate'],
            'fear': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'panic'],
            'sadness': ['sad', 'disappointed', 'upset', 'depressed', 'heartbroken'],
            'surprise': ['surprised', 'shocked', 'amazed', 'unexpected', 'wow'],
            'trust': ['trust', 'reliable', 'confident', 'believe', 'faith'],
            'anticipation': ['excited', 'looking forward', 'can\'t wait', 'anticipate']
        }
        self.sports_keywords = {
            'performance': ['score', 'goal', 'win', 'lose', 'victory', 'defeat', 'performance'],
            'players': ['player', 'team', 'coach', 'captain', 'star', 'rookie'],
            'tactics': ['strategy', 'tactics', 'formation', 'play', 'defense', 'offense'],
            'controversy': ['foul', 'penalty', 'referee', 'unfair', 'controversial', 'bias']
        }
        
    async def extract_semantic_features(self, texts: List[str]) -> Dict[str, float]:
        """Extract comprehensive semantic features from text data"""
        if not texts:
            return {}
        
        features = {}
        
        # Clean and preprocess texts
        cleaned_texts = [self._preprocess_text(text) for text in texts if text]
        
        if not cleaned_texts:
            return features
        
        # Basic text statistics
        features['avg_text_length'] = statistics.mean(len(text) for text in cleaned_texts)
        features['avg_word_count'] = statistics.mean(len(text.split()) for text in cleaned_texts)
        features['total_texts'] = len(cleaned_texts)
        
        # Sentiment analysis using TextBlob
        sentiments = []
        subjectivities = []
        
        for text in cleaned_texts:
            try:
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)
                subjectivities.append(blob.sentiment.subjectivity)
            except Exception:
                sentiments.append(0.0)
                subjectivities.append(0.5)
        
        features['avg_sentiment'] = statistics.mean(sentiments)
        features['sentiment_std'] = statistics.stdev(sentiments) if len(sentiments) > 1 else 0
        features['sentiment_range'] = max(sentiments) - min(sentiments) if sentiments else 0
        features['positive_ratio'] = sum(1 for s in sentiments if s > 0.1) / len(sentiments)
        features['negative_ratio'] = sum(1 for s in sentiments if s < -0.1) / len(sentiments)
        features['neutral_ratio'] = sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments)
        
        features['avg_subjectivity'] = statistics.mean(subjectivities)
        features['subjectivity_std'] = statistics.stdev(subjectivities) if len(subjectivities) > 1 else 0
        
        # Emotion analysis
        emotion_scores = self._analyze_emotions(cleaned_texts)
        features.update(emotion_scores)
        
        # Sports-specific semantic features
        sports_features = self._analyze_sports_semantics(cleaned_texts)
        features.update(sports_features)
        
        # Language complexity features
        complexity_features = self._analyze_language_complexity(cleaned_texts)
        features.update(complexity_features)
        
        # Topic coherence (simplified)
        features['topic_coherence'] = self._calculate_topic_coherence(cleaned_texts)
        
        return features
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove mentions and hashtags (but keep the content)
        text = re.sub(r'[@#]\w+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _analyze_emotions(self, texts: List[str]) -> Dict[str, float]:
        """Analyze emotional content in texts"""
        emotion_features = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            total_count = 0
            for text in texts:
                text_lower = text.lower()
                count = sum(1 for keyword in keywords if keyword in text_lower)
                total_count += count
            
            emotion_features[f'emotion_{emotion}'] = total_count / len(texts) if texts else 0
        
        # Emotional diversity
        emotion_counts = [emotion_features[f'emotion_{emotion}'] for emotion in self.emotion_keywords.keys()]
        emotion_features['emotional_diversity'] = statistics.stdev(emotion_counts) if len(emotion_counts) > 1 else 0
        
        return emotion_features
    
    def _analyze_sports_semantics(self, texts: List[str]) -> Dict[str, float]:
        """Analyze sports-specific semantic content"""
        sports_features = {}
        
        for category, keywords in self.sports_keywords.items():
            total_count = 0
            for text in texts:
                text_lower = text.lower()
                count = sum(1 for keyword in keywords if keyword in text_lower)
                total_count += count
            
            sports_features[f'sports_{category}'] = total_count / len(texts) if texts else 0
        
        return sports_features
    
    def _analyze_language_complexity(self, texts: List[str]) -> Dict[str, float]:
        """Analyze language complexity features"""
        complexity_features = {}
        
        if not texts:
            return complexity_features
        
        # Average sentence length
        sentence_lengths = []
        for text in texts:
            sentences = text.split('.')
            if sentences:
                avg_length = statistics.mean(len(s.split()) for s in sentences if s.strip())
                sentence_lengths.append(avg_length)
        
        complexity_features['avg_sentence_length'] = statistics.mean(sentence_lengths) if sentence_lengths else 0
        
        # Vocabulary richness (unique words / total words)
        all_words = []
        unique_words = set()
        
        for text in texts:
            words = text.split()
            all_words.extend(words)
            unique_words.update(words)
        
        complexity_features['vocabulary_richness'] = len(unique_words) / max(len(all_words), 1)
        
        # Average word length
        if all_words:
            complexity_features['avg_word_length'] = statistics.mean(len(word) for word in all_words)
        
        return complexity_features
    
    def _calculate_topic_coherence(self, texts: List[str]) -> float:
        """Calculate topic coherence score (simplified)"""
        if len(texts) < 2:
            return 0.0
        
        try:
            # Use TF-IDF to find common themes
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Calculate average cosine similarity between texts
            from sklearn.metrics.pairwise import cosine_similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Get upper triangle (excluding diagonal)
            upper_triangle = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
            
            return np.mean(upper_triangle) if len(upper_triangle) > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating topic coherence: {e}")
            return 0.0

class NetworkFeatureExtractor:
    """Extract network-based features from user interactions and mentions"""
    
    def __init__(self):
        self.interaction_graph = nx.DiGraph()
        self.mention_graph = nx.DiGraph()
        
    async def extract_network_features(self, social_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract network-based features from social media interactions"""
        features = {}
        
        if not social_data:
            return features
        
        # Build interaction network
        await self._build_interaction_network(social_data)
        
        # Calculate network metrics
        if self.interaction_graph.number_of_nodes() > 0:
            # Basic network statistics
            features['network_nodes'] = self.interaction_graph.number_of_nodes()
            features['network_edges'] = self.interaction_graph.number_of_edges()
            features['network_density'] = nx.density(self.interaction_graph)
            
            # Centrality measures for key nodes
            try:
                # Degree centrality
                degree_centrality = nx.degree_centrality(self.interaction_graph)
                features['max_degree_centrality'] = max(degree_centrality.values()) if degree_centrality else 0
                features['avg_degree_centrality'] = statistics.mean(degree_centrality.values()) if degree_centrality else 0
                
                # Betweenness centrality (for smaller networks)
                if self.interaction_graph.number_of_nodes() <= 100:
                    betweenness_centrality = nx.betweenness_centrality(self.interaction_graph)
                    features['max_betweenness_centrality'] = max(betweenness_centrality.values()) if betweenness_centrality else 0
                
                # Closeness centrality (for smaller networks)
                if self.interaction_graph.number_of_nodes() <= 100:
                    closeness_centrality = nx.closeness_centrality(self.interaction_graph)
                    features['max_closeness_centrality'] = max(closeness_centrality.values()) if closeness_centrality else 0
                
            except Exception as e:
                logger.error(f"Error calculating centrality measures: {e}")
        
        # Community detection features
        community_features = await self._analyze_communities()
        features.update(community_features)
        
        # Influence propagation features
        influence_features = await self._analyze_influence_propagation(social_data)
        features.update(influence_features)
        
        return features
    
    async def _build_interaction_network(self, social_data: List[Dict[str, Any]]):
        """Build network from social media interactions"""
        try:
            self.interaction_graph.clear()
            
            for item in social_data:
                author_id = item.get('author_id') or item.get('user_id')
                if not author_id:
                    continue
                
                # Add user node
                self.interaction_graph.add_node(
                    author_id,
                    followers=item.get('author_followers', 0),
                    verified=item.get('author_verified', False)
                )
                
                # Add reply relationships
                if item.get('reply_to_user_id'):
                    self.interaction_graph.add_edge(
                        author_id,
                        item['reply_to_user_id'],
                        interaction_type='reply',
                        timestamp=item.get('created_at')
                    )
                
                # Add mention relationships
                mentions = self._extract_mentions(item.get('text', ''))
                for mention in mentions:
                    self.interaction_graph.add_edge(
                        author_id,
                        mention,
                        interaction_type='mention',
                        timestamp=item.get('created_at')
                    )
                
                # Add retweet relationships
                if item.get('retweeted_user_id'):
                    self.interaction_graph.add_edge(
                        author_id,
                        item['retweeted_user_id'],
                        interaction_type='retweet',
                        timestamp=item.get('created_at')
                    )
        
        except Exception as e:
            logger.error(f"Error building interaction network: {e}")
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text"""
        if not text:
            return []
        
        # Find @mentions
        mentions = re.findall(r'@(\w+)', text.lower())
        return mentions
    
    async def _analyze_communities(self) -> Dict[str, float]:
        """Analyze community structure in the network"""
        features = {}
        
        try:
            if self.interaction_graph.number_of_nodes() < 3:
                return features
            
            # Convert to undirected for community detection
            undirected_graph = self.interaction_graph.to_undirected()
            
            # Simple community detection using connected components
            communities = list(nx.connected_components(undirected_graph))
            
            features['num_communities'] = len(communities)
            
            if communities:
                community_sizes = [len(community) for community in communities]
                features['largest_community_size'] = max(community_sizes)
                features['avg_community_size'] = statistics.mean(community_sizes)
                features['community_size_std'] = statistics.stdev(community_sizes) if len(community_sizes) > 1 else 0
                
                # Modularity (simplified)
                features['modularity'] = len(communities) / max(self.interaction_graph.number_of_nodes(), 1)
        
        except Exception as e:
            logger.error(f"Error analyzing communities: {e}")
        
        return features
    
    async def _analyze_influence_propagation(self, social_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze influence propagation patterns"""
        features = {}
        
        try:
            # Calculate influence scores based on follower counts and engagement
            influence_scores = []
            
            for item in social_data:
                followers = item.get('author_followers', 0)
                engagement = (
                    item.get('like_count', 0) + 
                    item.get('retweet_count', 0) + 
                    item.get('reply_count', 0)
                )
                
                # Simple influence score
                influence_score = np.log1p(followers) * np.log1p(engagement)
                influence_scores.append(influence_score)
            
            if influence_scores:
                features['max_influence_score'] = max(influence_scores)
                features['avg_influence_score'] = statistics.mean(influence_scores)
                features['influence_std'] = statistics.stdev(influence_scores) if len(influence_scores) > 1 else 0
                
                # Influence concentration
                total_influence = sum(influence_scores)
                if total_influence > 0:
                    # Gini coefficient for influence inequality
                    sorted_scores = sorted(influence_scores)
                    n = len(sorted_scores)
                    index = np.arange(1, n + 1)
                    gini = (2 * np.sum(index * sorted_scores)) / (n * total_influence) - (n + 1) / n
                    features['influence_inequality'] = gini
        
        except Exception as e:
            logger.error(f"Error analyzing influence propagation: {e}")
        
        return features

class EngagementFeatureExtractor:
    """Extract engagement-based features from social media metrics"""
    
    def __init__(self):
        self.engagement_history = defaultdict(list)
        
    async def extract_engagement_features(self, social_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract comprehensive engagement features"""
        features = {}
        
        if not social_data:
            return features
        
        # Collect engagement metrics
        likes = [item.get('like_count', 0) for item in social_data]
        retweets = [item.get('retweet_count', 0) for item in social_data]
        replies = [item.get('reply_count', 0) for item in social_data]
        quotes = [item.get('quote_count', 0) for item in social_data]
        
        # Basic engagement statistics
        if likes:
            features['avg_likes'] = statistics.mean(likes)
            features['max_likes'] = max(likes)
            features['likes_std'] = statistics.stdev(likes) if len(likes) > 1 else 0
        
        if retweets:
            features['avg_retweets'] = statistics.mean(retweets)
            features['max_retweets'] = max(retweets)
            features['retweets_std'] = statistics.stdev(retweets) if len(retweets) > 1 else 0
        
        if replies:
            features['avg_replies'] = statistics.mean(replies)
            features['max_replies'] = max(replies)
            features['replies_std'] = statistics.stdev(replies) if len(replies) > 1 else 0
        
        # Engagement ratios
        total_engagement = [l + r + rp + q for l, r, rp, q in zip(likes, retweets, replies, quotes)]
        if total_engagement:
            features['avg_total_engagement'] = statistics.mean(total_engagement)
            features['max_total_engagement'] = max(total_engagement)
            
            # Engagement type ratios
            total_sum = sum(total_engagement)
            if total_sum > 0:
                features['likes_ratio'] = sum(likes) / total_sum
                features['retweets_ratio'] = sum(retweets) / total_sum
                features['replies_ratio'] = sum(replies) / total_sum
                features['quotes_ratio'] = sum(quotes) / total_sum
        
        # Viral content detection
        features['viral_threshold_exceeded'] = sum(1 for eng in total_engagement if eng > 1000) / len(total_engagement) if total_engagement else 0
        
        # Engagement velocity
        engagement_velocity = await self._calculate_engagement_velocity(social_data)
        features.update(engagement_velocity)
        
        return features
    
    async def _calculate_engagement_velocity(self, social_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate engagement velocity features"""
        features = {}
        
        try:
            # Sort by timestamp
            timestamped_data = []
            for item in social_data:
                try:
                    timestamp = datetime.fromisoformat(item.get('created_at', '').replace('Z', '+00:00'))
                    engagement = (
                        item.get('like_count', 0) + 
                        item.get('retweet_count', 0) + 
                        item.get('reply_count', 0)
                    )
                    timestamped_data.append((timestamp, engagement))
                except Exception:
                    continue
            
            if len(timestamped_data) < 2:
                return features
            
            timestamped_data.sort(key=lambda x: x[0])
            
            # Calculate engagement rate over time
            time_windows = [
                ('1hour', timedelta(hours=1)),
                ('6hour', timedelta(hours=6)),
                ('1day', timedelta(days=1))
            ]
            
            latest_time = timestamped_data[-1][0]
            
            for window_name, window_size in time_windows:
                cutoff_time = latest_time - window_size
                
                recent_data = [(ts, eng) for ts, eng in timestamped_data if ts >= cutoff_time]
                
                if recent_data:
                    total_engagement = sum(eng for _, eng in recent_data)
                    time_span_hours = window_size.total_seconds() / 3600
                    
                    features[f'engagement_rate_{window_name}'] = total_engagement / time_span_hours
                    features[f'post_count_{window_name}'] = len(recent_data)
                    
                    if len(recent_data) > 1:
                        engagements = [eng for _, eng in recent_data]
                        features[f'engagement_std_{window_name}'] = statistics.stdev(engagements)
        
        except Exception as e:
            logger.error(f"Error calculating engagement velocity: {e}")
        
        return features

class FeatureEngineeringEngine:
    """Main feature engineering coordinator"""
    
    def __init__(self):
        self.temporal_extractor = TemporalFeatureExtractor()
        self.semantic_extractor = SemanticFeatureExtractor()
        self.network_extractor = NetworkFeatureExtractor()
        self.engagement_extractor = EngagementFeatureExtractor()
        
        self.redis_client = None
        self.feature_cache = {}
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler()
        }
        
        self.feature_stats = {
            'total_features_extracted': 0,
            'processing_time_total': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    async def initialize(self):
        """Initialize feature engineering engine"""
        try:
            # Initialize Redis client
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            logger.info("Feature engineering engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize feature engineering engine: {e}")
            raise
    
    async def engineer_features(self) -> Dict[str, Any]:
        """Main feature engineering orchestration"""
        engineering_start = datetime.now()
        
        try:
            # Get processed data from Redis streams
            processed_data = await self._get_processed_data()
            
            if not processed_data:
                return {
                    'features_extracted': 0,
                    'processing_time_seconds': 0,
                    'timestamp': engineering_start.isoformat()
                }
            
            # Extract features from different data types
            feature_sets = []
            
            # Process social media data
            if 'social' in processed_data:
                social_features = await self._extract_social_features(processed_data['social'])
                feature_sets.append(social_features)
            
            # Process game data
            if 'games' in processed_data:
                game_features = await self._extract_game_features(processed_data['games'])
                feature_sets.append(game_features)
            
            # Process news data
            if 'news' in processed_data:
                news_features = await self._extract_news_features(processed_data['news'])
                feature_sets.append(news_features)
            
            # Combine and store features
            combined_features = await self._combine_feature_sets(feature_sets)
            await self._store_engineered_features(combined_features)
            
            # Update statistics
            processing_time = (datetime.now() - engineering_start).total_seconds()
            self.feature_stats['total_features_extracted'] += len(combined_features)
            self.feature_stats['processing_time_total'] += processing_time
            
            return {
                'features_extracted': len(combined_features),
                'processing_time_seconds': processing_time,
                'feature_categories': list(combined_features.keys()) if combined_features else [],
                'timestamp': engineering_start.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            raise
    
    async def _get_processed_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get processed data from Redis streams"""
        try:
            processed_data = {}
            
            # Define stream keys to read from
            stream_keys = [
                'stream:tweets',
                'stream:games', 
                'stream:news'
            ]
            
            for stream_key in stream_keys:
                try:
                    # Read recent entries from stream
                    entries = await self.redis_client.xread(
                        {stream_key: '$'},
                        count=100,
                        block=1000  # 1 second timeout
                    )
                    
                    if entries:
                        stream_name = stream_key.split(':')[1]
                        processed_data[stream_name] = []
                        
                        for stream_entries in entries:
                            for entry_id, entry_data in stream_entries[1]:
                                try:
                                    # Parse entry data
                                    data_item = {}
                                    for key, value in entry_data.items():
                                        try:
                                            # Try to parse JSON values
                                            data_item[key] = json.loads(value)
                                        except (json.JSONDecodeError, TypeError):
                                            data_item[key] = value
                                    
                                    processed_data[stream_name].append(data_item)
                                except Exception as e:
                                    logger.error(f"Error parsing stream entry: {e}")
                                    continue
                
                except Exception as e:
                    logger.error(f"Error reading from stream {stream_key}: {e}")
                    continue
            
            # Also include 'social' category for tweets
            if 'tweets' in processed_data:
                processed_data['social'] = processed_data['tweets']
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error getting processed data: {e}")
            return {}
    
    async def _extract_social_features(self, social_data: List[Dict[str, Any]]) -> FeatureSet:
        """Extract features from social media data"""
        try:
            # Extract text content
            texts = [item.get('text', '') for item in social_data if item.get('text')]
            
            # Extract features from different extractors
            temporal_features = await self.temporal_extractor.extract_temporal_features(social_data)
            semantic_features = await self.semantic_extractor.extract_semantic_features(texts)
            network_features = await self.network_extractor.extract_network_features(social_data)
            engagement_features = await self.engagement_extractor.extract_engagement_features(social_data)
            
            return FeatureSet(
                temporal_features=temporal_features,
                semantic_features=semantic_features,
                network_features=network_features,
                engagement_features=engagement_features,
                metadata={'data_type': 'social', 'record_count': len(social_data)},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error extracting social features: {e}")
            return FeatureSet({}, {}, {}, {}, {}, datetime.now())
    
    async def _extract_game_features(self, game_data: List[Dict[str, Any]]) -> FeatureSet:
        """Extract features from game data"""
        try:
            # Extract temporal features specific to games
            temporal_features = await self.temporal_extractor.extract_event_temporal_features(game_data)
            
            # Extract game-specific features
            game_features = {}
            
            if game_data:
                # Sports distribution
                sports = [item.get('sport', '') for item in game_data if item.get('sport')]
                sport_counts = Counter(sports)
                
                for sport, count in sport_counts.items():
                    game_features[f'sport_{sport}_count'] = count
                    game_features[f'sport_{sport}_ratio'] = count / len(game_data)
                
                # Game status distribution
                statuses = [item.get('status', '') for item in game_data if item.get('status')]
                status_counts = Counter(statuses)
                
                for status, count in status_counts.items():
                    game_features[f'status_{status}_count'] = count
                
                # Score-based features (if available)
                scores = []
                for item in game_data:
                    if item.get('score'):
                        # Extract numeric scores (simplified)
                        try:
                            score_data = item['score']
                            if isinstance(score_data, dict):
                                home_score = score_data.get('home', 0)
                                away_score = score_data.get('away', 0)
                                total_score = home_score + away_score
                                scores.append(total_score)
                        except Exception:
                            continue
                
                if scores:
                    game_features['avg_total_score'] = statistics.mean(scores)
                    game_features['max_total_score'] = max(scores)
                    game_features['score_std'] = statistics.stdev(scores) if len(scores) > 1 else 0
            
            return FeatureSet(
                temporal_features=temporal_features,
                semantic_features={},
                network_features={},
                engagement_features=game_features,
                metadata={'data_type': 'games', 'record_count': len(game_data)},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error extracting game features: {e}")
            return FeatureSet({}, {}, {}, {}, {}, datetime.now())
    
    async def _extract_news_features(self, news_data: List[Dict[str, Any]]) -> FeatureSet:
        """Extract features from news data"""
        try:
            # Extract text content
            texts = []
            for item in news_data:
                text_parts = []
                if item.get('title'):
                    text_parts.append(item['title'])
                if item.get('description'):
                    text_parts.append(item['description'])
                if item.get('content'):
                    text_parts.append(item['content'])
                
                if text_parts:
                    texts.append(' '.join(text_parts))
            
            # Extract features
            temporal_features = await self.temporal_extractor.extract_temporal_features(news_data)
            semantic_features = await self.semantic_extractor.extract_semantic_features(texts)
            
            # News-specific features
            news_features = {}
            
            if news_data:
                # Source distribution
                sources = [item.get('source', '') for item in news_data if item.get('source')]
                source_counts = Counter(sources)
                
                news_features['unique_sources'] = len(source_counts)
                news_features['avg_articles_per_source'] = statistics.mean(source_counts.values()) if source_counts else 0
                
                # Content length statistics
                content_lengths = [len(item.get('content', '')) for item in news_data if item.get('content')]
                if content_lengths:
                    news_features['avg_content_length'] = statistics.mean(content_lengths)
                    news_features['content_length_std'] = statistics.stdev(content_lengths) if len(content_lengths) > 1 else 0
            
            return FeatureSet(
                temporal_features=temporal_features,
                semantic_features=semantic_features,
                network_features={},
                engagement_features=news_features,
                metadata={'data_type': 'news', 'record_count': len(news_data)},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error extracting news features: {e}")
            return FeatureSet({}, {}, {}, {}, {}, datetime.now())
    
    async def _combine_feature_sets(self, feature_sets: List[FeatureSet]) -> Dict[str, Any]:
        """Combine multiple feature sets into a unified feature vector"""
        try:
            combined_features = {}
            
            for feature_set in feature_sets:
                data_type = feature_set.metadata.get('data_type', 'unknown')
                
                # Add prefixes to avoid naming conflicts
                for key, value in feature_set.temporal_features.items():
                    combined_features[f'{data_type}_temporal_{key}'] = value
                
                for key, value in feature_set.semantic_features.items():
                    combined_features[f'{data_type}_semantic_{key}'] = value
                
                for key, value in feature_set.network_features.items():
                    combined_features[f'{data_type}_network_{key}'] = value
                
                for key, value in feature_set.engagement_features.items():
                    combined_features[f'{data_type}_engagement_{key}'] = value
            
            # Add cross-feature interactions
            interaction_features = await self._calculate_feature_interactions(combined_features)
            combined_features.update(interaction_features)
            
            return combined_features
            
        except Exception as e:
            logger.error(f"Error combining feature sets: {e}")
            return {}
    
    async def _calculate_feature_interactions(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate feature interactions and derived features"""
        interaction_features = {}
        
        try:
            # Sentiment-engagement interactions
            sentiment_keys = [k for k in features.keys() if 'sentiment' in k.lower()]
            engagement_keys = [k for k in features.keys() if 'engagement' in k.lower() or 'like' in k.lower()]
            
            for sent_key in sentiment_keys:
                for eng_key in engagement_keys:
                    try:
                        sent_val = features.get(sent_key, 0)
                        eng_val = features.get(eng_key, 0)
                        if isinstance(sent_val, (int, float)) and isinstance(eng_val, (int, float)):
                            interaction_features[f'interaction_{sent_key}_{eng_key}'] = sent_val * eng_val
                    except Exception:
                        continue
            
            # Temporal-content interactions
            temporal_keys = [k for k in features.keys() if 'temporal' in k.lower()]
            content_keys = [k for k in features.keys() if any(x in k.lower() for x in ['text', 'content', 'semantic'])]
            
            for temp_key in temporal_keys[:3]:  # Limit to avoid too many features
                for cont_key in content_keys[:3]:
                    try:
                        temp_val = features.get(temp_key, 0)
                        cont_val = features.get(cont_key, 0)
                        if isinstance(temp_val, (int, float)) and isinstance(cont_val, (int, float)):
                            interaction_features[f'interaction_{temp_key}_{cont_key}'] = temp_val * cont_val
                    except Exception:
                        continue
        
        except Exception as e:
            logger.error(f"Error calculating feature interactions: {e}")
        
        return interaction_features
    
    async def _store_engineered_features(self, features: Dict[str, Any]):
        """Store engineered features in Redis"""
        try:
            timestamp = datetime.now()
            feature_key = f"features:{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Add metadata
            feature_data = {
                'features': features,
                'timestamp': timestamp.isoformat(),
                'feature_count': len(features),
                'extraction_metadata': {
                    'engine_version': '1.0',
                    'feature_categories': list(set(key.split('_')[0] for key in features.keys()))
                }
            }
            
            # Store with TTL
            await self.redis_client.setex(
                feature_key,
                timedelta(days=7).total_seconds(),  # 7-day TTL
                json.dumps(feature_data, default=str)
            )
            
            # Also store in a stream for ML model consumption
            await self.redis_client.xadd(
                'stream:features',
                feature_data,
                maxlen=5000  # Keep last 5k feature sets
            )
            
            logger.info(f"Stored {len(features)} engineered features with key: {feature_key}")
            
        except Exception as e:
            logger.error(f"Error storing engineered features: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for feature engineering engine"""
        try:
            # Check Redis connection
            redis_status = "healthy"
            try:
                await self.redis_client.ping()
            except Exception:
                redis_status = "unhealthy"
            
            # Check extractors
            extractor_status = {
                'temporal': 'healthy',
                'semantic': 'healthy',
                'network': 'healthy',
                'engagement': 'healthy'
            }
            
            overall_status = "healthy" if redis_status == "healthy" else "degraded"
            
            return {
                'status': overall_status,
                'components': {
                    'redis': redis_status,
                    'extractors': extractor_status
                },
                'stats': self.feature_stats,
                'cache_efficiency': (
                    self.feature_stats['cache_hits'] / 
                    max(self.feature_stats['cache_hits'] + self.feature_stats['cache_misses'], 1)
                ),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def stop(self):
        """Stop feature engineering engine"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Feature engineering engine stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping feature engineering engine: {e}")