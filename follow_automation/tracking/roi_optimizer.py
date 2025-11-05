"""
Success Tracking and ROI Optimization System
Implements comprehensive metrics collection and adaptive optimization
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import statistics
from pathlib import Path
from ..config.settings import FollowAutomationConfig, ActionType

class MetricType(Enum):
    FOLLOW_SUCCESS = "follow_success"
    UNFOLLOW_SUCCESS = "unfollow_success"
    FOLLOW_BACK = "follow_back"
    RATE_LIMIT = "rate_limit"
    ERROR = "error"
    ENGAGEMENT = "engagement"

@dataclass
class ActionMetrics:
    """Metrics for a single action"""
    timestamp: datetime
    action_type: ActionType
    target_username: str
    success: bool
    response_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    relevance_score: Optional[float] = None

@dataclass
class ROIResult:
    """ROI calculation result"""
    period_days: int
    total_actions: int
    successful_actions: int
    success_rate: float
    follow_back_count: int
    follow_back_rate: float
    net_followers: int
    cost_per_follower: float
    roi_score: float

class MetricsCollector:
    """
    Collects and stores comprehensive metrics for analysis
    """
    
    def __init__(self, config: FollowAutomationConfig, db_path: str):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.db_path = Path(db_path)
        self._init_database()
        
        # In-memory cache for recent metrics
        self.recent_metrics: List[ActionMetrics] = []
        self.max_cache_size = 1000
        
        # Performance tracking
        self.session_metrics = {
            "actions_today": 0,
            "successes_today": 0,
            "followbacks_today": 0,
            "rate_limits_today": 0,
            "session_start": datetime.now()
        }
    
    def _init_database(self):
        """Initialize SQLite database for metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_username TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    response_code INTEGER,
                    response_time_ms REAL,
                    error_message TEXT,
                    relevance_score REAL,
                    session_id TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_action_type 
                ON metrics(action_type)
            """)
            
            conn.commit()
    
    def record_action(self, metrics: ActionMetrics):
        """Record action metrics"""
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metrics (
                    timestamp, action_type, target_username, success,
                    response_code, response_time_ms, error_message,
                    relevance_score, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp.isoformat(),
                metrics.action_type.value,
                metrics.target_username,
                metrics.success,
                metrics.response_code,
                metrics.response_time_ms,
                metrics.error_message,
                metrics.relevance_score,
                self._get_session_id()
            ))
            conn.commit()
        
        # Cache recent metrics
        self.recent_metrics.append(metrics)
        if len(self.recent_metrics) > self.max_cache_size:
            self.recent_metrics.pop(0)
        
        # Update session metrics
        self._update_session_metrics(metrics)
        
        self.logger.debug(f"Recorded action: {metrics.action_type.value} -> "
                         f"{metrics.target_username} ({metrics.success})")
    
    def _update_session_metrics(self, metrics: ActionMetrics):
        """Update in-session metrics"""
        if metrics.timestamp.date() == datetime.now().date():
            self.session_metrics["actions_today"] += 1
            
            if metrics.success:
                self.session_metrics["successes_today"] += 1
            
            if metrics.response_code == 429:
                self.session_metrics["rate_limits_today"] += 1
    
    def _get_session_id(self) -> str:
        """Get current session ID"""
        return f"session_{self.session_metrics['session_start'].strftime('%Y%m%d_%H%M')}"
    
    def get_recent_metrics(self, hours: int = 24) -> List[ActionMetrics]:
        """Get metrics from last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff.isoformat(),))
            
            return [
                ActionMetrics(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    action_type=ActionType(row["action_type"]),
                    target_username=row["target_username"],
                    success=bool(row["success"]),
                    response_code=row["response_code"],
                    response_time_ms=row["response_time_ms"],
                    error_message=row["error_message"],
                    relevance_score=row["relevance_score"]
                )
                for row in cursor.fetchall()
            ]
    
    def get_action_statistics(self, days: int = 7) -> Dict:
        """Get comprehensive action statistics"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    action_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                    AVG(CASE WHEN success THEN response_time_ms ELSE NULL END) as avg_response_time,
                    COUNT(DISTINCT target_username) as unique_targets
                FROM metrics 
                WHERE timestamp > ?
                GROUP BY action_type
            """, (cutoff.isoformat(),))
            
            stats = {}
            for row in cursor.fetchall():
                action_type = ActionType(row["action_type"])
                total = row["total"]
                successful = row["successful"] or 0
                
                stats[action_type.value] = {
                    "total_actions": total,
                    "successful_actions": successful,
                    "success_rate": (successful / total * 100) if total > 0 else 0,
                    "avg_response_time_ms": row["avg_response_time"] or 0,
                    "unique_targets": row["unique_targets"] or 0
                }
        
        return stats

