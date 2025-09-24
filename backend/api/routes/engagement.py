from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime

from api.main import get_models
from models.cross_sport_normalizer import CrossSportNormalizer
from models.engagement_model import EngagementFeatureExtractor

router = APIRouter()

class EngagementRequest(BaseModel):
    sport: str = Field(..., description="Sport type")
    data: Dict = Field(..., description="Sport-specific data")
    include_confidence: bool = Field(False, description="Include confidence intervals")

class EngagementResponse(BaseModel):
    engagement_score: float
    confidence: Optional[float]
    factors: Dict
    recommendations: List[str]
    timestamp: datetime

@router.post("/predict", response_model=EngagementResponse)
async def predict_engagement(request: EngagementRequest):
    """
    Predict engagement level for given input
    """
    try:
        models = get_models()
        engagement_model = models.get('engagement')
        
        if not engagement_model:
            raise HTTPException(status_code=503, detail="Engagement model not loaded")
        
        # Normalize sport-specific data
        normalizer = CrossSportNormalizer()
        normalized_features = normalizer.normalize(request.data, request.sport)
        
        # Extract additional engagement features
        engagement_features = EngagementFeatureExtractor.extract_features(request.data)
        
        # Combine features
        combined_features = np.concatenate([normalized_features, engagement_features.flatten()])
        
        # Predict
        if request.include_confidence:
            prediction, confidence = engagement_model.predict_with_confidence(
                combined_features.reshape(1, -1)
            )
            engagement_score = float(prediction[0])
            confidence_value = float(confidence[0])
        else:
            prediction = engagement_model.predict(combined_features.reshape(1, -1))
            engagement_score = float(prediction[0])
            confidence_value = None
        
        # Analyze factors
        factors = analyze_engagement_factors(request.data, engagement_score)
        
        # Generate recommendations
        recommendations = generate_engagement_recommendations(
            engagement_score, 
            factors, 
            request.sport
        )
        
        return EngagementResponse(
            engagement_score=engagement_score,
            confidence=confidence_value,
            factors=factors,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/historical")
async def get_historical_engagement(
    sport: str,
    start_date: datetime,
    end_date: datetime,
    granularity: str = "daily"
):
    """
    Get historical engagement data
    """
    try:
        # This would typically query from database
        # For demo, returning mock data
        
        data_points = []
        current = start_date
        
        while current <= end_date:
            data_points.append({
                'date': current.isoformat(),
                'engagement': np.random.uniform(0.3, 0.8),
                'sport': sport
            })
            
            if granularity == "hourly":
                current += pd.Timedelta(hours=1)
            elif granularity == "daily":
                current += pd.Timedelta(days=1)
            else:
                current += pd.Timedelta(weeks=1)
        
        return {
            'sport': sport,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'granularity': granularity,
            'data': data_points
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def analyze_engagement_factors(data: Dict, score: float) -> Dict:
    """Analyze factors contributing to engagement score"""
    factors = {
        'timing': 'optimal' if data.get('hour_of_day', 12) in [18, 19, 20] else 'suboptimal',
        'sentiment': 'positive' if data.get('current_sentiment', 0.5) > 0.6 else 'neutral',
        'competition': 'low' if data.get('competitor_activity', 0.5) < 0.3 else 'high',
        'content_quality': 'high' if data.get('media_richness', 0.5) > 0.7 else 'medium'
    }
    return factors

def generate_engagement_recommendations(
    score: float, 
    factors: Dict, 
    sport: str
) -> List[str]:
    """Generate actionable recommendations based on engagement analysis"""
    recommendations = []
    
    if score < 0.3:
        recommendations.append("Critical: Immediate action needed to boost engagement")
        recommendations.append("Consider launching a viral campaign or contest")
    elif score < 0.5:
        recommendations.append("Engagement below average - increase content frequency")
        recommendations.append("Experiment with different content formats")
    
    if factors['timing'] == 'suboptimal':
        recommendations.append("Adjust posting schedule to peak hours (6-8 PM)")
    
    if factors['sentiment'] != 'positive':
        recommendations.append("Focus on positive, uplifting content")
    
    if factors['competition'] == 'high':
        recommendations.append("Differentiate content from competitors")
    
    # Sport-specific recommendations
    sport_recs = {
        'cricket': "Leverage match highlights and player interviews",
        'football': "Create tactical analysis content",
        'basketball': "Share behind-the-scenes training footage",
        'tennis': "Focus on player journey stories"
    }
    
    if sport in sport_recs:
        recommendations.append(sport_recs[sport])
    
    return recommendations[:5]  # Return top 5 recommendations