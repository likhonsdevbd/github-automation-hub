"""
Anomaly Detection for Repository Growth Patterns

This module implements advanced anomaly detection algorithms to identify
unusual growth patterns, potential issues, or significant changes in repository metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import defaultdict, deque
import warnings

try:
    from scipy import stats
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy or sklearn not available, using simple anomaly detection")


@dataclass
class AnomalyResult:
    """Data class for anomaly detection results."""
    date: datetime
    metric: str
    value: float
    expected_value: Optional[float]
    anomaly_score: float
    severity: str
    description: str
    confidence: float
    recommendation: str


@dataclass
class AnomalyPattern:
    """Data class for detected anomaly patterns."""
    pattern_type: str
    start_date: datetime
    end_date: Optional[datetime]
    affected_metrics: List[str]
    severity: str
    confidence: float
    description: str
    impact_estimate: Optional[float]
    recommendations: List[str]


class AnomalyDetector:
    """
    Advanced anomaly detection system for repository growth metrics.
    
    Uses multiple detection methods including statistical tests,
    machine learning algorithms, and pattern recognition.
    """
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.baseline_stats = {}
        self.seasonal_patterns = {}
        self.recent_anomalies = deque(maxlen=100)  # Keep last 100 anomalies
        self.model_thresholds = {}
        
    def detect_anomalies(self, growth_data: List) -> Tuple[List[AnomalyResult], List[AnomalyPattern]]:
        """
        Detect anomalies in growth data using multiple methods.
        
        Args:
            growth_data: List of growth metrics
            
        Returns:
            Tuple of (individual_anomalies, anomaly_patterns)
        """
        if len(growth_data) < 5:
            return [], []
        
        df = pd.DataFrame([{
            'date': d.date,
            'stars': d.stars,
            'forks': d.forks,
            'watchers': d.watchers,
            'issues': d.issues,
            'pull_requests': d.pull_requests,
            'commits': d.commits
        } for d in growth_data])
        
        df = df.sort_values('date').reset_index(drop=True)
        
        # Calculate derived metrics
        df['star_fork_ratio'] = df['stars'] / (df['forks'] + 1)
        df['issue_pr_ratio'] = df['issues'] / (df['pull_requests'] + 1)
        df['activity_score'] = df['commits'] + df['pull_requests']
        
        # Calculate growth rates
        metrics = ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']
        for metric in metrics:
            df[f'{metric}_growth_rate'] = df[metric].pct_change()
        
        # Detect individual anomalies
        anomalies = []
        anomalies.extend(self._detect_statistical_anomalies(df))
        anomalies.extend(self._detect_trend_anomalies(df))
        anomalies.extend(self._detect_seasonal_anomalies(df))
        anomalies.extend(self._detect_ml_anomalies(df))
        
        # Detect anomaly patterns
        patterns = self._detect_anomaly_patterns(anomalies, df)
        
        # Store recent anomalies for trend analysis
        self.recent_anomalies.extend(anomalies)
        
        return anomalies, patterns
    
    def _detect_statistical_anomalies(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies using statistical methods (Z-score, IQR)."""
        anomalies = []
        metrics = ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']
        
        for metric in metrics:
            values = df[metric].values
            
            # Z-score method
            z_scores = np.abs(stats.zscore(values)) if SCIPY_AVAILABLE else np.abs((values - np.mean(values)) / np.std(values))
            z_threshold = 2.5
            
            for i, (date, value, z_score) in enumerate(zip(df['date'], values, z_scores)):
                if z_score > z_threshold and not pd.isna(z_score):
                    severity = self._classify_anomaly_severity(z_score, 'high')
                    
                    anomaly = AnomalyResult(
                        date=date,
                        metric=metric,
                        value=value,
                        expected_value=np.mean(values),
                        anomaly_score=z_score,
                        severity=severity,
                        description=f"Statistical anomaly in {metric}: {value:.2f} (Z-score: {z_score:.2f})",
                        confidence=min(z_score / 4.0, 1.0),
                        recommendation=self._get_statistical_recommendation(metric, severity)
                    )
                    anomalies.append(anomaly)
            
            # IQR method (more robust for non-normal distributions)
            Q1 = np.percentile(values, 25)
            Q3 = np.percentile(values, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            for i, (date, value) in enumerate(zip(df['date'], values)):
                if value < lower_bound or value > upper_bound:
                    # Check if this anomaly was already detected by Z-score
                    is_duplicate = any(
                        a.date == date and a.metric == metric for a in anomalies
                    )
                    
                    if not is_duplicate:
                        # Calculate distance from bounds
                        distance = max(value - upper_bound, lower_bound - value, 0)
                        distance_ratio = distance / IQR if IQR > 0 else 0
                        severity = self._classify_anomaly_severity(distance_ratio, 'medium')
                        
                        anomaly = AnomalyResult(
                            date=date,
                            metric=metric,
                            value=value,
                            expected_value=(Q1 + Q3) / 2,
                            anomaly_score=distance_ratio,
                            severity=severity,
                            description=f"IQR anomaly in {metric}: {value:.2f} (outside [{lower_bound:.2f}, {upper_bound:.2f}])",
                            confidence=min(distance_ratio / 2.0, 1.0),
                            recommendation=self._get_statistical_recommendation(metric, severity)
                        )
                        anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_trend_anomalies(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies in growth trends."""
        anomalies = []
        metrics = ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']
        
        for metric in metrics:
            growth_col = f'{metric}_growth_rate'
            if growth_col not in df.columns:
                continue
                
            growth_rates = df[growth_col].dropna().values
            
            if len(growth_rates) < 3:
                continue
            
            # Detect sudden growth spikes
            for i, (date, growth_rate) in enumerate(zip(df['date'], df[growth_col])):
                if pd.isna(growth_rate):
                    continue
                
                # Calculate rolling mean and std for recent trend
                window = min(7, i)
                if window > 2:
                    recent_rates = df[growth_col].iloc[max(0, i-window):i].dropna()
                    if len(recent_rates) > 1:
                        recent_mean = np.mean(recent_rates)
                        recent_std = np.std(recent_rates)
                        
                        # Z-score for growth rate anomaly
                        if recent_std > 0:
                            z_score = abs(growth_rate - recent_mean) / recent_std
                            
                            # Threshold for growth anomalies (more lenient than value anomalies)
                            growth_threshold = 3.0
                            
                            if z_score > growth_threshold:
                                severity = self._classify_anomaly_severity(z_score, 'high')
                                
                                anomaly = AnomalyResult(
                                    date=date,
                                    metric=f"{metric}_growth",
                                    value=growth_rate,
                                    expected_value=recent_mean,
                                    anomaly_score=z_score,
                                    severity=severity,
                                    description=f"Growth anomaly in {metric}: {growth_rate:.1%} (Z-score: {z_score:.2f})",
                                    confidence=min(z_score / 4.0, 1.0),
                                    recommendation=self._get_growth_recommendation(metric, severity, growth_rate)
                                )
                                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_seasonal_anomalies(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies against seasonal patterns."""
        anomalies = []
        
        # Create seasonal baselines
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        df['hour'] = pd.to_datetime(df['date']).dt.hour
        df['month'] = pd.to_datetime(df['date']).dt.month
        
        metrics = ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']
        
        for metric in metrics:
            # Calculate seasonal baselines
            dow_baseline = df.groupby('day_of_week')[metric].mean()
            month_baseline = df.groupby('month')[metric].mean()
            
            for i, row in df.iterrows():
                date = row['date']
                value = row[metric]
                
                # Expected value based on seasonal pattern
                expected_dow = dow_baseline.get(row['day_of_week'], value)
                expected_month = month_baseline.get(row['month'], value)
                expected_value = (expected_dow + expected_month) / 2
                
                if expected_value > 0:
                    relative_deviation = abs(value - expected_value) / expected_value
                    
                    # Threshold for seasonal anomalies
                    seasonal_threshold = 0.5  # 50% deviation
                    
                    if relative_deviation > seasonal_threshold:
                        severity = self._classify_anomaly_severity(relative_deviation, 'medium')
                        
                        anomaly = AnomalyResult(
                            date=date,
                            metric=f"{metric}_seasonal",
                            value=value,
                            expected_value=expected_value,
                            anomaly_score=relative_deviation,
                            severity=severity,
                            description=f"Seasonal anomaly in {metric}: {value:.2f} vs expected {expected_value:.2f}",
                            confidence=min(relative_deviation, 1.0),
                            recommendation=self._get_seasonal_recommendation(metric, severity, relative_deviation)
                        )
                        anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_ml_anomalies(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies using machine learning methods."""
        anomalies = []
        
        if not SCIPY_AVAILABLE or len(df) < 10:
            return anomalies
        
        metrics = ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']
        
        for metric in metrics:
            try:
                # Prepare data for ML anomaly detection
                feature_cols = ['day_of_week', 'month', 'hour']
                X = df[feature_cols].values
                y = df[metric].values.reshape(-1, 1)
                
                # Combine features and target
                X_combined = np.column_stack([X, y])
                
                # Remove any rows with NaN
                valid_mask = ~np.isnan(X_combined).any(axis=1)
                if not np.any(valid_mask):
                    continue
                
                X_clean = X_combined[valid_mask]
                dates_clean = df['date'][valid_mask]
                values_clean = df[metric][valid_mask]
                
                if len(X_clean) < 5:
                    continue
                
                # Standardize features
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X_clean)
                
                # Isolation Forest
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomaly_labels = iso_forest.fit_predict(X_scaled)
                
                # DBSCAN for clustering-based anomaly detection
                dbscan = DBSCAN(eps=0.5, min_samples=3)
                cluster_labels = dbscan.fit_predict(X_scaled)
                
                # Combine results
                for i, (date, value, iso_label, cluster_label) in enumerate(zip(dates_clean, values_clean, anomaly_labels, cluster_labels)):
                    if iso_label == -1:  # Isolated Forest anomaly
                        severity = 'high'
                        
                        anomaly = AnomalyResult(
                            date=date,
                            metric=f"{metric}_ml",
                            value=value,
                            expected_value=np.median(values_clean),
                            anomaly_score=1.0,
                            severity=severity,
                            description=f"ML anomaly in {metric}: {value:.2f} (isolated by algorithm)",
                            confidence=0.8,
                            recommendation=self._get_ml_recommendation(metric, severity)
                        )
                        anomalies.append(anomaly)
                    
                    elif cluster_label == -1:  # DBSCAN outlier
                        severity = 'medium'
                        
                        anomaly = AnomalyResult(
                            date=date,
                            metric=f"{metric}_clustering",
                            value=value,
                            expected_value=np.median(values_clean),
                            anomaly_score=0.7,
                            severity=severity,
                            description=f"Clustering anomaly in {metric}: {value:.2f} (outlier cluster)",
                            confidence=0.6,
                            recommendation=self._get_ml_recommendation(metric, severity)
                        )
                        anomalies.append(anomaly)
                        
            except Exception as e:
                warnings.warn(f"ML anomaly detection failed for {metric}: {str(e)}")
                continue
        
        return anomalies
    
    def _detect_anomaly_patterns(self, anomalies: List[AnomalyResult], df: pd.DataFrame) -> List[AnomalyPattern]:
        """Detect patterns across multiple anomalies."""
        patterns = []
        
        if not anomalies:
            return patterns
        
        # Group anomalies by type and time proximity
        anomaly_groups = self._group_anomalies_by_proximity(anomalies)
        
        for group in anomaly_groups:
            if len(group) >= 3:  # Need at least 3 anomalies to form a pattern
                pattern = self._create_anomaly_pattern(group)
                if pattern:
                    patterns.append(pattern)
        
        # Detect specific patterns
        patterns.extend(self._detect_repeated_spikes(anomalies, df))
        patterns.extend(self._detect_sustained_anomalies(anomalies))
        patterns.extend(self._detect_metric_interaction_anomalies(anomalies))
        
        return patterns
    
    def _group_anomalies_by_proximity(self, anomalies: List[AnomalyResult], 
                                     max_days_apart: int = 3) -> List[List[AnomalyResult]]:
        """Group anomalies that occur within a specified time window."""
        if not anomalies:
            return []
        
        # Sort by date
        sorted_anomalies = sorted(anomalies, key=lambda x: x.date)
        groups = []
        current_group = [sorted_anomalies[0]]
        
        for i in range(1, len(sorted_anomalies)):
            current = sorted_anomalies[i]
            last_in_group = current_group[-1]
            
            if (current.date - last_in_group.date).days <= max_days_apart:
                current_group.append(current)
            else:
                if len(current_group) >= 2:  # Only keep groups with multiple anomalies
                    groups.append(current_group)
                current_group = [current]
        
        # Add the last group if it has sufficient anomalies
        if len(current_group) >= 2:
            groups.append(current_group)
        
        return groups
    
    def _create_anomaly_pattern(self, anomaly_group: List[AnomalyResult]) -> Optional[AnomalyPattern]:
        """Create an anomaly pattern from a group of related anomalies."""
        if not anomaly_group:
            return None
        
        # Analyze the group characteristics
        metrics_affected = list(set(a.metric for a in anomaly_group))
        start_date = min(a.date for a in anomaly_group)
        end_date = max(a.date for a in anomaly_group)
        avg_severity = np.mean([1 if a.severity == 'high' else 0.5 for a in anomaly_group])
        
        # Determine pattern type
        if len(anomaly_group) >= 5:
            pattern_type = "anomaly_cluster"
            description = f"Cluster of {len(anomaly_group)} anomalies affecting {len(metrics_affected)} metrics"
        elif len(set(a.date for a in anomaly_group)) == 1:
            pattern_type = "multi_metric_spike"
            description = f"Simultaneous anomalies in {len(metrics_affected)} metrics"
        else:
            pattern_type = "anomaly_sequence"
            description = f"Sequence of {len(anomaly_group)} anomalies over {(end_date - start_date).days} days"
        
        # Calculate impact estimate
        total_impact = sum(a.anomaly_score for a in anomaly_group)
        
        recommendations = []
        if len(metrics_affected) > 2:
            recommendations.append("Multiple metrics affected - investigate systemic changes")
        if avg_severity > 0.7:
            recommendations.append("High severity pattern detected - immediate attention recommended")
        recommendations.append("Review recent commits, releases, or external factors")
        
        return AnomalyPattern(
            pattern_type=pattern_type,
            start_date=start_date,
            end_date=end_date,
            affected_metrics=metrics_affected,
            severity='high' if avg_severity > 0.7 else 'medium',
            confidence=len(anomaly_group) / 10.0,  # Higher confidence with more anomalies
            description=description,
            impact_estimate=total_impact,
            recommendations=recommendations
        )
    
    def _detect_repeated_spikes(self, anomalies: List[AnomalyResult], 
                              df: pd.DataFrame) -> List[AnomalyPattern]:
        """Detect repeated spikes in the same metric."""
        patterns = []
        
        # Group anomalies by metric
        metric_anomalies = defaultdict(list)
        for anomaly in anomalies:
            # Extract base metric name (remove suffix)
            base_metric = anomaly.metric.split('_')[0]
            if base_metric in ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']:
                metric_anomalies[base_metric].append(anomaly)
        
        for metric, metric_anomalies_list in metric_anomalies.items():
            if len(metric_anomalies_list) >= 3:
                # Check for repeated spikes (anomalies on different days)
                spike_dates = sorted(set(a.date for a in metric_anomalies_list))
                
                if len(spike_dates) >= 3:
                    # Check if spikes are somewhat regular
                    gaps = [spike_dates[i+1] - spike_dates[i] for i in range(len(spike_dates)-1)]
                    avg_gap = np.mean([gap.days for gap in gaps])
                    
                    if 3 <= avg_gap <= 30:  # Spikes roughly every 3-30 days
                        pattern = AnomalyPattern(
                            pattern_type="repeated_spikes",
                            start_date=spike_dates[0],
                            end_date=spike_dates[-1],
                            affected_metrics=[metric],
                            severity='medium',
                            confidence=0.8,
                            description=f"Repeated spikes in {metric} every ~{avg_gap:.1f} days",
                            impact_estimate=sum(a.anomaly_score for a in metric_anomalies_list),
                            recommendations=[
                                f"Regular spikes in {metric} detected - investigate underlying causes",
                                "Consider if these are related to release cycles or external events",
                                "Monitor for trend changes or external factors"
                            ]
                        )
                        patterns.append(pattern)
        
        return patterns
    
    def _detect_sustained_anomalies(self, anomalies: List[AnomalyResult]) -> List[AnomalyPattern]:
        """Detect sustained anomalies over longer periods."""
        patterns = []
        
        if not anomalies:
            return patterns
        
        # Group consecutive anomalies
        sorted_anomalies = sorted(anomalies, key=lambda x: x.date)
        
        current_sequence = [sorted_anomalies[0]]
        
        for i in range(1, len(sorted_anomalies)):
            current = sorted_anomalies[i]
            last = current_sequence[-1]
            
            # Check if anomalies are consecutive (within 1 day)
            if (current.date - last.date).days <= 1:
                current_sequence.append(current)
            else:
                # Process the completed sequence
                if len(current_sequence) >= 3:  # At least 3 consecutive days
                    sustained_pattern = self._create_sustained_pattern(current_sequence)
                    if sustained_pattern:
                        patterns.append(sustained_pattern)
                
                current_sequence = [current]
        
        # Process the last sequence
        if len(current_sequence) >= 3:
            sustained_pattern = self._create_sustained_pattern(current_sequence)
            if sustained_pattern:
                patterns.append(sustained_pattern)
        
        return patterns
    
    def _create_sustained_pattern(self, sequence: List[AnomalyResult]) -> Optional[AnomalyPattern]:
        """Create a pattern for sustained anomalies."""
        if len(sequence) < 3:
            return None
        
        metrics_affected = list(set(a.metric for a in sequence))
        start_date = sequence[0].date
        end_date = sequence[-1].date
        duration = (end_date - start_date).days + 1
        
        # Only consider sustained patterns that last at least 3 days
        if duration < 3:
            return None
        
        avg_severity = np.mean([1 if a.severity == 'high' else 0.5 for a in sequence])
        
        return AnomalyPattern(
            pattern_type="sustained_anomaly",
            start_date=start_date,
            end_date=end_date,
            affected_metrics=metrics_affected,
            severity='high' if avg_severity > 0.6 else 'medium',
            confidence=min(len(sequence) / 10.0, 1.0),
            description=f"Sustained anomalies lasting {duration} days in {len(metrics_affected)} metrics",
            impact_estimate=sum(a.anomaly_score for a in sequence) / duration,
            recommendations=[
                f"Sustained anomalies detected - investigate prolonged causes",
                "Check for ongoing infrastructure issues or external factors",
                "Consider temporary measures to stabilize growth"
            ]
        )
    
    def _detect_metric_interaction_anomalies(self, anomalies: List[AnomalyResult]) -> List[AnomalyPattern]:
        """Detect anomalies where related metrics behave unusually."""
        patterns = []
        
        # Define metric relationships
        relationships = {
            'stars': ['forks', 'watchers'],
            'forks': ['stars'],
            'watchers': ['stars'],
            'issues': ['pull_requests'],
            'pull_requests': ['commits', 'issues'],
            'commits': ['pull_requests']
        }
        
        # Group anomalies by date to find simultaneous but related anomalies
        date_anomalies = defaultdict(list)
        for anomaly in anomalies:
            base_metric = anomaly.metric.split('_')[0]
            if base_metric in relationships:
                date_anomalies[anomaly.date].append((base_metric, anomaly))
        
        for date, day_anomalies in date_anomalies.items():
            if len(day_anomalies) >= 2:
                metrics_involved = [m[0] for m in day_anomalies]
                
                # Check for related metrics
                related_pairs = []
                for i, (metric1, anomaly1) in enumerate(day_anomalies):
                    for j, (metric2, anomaly2) in enumerate(day_anomalies):
                        if i < j and metric2 in relationships.get(metric1, []):
                            related_pairs.append((metric1, metric2, anomaly1, anomaly2))
                
                if related_pairs:
                    pattern = AnomalyPattern(
                        pattern_type="metric_interaction",
                        start_date=date,
                        end_date=date,
                        affected_metrics=list(set(metrics_involved)),
                        severity='medium',
                        confidence=len(related_pairs) / 3.0,
                        description=f"Related metrics showing simultaneous anomalies: {', '.join(metrics_involved)}",
                        impact_estimate=sum(a[2].anomaly_score + a[3].anomaly_score for a in related_pairs) / len(related_pairs),
                        recommendations=[
                            "Related metrics showing anomalies - investigate causal relationships",
                            "Check if changes in one metric are driving changes in others",
                            "Consider systematic factors affecting multiple related metrics"
                        ]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _classify_anomaly_severity(self, score: float, default: str) -> str:
        """Classify anomaly severity based on score."""
        if score > 4.0:
            return 'critical'
        elif score > 3.0:
            return 'high'
        elif score > 2.0:
            return 'medium'
        else:
            return 'low'
    
    def _get_statistical_recommendation(self, metric: str, severity: str) -> str:
        """Get recommendation for statistical anomalies."""
        base_recommendations = {
            'stars': 'Monitor for sudden changes in repository visibility or external factors',
            'forks': 'Check for viral content, marketing campaigns, or influencer mentions',
            'watchers': 'Review community engagement and notification preferences',
            'issues': 'Investigate bug reports, feature requests, or community support needs',
            'pull_requests': 'Analyze development activity and code review processes',
            'commits': 'Review development workflow and commit patterns'
        }
        
        severity_addons = {
            'critical': 'URGENT: Immediate investigation required',
            'high': 'High priority investigation recommended',
            'medium': 'Monitor closely for pattern continuation',
            'low': 'Standard monitoring recommended'
        }
        
        base = base_recommendations.get(metric, 'Monitor metric for continued anomalies')
        addon = severity_addons.get(severity, 'Monitor for changes')
        
        return f"{base}. {addon}"
    
    def _get_growth_recommendation(self, metric: str, severity: str, growth_rate: float) -> str:
        """Get recommendation for growth anomalies."""
        if growth_rate > 0.5:  # 50% growth
            return f"Rapid growth in {metric} detected. Investigate viral factors, marketing campaigns, or external attention."
        elif growth_rate < -0.3:  # 30% decline
            return f"Significant decline in {metric}. Check for issues, downtime, or negative external factors."
        else:
            return f"Unusual growth pattern in {metric}. Review recent changes and external factors."
    
    def _get_seasonal_recommendation(self, metric: str, severity: str, deviation: float) -> str:
        """Get recommendation for seasonal anomalies."""
        return f"Seasonal pattern deviation in {metric}. This may indicate unusual external factors or changing user behavior patterns."
    
    def _get_ml_recommendation(self, metric: str, severity: str) -> str:
        """Get recommendation for ML-detected anomalies."""
        return f"Machine learning algorithm detected unusual pattern in {metric}. Review recent changes and external factors for explanation."
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """
        Get a summary of anomaly detection results.
        
        Returns:
            Dictionary containing anomaly summary statistics
        """
        if not self.recent_anomalies:
            return {"error": "No anomalies detected yet"}
        
        # Convert deque to list for analysis
        recent_anomalies = list(self.recent_anomalies)
        
        # Basic statistics
        total_anomalies = len(recent_anomalies)
        metrics_affected = list(set(a.metric for a in recent_anomalies))
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for anomaly in recent_anomalies:
            severity_counts[anomaly.severity] += 1
        
        # Date range
        if recent_anomalies:
            date_range = {
                'earliest': min(a.date for a in recent_anomalies).isoformat(),
                'latest': max(a.date for a in recent_anomalies).isoformat(),
                'span_days': (max(a.date for a in recent_anomalies) - min(a.date for a in recent_anomalies)).days
            }
        else:
            date_range = {}
        
        # Top affected metrics
        metric_counts = defaultdict(int)
        for anomaly in recent_anomalies:
            base_metric = anomaly.metric.split('_')[0]
            metric_counts[base_metric] += 1
        
        top_metrics = sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_anomalies': total_anomalies,
            'metrics_affected': len(metrics_affected),
            'severity_breakdown': severity_counts,
            'affected_metric_list': metrics_affected,
            'date_range': date_range,
            'top_affected_metrics': top_metrics,
            'average_anomaly_score': np.mean([a.anomaly_score for a in recent_anomalies]) if recent_anomalies else 0
        }