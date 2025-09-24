import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Preprocess data for ML models"""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = {}
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # Remove mentions and hashtags (but keep the text)
        text = re.sub(r'@\w+|#(\w+)', r'\1', text)
        
        # Remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def preprocess_sentiment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess data for sentiment analysis"""
        # Clean text
        if 'text' in df.columns:
            df['cleaned_text'] = df['text'].apply(self.preprocess_text)
        
        # Extract features
        df['text_length'] = df['cleaned_text'].str.len()
        df['word_count'] = df['cleaned_text'].str.split().str.len()
        
        # Time features
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['hour'] = df['created_at'].dt.hour
            df['day_of_week'] = df['created_at'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        return df
    
    def preprocess_engagement_data(self, df: pd.DataFrame, sport: str) -> np.ndarray:
        """Preprocess data for engagement prediction"""
        feature_cols = []
        
        # Common features across sports
        common_features = ['sentiment', 'hour_of_day', 'day_of_week', 
                          'is_weekend', 'prev_engagement_rate']
        
        # Sport-specific features
        sport_features = {
            'cricket': ['match_type', 'venue', 'toss_decision', 'win_margin'],
            'football': ['competition', 'home_goals', 'away_goals', 'possession'],
            'basketball': ['home_pts', 'away_pts', 'season_phase', 'arena_attendance'],
            'tennis': ['tournament', 'surface', 'round', 'match_duration']
        }
        
        # Select features based on sport
        if sport in sport_features:
            feature_cols = common_features + sport_features[sport]
        else:
            feature_cols = common_features
        
        # Handle missing columns
        for col in feature_cols:
            if col not in df.columns:
                if col in ['hour_of_day', 'day_of_week']:
                    df[col] = 0
                elif col == 'is_weekend':
                    df[col] = 0
                elif col == 'prev_engagement_rate':
                    df[col] = 0.5
                else:
                    df[col] = 0
        
        # Encode categorical variables
        categorical_cols = df[feature_cols].select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                df[col] = self.encoders[col].fit_transform(df[col].astype(str))
            else:
                df[col] = self.encoders[col].transform(df[col].astype(str))
        
        # Scale numerical features
        if 'engagement' not in self.scalers:
            self.scalers['engagement'] = StandardScaler()
            X = self.scalers['engagement'].fit_transform(df[feature_cols])
        else:
            X = self.scalers['engagement'].transform(df[feature_cols])
        
        return X
    
    def create_time_series_features(self, df: pd.DataFrame, 
                                   target_col: str,
                                   lookback_days: int = 7) -> pd.DataFrame:
        """Create time series features for prediction"""
        df = df.sort_values('date')
        
        # Lag features
        for i in range(1, lookback_days + 1):
            df[f'{target_col}_lag_{i}'] = df[target_col].shift(i)
        
        # Rolling statistics
        df[f'{target_col}_rolling_mean_7d'] = df[target_col].rolling(window=7).mean()
        df[f'{target_col}_rolling_std_7d'] = df[target_col].rolling(window=7).std()
        df[f'{target_col}_rolling_max_7d'] = df[target_col].rolling(window=7).max()
        df[f'{target_col}_rolling_min_7d'] = df[target_col].rolling(window=7).min()
        
        # Trend features
        df[f'{target_col}_trend'] = df[f'{target_col}_rolling_mean_7d'].diff()
        
        # Drop NaN rows created by lag and rolling features
        df = df.dropna()
        
        return df
    
    def prepare_training_data(self, df: pd.DataFrame, 
                            target_col: str,
                            feature_cols: List[str],
                            test_size: float = 0.2) -> Tuple[np.ndarray, np.ndarray, 
                                                            np.ndarray, np.ndarray]:
        """Prepare data for model training"""
        from sklearn.model_selection import train_test_split
        
        # Handle missing values
        df = df.dropna(subset=[target_col])
        
        # Select features
        X = df[feature_cols].values
        y = df[target_col].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        return X_train, X_test, y_train, y_test
    
    def augment_sentiment_data(self, texts: List[str], 
                              labels: List[str]) -> Tuple[List[str], List[str]]:
        """Augment sentiment training data"""
        augmented_texts = []
        augmented_labels = []
        
        # Simple augmentation techniques
        for text, label in zip(texts, labels):
            # Original
            augmented_texts.append(text)
            augmented_labels.append(label)
            
            # Uppercase
            augmented_texts.append(text.upper())
            augmented_labels.append(label)
            
            # Add exclamation
            if label == 'positive':
                augmented_texts.append(text + '!')
                augmented_labels.append(label)
            
            # Add question mark for negative
            if label == 'negative':
                augmented_texts.append(text + '?')
                augmented_labels.append(label)
        
        return augmented_texts, augmented_labels