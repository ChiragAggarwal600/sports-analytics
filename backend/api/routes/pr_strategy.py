from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np

from api.main import get_models

router = APIRouter()

class PRStrategyRequest(BaseModel):
    sport: str = Field(..., description="Sport type")
    current_sentiment: float = Field(..., ge=0, le=1)
    current_engagement: float = Field(..., ge=0, le=1)
    budget_remaining: float = Field(1.0, ge=0, le=1)
    crisis_level: float = Field(0, ge=0, le=1)
    additional_context: Optional[Dict] = Field(default_factory=dict)

class PRStrategyResponse(BaseModel):
    recommended_action: Dict
    risk_assessment: Dict
    timing_recommendation: Dict
    expected_outcomes: Dict
    alternative_strategies: List[Dict]
    timestamp: datetime

@router.post("/recommend", response_model=PRStrategyResponse)
async def recommend_pr_strategy(request: PRStrategyRequest):
    """
    Get AI-powered PR strategy recommendation
    """
    try:
        models = get_models()
        rl_optimizer = models.get('rl_optimizer')
        
        if not rl_optimizer:
            raise HTTPException(status_code=503, detail="RL model not loaded")
        
        # Prepare state for RL model
        state = {
            'sentiment': request.current_sentiment,
            'engagement': request.current_engagement,
            'budget_remaining': request.budget_remaining,
            'crisis_level': request.crisis_level,
            'competitor_activity': request.additional_context.get('competitor_activity', 0.5),
            'time_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'trending_topics': request.additional_context.get('trending_topics', 0),
            'brand_mentions': request.additional_context.get('brand_mentions', 0),
            'opportunity_score': calculate_opportunity_score(request)
        }
        
        # Get RL recommendation
        recommendation = rl_optimizer.recommend_action(state)
        
        # Assess risks
        risk_assessment = assess_pr_risks(request, recommendation)
        
        # Timing recommendation
        timing = recommend_timing(request, recommendation)
        
        # Expected outcomes
        outcomes = predict_outcomes(request, recommendation)
        
        return PRStrategyResponse(
            recommended_action=recommendation,
            risk_assessment=risk_assessment,
            timing_recommendation=timing,
            expected_outcomes=outcomes,
            alternative_strategies=recommendation.get('alternative_actions', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate")
async def simulate_pr_campaign(
    strategy: str,
    duration_days: int = 7,
    sport: str = "general",
    initial_sentiment: float = 0.5,
    initial_engagement: float = 0.5
):
    """
    Simulate PR campaign outcomes
    """
    try:
        models = get_models()
        
        # Simulate campaign over time
        simulation_results = []
        current_sentiment = initial_sentiment
        current_engagement = initial_engagement
        
        for day in range(duration_days):
            # Simulate daily changes based on strategy
            if strategy == "aggressive":
                sentiment_change = np.random.uniform(0.05, 0.15)
                engagement_change = np.random.uniform(0.1, 0.2)
                cost = 0.15
            elif strategy == "moderate":
                sentiment_change = np.random.uniform(0.02, 0.08)
                engagement_change = np.random.uniform(0.05, 0.12)
                cost = 0.08
            else:  # conservative
                sentiment_change = np.random.uniform(0.01, 0.04)
                engagement_change = np.random.uniform(0.02, 0.06)
                cost = 0.03
            
            # Apply changes with some randomness
            current_sentiment = min(1.0, current_sentiment + sentiment_change * np.random.uniform(0.8, 1.2))
            current_engagement = min(1.0, current_engagement + engagement_change * np.random.uniform(0.7, 1.1))
            
            # Natural decay
            current_engagement *= 0.95
            
            simulation_results.append({
                'day': day + 1,
                'sentiment': current_sentiment,
                'engagement': current_engagement,
                'cost_accumulated': cost * (day + 1),
                'roi': (current_sentiment + current_engagement - 1) / (cost * (day + 1)) if cost > 0 else 0
            })
        
        return {
            'strategy': strategy,
            'duration_days': duration_days,
            'sport': sport,
            'simulation': simulation_results,
            'summary': {
                'final_sentiment': current_sentiment,
                'final_engagement': current_engagement,
                'total_cost': cost * duration_days,
                'sentiment_improvement': current_sentiment - initial_sentiment,
                'engagement_improvement': current_engagement - initial_engagement
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_opportunity_score(request: PRStrategyRequest) -> float:
    """Calculate opportunity score based on current conditions"""
    score = 0.5
    
    # Low sentiment but high engagement = opportunity
    if request.current_sentiment < 0.4 and request.current_engagement > 0.6:
        score += 0.3
    
    # Crisis can be opportunity if handled well
    if request.crisis_level > 0.5:
        score += 0.2
    
    # Budget availability
    score += request.budget_remaining * 0.2
    
    return min(score, 1.0)

def assess_pr_risks(request: PRStrategyRequest, recommendation: Dict) -> Dict:
    """Assess risks associated with PR strategy"""
    risks = {
        'backlash_risk': 0.1,
        'oversaturation_risk': 0.1,
        'budget_risk': 0.1,
        'timing_risk': 0.1
    }
    
    # High crisis + aggressive action = higher backlash risk
    if request.crisis_level > 0.5 and recommendation['action'] == 'campaign':
        risks['backlash_risk'] += 0.4
    
    # High sentiment + more PR = oversaturation
    if request.current_sentiment > 0.8 and recommendation['action'] != 'wait':
        risks['oversaturation_risk'] += 0.3
    
    # Low budget + expensive action
    if request.budget_remaining < 0.3 and recommendation['action'] in ['campaign', 'influencer']:
        risks['budget_risk'] += 0.5
    
    # Calculate overall risk
    overall_risk = np.mean(list(risks.values()))
    
    return {
        'individual_risks': risks,
        'overall_risk': overall_risk,
        'risk_level': 'high' if overall_risk > 0.5 else 'medium' if overall_risk > 0.3 else 'low'
    }

def recommend_timing(request: PRStrategyRequest, recommendation: Dict) -> Dict:
    """Recommend optimal timing for PR action"""
    current_hour = datetime.now().hour
    current_day = datetime.now().weekday()
    
    # Optimal hours for different actions
    optimal_hours = {
        'social_post': [9, 12, 18, 20],
        'press_release': [10, 14],
        'influencer': [15, 16, 17, 18],
        'campaign': [9, 10, 11]
    }
    
    action = recommendation.get('action', 'wait')
    
    if action == 'wait':
        return {
            'immediate': False,
            'recommended_time': 'No action needed',
            'reason': 'Current conditions do not warrant PR activity'
        }
    
    best_hours = optimal_hours.get(action, [12])
    
    # Find next optimal time
    next_optimal = None
    for hour in best_hours:
        if hour > current_hour:
            next_optimal = hour
            break
    
    if not next_optimal:
        next_optimal = best_hours[0]  # Next day
        days_until = 1
    else:
        days_until = 0
    
    return {
        'immediate': current_hour in best_hours,
        'recommended_time': f"{next_optimal:02d}:00",
        'days_until': days_until,
        'reason': f"Optimal engagement window for {action}"
    }

def predict_outcomes(request: PRStrategyRequest, recommendation: Dict) -> Dict:
    """Predict expected outcomes of PR strategy"""
    action = recommendation.get('action', 'wait')
    
    # Base predictions
    outcomes = {
        'sentiment_change': 0,
        'engagement_change': 0,
        'reach_multiplier': 1.0,
        'cost_efficiency': 1.0
    }
    
    # Action-specific predictions
    if action == 'social_post':
        outcomes['sentiment_change'] = 0.05
        outcomes['engagement_change'] = 0.10
        outcomes['reach_multiplier'] = 1.5
        outcomes['cost_efficiency'] = 0.9
    elif action == 'press_release':
        outcomes['sentiment_change'] = 0.08
        outcomes['engagement_change'] = 0.06
        outcomes['reach_multiplier'] = 2.0
        outcomes['cost_efficiency'] = 0.7
    elif action == 'influencer':
        outcomes['sentiment_change'] = 0.12
        outcomes['engagement_change'] = 0.15
        outcomes['reach_multiplier'] = 3.0
        outcomes['cost_efficiency'] = 0.6
    elif action == 'campaign':
        outcomes['sentiment_change'] = 0.20
        outcomes['engagement_change'] = 0.25
        outcomes['reach_multiplier'] = 5.0
        outcomes['cost_efficiency'] = 0.4
    
    # Adjust based on current conditions
    if request.crisis_level > 0.5:
        outcomes['sentiment_change'] *= 0.5  # Reduced effectiveness during crisis
    
    if request.current_engagement > 0.7:
        outcomes['reach_multiplier'] *= 1.5  # Leverage high engagement
    
    return outcomes