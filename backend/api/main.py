from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from config.settings import settings
from api.routes import sentiment, engagement, pr_strategy
from models.sentiment_model import SentimentAnalyzer
from models.engagement_model import EngagementPredictor
from models.rl_module import RLPROptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instances
models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize models on startup"""
    logger.info("Loading ML models...")
    
    try:
        models['sentiment'] = SentimentAnalyzer()
        models['engagement'] = EngagementPredictor()
        models['rl_optimizer'] = RLPROptimizer()
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        
    yield
    
    # Cleanup
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sentiment.router, prefix=f"{settings.API_PREFIX}/sentiment", tags=["sentiment"])
app.include_router(engagement.router, prefix=f"{settings.API_PREFIX}/engagement", tags=["engagement"])
app.include_router(pr_strategy.router, prefix=f"{settings.API_PREFIX}/pr-strategy", tags=["pr_strategy"])

@app.get("/")
async def root():
    return {
        "message": "Cross-Sport PR Analytics API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models_loaded": len(models) > 0
    }

# Export models for use in routes
def get_models():
    return models