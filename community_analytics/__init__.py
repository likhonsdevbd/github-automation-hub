"""
Community Analytics System

A comprehensive analytics system for tracking community engagement patterns,
member lifecycle, retention, and predicting community health trends.
"""

from .core.lifecycle_tracker import MemberLifecycleTracker
from .core.engagement_scorer import EngagementScorer
from .core.health_indicators import CommunityHealthIndicator
from .core.retention_analyzer import RetentionAnalyzer
from .core.network_analyzer import SocialNetworkAnalyzer

from .models.prediction_engine import EngagementPredictionEngine

__version__ = "1.0.0"
__all__ = [
    "MemberLifecycleTracker",
    "EngagementScorer", 
    "CommunityHealthIndicator",
    "RetentionAnalyzer",
    "SocialNetworkAnalyzer",
    "EngagementPredictionEngine"
]