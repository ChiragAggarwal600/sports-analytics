#!/usr/bin/env python3
"""
Train all ML models for the PR Analytics system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
from pathlib import Path
import joblib
import torch
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error

from data.data_loader import KaggleDataLoader
from data.preprocessor import DataPreprocessor
from models.sentiment_model import SentimentAnalyzer
from models.engagement_model import EngagementPredictor
from models.rl_module import RLPROptimizer
from models.cross_sport_normalizer import CrossSportNormalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_sentiment_model(data_path: str = "data/raw"):
    """Train sentiment analysis model"""
    logger.info("Training sentiment model...")
    
    # Load data
    loader = KaggleDataLoader(data_path)
    sentiment_data = loader.load_sentiment_data()
    
    # Preprocess
    preprocessor = DataPreprocessor()
    sentiment_data = preprocessor.preprocess_sentiment_data(sentiment_data)
    
    # Prepare training data
    texts = sentiment_data['cleaned_text'].tolist()
    
    # Convert sentiment labels to numeric
    label_map = {'positive': 2, 'neutral': 1, 'negative': 0}
    labels = sentiment_data['sentiment'].map(label_map).tolist()
    
    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )
    
    # Initialize and train model
    model = SentimentAnalyzer()
    
    # Fine-tune on sport-specific data
    train_data = list(zip(train_texts, train_labels))
    model.fine_tune(train_data, epochs=3)
    
    # Evaluate
    val_predictions = model.predict(val_texts)
    val_pred_labels = [label_map[p['overall']] for p in val_predictions]
    
    accuracy = accuracy_score(val_labels, val_pred_labels)
    logger.info(f"Sentiment model validation accuracy: {accuracy:.4f}")
    
    # Save model
    model_dir = Path("models/saved")
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_dir / "sentiment_model"))
    
    logger.info("Sentiment model saved successfully")
    return model

def train_engagement_model(data_path: str = "data/raw"):
    """Train engagement prediction model"""
    logger.info("Training engagement model...")
    
    # Load data
    loader = KaggleDataLoader(data_path)
    combined_data = loader.get_combined_dataset()
    
    # Prepare features
    normalizer = CrossSportNormalizer()
    preprocessor = DataPreprocessor()
    
    features_list = []
    targets = []
    
    for sport in ['cricket', 'football', 'basketball', 'tennis']:
        sport_data = combined_data[combined_data['match_type'] == sport]
        
        for _, row in sport_data.iterrows():
            try:
                # Normalize features
                normalized = normalizer.normalize(row.to_dict(), sport)
                features_list.append(normalized)
                targets.append(row['engagement'])
            except Exception as e:
                logger.warning(f"Failed to process row: {e}")
                continue
    
    X = np.array(features_list)
    y = np.array(targets)
    
    # Train model
    model = EngagementPredictor(model_type="xgboost")
    metrics = model.train(X, y, validation_split=0.2)
    
    logger.info(f"Engagement model metrics: {metrics}")
    
    # Save model
    model_dir = Path("models/saved")
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_dir / "engagement_model.pkl"))
    
    logger.info("Engagement model saved successfully")
    return model

def train_rl_model(episodes: int = 100):
    """Train reinforcement learning model for PR strategy"""
    logger.info("Training RL model...")
    
    # Initialize RL optimizer
    model = RLPROptimizer()
    
    # Train
    rewards_history = model.train(episodes=episodes)
    
    # Log training progress
    avg_reward = np.mean(rewards_history[-10:])
    logger.info(f"RL model final average reward: {avg_reward:.4f}")
    
    # Save model
    model_dir = Path("models/saved")
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_dir / "rl_model.pt"))
    
    logger.info("RL model saved successfully")
    return model

def main():
    parser = argparse.ArgumentParser(description="Train ML models for PR Analytics")
    parser.add_argument("--data-path", type=str, default="data/raw",
                       help="Path to raw data directory")
    parser.add_argument("--model", type=str, default="all",
                       choices=["all", "sentiment", "engagement", "rl"],
                       help="Which model to train")
    parser.add_argument("--episodes", type=int, default=100,
                       help="Number of episodes for RL training")
    
    args = parser.parse_args()
    
    if args.model in ["all", "sentiment"]:
        train_sentiment_model(args.data_path)
    
    if args.model in ["all", "engagement"]:
        train_engagement_model(args.data_path)
    
    if args.model in ["all", "rl"]:
        train_rl_model(args.episodes)
    
    logger.info("Training completed!")

if __name__ == "__main__":
    main()