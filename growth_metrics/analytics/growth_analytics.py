"""
Analytics Engine
================

Historical data collection and trend analysis for growth metrics:
- Health score calculation
- Trend analysis and forecasting
- Anomaly detection
- Community engagement metrics
- Performance benchmarking
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import logging
import statistics
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import IsolationForest
import json

logger = logging.getLogger(__name__)


@dataclass
class HealthScoreComponents:
    """Components of repository health score"""
    contributors_score: float
    pr_throughput_score: float
    review_velocity_score: float
    issue_freshness_score: float
    fork_growth_score: float
    overall_score: float


@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    metric_name: str
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # 0-1 correlation with time
    growth_rate: float  # Percentage change per period
    seasonality_detected: bool
    seasonal_periods: List[int]
    confidence: float  # 0-1 confidence in trend
    forecast_values: List[float]
    forecast_dates: List[datetime]


@dataclass
class AnomalyDetection:
    """Anomaly detection results"""
    metric_name: str
    anomaly_type: str  # 'spike', 'drop', 'pattern_change'
    anomaly_score: float  # 0-1 confidence
    value: float
    expected_value: float
    date: datetime
    severity: str  # 'low', 'medium', 'high'
    description: str


class HealthScoreCalculator:
    """
    Calculate repository health score based on multiple metrics
    
    Implements the health scoring methodology from the design document:
    - 30% Contributors (unique monthly contributors, retention)
    - 20% PR Throughput (opened and merged per period)
    - 20% Review Velocity (median time-to-merge)
    - 15% Issue Freshness (mean age of open issues)
    - 15% Fork Growth (experimentation signal)
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            'contributors': 0.30,
            'pr_throughput': 0.20,
            'review_velocity': 0.20,
            'issue_freshness': 0.15,
            'fork_growth': 0.15
        }
        
        # Normalization ranges based on project history
        self.normalization_ranges = {
            'contributors': {'min': 1, 'max': 100},  # 1-100 contributors per month
            'pr_throughput': {'min': 0, 'max': 50},  # 0-50 PRs per month
            'review_velocity': {'min': 2, 'max': 168},  # 2-168 hours (2 days to 1 week)
            'issue_freshness': {'min': 1, 'max': 30},  # 1-30 days
            'fork_growth': {'min': 0, 'max': 20}  # 0-20 new forks per month
        }
        
    def calculate_health_score(self, metrics_data: Dict[str, Any], 
                             historical_data: List[Dict[str, Any]] = None) -> HealthScoreComponents:
        """Calculate comprehensive health score from metrics data"""
        
        # Get individual component scores
        contributors_score = self._calculate_contributors_score(metrics_data, historical_data)
        pr_throughput_score = self._calculate_pr_throughput_score(metrics_data, historical_data)
        review_velocity_score = self._calculate_review_velocity_score(metrics_data, historical_data)
        issue_freshness_score = self._calculate_issue_freshness_score(metrics_data, historical_data)
        fork_growth_score = self._calculate_fork_growth_score(metrics_data, historical_data)
        
        # Calculate weighted overall score
        overall_score = (
            contributors_score * self.weights['contributors'] +
            pr_throughput_score * self.weights['pr_throughput'] +
            review_velocity_score * self.weights['review_velocity'] +
            issue_freshness_score * self.weights['issue_freshness'] +
            fork_growth_score * self.weights['fork_growth']
        )
        
        return HealthScoreComponents(
            contributors_score=contributors_score,
            pr_throughput_score=pr_throughput_score,
            review_velocity_score=review_velocity_score,
            issue_freshness_score=issue_freshness_score,
            fork_growth_score=fork_growth_score,
            overall_score=overall_score
        )
        
    def _calculate_contributors_score(self, metrics_data: Dict[str, Any], 
                                    historical_data: List[Dict[str, Any]] = None) -> float:
        """Calculate contributors score (30% weight)"""
        
        current_contributors = metrics_data.get('contributors_count', 0)
        
        # Get historical baseline if available
        baseline_contributors = self._get_historical_baseline(historical_data, 'contributors_count', 30)
        
        if baseline_contributors and baseline_contributors > 0:
            # Calculate growth rate
            growth_rate = (current_contributors - baseline_contributors) / baseline_contributors
            score = 0.5 + min(max(growth_rate / 2, -0.5), 0.5)  # Normalize to 0-1 range
        else:
            # First-time calculation, use normalization
            normalized = self._normalize_value(current_contributors, 'contributors')
            score = normalized
            
        return max(0, min(1, score))
        
    def _calculate_pr_throughput_score(self, metrics_data: Dict[str, Any],
                                     historical_data: List[Dict[str, Any]] = None) -> float:
        """Calculate PR throughput score (20% weight)"""
        
        pr_opened = metrics_data.get('prs_opened', 0)
        pr_merged = metrics_data.get('prs_merged', 0)
        
        # Combine opened and merged PRs for throughput
        total_throughput = pr_opened + pr_merged
        
        # Get historical baseline
        baseline_throughput = self._get_historical_baseline(historical_data, 'prs_opened', 30)
        if baseline_throughput is None:
            baseline_throughput = pr_opened
            
        if baseline_throughput and baseline_throughput > 0:
            # Calculate throughput ratio and consistency
            throughput_ratio = pr_opened / max(baseline_throughput, 1)
            merge_ratio = pr_merged / max(pr_opened, 1) if pr_opened > 0 else 0
            
            # Score based on both activity and merge efficiency
            activity_score = min(throughput_ratio / 1.2, 1)  # Good if 20% above baseline
            efficiency_score = merge_ratio
            
            score = (activity_score + efficiency_score) / 2
        else:
            # First-time calculation
            normalized = self._normalize_value(total_throughput, 'pr_throughput')
            score = normalized
            
        return max(0, min(1, score))
        
    def _calculate_review_velocity_score(self, metrics_data: Dict[str, Any],
                                       historical_data: List[Dict[str, Any]] = None) -> float:
        """Calculate review velocity score (20% weight)"""
        
        avg_time_to_merge = metrics_data.get('avg_time_to_merge_hours', 0)
        
        if avg_time_to_merge <= 0:
            return 0.5  # Neutral score if no PRs
            
        # Convert time to score (faster is better)
        # Invert the time scale and normalize
        max_time = self.normalization_ranges['review_velocity']['max']
        normalized_time = min(avg_time_to_merge / max_time, 1)
        
        # Convert to score (1 - normalized_time so faster = higher score)
        score = 1 - normalized_time
        
        # Adjust based on historical performance if available
        if historical_data:
            historical_times = [d.get('avg_time_to_merge_hours', 0) for d in historical_data[-30:] if d.get('avg_time_to_merge_hours', 0) > 0]
            if historical_times:
                historical_avg = statistics.mean(historical_times)
                if avg_time_to_merge < historical_avg:
                    score = min(score * 1.2, 1)  # Boost for being faster than historical
                else:
                    score = score * 0.8  # Penalty for being slower
                    
        return max(0, min(1, score))
        
    def _calculate_issue_freshness_score(self, metrics_data: Dict[str, Any],
                                       historical_data: List[Dict[str, Any]] = None) -> float:
        """Calculate issue freshness score (15% weight)"""
        
        # For simplicity, we'll use issue data from the current snapshot
        # In practice, you'd want more sophisticated calculation based on issue aging
        
        current_time = datetime.now()
        issues = metrics_data.get('issues', [])
        
        if not issues:
            return 0.5  # Neutral score if no issues
            
        # Calculate average age of open issues
        open_issues = [issue for issue in issues if issue.get('state') == 'open']
        if not open_issues:
            return 0.5  # Neutral score if no open issues
            
        total_age = 0
        for issue in open_issues:
            created_at = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
            age_days = (current_time - created_at).days
            total_age += age_days
            
        avg_age = total_age / len(open_issues)
        
        # Convert age to score (lower age is better)
        max_age = self.normalization_ranges['issue_freshness']['max']
        normalized_age = min(avg_age / max_age, 1)
        
        # Score is inverse of normalized age
        score = 1 - normalized_age
        
        return max(0, min(1, score))
        
    def _calculate_fork_growth_score(self, metrics_data: Dict[str, Any],
                                   historical_data: List[Dict[str, Any]] = None) -> float:
        """Calculate fork growth score (15% weight)"""
        
        current_forks = metrics_data.get('forks_count', 0)
        
        # Get historical baseline if available
        baseline_forks = self._get_historical_baseline(historical_data, 'forks_count', 30)
        
        if baseline_forks and baseline_forks > 0:
            # Calculate fork growth rate
            growth_rate = (current_forks - baseline_forks) / baseline_forks
            score = 0.5 + min(max(growth_rate / 0.5, -0.5), 0.5)  # Normalize
        else:
            # First-time calculation, use normalized value
            forks_change = self._calculate_fork_change(historical_data)
            normalized = self._normalize_value(forks_change, 'fork_growth')
            score = normalized
            
        return max(0, min(1, score))
        
    def _normalize_value(self, value: float, metric_type: str) -> float:
        """Normalize value to 0-1 range based on typical ranges"""
        
        if value <= 0:
            return 0
            
        range_info = self.normalization_ranges[metric_type]
        min_val = range_info['min']
        max_val = range_info['max']
        
        if value <= min_val:
            return 0.1  # Low but not zero
        elif value >= max_val:
            return 1.0  # At or above maximum
        else:
            # Linear interpolation
            return (value - min_val) / (max_val - min_val)
            
    def _get_historical_baseline(self, historical_data: List[Dict[str, Any]], 
                               metric_name: str, days: int) -> Optional[float]:
        """Get historical baseline for a metric"""
        
        if not historical_data:
            return None
            
        # Get last N days of data
        recent_data = historical_data[-days:] if len(historical_data) >= days else historical_data
        
        # Calculate average
        values = [d.get(metric_name, 0) for d in recent_data if d.get(metric_name, 0) > 0]
        
        if values:
            return statistics.mean(values)
        else:
            return None
            
    def _calculate_fork_change(self, historical_data: List[Dict[str, Any]]) -> int:
        """Calculate change in fork count"""
        
        if len(historical_data) < 2:
            return 0
            
        current = historical_data[-1].get('forks_count', 0)
        previous = historical_data[-2].get('forks_count', 0)
        
        return current - previous