class ROICalculator:
    """
    Calculates Return on Investment for follow/unfollow automation
    """
    
    def __init__(self, config: FollowAutomationConfig, metrics_collector: MetricsCollector):
        self.config = config
        self.metrics = metrics_collector
        self.logger = logging.getLogger(__name__)
    
    def calculate_roi(self, period_days: int = 30) -> ROIResult:
        """Calculate ROI for the specified period"""
        cutoff = datetime.now() - timedelta(days=period_days)
        
        # Get metrics for period
        metrics = self.metrics.get_recent_metrics(hours=period_days * 24)
        
        # Calculate basic metrics
        total_actions = len(metrics)
        successful_actions = sum(1 for m in metrics if m.success)
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
        
        # Calculate follow-back rate
        follow_actions = [m for m in metrics if m.action_type == ActionType.FOLLOW]
        follow_backs = follow_actions.count(lambda m: m.success)  # This would need follow-back detection data
        
        follow_back_rate = (follow_backs / len(follow_actions) * 100) if follow_actions else 0
        
        # Calculate net followers (simplified)
        net_followers = self._calculate_net_followers(metrics)
        
        # Calculate cost metrics
        # Cost = time spent + rate limit headroom used + operational complexity
        total_time_hours = self._estimate_time_cost(metrics)
        cost_per_follower = total_time_hours / max(net_followers, 1)
        
        # ROI score (higher is better)
        roi_score = self._calculate_roi_score(success_rate, follow_back_rate, net_followers, total_actions)
        
        return ROIResult(
            period_days=period_days,
            total_actions=total_actions,
            successful_actions=successful_actions,
            success_rate=success_rate,
            follow_back_count=follow_backs,
            follow_back_rate=follow_back_rate,
            net_followers=net_followers,
            cost_per_follower=cost_per_follower,
            roi_score=roi_score
        )
    
    def _calculate_net_followers(self, metrics: List[ActionMetrics]) -> int:
        """Calculate net follower change"""
        follows = sum(1 for m in metrics 
                     if m.action_type == ActionType.FOLLOW and m.success)
        unfollows = sum(1 for m in metrics 
                       if m.action_type == ActionType.UNFOLLOW and m.success)
        
        return follows - unfollows
    
    def _estimate_time_cost(self, metrics: List[ActionMetrics]) -> float:
        """Estimate time cost in hours"""
        # Base time per action (including API calls, delays, etc.)
        avg_time_per_action_seconds = 15  # Conservative estimate
        
        # Time spent on rate limits and errors
        rate_limit_penalty = sum(1 for m in metrics if m.response_code == 429) * 60
        error_penalty = sum(1 for m in metrics if not m.success) * 30
        
        total_seconds = (
            len(metrics) * avg_time_per_action_seconds + 
            rate_limit_penalty + 
            error_penalty
        )
        
        return total_seconds / 3600  # Convert to hours
    
    def _calculate_roi_score(self, success_rate: float, follow_back_rate: float, 
                           net_followers: int, total_actions: int) -> float:
        """Calculate composite ROI score"""
        if total_actions == 0:
            return 0.0
        
        # Components of ROI score
        success_component = success_rate / 100 * 40  # 40% weight
        follow_back_component = follow_back_rate / 100 * 30  # 30% weight
        growth_component = min(net_followers / total_actions * 100, 20) * 20  # 20% weight, capped
        efficiency_component = min(100 - (total_actions / 30), 100) * 10  # 10% weight for efficiency
        
        roi_score = (success_component + follow_back_component + 
                    growth_component + efficiency_component)
        
        return round(roi_score, 2)

