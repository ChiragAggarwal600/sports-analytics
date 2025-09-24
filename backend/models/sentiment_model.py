import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Fine-tuned BERT model for sports sentiment analysis"""
    
    def __init__(self, model_name: str = "bert-base-uncased"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            num_labels=3  # Positive, Neutral, Negative
        )
        self.model.to(self.device)
        self.model.eval()
        
    def predict(self, texts: List[str]) -> List[Dict]:
        """
        Predict sentiment for batch of texts
        Returns: List of dicts with sentiment scores
        """
        results = []
        
        for text in texts:
            inputs = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
            sentiment_scores = predictions.cpu().numpy()[0]
            
            results.append({
                'text': text[:100],  # First 100 chars for reference
                'positive': float(sentiment_scores[2]),
                'neutral': float(sentiment_scores[1]),
                'negative': float(sentiment_scores[0]),
                'overall': self._get_overall_sentiment(sentiment_scores)
            })
            
        return results
    
    def _get_overall_sentiment(self, scores: np.ndarray) -> str:
        """Determine overall sentiment from scores"""
        labels = ['negative', 'neutral', 'positive']
        return labels[np.argmax(scores)]
    
    def fine_tune(self, train_data: List[Tuple[str, int]], epochs: int = 3):
        """Fine-tune model on sport-specific data"""
        from torch.utils.data import DataLoader, Dataset
        
        class SentimentDataset(Dataset):
            def __init__(self, texts, labels, tokenizer, max_length=512):
                self.texts = texts
                self.labels = labels
                self.tokenizer = tokenizer
                self.max_length = max_length
                
            def __len__(self):
                return len(self.texts)
            
            def __getitem__(self, idx):
                text = self.texts[idx]
                label = self.labels[idx]
                
                encoding = self.tokenizer(
                    text,
                    truncation=True,
                    padding='max_length',
                    max_length=self.max_length,
                    return_tensors='pt'
                )
                
                return {
                    'input_ids': encoding['input_ids'].flatten(),
                    'attention_mask': encoding['attention_mask'].flatten(),
                    'labels': torch.tensor(label, dtype=torch.long)
                }
        
        texts, labels = zip(*train_data)
        dataset = SentimentDataset(texts, labels, self.tokenizer)
        dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=2e-5)
        self.model.train()
        
        for epoch in range(epochs):
            total_loss = 0
            for batch in dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                outputs = self.model(**batch)
                loss = outputs.loss
                
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
                
                total_loss += loss.item()
                
            avg_loss = total_loss / len(dataloader)
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        self.model.eval()
        
    def save_model(self, path: str):
        """Save fine-tuned model"""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        
    def load_model(self, path: str):
        """Load fine-tuned model"""
        self.model = AutoModelForSequenceClassification.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model.to(self.device)
        self.model.eval()