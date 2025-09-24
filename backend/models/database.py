from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import settings

Base = declarative_base()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Sport(Base):
    __tablename__ = "sports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analyses = relationship("Analysis", back_populates="sport")
    predictions = relationship("Prediction", back_populates="sport")

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    sport_id = Column(Integer, ForeignKey("sports.id"))
    analysis_type = Column(String)  # sentiment, engagement, pr_strategy
    input_data = Column(JSON)
    result = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sport = relationship("Sport", back_populates="analyses")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    sport_id = Column(Integer, ForeignKey("sports.id"))
    prediction_type = Column(String)
    features = Column(JSON)
    prediction = Column(Float)
    confidence = Column(Float)
    actual = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sport = relationship("Sport", back_populates="predictions")

class PRCampaign(Base):
    __tablename__ = "pr_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    sport = Column(String)
    strategy = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    budget = Column(Float)
    target_sentiment = Column(Float)
    target_engagement = Column(Float)
    actual_sentiment = Column(Float, nullable=True)
    actual_engagement = Column(Float, nullable=True)
    status = Column(String, default="planned")  # planned, active, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SentimentHistory(Base):
    __tablename__ = "sentiment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String)
    text = Column(String)
    sentiment = Column(String)
    positive_score = Column(Float)
    negative_score = Column(Float)
    neutral_score = Column(Float)
    source = Column(String)  # twitter, reddit, news
    created_at = Column(DateTime, default=datetime.utcnow)

class EngagementMetric(Base):
    __tablename__ = "engagement_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String)
    metric_type = Column(String)  # likes, shares, comments, views
    value = Column(Float)
    platform = Column(String)  # twitter, instagram, facebook
    recorded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Database helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()