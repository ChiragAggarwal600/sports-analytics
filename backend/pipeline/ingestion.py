"""
Data Ingestion Manager
Handles multi-source data collection including social APIs, game stats, and news
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import tweepy
import httpx
from dataclasses import dataclass
import aioredis
from kafka import KafkaProducer
from confluent_kafka import Producer as ConfluentProducer

from config.settings import settings

settings = get_settings()
logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Data source configuration"""
    name: str
    source_type: str  # 'api', 'feed', 'scraper'
    endpoint: str
    auth_config: Dict[str, Any]
    rate_limit: int
    batch_size: int
    enabled: bool = True

class TwitterIngestion:
    """Twitter/X data ingestion using Tweepy"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api = None
        self.client = None
        
    async def initialize(self):
        """Initialize Twitter API clients"""
        try:
            # Twitter API v2 client
            self.client = tweepy.Client(
                bearer_token=self.config.get("bearer_token"),
                consumer_key=self.config.get("consumer_key"),
                consumer_secret=self.config.get("consumer_secret"),
                access_token=self.config.get("access_token"),
                access_token_secret=self.config.get("access_token_secret"),
                wait_on_rate_limit=True
            )
            
            # Legacy API for additional features
            auth = tweepy.OAuthHandler(
                self.config.get("consumer_key"),
                self.config.get("consumer_secret")
            )
            auth.set_access_token(
                self.config.get("access_token"),
                self.config.get("access_token_secret")
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            logger.info("Twitter API clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API: {e}")
            raise
    
    async def collect_tweets(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Collect tweets based on query"""
        try:
            tweets = []
            
            # Search recent tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=[
                    'created_at', 'author_id', 'public_metrics',
                    'context_annotations', 'lang', 'geo', 'reply_settings'
                ],
                user_fields=['username', 'public_metrics', 'verified', 'location'],
                expansions=['author_id']
            )
            
            if response.data:
                # Create user lookup
                users = {user.id: user for user in response.includes.get('users', [])}
                
                for tweet in response.data:
                    user = users.get(tweet.author_id)
                    
                    tweet_data = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'author_id': tweet.author_id,
                        'author_username': user.username if user else None,
                        'author_verified': user.verified if user else False,
                        'author_followers': user.public_metrics['followers_count'] if user else 0,
                        'retweet_count': tweet.public_metrics['retweet_count'],
                        'like_count': tweet.public_metrics['like_count'],
                        'reply_count': tweet.public_metrics['reply_count'],
                        'quote_count': tweet.public_metrics['quote_count'],
                        'lang': tweet.lang,
                        'context_annotations': tweet.context_annotations,
                        'source': 'twitter',
                        'collected_at': datetime.now().isoformat()
                    }
                    tweets.append(tweet_data)
            
            logger.info(f"Collected {len(tweets)} tweets for query: {query}")
            return tweets
            
        except Exception as e:
            logger.error(f"Failed to collect tweets: {e}")
            return []