class OptimizationEngine:
    """
    Analyzes metrics and provides optimization recommendations
    """
    
    def __init__(self, config: FollowAutomationConfig, metrics_collector: MetricsCollector):
        self.config = config
        self.metrics = metrics_collector
        self.logger = logging.getLogger(__name__)
        
        # Historical performance data
        self.performance_history: List[Dict] = []
    
    def analyze_performance(self, days: int = 7) -> Dict:
        """Comprehensive performance analysis"""
        roi_result = ROICalculator(self.config, self.metrics).calculate_roi(days)
        action_stats = self.metrics.get_action_statistics(days)
        
        # Analyze trends
        trend_analysis = self._analyze_trends(days)
        
        # Generate optimization recommendations
        recommendations = self._generate_recommendations(
            roi_result, action_stats, trend_analysis
        )
        
        # Store analysis for historical tracking
        analysis = {
            "analysis_date": datetime.now().isoformat(),
            "period_days": days,
            "roi_result": roi_result.__dict__,
            "action_statistics": action_stats,
            "trend_analysis": trend_analysis,
            "recommendations": recommendations
        }
        
        self.performance_history.append(analysis)
        
        return analysis
    
    def _analyze_trends(self, days: int) -> Dict:
        """Analyze performance trends over time"""
        recent_metrics = self.metrics.get_recent_metrics(hours=days * 24)
        
        if len(recent_metrics) < 10:
            return {"trend_data_insufficient": True}
        
        # Analyze success rate trend
        hourly_success_rates = self._calculate_hourly_success_rates(recent_metrics)
        success_trend = self._calculate_trend(hourly_success_rates)
        
        # Analyze response time trends
        response_times = [m.response_time_ms for m in recent_metrics if m.response_time_ms]
        response_time_trend = self._calculate_trend(response_times)
        
        # Analyze error patterns
        error_patterns = self._analyze_error_patterns(recent_metrics)
        
        return {
            "success_rate_trend": success_trend,
            "response_time_trend": response_time_trend,
            "error_patterns": error_patterns,
            "sample_size": len(recent_metrics)
        }
    
    def _calculate_hourly_success_rates(self, metrics: List[ActionMetrics]) -> List[float]:
        """Calculate success rates by hour"""
        hourly_data = {}
        
        for metric in metrics:
            hour = metric.timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
            if hour not in hourly_data:
                hourly_data[hour] = {"successes": 0, "total": 0}
            
            hourly_data[hour]["total"] += 1
            if metric.success:
                hourly_data[hour]["successes"] += 1
        
        return [
            data["successes"] / data["total"]
            for data in hourly_data.values()
        ]
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 3:
            return "insufficient_data"
        
        # Simple linear trend
        x = list(range(len(values)))
        y = values
        
        # Calculate correlation coefficient
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            return "stable"
        
        correlation = numerator / denominator
        
        if correlation > 0.3:
            return "improving"
        elif correlation < -0.3:
            return "declining"
        else:
            return "stable"
    
    def _analyze_error_patterns(self, metrics: List[ActionMetrics]) -> Dict:
        """Analyze error patterns"""
        errors = [m for m in metrics if not m.success]
        
        error_codes = {}
        error_messages = {}
        
        for error in errors:
            if error.response_code:
                error_codes[error.response_code] = error_codes.get(error.response_code, 0) + 1
            
            if error.error_message:
                msg_key = error.error_message[:50]  # Truncate long messages
                error_messages[msg_key] = error_messages.get(msg_key, 0) + 1
        
        return {
            "total_errors": len(errors),
            "error_rate": len(errors) / len(metrics) * 100,
            "most_common_error_codes": dict(sorted(error_codes.items(), 
                                                  key=lambda x: x[1], reverse=True)[:5]),
            "most_common_error_messages": dict(sorted(error_messages.items(), 
                                                     key=lambda x: x[1], reverse=True)[:5])
        }
    
    def _generate_recommendations(self, roi_result: ROIResult, 
                                action_stats: Dict, trend_analysis: Dict) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Success rate recommendations
        if roi_result.success_rate < 80:
            recommendations.append({
                "type": "success_rate",
                "priority": "high",
                "message": "Success rate is below 80%. Consider reviewing target selection and timing.",
                "actions": ["Improve target relevance scoring", "Increase delay times", "Review user profiles"]
            })
        
        # Rate limit recommendations
        total_rate_limits = sum(
            stats.get("success_rate", 0) for stats in action_stats.values()
        )
        
        if trend_analysis.get("error_patterns", {}).get("error_rate", 0) > 5:
            recommendations.append({
                "type": "rate_limiting",
                "priority": "medium",
                "message": "High error rate detected. Consider reducing action frequency.",
                "actions": ["Decrease actions per hour", "Increase delay between actions", "Review rate limit handling"]
            })
        
        # ROI recommendations
        if roi_result.roi_score < 50:
            recommendations.append({
                "type": "roi_optimization",
                "priority": "high",
                "message": "ROI score is low. Focus on higher-quality targets and better timing.",
                "actions": ["Improve target relevance scoring", "Focus on mutual collaborators", "Adjust follow-back detection timing"]
            })
        
        # Trend recommendations
        if trend_analysis.get("success_rate_trend") == "declining":
            recommendations.append({
                "type": "trend_correction",
                "priority": "high",
                "message": "Success rate is declining. Immediate optimization needed.",
                "actions": ["Review recent changes", "Reduce activity temporarily", "Analyze error patterns"]
            })
        
        return recommendations
    
    def get_optimization_summary(self) -> Dict:
        """Get current optimization summary"""
        if not self.performance_history:
            return {"status": "no_data"}
        
        latest = self.performance_history[-1]
        
        return {
            "latest_roi_score": latest["roi_result"]["roi_score"],
            "latest_success_rate": latest["roi_result"]["success_rate"],
            "recent_trend": latest["trend_analysis"].get("success_rate_trend", "unknown"),
            "active_recommendations": len(latest["recommendations"]),
            "performance_history_length": len(self.performance_history)
        }

