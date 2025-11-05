"""
Growth Analysis Engine for Repository Intelligence

This module provides comprehensive growth analysis capabilities including:
- Growth pattern analysis algorithms
- Predictive modeling for repository growth
- Anomaly detection for unusual growth patterns
- Benchmarking against similar repositories
- Trend forecasting with confidence intervals
- Growth strategy recommendations based on patterns

Author: Automation Hub
Version: 1.0.0
"""

from .core import GrowthAnalyzer
from .predictors import GrowthPredictor
from .anomaly_detector import AnomalyDetector
from .benchmarking import BenchmarkAnalyzer
from .forecasting import TrendForecaster
from .recommendations import StrategyRecommender

__version__ = "1.0.0"
__all__ = [
    "GrowthAnalyzer",
    "GrowthPredictor", 
    "AnomalyDetector",
    "BenchmarkAnalyzer",
    "TrendForecaster",
    "StrategyRecommender"
]

def get_growth_engine():
    """Factory function to create and return a complete growth analysis engine."""
    return {
        'analyzer': GrowthAnalyzer(),
        'predictor': GrowthPredictor(),
        'anomaly_detector': AnomalyDetector(),
        'benchmark_analyzer': BenchmarkAnalyzer(),
        'trend_forecaster': TrendForecaster(),
        'strategy_recommender': StrategyRecommender()
    }