class TrendAnalyzer:
    """Analyze trends in repository metrics over time"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        
    def analyze_trends(self, metrics_data: List[Dict[str, Any]], 
                      metric_names: List[str] = None) -> List[TrendAnalysis]:
        """Analyze trends for multiple metrics"""
        
        if not metrics_data:
            return []
            
        if metric_names is None:
            # Auto-detect numeric metrics
            metric_names = self._detect_numeric_metrics(metrics_data)
            
        trends = []
        
        for metric_name in metric_names:
            try:
                trend = self._analyze_single_trend(metrics_data, metric_name)
                if trend:
                    trends.append(trend)
            except Exception as e:
                logger.warning(f"Failed to analyze trend for {metric_name}: {e}")
                
        return trends
        
    def _detect_numeric_metrics(self, metrics_data: List[Dict[str, Any]]) -> List[str]:
        """Auto-detect numeric metrics from data"""
        
        numeric_metrics = []
        if not metrics_data:
            return numeric_metrics
            
        # Sample first few records to detect types
        sample_size = min(10, len(metrics_data))
        sample_data = metrics_data[:sample_size]
        
        for key in sample_data[0].keys():
            # Skip non-numeric data
            if key in ['repository', 'timestamp', 'error']:
                continue
                
            # Check if values are numeric
            numeric_values = []
            for record in sample_data:
                value = record.get(key)
                if isinstance(value, (int, float)):
                    numeric_values.append(value)
                elif isinstance(value, str):
                    try:
                        numeric_values.append(float(value))
                    except ValueError:
                        continue
                        
            if len(numeric_values) >= sample_size * 0.8:  # 80% numeric
                numeric_metrics.append(key)
                
        return numeric_metrics
        
    def _analyze_single_trend(self, metrics_data: List[Dict[str, Any]], 
                            metric_name: str) -> Optional[TrendAnalysis]:
        """Analyze trend for a single metric"""
        
        # Extract metric values and dates
        values = []
        dates = []
        
        for record in metrics_data:
            value = record.get(metric_name)
            if value is not None and not isinstance(value, (dict, list)):
                try:
                    numeric_value = float(value)
                    values.append(numeric_value)
                    
                    # Extract date (use timestamp or create from sequence)
                    date_str = record.get('snapshot_date') or record.get('timestamp')
                    if date_str:
                        if isinstance(date_str, str):
                            if date_str.endswith('Z'):
                                date_str = date_str[:-1] + '+00:00'
                            dates.append(datetime.fromisoformat(date_str))
                        else:
                            dates.append(date_str)
                    else:
                        dates.append(datetime.now() - timedelta(days=len(values)-1))
                except (ValueError, TypeError):
                    continue
                    
        if len(values) < 3:  # Need at least 3 points for trend analysis
            return None
            
        # Convert to numpy arrays for analysis
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate trend direction and strength
        correlation, p_value = stats.pearsonr(x, y)
        
        # Determine trend direction
        if correlation > 0.3:
            trend_direction = 'increasing'
        elif correlation < -0.3:
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'
            
        # Calculate growth rate
        if values[0] != 0:
            total_change = (values[-1] - values[0]) / values[0] * 100
            periods = len(values) - 1
            growth_rate = total_change / periods if periods > 0 else 0
        else:
            growth_rate = 0
            
        # Detect seasonality
        seasonality_detected, seasonal_periods = self._detect_seasonality(y)
        
        # Generate simple forecast
        forecast_values, forecast_dates = self._generate_simple_forecast(y, dates, periods=7)
        
        # Calculate confidence (based on correlation and number of data points)
        confidence = min(abs(correlation) * (len(values) / 30), 1.0)  # Higher with more data
        
        return TrendAnalysis(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=abs(correlation),
            growth_rate=growth_rate,
            seasonality_detected=seasonality_detected,
            seasonal_periods=seasonal_periods,
            confidence=confidence,
            forecast_values=forecast_values,
            forecast_dates=forecast_dates
        )
        
    def _detect_seasonality(self, values: np.ndarray) -> Tuple[bool, List[int]]:
        """Detect seasonal patterns in data"""
        
        if len(values) < 8:  # Need minimum data for seasonality
            return False, []
            
        try:
            # Simple autocorrelation analysis
            autocorrs = []
            for lag in range(1, min(len(values) // 2, 7)):
                if len(values) > lag:
                    correlation = np.corrcoef(values[:-lag], values[lag:])[0, 1]
                    autocorrs.append((lag, abs(correlation)))
                    
            # Find strong autocorrelations
            strong_autocorrs = [lag for lag, corr in autocorrs if corr > 0.5]
            
            return len(strong_autocorrs) > 0, strong_autocorrs
            
        except Exception:
            return False, []
            
    def _generate_simple_forecast(self, values: np.ndarray, dates: List[datetime], 
                                periods: int = 7) -> Tuple[List[float], List[datetime]]:
        """Generate simple linear forecast"""
        
        if len(values) < 2:
            return [], []
            
        # Simple linear trend
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        
        # Generate forecast
        forecast_x = np.arange(len(values), len(values) + periods)
        forecast_values = np.polyval(coeffs, forecast_x).tolist()
        
        # Generate forecast dates
        last_date = dates[-1] if dates else datetime.now()
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(periods)]
        
        # Ensure non-negative values for counts
        forecast_values = [max(0, val) for val in forecast_values]
        
        return forecast_values, forecast_dates


class AnomalyDetector:
    """Detect anomalies in repository metrics"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        
    def detect_anomalies(self, metrics_data: List[Dict[str, Any]], 
                        metric_names: List[str] = None) -> List[AnomalyDetection]:
        """Detect anomalies in multiple metrics"""
        
        if not metrics_data or len(metrics_data) < 5:
            return []
            
        if metric_names is None:
            # Auto-detect numeric metrics
            metric_names = self._detect_numeric_metrics(metrics_data)
            
        anomalies = []
        
        for metric_name in metric_names:
            try:
                metric_anomalies = self._detect_metric_anomalies(metrics_data, metric_name)
                anomalies.extend(metric_anomalies)
            except Exception as e:
                logger.warning(f"Failed to detect anomalies for {metric_name}: {e}")
                
        return anomalies
        
    def _detect_numeric_metrics(self, metrics_data: List[Dict[str, Any]]) -> List[str]:
        """Auto-detect numeric metrics from data"""
        
        numeric_metrics = []
        if not metrics_data:
            return numeric_metrics
            
        sample_data = metrics_data[:5]
        
        for key in sample_data[0].keys():
            if key in ['repository', 'timestamp', 'error']:
                continue
                
            numeric_count = 0
            for record in sample_data:
                value = record.get(key)
                if isinstance(value, (int, float)) or (isinstance(value, str) and self._is_numeric_string(value)):
                    numeric_count += 1
                    
            if numeric_count >= len(sample_data) * 0.8:
                numeric_metrics.append(key)
                
        return numeric_metrics
        
    def _is_numeric_string(self, value: str) -> bool:
        """Check if string can be converted to numeric"""
        try:
            float(value)
            return True
        except ValueError:
            return False
            
    def _detect_metric_anomalies(self, metrics_data: List[Dict[str, Any]], 
                               metric_name: str) -> List[AnomalyDetection]:
        """Detect anomalies for a single metric"""
        
        # Extract values and create feature matrix
        values = []
        dates = []
        
        for record in metrics_data:
            value = record.get(metric_name)
            if value is not None and not isinstance(value, (dict, list)):
                try:
                    numeric_value = float(value)
                    values.append(numeric_value)
                    
                    # Extract date
                    date_str = record.get('snapshot_date') or record.get('timestamp')
                    if date_str:
                        if isinstance(date_str, str):
                            if date_str.endswith('Z'):
                                date_str = date_str[:-1] + '+00:00'
                            dates.append(datetime.fromisoformat(date_str))
                        else:
                            dates.append(date_str)
                    else:
                        dates.append(datetime.now() - timedelta(days=len(values)-1))
                except (ValueError, TypeError):
                    continue
                    
        if len(values) < 5:
            return []
            
        anomalies = []
        
        # Method 1: Statistical anomaly detection (Z-score)
        z_scores = np.abs(stats.zscore(values))
        z_threshold = 2.5
        
        for i, (date, value, z_score) in enumerate(zip(dates, values, z_scores)):
            if z_score > z_threshold:
                # Determine anomaly type
                anomaly_type = self._classify_anomaly_type(value, values, i)
                
                # Calculate expected value (median)
                expected_value = np.median(values)
                
                # Determine severity
                severity = self._calculate_severity(z_score)
                
                anomaly = AnomalyDetection(
                    metric_name=metric_name,
                    anomaly_type=anomaly_type,
                    anomaly_score=min(z_score / 4.0, 1.0),  # Normalize to 0-1
                    value=value,
                    expected_value=expected_value,
                    date=date,
                    severity=severity,
                    description=f"{anomaly_type.title()} detected: {value:.2f} (z-score: {z_score:.2f})"
                )
                anomalies.append(anomaly)
                
        # Method 2: Isolation Forest (if enough data)
        if len(values) >= 10:
            try:
                # Prepare features for isolation forest
                X = np.array(values).reshape(-1, 1)
                
                # Fit isolation forest
                isolation_forest = IsolationForest(contamination=0.1, random_state=42)
                anomaly_labels = isolation_forest.fit_predict(X)
                
                for i, (date, value, label) in enumerate(zip(dates, values, anomaly_labels)):
                    if label == -1:  # Anomaly
                        # Calculate distance from centroid
                        expected_value = np.median(values)
                        distance = abs(value - expected_value) / (np.std(values) + 1e-8)
                        
                        # Check if already detected by Z-score
                        if not any(a.date == date and a.metric_name == metric_name for a in anomalies):
                            anomaly_type = self._classify_anomaly_type(value, values, i)
                            severity = self._calculate_severity(distance)
                            
                            anomaly = AnomalyDetection(
                                metric_name=metric_name,
                                anomaly_type=anomaly_type,
                                anomaly_score=min(distance / 3.0, 1.0),
                                value=value,
                                expected_value=expected_value,
                                date=date,
                                severity=severity,
                                description=f"{anomaly_type.title()} detected by isolation forest: {value:.2f}"
                            )
                            anomalies.append(anomaly)
            except Exception as e:
                logger.warning(f"Isolation forest failed for {metric_name}: {e}")
                
        return anomalies
        
    def _classify_anomaly_type(self, value: float, values: List[float], index: int) -> str:
        """Classify the type of anomaly"""
        
        median_val = np.median(values)
        
        if index > 0:
            prev_value = values[index-1]
            change_ratio = (value - prev_value) / max(prev_value, 1)
            
            if change_ratio > 1.0:  # More than 100% increase
                return 'spike'
            elif change_ratio < -0.5:  # More than 50% decrease
                return 'drop'
        else:
            # For first data point, compare to median
            if value > median_val * 2:
                return 'spike'
            elif value < median_val * 0.5:
                return 'drop'
                
        return 'pattern_change'
        
    def _calculate_severity(self, score: float) -> str:
        """Calculate anomaly severity"""
        
        if score >= 4.0:
            return 'high'
        elif score >= 2.5:
            return 'medium'
        else:
            return 'low'