class AnalyticsDashboard:
    """
    Provides dashboard data for monitoring and reporting
    """
    
    def __init__(self, metrics_collector: MetricsCollector, 
                 roi_calculator: ROICalculator, optimizer: OptimizationEngine):
        self.metrics = metrics_collector
        self.roi = roi_calculator
        self.optimizer = optimizer
        self.logger = logging.getLogger(__name__)
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        # Current metrics
        recent_metrics = self.metrics.get_recent_metrics(hours=24)
        action_stats = self.metrics.get_action_statistics(days=7)
        
        # ROI analysis
        roi_30_day = self.roi.calculate_roi(30)
        roi_7_day = self.roi.calculate_roi(7)
        
        # Optimization insights
        optimization_summary = self.optimizer.get_optimization_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "session_metrics": self.metrics.session_metrics,
            "daily_action_statistics": action_stats,
            "roi_30_day": roi_30_day.__dict__,
            "roi_7_day": roi_7_day.__dict__,
            "optimization_summary": optimization_summary,
            "recent_performance": {
                "actions_last_24h": len(recent_metrics),
                "success_rate_24h": (
                    sum(1 for m in recent_metrics if m.success) / 
                    max(len(recent_metrics), 1) * 100
                )
            }
        }
    
    def export_report(self, filepath: str, days: int = 30) -> str:
        """Export comprehensive report"""
        report_data = {
            "report_generated": datetime.now().isoformat(),
            "report_period_days": days,
            "dashboard_data": self.get_dashboard_data(),
            "performance_analysis": self.optimizer.analyze_performance(days)
        }
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Report exported to {filepath}")
        return filepath