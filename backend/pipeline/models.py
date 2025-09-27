"""
Ensemble Model Manager
Handles XGBoost, BiLSTM, BERT, and GCN models for sentiment and engagement prediction
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass
import aioredis
import joblib
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
from collections import defaultdict, deque

from config.settings import settings

        # settings imported above
logger = logging.getLogger(__name__)

@dataclass
class ModelPrediction:
    """Container for model predictions"""
    model_name: str
    prediction: Any
    confidence: float
    features_used: List[str]
    processing_time: float
    timestamp: datetime

@dataclass
class EnsemblePrediction:
    """Container for ensemble predictions"""
    final_prediction: Any
    individual_predictions: List[ModelPrediction]
    ensemble_confidence: float
    model_weights: Dict[str, float]
    timestamp: datetime

class BertSentimentModel(nn.Module):
    """BERT-based sentiment analysis model"""
    
    def __init__(self, model_name='bert-base-uncased', num_classes=3):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_classes)
        
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        output = self.dropout(pooled_output)
        return self.classifier(output)

class BiLSTMModel(nn.Module):
    """Bidirectional LSTM for sequence modeling"""
    
    def __init__(self, vocab_size, embedding_dim=128, hidden_dim=64, num_layers=2, num_classes=3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers, 
                           batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)
        
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, _) = self.lstm(embedded)
        # Use the last hidden state
        output = self.dropout(lstm_out[:, -1, :])
        return self.fc(output)

class GCNModel(nn.Module):
    """Graph Convolutional Network for network-based features"""
    
    def __init__(self, input_dim, hidden_dim=64, num_classes=3):
        super().__init__()
        self.gc1 = nn.Linear(input_dim, hidden_dim)
        self.gc2 = nn.Linear(hidden_dim, hidden_dim)
        self.classifier = nn.Linear(hidden_dim, num_classes)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()
        
    def forward(self, x, adj_matrix):
        # Simple GCN implementation
        x = torch.mm(adj_matrix, x)
        x = self.relu(self.gc1(x))
        x = self.dropout(x)
        
        x = torch.mm(adj_matrix, x)
        x = self.relu(self.gc2(x))
        x = self.dropout(x)
        
        return self.classifier(x)

class XGBoostWrapper:
    """Wrapper for XGBoost model with async capabilities"""
    
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.is_trained = False
        
    async def initialize(self, model_path: str = None):
        """Initialize XGBoost model"""
        try:
            if model_path and os.path.exists(model_path):
                self.model = joblib.load(model_path)
                self.is_trained = True
                logger.info(f"Loaded XGBoost model from {model_path}")
            else:
                # Initialize with default parameters
                self.model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                )
                logger.info("Initialized new XGBoost model")
        except Exception as e:
            logger.error(f"Failed to initialize XGBoost model: {e}")
            raise
    
    async def predict(self, features: Dict[str, float]) -> Tuple[Any, float]:
        """Make prediction with confidence score"""
        try:
            if not self.is_trained:
                return 0, 0.0
            
            # Convert features to DataFrame
            feature_df = pd.DataFrame([features])
            
            # Ensure feature order matches training
            if self.feature_names:
                feature_df = feature_df.reindex(columns=self.feature_names, fill_value=0)
            
            # Make prediction
            prediction = self.model.predict(feature_df)[0]
            
            # Get prediction probabilities for confidence
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(feature_df)[0]
                confidence = float(np.max(probabilities))
            else:
                confidence = 0.7  # Default confidence
            
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"XGBoost prediction failed: {e}")
            return 0, 0.0

class DeepModelManager:
    """Manager for PyTorch-based deep learning models"""
    
    def __init__(self):
        self.bert_model = None
        self.bilstm_model = None
        self.gcn_model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    async def initialize(self):
        """Initialize deep learning models"""
        try:
            # Initialize BERT model
            self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
            self.bert_model = BertSentimentModel()
            self.bert_model.to(self.device)
            self.bert_model.eval()
            
            # Initialize BiLSTM model
            vocab_size = 10000  # This would be set based on actual vocabulary
            self.bilstm_model = BiLSTMModel(vocab_size)
            self.bilstm_model.to(self.device)
            self.bilstm_model.eval()
            
            # Initialize GCN model
            input_dim = 50  # This would be set based on network features
            self.gcn_model = GCNModel(input_dim)
            self.gcn_model.to(self.device)
            self.gcn_model.eval()
            
            logger.info("Deep learning models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize deep models: {e}")
            raise
    
    async def predict_bert_sentiment(self, text: str) -> Tuple[int, float]:
        """Predict sentiment using BERT model"""
        try:
            if not self.bert_model or not self.tokenizer:
                return 1, 0.5  # Neutral with low confidence
            
            # Tokenize text
            inputs = self.tokenizer(
                text,
                add_special_tokens=True,
                max_length=512,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            
            # Make prediction
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs, dim=-1)
                predicted_class = torch.argmax(predictions, dim=-1).item()
                confidence = torch.max(predictions).item()
            
            return predicted_class, confidence
            
        except Exception as e:
            logger.error(f"BERT prediction failed: {e}")
            return 1, 0.5
    
    async def predict_bilstm(self, sequence_features: List[int]) -> Tuple[int, float]:
        """Predict using BiLSTM model"""
        try:
            if not self.bilstm_model:
                return 1, 0.5
            
            # Convert to tensor
            input_tensor = torch.tensor([sequence_features], dtype=torch.long).to(self.device)
            
            # Make prediction
            with torch.no_grad():
                outputs = self.bilstm_model(input_tensor)
                predictions = torch.nn.functional.softmax(outputs, dim=-1)
                predicted_class = torch.argmax(predictions, dim=-1).item()
                confidence = torch.max(predictions).item()
            
            return predicted_class, confidence
            
        except Exception as e:
            logger.error(f"BiLSTM prediction failed: {e}")
            return 1, 0.5
    
    async def predict_gcn(self, node_features: np.ndarray, adj_matrix: np.ndarray) -> Tuple[int, float]:
        """Predict using GCN model"""
        try:
            if not self.gcn_model:
                return 1, 0.5
            
            # Convert to tensors
            node_tensor = torch.tensor(node_features, dtype=torch.float32).to(self.device)
            adj_tensor = torch.tensor(adj_matrix, dtype=torch.float32).to(self.device)
            
            # Make prediction
            with torch.no_grad():
                outputs = self.gcn_model(node_tensor, adj_tensor)
                predictions = torch.nn.functional.softmax(outputs, dim=-1)
                
                # Take mean prediction across nodes
                mean_prediction = torch.mean(predictions, dim=0)
                predicted_class = torch.argmax(mean_prediction).item()
                confidence = torch.max(mean_prediction).item()
            
            return predicted_class, confidence
            
        except Exception as e:
            logger.error(f"GCN prediction failed: {e}")
            return 1, 0.5

class EnsembleModelManager:
    """Main ensemble model manager coordinating all models"""
    
    def __init__(self):
        self.xgboost_model = XGBoostWrapper()
        self.deep_model_manager = DeepModelManager()
        self.redis_client = None
        
        # Model weights for ensemble (learned over time)
        self.model_weights = {
            'xgboost': 0.3,
            'bert': 0.25,
            'bilstm': 0.2,
            'gcn': 0.25
        }
        
        # Performance tracking
        self.model_performance = defaultdict(lambda: {
            'predictions_made': 0,
            'avg_confidence': 0.0,
            'processing_time_avg': 0.0,
            'last_updated': datetime.now()
        })
        
        self.prediction_cache = {}
        self.lightweight_mode = False
        
    async def initialize(self):
        """Initialize all models"""
        try:
            # Initialize Redis client
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize models
            await self.xgboost_model.initialize(settings.ENGAGEMENT_MODEL_PATH)
            await self.deep_model_manager.initialize()
            
            # Load model weights from storage if available
            await self._load_model_weights()
            
            logger.info("Ensemble model manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ensemble model manager: {e}")
            raise
    
    async def run_inference(self) -> Dict[str, Any]:
        """Run inference on all available features"""
        inference_start = datetime.now()
        
        try:
            # Get engineered features from Redis
            feature_data = await self._get_latest_features()
            
            if not feature_data:
                return {
                    'predictions_made': 0,
                    'processing_time_seconds': 0,
                    'timestamp': inference_start.isoformat()
                }
            
            # Run ensemble prediction
            predictions = []
            
            for feature_set in feature_data:
                try:
                    ensemble_prediction = await self._run_ensemble_prediction(feature_set)
                    if ensemble_prediction:
                        predictions.append(ensemble_prediction)
                except Exception as e:
                    logger.error(f"Failed to run prediction on feature set: {e}")
                    continue
            
            # Store predictions
            if predictions:
                await self._store_predictions(predictions)
            
            # Update model performance metrics
            await self._update_performance_metrics(predictions)
            
            processing_time = (datetime.now() - inference_start).total_seconds()
            
            return {
                'predictions_made': len(predictions),
                'processing_time_seconds': processing_time,
                'avg_ensemble_confidence': np.mean([p.ensemble_confidence for p in predictions]) if predictions else 0,
                'models_used': list(self.model_weights.keys()),
                'lightweight_mode': self.lightweight_mode,
                'timestamp': inference_start.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            raise
    
    async def _get_latest_features(self) -> List[Dict[str, Any]]:
        """Get latest engineered features from Redis"""
        try:
            # Read from features stream
            entries = await self.redis_client.xread(
                {'stream:features': '$'},
                count=50,
                block=1000
            )
            
            feature_sets = []
            
            for stream_entries in entries:
                for entry_id, entry_data in stream_entries[1]:
                    try:
                        # Parse feature data
                        features = {}
                        for key, value in entry_data.items():
                            if key == 'features':
                                features = json.loads(value)
                            elif key not in ['timestamp', 'feature_count']:
                                try:
                                    features[key] = float(value)
                                except (ValueError, TypeError):
                                    features[key] = value
                        
                        if features:
                            feature_sets.append(features)
                            
                    except Exception as e:
                        logger.error(f"Error parsing feature entry: {e}")
                        continue
            
            return feature_sets
            
        except Exception as e:
            logger.error(f"Error getting latest features: {e}")
            return []
    
    async def _run_ensemble_prediction(self, features: Dict[str, Any]) -> Optional[EnsemblePrediction]:
        """Run ensemble prediction on feature set"""
        try:
            individual_predictions = []
            
            # XGBoost prediction
            if not self.lightweight_mode or 'xgboost' in self.model_weights:
                start_time = datetime.now()
                xgb_pred, xgb_conf = await self.xgboost_model.predict(features)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                individual_predictions.append(ModelPrediction(
                    model_name='xgboost',
                    prediction=xgb_pred,
                    confidence=xgb_conf,
                    features_used=list(features.keys()),
                    processing_time=processing_time,
                    timestamp=datetime.now()
                ))
            
            # BERT prediction (if text features available)
            text_features = self._extract_text_for_bert(features)
            if text_features and (not self.lightweight_mode or 'bert' in self.model_weights):
                start_time = datetime.now()
                bert_pred, bert_conf = await self.deep_model_manager.predict_bert_sentiment(text_features)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                individual_predictions.append(ModelPrediction(
                    model_name='bert',
                    prediction=bert_pred,
                    confidence=bert_conf,
                    features_used=['text_features'],
                    processing_time=processing_time,
                    timestamp=datetime.now()
                ))
            
            # BiLSTM prediction (if sequence features available)
            sequence_features = self._extract_sequence_features(features)
            if sequence_features and (not self.lightweight_mode or 'bilstm' in self.model_weights):
                start_time = datetime.now()
                lstm_pred, lstm_conf = await self.deep_model_manager.predict_bilstm(sequence_features)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                individual_predictions.append(ModelPrediction(
                    model_name='bilstm',
                    prediction=lstm_pred,
                    confidence=lstm_conf,
                    features_used=['sequence_features'],
                    processing_time=processing_time,
                    timestamp=datetime.now()
                ))
            
            # GCN prediction (if network features available)
            network_data = self._extract_network_features(features)
            if network_data and (not self.lightweight_mode or 'gcn' in self.model_weights):
                node_features, adj_matrix = network_data
                start_time = datetime.now()
                gcn_pred, gcn_conf = await self.deep_model_manager.predict_gcn(node_features, adj_matrix)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                individual_predictions.append(ModelPrediction(
                    model_name='gcn',
                    prediction=gcn_pred,
                    confidence=gcn_conf,
                    features_used=['network_features'],
                    processing_time=processing_time,
                    timestamp=datetime.now()
                ))
            
            if not individual_predictions:
                return None
            
            # Ensemble combination
            final_prediction, ensemble_confidence = self._combine_predictions(individual_predictions)
            
            return EnsemblePrediction(
                final_prediction=final_prediction,
                individual_predictions=individual_predictions,
                ensemble_confidence=ensemble_confidence,
                model_weights=self.model_weights.copy(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error running ensemble prediction: {e}")
            return None
    
    def _extract_text_for_bert(self, features: Dict[str, Any]) -> Optional[str]:
        """Extract text content for BERT model"""
        # This would extract actual text from the original data
        # For now, return a placeholder
        return "sample text for sentiment analysis"
    
    def _extract_sequence_features(self, features: Dict[str, Any]) -> Optional[List[int]]:
        """Extract sequence features for BiLSTM"""
        # Convert relevant features to sequence
        temporal_features = [v for k, v in features.items() if 'temporal' in k.lower()]
        if temporal_features:
            # Convert to integer sequence (simplified)
            return [int(abs(f * 100)) % 1000 for f in temporal_features[:20]]
        return None
    
    def _extract_network_features(self, features: Dict[str, Any]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Extract network features for GCN"""
        network_features = [v for k, v in features.items() if 'network' in k.lower()]
        if len(network_features) >= 4:
            # Create simple node features and adjacency matrix
            node_features = np.array([network_features[:4]] * 5)  # 5 nodes
            adj_matrix = np.eye(5) + 0.1 * np.random.rand(5, 5)  # Simple adjacency
            return node_features, adj_matrix
        return None
    
    def _combine_predictions(self, predictions: List[ModelPrediction]) -> Tuple[Any, float]:
        """Combine individual model predictions using ensemble weights"""
        try:
            if not predictions:
                return 0, 0.0
            
            # Weighted voting for classification
            weighted_votes = defaultdict(float)
            total_weight = 0.0
            confidence_sum = 0.0
            
            for pred in predictions:
                model_name = pred.model_name
                weight = self.model_weights.get(model_name, 0.25)
                
                weighted_votes[pred.prediction] += weight * pred.confidence
                total_weight += weight
                confidence_sum += pred.confidence
            
            # Get prediction with highest weighted vote
            if weighted_votes:
                final_prediction = max(weighted_votes.items(), key=lambda x: x[1])[0]
                ensemble_confidence = confidence_sum / len(predictions)
            else:
                final_prediction = predictions[0].prediction
                ensemble_confidence = predictions[0].confidence
            
            return final_prediction, ensemble_confidence
            
        except Exception as e:
            logger.error(f"Error combining predictions: {e}")
            return 0, 0.0
    
    async def _store_predictions(self, predictions: List[EnsemblePrediction]):
        """Store predictions in Redis"""
        try:
            for prediction in predictions:
                # Store individual prediction
                pred_key = f"prediction:{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                
                pred_data = {
                    'final_prediction': prediction.final_prediction,
                    'ensemble_confidence': prediction.ensemble_confidence,
                    'model_weights': json.dumps(prediction.model_weights),
                    'individual_predictions': json.dumps([
                        {
                            'model_name': p.model_name,
                            'prediction': p.prediction,
                            'confidence': p.confidence,
                            'processing_time': p.processing_time
                        }
                        for p in prediction.individual_predictions
                    ]),
                    'timestamp': prediction.timestamp.isoformat()
                }
                
                # Store with TTL
                await self.redis_client.setex(
                    pred_key,
                    timedelta(days=3).total_seconds(),
                    json.dumps(pred_data)
                )
                
                # Also add to predictions stream
                await self.redis_client.xadd(
                    'stream:predictions',
                    pred_data,
                    maxlen=2000
                )
            
            logger.info(f"Stored {len(predictions)} ensemble predictions")
            
        except Exception as e:
            logger.error(f"Error storing predictions: {e}")
    
    async def _update_performance_metrics(self, predictions: List[EnsemblePrediction]):
        """Update model performance metrics"""
        try:
            for prediction in predictions:
                for individual_pred in prediction.individual_predictions:
                    model_name = individual_pred.model_name
                    
                    # Update performance stats
                    stats = self.model_performance[model_name]
                    stats['predictions_made'] += 1
                    
                    # Update average confidence
                    old_conf = stats['avg_confidence']
                    count = stats['predictions_made']
                    stats['avg_confidence'] = (old_conf * (count - 1) + individual_pred.confidence) / count
                    
                    # Update average processing time
                    old_time = stats['processing_time_avg']
                    stats['processing_time_avg'] = (old_time * (count - 1) + individual_pred.processing_time) / count
                    
                    stats['last_updated'] = datetime.now()
        
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def _load_model_weights(self):
        """Load model weights from storage"""
        try:
            weights_data = await self.redis_client.get("model_weights")
            if weights_data:
                stored_weights = json.loads(weights_data)
                self.model_weights.update(stored_weights)
                logger.info(f"Loaded model weights: {self.model_weights}")
        except Exception as e:
            logger.error(f"Error loading model weights: {e}")
    
    async def enable_lightweight_mode(self):
        """Enable lightweight mode for graceful degradation"""
        self.lightweight_mode = True
        # Keep only the most efficient models
        self.model_weights = {
            'xgboost': 0.6,
            'bert': 0.4
        }
        logger.info("Enabled lightweight mode for ensemble models")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for ensemble model manager"""
        try:
            # Check Redis connection
            redis_status = "healthy"
            try:
                await self.redis_client.ping()
            except Exception:
                redis_status = "unhealthy"
            
            # Check model status
            model_status = {
                'xgboost': 'healthy' if self.xgboost_model.is_trained else 'not_trained',
                'bert': 'healthy' if self.deep_model_manager.bert_model else 'not_loaded',
                'bilstm': 'healthy' if self.deep_model_manager.bilstm_model else 'not_loaded',
                'gcn': 'healthy' if self.deep_model_manager.gcn_model else 'not_loaded'
            }
            
            # Overall status
            if redis_status != "healthy":
                overall_status = "critical"
            elif any(status == "not_loaded" for status in model_status.values()):
                overall_status = "degraded"
            else:
                overall_status = "healthy"
            
            return {
                'status': overall_status,
                'components': {
                    'redis': redis_status,
                    'models': model_status
                },
                'performance': dict(self.model_performance),
                'model_weights': self.model_weights,
                'lightweight_mode': self.lightweight_mode,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def stop(self):
        """Stop ensemble model manager"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Ensemble model manager stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping ensemble model manager: {e}")