class CommunityEngagementAnalyzer:
    """Analyze community engagement metrics"""
    
    def analyze_engagement(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze community engagement from metrics data"""
        
        analysis = {
            'total_contributors': len(metrics_data.get('contributors', [])),
            'new_contributors': 0,  # Would need to compare with historical data
            'contribution_diversity': self._calculate_contribution_diversity(metrics_data),
            'contributor_retention': self._calculate_contributor_retention(metrics_data),
            'issue_response_time': self._calculate_issue_response_time(metrics_data),
            'pr_review_velocity': self._calculate_pr_review_velocity(metrics_data),
            'community_activity_score': 0.0
        }
        
        # Calculate overall community activity score
        analysis['community_activity_score'] = self._calculate_community_score(analysis)
        
        return analysis
        
    def _calculate_contribution_diversity(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate diversity of contribution types"""
        
        # This is simplified - in practice you'd analyze commit types, PR categories, etc.
        commits = metrics_data.get('commits', [])
        issues = metrics_data.get('issues', [])
        prs = metrics_data.get('pull_requests', [])
        
        # Simple diversity score based on activity types
        activity_types = {
            'commits': len(commits),
            'issues': len(issues),
            'pull_requests': len(prs)
        }
        
        total_activities = sum(activity_types.values())
        if total_activities == 0:
            return {'diversity_score': 0, 'activity_breakdown': activity_types}
            
        # Calculate Shannon diversity index
        diversity_score = 0
        for count in activity_types.values():
            if count > 0:
                proportion = count / total_activities
                diversity_score -= proportion * np.log(proportion)
                
        return {
            'diversity_score': diversity_score,
            'activity_breakdown': activity_types,
            'normalized_diversity': diversity_score / np.log(len(activity_types))  # Normalize to 0-1
        }
        
    def _calculate_contributor_retention(self, metrics_data: Dict[str, Any]) -> float:
        """Calculate contributor retention rate"""
        
        # This is simplified - in practice you'd need historical data
        contributors = metrics_data.get('contributors', [])
        
        # Estimate retention based on contribution patterns
        # High contributors likely to return
        retention_score = 0.5  # Default
        
        if contributors:
            # Simple heuristic: more high-contribution contributors = higher retention
            high_contributors = [c for c in contributors if c.get('contributions', 0) > 5]
            retention_score = min(len(high_contributors) / len(contributors) + 0.3, 1.0)
            
        return retention_score
        
    def _calculate_issue_response_time(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate time to first response for issues"""
        
        issues = metrics_data.get('issues', [])
        if not issues:
            return {'avg_response_time_hours': 0, 'issues_responded': 0, 'total_issues': 0}
            
        # This is simplified - would need comment/response data
        # For now, estimate based on issue age and state
        open_issues = [i for i in issues if i.get('state') == 'open']
        
        current_time = datetime.now()
        response_times = []
        
        for issue in open_issues:
            created_at = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
            age_hours = (current_time - created_at).total_seconds() / 3600
            
            # Estimate response time (many issues get first response within 24-48 hours)
            if age_hours < 24:
                response_times.append(age_hours)
            elif age_hours < 48:
                response_times.append(36)  # Midpoint estimate
            else:
                response_times.append(age_hours)  # May not have been responded to
                
        if response_times:
            avg_response_time = statistics.mean(response_times)
            responded_issues = len([rt for rt in response_times if rt <= 48])  # Responded within 2 days
        else:
            avg_response_time = 0
            responded_issues = 0
            
        return {
            'avg_response_time_hours': avg_response_time,
            'issues_responded': responded_issues,
            'total_issues': len(open_issues),
            'response_rate': responded_issues / len(open_issues) if open_issues else 0
        }
        
    def _calculate_pr_review_velocity(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate PR review velocity"""
        
        prs = metrics_data.get('pull_requests', [])
        if not prs:
            return {'avg_review_time_hours': 0, 'prs_with_reviews': 0, 'total_prs': 0}
            
        merged_prs = [pr for pr in prs if pr.get('merged_at')]
        
        if not merged_prs:
            return {'avg_review_time_hours': 0, 'prs_with_reviews': 0, 'total_prs': len(prs)}
            
        review_times = []
        
        for pr in merged_prs:
            try:
                created_at = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                merged_at = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                review_hours = (merged_at - created_at).total_seconds() / 3600
                review_times.append(review_hours)
            except (ValueError, TypeError):
                continue
                
        if review_times:
            avg_review_time = statistics.mean(review_times)
        else:
            avg_review_time = 0
            
        return {
            'avg_review_time_hours': avg_review_time,
            'prs_with_reviews': len(merged_prs),
            'total_prs': len(prs),
            'review_rate': len(merged_prs) / len(prs) if prs else 0
        }
        
    def _calculate_community_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall community engagement score"""
        
        # Simple weighted scoring
        diversity_score = analysis['contribution_diversity']['normalized_diversity']
        retention_score = analysis['contributor_retention']
        response_score = analysis['issue_response_time']['response_rate']
        review_score = analysis['pr_review_velocity']['review_rate']
        
        # Weights for different aspects
        weights = {
            'diversity': 0.25,
            'retention': 0.25,
            'response': 0.25,
            'review': 0.25
        }
        
        community_score = (
            diversity_score * weights['diversity'] +
            retention_score * weights['retention'] +
            response_score * weights['response'] +
            review_score * weights['review']
        )
        
        return community_score


class GrowthAnalyticsEngine:
    """
    Main analytics engine that combines all analysis components
    
    Provides:
    - Health score calculation
    - Trend analysis and forecasting
    - Anomaly detection
    - Community engagement analysis
    - Comprehensive reporting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize analyzers
        self.health_calculator = HealthScoreCalculator(
            self.config.get('health_score_weights')
        )
        self.trend_analyzer = TrendAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.engagement_analyzer = CommunityEngagementAnalyzer()
        
    def analyze_repository_growth(self, current_metrics: Dict[str, Any],
                                historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Comprehensive growth analysis for a repository"""
        
        analysis_results = {
            'repository': current_metrics.get('repository', 'unknown'),
            'analysis_timestamp': datetime.now().isoformat(),
            'health_score': None,
            'trend_analysis': [],
            'anomalies': [],
            'community_engagement': None,
            'recommendations': []
        }
        
        try:
            # Calculate health score
            if current_metrics:
                health_score = self.health_calculator.calculate_health_score(
                    current_metrics, historical_data
                )
                analysis_results['health_score'] = asdict(health_score)
                
            # Analyze trends if historical data available
            if historical_data and len(historical_data) >= 5:
                combined_data = historical_data + [current_metrics] if current_metrics else historical_data
                
                trends = self.trend_analyzer.analyze_trends(combined_data)
                analysis_results['trend_analysis'] = [asdict(trend) for trend in trends]
                
                anomalies = self.anomaly_detector.detect_anomalies(combined_data)
                analysis_results['anomalies'] = [asdict(anomaly) for anomaly in anomalies]
                
            # Analyze community engagement
            if current_metrics:
                engagement = self.engagement_analyzer.analyze_engagement(current_metrics)
                analysis_results['community_engagement'] = engagement
                
            # Generate recommendations
            recommendations = self._generate_recommendations(analysis_results)
            analysis_results['recommendations'] = recommendations
            
        except Exception as e:
            logger.error(f"Failed to complete analysis: {e}")
            analysis_results['error'] = str(e)
            
        return analysis_results
        
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        
        recommendations = []
        
        # Health score recommendations
        health_score = analysis_results.get('health_score')
        if health_score:
            overall_score = health_score.get('overall_score', 0)
            
            if overall_score < 0.3:
                recommendations.append("Repository health is low. Focus on increasing contributor activity and improving response times.")
            elif overall_score < 0.6:
                recommendations.append("Repository health is moderate. Consider implementing better review processes and issue triage.")
            else:
                recommendations.append("Repository health is strong. Continue current practices and consider mentoring other projects.")
                
            # Component-specific recommendations
            components = health_score.get('overall_score', 0)
            
        # Trend-based recommendations
        trends = analysis_results.get('trend_analysis', [])
        for trend in trends:
            if trend['trend_direction'] == 'decreasing':
                recommendations.append(f"Declining trend detected in {trend['metric_name']}. Consider investigating root causes.")
            elif trend['growth_rate'] < -5:  # More than 5% decline per period
                recommendations.append(f"Significant decline in {trend['metric_name']} ({trend['growth_rate']:.1f}% per period). Action may be needed.")
                
        # Anomaly-based recommendations
        anomalies = analysis_results.get('anomalies', [])
        high_severity_anomalies = [a for a in anomalies if a['severity'] == 'high']
        if high_severity_anomalies:
            for anomaly in high_severity_anomalies[:3]:  # Top 3 high severity
                recommendations.append(f"High severity anomaly detected in {anomaly['metric_name']}: {anomaly['description']}")
                
        # Community engagement recommendations
        engagement = analysis_results.get('community_engagement', {})
        if engagement:
            response_rate = engagement.get('issue_response_time', {}).get('response_rate', 0)
            if response_rate < 0.5:
                recommendations.append("Low issue response rate. Consider assigning maintainers to respond to new issues more quickly.")
                
            review_time = engagement.get('pr_review_velocity', {}).get('avg_review_time_hours', 0)
            if review_time > 72:  # More than 3 days
                recommendations.append("Slow PR review times. Consider adding more reviewers or setting SLAs.")
                
        return recommendations[:10]  # Limit to top 10 recommendations
        
    def get_performance_benchmark(self, repository_data: Dict[str, Any],
                                peer_repositories: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Compare repository performance against peers"""
        
        if not peer_repositories:
            # Use generic benchmarks
            benchmarks = {
                'health_score': {'excellent': 0.8, 'good': 0.6, 'fair': 0.4},
                'contributors_monthly': {'excellent': 20, 'good': 10, 'fair': 5},
                'pr_acceptance_rate': {'excellent': 0.9, 'good': 0.7, 'fair': 0.5},
                'issue_response_hours': {'excellent': 24, 'good': 48, 'fair': 168}
            }
            
            return {'benchmarks': benchmarks, 'comparison': 'generic'}
            
        # Compare against peer repositories
        benchmark_metrics = {}
        
        for metric in ['stargazers_count', 'forks_count', 'contributors_count']:
            values = [repo.get(metric, 0) for repo in peer_repositories if repo.get(metric, 0) > 0]
            if values:
                benchmark_metrics[metric] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0,
                    'percentiles': {
                        '25': np.percentile(values, 25),
                        '50': np.percentile(values, 50),
                        '75': np.percentile(values, 75),
                        '90': np.percentile(values, 90)
                    }
                }
                
        return {
            'benchmarks': benchmark_metrics,
            'comparison': 'peer_based',
            'peer_count': len(peer_repositories)
        }