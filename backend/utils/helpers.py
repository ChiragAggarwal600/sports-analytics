import hashlib
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

def timer(func):
    """Decorator to time function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.3f} seconds")
        return result
    return wrapper

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = {"args": args, "kwargs": kwargs}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()

def validate_sport(sport: str) -> bool:
    """Validate if sport is supported"""
    valid_sports = ['cricket', 'football', 'basketball', 'tennis', 'all', 'general']
    return sport.lower() in valid_sports

def calculate_trend(values: List[float], window: int = 7) -> str:
    """Calculate trend from time series values"""
    if len(values) < window:
        return "insufficient_data"
    
    recent = np.mean(values[-window:])
    previous = np.mean(values[-window*2:-window])
    
    if recent > previous * 1.1:
        return "increasing"
    elif recent < previous * 0.9:
        return "decreasing"
    else:
        return "stable"

def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value * 100:.1f}%"

def get_time_range_filter(time_range: str) -> Dict[str, datetime]:
    """Get datetime filter based on time range string"""
    now = datetime.utcnow()
    
    ranges = {
        "1h": now - timedelta(hours=1),
        "1d": now - timedelta(days=1),
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "90d": now - timedelta(days=90)
    }
    
    return {
        "start": ranges.get(time_range, now - timedelta(days=7)),
        "end": now
    }

def aggregate_metrics(data: pd.DataFrame, 
                     metric: str,
                     aggregation: str = "mean") -> float:
    """Aggregate metrics from dataframe"""
    if metric not in data.columns:
        return 0.0
    
    agg_funcs = {
        "mean": np.mean,
        "sum": np.sum,
        "max": np.max,
        "min": np.min,
        "median": np.median
    }
    
    agg_func = agg_funcs.get(aggregation, np.mean)
    return float(agg_func(data[metric]))

def normalize_score(value: float, min_val: float = 0, max_val: float = 1) -> float:
    """Normalize score to 0-1 range"""
    return max(min_val, min(max_val, value))

def generate_mock_data(sport: str, days: int = 30) -> pd.DataFrame:
    """Generate mock data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    data = pd.DataFrame({
        'date': dates,
        'sport': sport,
        'sentiment': np.random.uniform(0.3, 0.9, days),
        'engagement': np.random.uniform(0.4, 0.95, days),
        'mentions': np.random.randint(100, 10000, days),
        'reach': np.random.randint(10000, 1000000, days)
    })
    
    return data