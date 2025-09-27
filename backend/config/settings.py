from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from pydantic import Field
import os

class Settings(BaseSettings):
    # API Settings
    APP_NAME: str = "Cross-Sport PR Analytics"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/pranalytics")
    
    # ML Model Paths
    SENTIMENT_MODEL_PATH: str = "models/saved/sentiment_model.pt"
    ENGAGEMENT_MODEL_PATH: str = "models/saved/engagement_model.pkl"
    RL_MODEL_PATH: str = "models/saved/rl_model.pkl"
    
    # External APIs
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    
    # Redis Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: List[str] = Field(default=["localhost:9092"])
    KAFKA_TOPIC_PREFIX: str = Field(default="sports_analytics_")
    
    # Data Source Configurations
    TWITTER_CONFIG: Dict[str, Any] = Field(default={
        "enabled": True,
        "bearer_token": os.getenv("TWITTER_BEARER_TOKEN", ""),
        "consumer_key": os.getenv("TWITTER_CONSUMER_KEY", ""),
        "consumer_secret": os.getenv("TWITTER_CONSUMER_SECRET", ""),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN", ""),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    })
    
    SPORTS_API_CONFIG: Dict[str, Any] = Field(default={
        "enabled": True,
        "football_api_key": os.getenv("FOOTBALL_API_KEY", ""),
        "basketball_api_key": os.getenv("BASKETBALL_API_KEY", ""),
        "cricket_api_key": os.getenv("CRICKET_API_KEY", "")
    })
    
    NEWS_API_CONFIG: Dict[str, Any] = Field(default={
        "enabled": True,
        "news_api_key": os.getenv("NEWS_API_KEY", "")
    })
    
    # Data Collection Configuration
    TWITTER_QUERIES: List[str] = Field(default=[
        "football OR soccer OR FIFA",
        "basketball OR NBA",
        "cricket OR ICC", 
        "sports betting OR gambling",
        "sports scandal OR controversy"
    ])
    
    SPORTS_TO_MONITOR: List[str] = Field(default=["football", "basketball", "cricket"])
    
    NEWS_KEYWORDS: List[str] = Field(default=[
        "football", "soccer", "basketball", "cricket", "sports",
        "athlete", "team", "championship", "tournament", "scandal",
        "betting", "gambling", "match fixing", "doping"
    ])
    
    # Pipeline Intervals (in seconds)
    INGESTION_INTERVAL: int = Field(default=60)
    FEATURE_ENGINEERING_INTERVAL: int = Field(default=120)
    MODEL_INFERENCE_INTERVAL: int = Field(default=180)
    RISK_ASSESSMENT_INTERVAL: int = Field(default=300)
    INTERVENTION_INTERVAL: int = Field(default=600)
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables

settings = Settings()