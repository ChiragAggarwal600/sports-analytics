import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from dataclasses import dataclass

@dataclass
class SportFeatures:
    """Standardized features across all sports"""
    timestamp: float
    event_importance: float  # 0-1 scale
    player_performance: float  # normalized score
    team_performance: float
    competition_stage: float  # regular season, playoffs, etc.
    media_coverage: float
    historical_sentiment: float
    fan_engagement_rate: float
    
class CrossSportNormalizer:
    """Normalizes sport-specific data into unified features"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_mappings = {
            'cricket': self._normalize_cricket,
            'football': self._normalize_football,
            'basketball': self._normalize_basketball,
            'tennis': self._normalize_tennis
        }
        
    def normalize(self, data: Dict[str, Any], sport: str) -> np.ndarray:
        """
        Convert sport-specific data to normalized feature vector
        """
        if sport not in self.feature_mappings:
            raise ValueError(f"Sport {sport} not supported")
            
        normalized_features = self.feature_mappings[sport](data)
        return self._create_feature_vector(normalized_features)
    
    def _normalize_cricket(self, data: Dict) -> SportFeatures:
        """Cricket-specific normalization (IPL)"""
        return SportFeatures(
            timestamp=self._normalize_timestamp(data.get('match_date')),
            event_importance=self._get_cricket_importance(data),
            player_performance=self._normalize_cricket_performance(data),
            team_performance=data.get('team_win_rate', 0.5),
            competition_stage=self._get_competition_stage(data.get('match_type')),
            media_coverage=data.get('viewership_millions', 0) / 100,
            historical_sentiment=data.get('prev_sentiment', 0.5),
            fan_engagement_rate=data.get('social_mentions', 0) / 10000
        )
    
    def _normalize_football(self, data: Dict) -> SportFeatures:
        """Football-specific normalization"""
        return SportFeatures(
            timestamp=self._normalize_timestamp(data.get('match_date')),
            event_importance=self._get_football_importance(data),
            player_performance=self._normalize_football_performance(data),
            team_performance=data.get('team_form', 0.5),
            competition_stage=self._get_competition_stage(data.get('competition')),
            media_coverage=data.get('tv_audience', 0) / 100,
            historical_sentiment=data.get('prev_sentiment', 0.5),
            fan_engagement_rate=data.get('social_engagement', 0) / 10000
        )
    
    def _normalize_basketball(self, data: Dict) -> SportFeatures:
        """Basketball-specific normalization (NBA)"""
        return SportFeatures(
            timestamp=self._normalize_timestamp(data.get('game_date')),
            event_importance=self._get_basketball_importance(data),
            player_performance=self._normalize_basketball_performance(data),
            team_performance=data.get('win_percentage', 0.5),
            competition_stage=self._get_competition_stage(data.get('season_phase')),
            media_coverage=data.get('national_tv', 0),
            historical_sentiment=data.get('prev_sentiment', 0.5),
            fan_engagement_rate=data.get('arena_attendance', 0) / 20000
        )
    
    def _normalize_tennis(self, data: Dict) -> SportFeatures:
        """Tennis-specific normalization (ATP)"""
        return SportFeatures(
            timestamp=self._normalize_timestamp(data.get('match_date')),
            event_importance=self._get_tennis_importance(data),
            player_performance=self._normalize_tennis_performance(data),
            team_performance=0.5,  # Not applicable for tennis
            competition_stage=self._get_tennis_stage(data.get('round')),
            media_coverage=data.get('tournament_tier', 1) / 5,
            historical_sentiment=data.get('prev_sentiment', 0.5),
            fan_engagement_rate=data.get('match_views', 0) / 1000000
        )
    
    def _normalize_timestamp(self, timestamp: Any) -> float:
        """Convert timestamp to normalized float"""
        if isinstance(timestamp, str):
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp)
            return dt.timestamp() / 1e10
        return float(timestamp) / 1e10
    
    def _get_cricket_importance(self, data: Dict) -> float:
        """Calculate cricket match importance"""
        importance = 0.3  # base
        if data.get('is_final'): importance += 0.4
        if data.get('is_playoff'): importance += 0.2
        if data.get('rivalry_match'): importance += 0.1
        return min(importance, 1.0)
    
    def _get_football_importance(self, data: Dict) -> float:
        """Calculate football match importance"""
        importance = 0.3
        if 'champions' in str(data.get('competition', '')).lower(): importance += 0.3
        if data.get('is_derby'): importance += 0.2
        if data.get('title_decider'): importance += 0.2
        return min(importance, 1.0)
    
    def _get_basketball_importance(self, data: Dict) -> float:
        """Calculate basketball game importance"""
        importance = 0.3
        if data.get('is_playoffs'): importance += 0.3
        if data.get('is_finals'): importance += 0.2
        if data.get('rivalry_game'): importance += 0.2
        return min(importance, 1.0)
    
    def _get_tennis_importance(self, data: Dict) -> float:
        """Calculate tennis match importance"""
        importance = 0.2
        tournament_tier = data.get('tournament_tier', 1)
        importance += tournament_tier * 0.15
        if data.get('is_final'): importance += 0.3
        if data.get('top10_matchup'): importance += 0.2
        return min(importance, 1.0)
    
    def _normalize_cricket_performance(self, data: Dict) -> float:
        """Normalize cricket player/team performance"""
        strike_rate = data.get('strike_rate', 100) / 200
        average = data.get('batting_average', 25) / 50
        return (strike_rate + average) / 2
    
    def _normalize_football_performance(self, data: Dict) -> float:
        """Normalize football player/team performance"""
        goals = data.get('goals_scored', 0) / 5
        possession = data.get('possession', 50) / 100
        return (goals + possession) / 2
    
    def _normalize_basketball_performance(self, data: Dict) -> float:
        """Normalize basketball player/team performance"""
        points = data.get('points_per_game', 20) / 40
        efficiency = data.get('player_efficiency', 15) / 30
        return (points + efficiency) / 2
    
    def _normalize_tennis_performance(self, data: Dict) -> float:
        """Normalize tennis player performance"""
        ranking = 1 - (data.get('ranking', 50) / 100)
        win_rate = data.get('win_rate', 0.5)
        return (ranking + win_rate) / 2
    
    def _get_competition_stage(self, stage: str) -> float:
        """Convert competition stage to normalized value"""
        stages = {
            'regular': 0.3,
            'playoff': 0.6,
            'semifinal': 0.8,
            'final': 1.0
        }
        return stages.get(str(stage).lower(), 0.3)
    
    def _get_tennis_stage(self, round_name: str) -> float:
        """Convert tennis round to normalized value"""
        rounds = {
            'r128': 0.1, 'r64': 0.2, 'r32': 0.3,
            'r16': 0.4, 'qf': 0.6, 'sf': 0.8, 'f': 1.0
        }
        return rounds.get(str(round_name).lower(), 0.1)
    
    def _create_feature_vector(self, features: SportFeatures) -> np.ndarray:
        """Convert SportFeatures to numpy array"""
        return np.array([
            features.timestamp,
            features.event_importance,
            features.player_performance,
            features.team_performance,
            features.competition_stage,
            features.media_coverage,
            features.historical_sentiment,
            features.fan_engagement_rate
        ])