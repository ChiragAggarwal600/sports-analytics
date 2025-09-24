import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EngagementPredictor:
    """Predicts fan engagement using ensemble methods"""
    
    def __init__(self, model_type: str = "xgboost"):
        self.model_type = model_type
        self.scaler = StandardScaler()
        
        if model_type == "xgboost":
            self.model = XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
        self.feature_importance = {}
        self.is_trained = False
        
    def train(self, X: np.ndarray, y: np.ndarray, 
              validation_split: float = 0.2) -> Dict:
        """
        Train engagement prediction model
        """
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_pred = self.model.predict(X_train_scaled)
        val_pred = self.model.predict(X_val_scaled)
        
        metrics = {
            'train_mae': mean_absolute_error(y_train, train_pred),
            'val_mae': mean_absolute_error(y_val, val_pred),
            'train_r2': r2_score(y_train, train_pred),
            'val_r2': r2_score(y_val, val_pred)
        }
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = dict(enumerate(self.model.feature_importances_))
        
        self.is_trained = True
        logger.info(f"Model trained with metrics: {metrics}")
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict engagement levels
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
            
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        # Clip predictions to valid range [0, 1]
        return np.clip(predictions, 0, 1)
    
    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict with confidence intervals
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
            
        X_scaled = self.scaler.transform(X)
        
        if self.model_type == "random_forest":
            # Use tree predictions for confidence
            tree_predictions = np.array([
                tree.predict(X_scaled) for tree in self.model.estimators_
            ])
            
            mean_pred = np.mean(tree_predictions, axis=0)
            std_pred = np.std(tree_predictions, axis=0)
            
            return mean_pred, std_pred * 1.96  # 95% confidence
        else:
            # For XGBoost, use simple prediction
            predictions = self.model.predict(X_scaled)
            # Estimate confidence based on prediction value
            confidence = np.abs(predictions - 0.5) * 2  # Higher confidence at extremes
            
            return predictions, confidence
    
    def get_feature_importance(self) -> Dict[int, float]:
        """Get feature importance scores"""
        return self.feature_importance
    
    def save_model(self, path: str):
        """Save trained model"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_importance': self.feature_importance,
            'model_type': self.model_type,
            'is_trained': self.is_trained
        }, path)
        
    def load_model(self, path: str):
        """Load trained model"""
        saved_data = joblib.load(path)
        self.model = saved_data['model']
        self.scaler = saved_data['scaler']
        self.feature_importance = saved_data['feature_importance']
        self.model_type = saved_data['model_type']
        self.is_trained = saved_data['is_trained']

class EngagementFeatureExtractor:
    """Extract engagement-relevant features from raw data"""
    
    @staticmethod
    def extract_features(data: Dict) -> np.ndarray:
        """
        Extract engagement prediction features
        """
        features = []
        
        # Temporal features
        features.append(data.get('hour_of_day', 12) / 24)
        features.append(data.get('day_of_week', 3) / 7)
        features.append(data.get('is_weekend', 0))
        
        # Historical engagement
        features.append(data.get('prev_engagement_rate', 0.5))
        features.append(data.get('avg_engagement_7d', 0.5))
        features.append(data.get('trend_engagement', 0))
        
        # Content features
        features.append(data.get('content_type_score', 0.5))
        features.append(data.get('media_richness', 0.5))
        features.append(data.get('hashtag_count', 0) / 10)
        
        # Sentiment features
        features.append(data.get('current_sentiment', 0.5))
        features.append(data.get('sentiment_volatility', 0.1))
        
        # Competition features
        features.append(data.get('competitor_activity', 0.5))
        features.append(data.get('market_saturation', 0.3))
        
        return np.array(features).reshape(1, -1)