class SportsAPIIngestion:
    """Sports data ingestion from various APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "SportsAnalytics/1.0"}
        )
        logger.info("Sports API client initialized")
    
    async def collect_game_stats(self, sport: str, date: str) -> List[Dict[str, Any]]:
        """Collect game statistics"""
        try:
            # Example API endpoints (replace with actual APIs)
            endpoints = {
                'football': f"https://api.football-data.org/v4/matches?date={date}",
                'basketball': f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}",
                'cricket': f"https://cricapi.com/api/matches?apikey={self.config.get('cricket_api_key')}"
            }
            
            if sport not in endpoints:
                logger.warning(f"No API endpoint configured for sport: {sport}")
                return []
            
            headers = {}
            if sport == 'football':
                headers['X-Auth-Token'] = self.config.get('football_api_key')
            elif sport == 'basketball':
                headers['Ocp-Apim-Subscription-Key'] = self.config.get('basketball_api_key')
            
            response = await self.session.get(endpoints[sport], headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Normalize data structure
            games = []
            for game in data.get('matches', data.get('games', data.get('data', []))):
                game_data = {
                    'id': game.get('id'),
                    'sport': sport,
                    'home_team': game.get('homeTeam', {}).get('name', game.get('HomeTeam')),
                    'away_team': game.get('awayTeam', {}).get('name', game.get('AwayTeam')),
                    'date': game.get('utcDate', game.get('DateTime', game.get('date'))),
                    'status': game.get('status'),
                    'score': game.get('score'),
                    'venue': game.get('venue'),
                    'source': f'{sport}_api',
                    'collected_at': datetime.now().isoformat()
                }
                games.append(game_data)
            
            logger.info(f"Collected {len(games)} {sport} games for {date}")
            return games
            
        except Exception as e:
            logger.error(f"Failed to collect {sport} stats: {e}")
            return []

class NewsIngestion:
    """News data ingestion from various sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = httpx.AsyncClient(timeout=30.0)
        logger.info("News API client initialized")
    
    async def collect_news(self, keywords: List[str], language: str = 'en') -> List[Dict[str, Any]]:
        """Collect news articles"""
        try:
            articles = []
            
            # NewsAPI
            if self.config.get('news_api_key'):
                query = ' OR '.join(keywords)
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': query,
                    'language': language,
                    'sortBy': 'publishedAt',
                    'pageSize': 100,
                    'apiKey': self.config['news_api_key']
                }
                
                response = await self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                for article in data.get('articles', []):
                    if article.get('title') and article.get('description'):
                        article_data = {
                            'title': article['title'],
                            'description': article['description'],
                            'content': article.get('content'),
                            'url': article['url'],
                            'source': article['source']['name'],
                            'author': article.get('author'),
                            'published_at': article['publishedAt'],
                            'url_to_image': article.get('urlToImage'),
                            'collected_at': datetime.now().isoformat()
                        }
                        articles.append(article_data)
            
            logger.info(f"Collected {len(articles)} news articles")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to collect news: {e}")
            return []

