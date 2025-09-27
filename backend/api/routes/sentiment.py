from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime

from api.model_registry import get_models
from models.cross_sport_normalizer import CrossSportNormalizer

router = APIRouter()

class SentimentRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to analyze")
    sport: Optional[str] = Field("general", description="Sport context")
    metadata: Optional[Dict] = Field(default_factory=dict)

class SentimentResponse(BaseModel):
    results: List[Dict]
    summary: Dict
    timestamp: datetime

@router.post("/predict", response_model=SentimentResponse)
async def predict_sentiment(request: SentimentRequest):
    """
    Predict sentiment for given texts
    """
    try:
        models = get_models()
        sentiment_model = models.get('sentiment')
        
        if not sentiment_model:
            raise HTTPException(status_code=503, detail="Sentiment model not loaded")
        
        # Predict sentiment
        results = sentiment_model.predict(request.texts)
        
        # Calculate summary statistics
        sentiments = [r['overall'] for r in results]
        summary = {
            'total_texts': len(request.texts),
            'positive_ratio': sum(1 for s in sentiments if s == 'positive') / len(sentiments),
            'negative_ratio': sum(1 for s in sentiments if s == 'negative') / len(sentiments),
            'neutral_ratio': sum(1 for s in sentiments if s == 'neutral') / len(sentiments),
            'average_positive_score': np.mean([r['positive'] for r in results]),
            'sport_context': request.sport
        }
        
        return SentimentResponse(
            results=results,
            summary=summary,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analyze")
async def batch_analyze(
    texts: List[str],
    sport: str = "general",
    include_trends: bool = False
):
    """
    Batch sentiment analysis with optional trend analysis
    """
    try:
        models = get_models()
        sentiment_model = models.get('sentiment')
        
        if not sentiment_model:
            raise HTTPException(status_code=503, detail="Sentiment model not loaded")
        
        # Process in batches
        batch_size = 100
        all_results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            results = sentiment_model.predict(batch)
            all_results.extend(results)
        
        response = {
            'results': all_results,
            'count': len(all_results)
        }
        
        if include_trends:
            # Calculate sentiment trends
            response['trends'] = calculate_sentiment_trends(all_results)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_sentiment_trends(results: List[Dict]) -> Dict:
    """Calculate sentiment trends from results"""
    trends = {
        'sentiment_distribution': {
            'positive': sum(1 for r in results if r['overall'] == 'positive'),
            'negative': sum(1 for r in results if r['overall'] == 'negative'),
            'neutral': sum(1 for r in results if r['overall'] == 'neutral')
        },
        'average_scores': {
            'positive': np.mean([r['positive'] for r in results]),
            'negative': np.mean([r['negative'] for r in results]),
            'neutral': np.mean([r['neutral'] for r in results])
        }
    }
    return trends