class DataIngestionManager:
    """Main data ingestion manager coordinating all sources"""
    
    def __init__(self):
        self.twitter = TwitterIngestion(settings.TWITTER_CONFIG)
        self.sports_api = SportsAPIIngestion(settings.SPORTS_API_CONFIG)
        self.news = NewsIngestion(settings.NEWS_API_CONFIG)
        
        self.redis_client = None
        self.kafka_producer = None
        self.confluent_producer = None
        
        self.ingestion_stats = {
            'total_records': 0,
            'by_source': {},
            'errors': 0,
            'last_ingestion': None
        }
    
    async def initialize(self):
        """Initialize all ingestion components"""
        try:
            # Initialize data source clients
            await self.twitter.initialize()
            await self.sports_api.initialize()
            await self.news.initialize()
            
            # Initialize Redis
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize Kafka producers
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10
            )
            
            # Confluent Kafka for better performance
            self.confluent_producer = ConfluentProducer({
                'bootstrap.servers': ','.join(settings.KAFKA_BOOTSTRAP_SERVERS),
                'acks': 'all',
                'retries': 3,
                'batch.size': 16384,
                'linger.ms': 10,
                'compression.type': 'snappy'
            })
            
            logger.info("Data ingestion manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize data ingestion manager: {e}")
            raise
    
    async def collect_data(self) -> Dict[str, Any]:
        """Main data collection orchestration"""
        collection_start = datetime.now()
        collected_data = {
            'tweets': [],
            'games': [],
            'news': [],
            'timestamp': collection_start.isoformat()
        }
        
        try:
            # Define collection tasks
            tasks = []
            
            # Twitter collection
            if settings.TWITTER_CONFIG.get('enabled', True):
                for query in settings.TWITTER_QUERIES:
                    tasks.append(self._collect_twitter_data(query))
            
            # Sports data collection
            if settings.SPORTS_API_CONFIG.get('enabled', True):
                for sport in settings.SPORTS_TO_MONITOR:
                    tasks.append(self._collect_sports_data(sport))
            
            # News collection
            if settings.NEWS_API_CONFIG.get('enabled', True):
                tasks.append(self._collect_news_data())
            
            # Execute all collection tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Collection task failed: {result}")
                    self.ingestion_stats['errors'] += 1
                elif isinstance(result, dict):
                    for key, value in result.items():
                        if key in collected_data and isinstance(value, list):
                            collected_data[key].extend(value)
            
            # Store in Redis and Kafka
            await self._store_collected_data(collected_data)
            
            # Update statistics
            total_records = sum(len(v) for v in collected_data.values() if isinstance(v, list))
            self.ingestion_stats['total_records'] += total_records
            self.ingestion_stats['last_ingestion'] = collection_start.isoformat()
            
            for source, data in collected_data.items():
                if isinstance(data, list):
                    self.ingestion_stats['by_source'][source] = self.ingestion_stats['by_source'].get(source, 0) + len(data)
            
            collection_time = (datetime.now() - collection_start).total_seconds()
            
            return {
                'records_collected': total_records,
                'collection_time_seconds': collection_time,
                'sources': {k: len(v) for k, v in collected_data.items() if isinstance(v, list)},
                'timestamp': collection_start.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            self.ingestion_stats['errors'] += 1
            raise
    
    async def _collect_twitter_data(self, query: str) -> Dict[str, List]:
        """Collect Twitter data for a specific query"""
        try:
            tweets = await self.twitter.collect_tweets(query, max_results=100)
            return {'tweets': tweets}
        except Exception as e:
            logger.error(f"Twitter collection failed for query '{query}': {e}")
            return {'tweets': []}
    
    async def _collect_sports_data(self, sport: str) -> Dict[str, List]:
        """Collect sports data for a specific sport"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            games = await self.sports_api.collect_game_stats(sport, today)
            return {'games': games}
        except Exception as e:
            logger.error(f"Sports data collection failed for {sport}: {e}")
            return {'games': []}
    
    async def _collect_news_data(self) -> Dict[str, List]:
        """Collect news data"""
        try:
            keywords = settings.NEWS_KEYWORDS
            articles = await self.news.collect_news(keywords)
            return {'news': articles}
        except Exception as e:
            logger.error(f"News collection failed: {e}")
            return {'news': []}
    
    async def _store_collected_data(self, data: Dict[str, Any]):
        """Store collected data in Redis and Kafka"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Store in Redis for quick access
            redis_key = f"ingestion:{timestamp}"
            await self.redis_client.setex(
                redis_key,
                timedelta(hours=24).total_seconds(),
                json.dumps(data)
            )
            
            # Send to Kafka topics for stream processing
            for data_type, records in data.items():
                if isinstance(records, list) and records:
                    topic = f"{settings.KAFKA_TOPIC_PREFIX}{data_type}"
                    
                    for record in records:
                        record['ingestion_timestamp'] = timestamp
                        
                        # Send to Kafka
                        self.confluent_producer.produce(
                            topic,
                            key=record.get('id', ''),
                            value=json.dumps(record),
                            callback=self._kafka_delivery_callback
                        )
            
            # Flush Kafka producer
            self.confluent_producer.flush()
            
            logger.info(f"Data stored successfully - Redis key: {redis_key}")
            
        except Exception as e:
            logger.error(f"Failed to store collected data: {e}")
            raise
    
    def _kafka_delivery_callback(self, err, msg):
        """Kafka delivery callback"""
        if err:
            logger.error(f"Kafka delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for ingestion manager"""
        try:
            # Check Redis connection
            redis_status = "healthy"
            try:
                await self.redis_client.ping()
            except Exception:
                redis_status = "unhealthy"
            
            # Check Kafka connection
            kafka_status = "healthy"
            try:
                # Simple connectivity check
                metadata = self.confluent_producer.list_topics(timeout=5)
            except Exception:
                kafka_status = "unhealthy"
            
            # Check API clients
            api_status = {
                'twitter': 'healthy' if self.twitter.client else 'unhealthy',
                'sports': 'healthy' if self.sports_api.session else 'unhealthy',
                'news': 'healthy' if self.news.session else 'unhealthy'
            }
            
            overall_status = "healthy"
            if redis_status != "healthy" or kafka_status != "healthy":
                overall_status = "degraded"
            if all(status != "healthy" for status in api_status.values()):
                overall_status = "critical"
            
            return {
                'status': overall_status,
                'components': {
                    'redis': redis_status,
                    'kafka': kafka_status,
                    'apis': api_status
                },
                'stats': self.ingestion_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def stop(self):
        """Stop ingestion manager"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.kafka_producer:
                self.kafka_producer.close()
            
            if self.confluent_producer:
                self.confluent_producer.flush()
            
            # Close API sessions
            if self.sports_api.session:
                await self.sports_api.session.aclose()
            if self.news.session:
                await self.news.session.aclose()
            
            logger.info("Data ingestion manager stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping ingestion manager: {e}")