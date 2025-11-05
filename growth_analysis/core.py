"""
Core Growth Analysis Module

This module contains the fundamental algorithms and data structures for
analyzing repository growth patterns and metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import statistics
from scipy import stats
import warnings


@dataclass
class GrowthMetrics:
    """Data class to store various growth metrics."""
    date: datetime
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    issues: int = 0
    pull_requests: int = 0
    commits: int = 0
    contributors: int = 0
    network_size: int = 0
    subscribers: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'date': self.date.isoformat(),
            'stars': self.stars,
            'forks': self.forks,
            'watchers': self.watchers,
            'issues': self.issues,
            'pull_requests': self.pull_requests,
            'commits': self.commits,
            'contributors': self.contributors,
            'network_size': self.network_size,
            'subscribers': self.subscribers
        }


@dataclass 
class GrowthPattern:
    """Data class to store detected growth patterns."""
    pattern_type: str
    confidence: float
    description: str
    start_date: datetime
    end_date: Optional[datetime]
    metrics: List[str]
    statistics: Dict[str, float]
    recommendations: List[str]


class GrowthAnalyzer:
    """
    Core growth analysis engine that implements pattern recognition
    and statistical analysis for repository growth data.
    """
    
    def __init__(self):
        self.growth_data = []
        self.patterns = []
        self.baseline_metrics = {}
        
    def add_growth_data(self, data: List[GrowthMetrics]) -> None:
        """
        Add growth metrics data to the analyzer.
        
        Args:
            data: List of GrowthMetrics objects ordered by date
        """
        # Sort data by date
        sorted_data = sorted(data, key=lambda x: x.date)
        self.growth_data = sorted_data
        self._calculate_baseline_metrics()
        
    def analyze_growth_patterns(self) -> List[GrowthPattern]:
        """
        Analyze growth patterns in the data and detect significant trends.
        
        Returns:
            List of detected growth patterns
        """
        if len(self.growth_data) < 2:
            return []
            
        self.patterns = []
        df = pd.DataFrame([d.to_dict() for d in self.growth_data])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Analyze each metric for patterns
        metrics_to_analyze = ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']
        
        for metric in metrics_to_analyze:
            if metric in df.columns:
                patterns = self._detect_patterns(df, metric)
                self.patterns.extend(patterns)
                
        return self.patterns
    
    def _detect_patterns(self, df: pd.DataFrame, metric: str) -> List[GrowthPattern]:
        """Detect specific patterns in a metric time series."""
        patterns = []
        
        # Calculate day-over-day growth rates
        df[f'{metric}_growth_rate'] = df[metric].pct_change()
        
        # Detect exponential growth
        exp_pattern = self._detect_exponential_growth(df, metric)
        if exp_pattern:
            patterns.append(exp_pattern)
            
        # Detect linear growth
        linear_pattern = self._detect_linear_growth(df, metric)
        if linear_pattern:
            patterns.append(linear_pattern)
            
        # Detect seasonal patterns
        seasonal_patterns = self._detect_seasonal_patterns(df, metric)
        patterns.extend(seasonal_patterns)
        
        # Detect plateau periods
        plateau_pattern = self._detect_plateau_periods(df, metric)
        if plateau_pattern:
            patterns.append(plateau_pattern)
            
        # Detect growth acceleration/deceleration
        accel_pattern = self._detect_acceleration(df, metric)
        if accel_pattern:
            patterns.append(accel_pattern)
            
        return patterns
    
    def _detect_exponential_growth(self, df: pd.DataFrame, metric: str) -> Optional[GrowthPattern]:
        """Detect exponential growth patterns."""
        try:
            values = df[metric].values
            dates = pd.to_datetime(df['date']).values
            
            # Remove zero and negative values for log transform
            positive_values = values[values > 0]
            positive_dates = dates[values > 0]
            
            if len(positive_values) < 5:
                return None
                
            log_values = np.log(positive_values)
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                range(len(log_values)), log_values
            )
            
            # Check if exponential (high R-squared)
            if r_value ** 2 > 0.8 and p_value < 0.05 and slope > 0:
                growth_rate = (np.exp(slope) - 1) * 100  # Convert to percentage
                
                return GrowthPattern(
                    pattern_type="exponential_growth",
                    confidence=r_value ** 2,
                    description=f"Exponential growth detected with {growth_rate:.2f}% daily growth rate",
                    start_date=pd.to_datetime(positive_dates[0]),
                    end_date=pd.to_datetime(positive_dates[-1]),
                    metrics=[metric],
                    statistics={
                        'growth_rate': growth_rate,
                        'r_squared': r_value ** 2,
                        'p_value': p_value,
                        'daily_multiplier': np.exp(slope)
                    },
                    recommendations=[
                        f"Exponential growth in {metric} - monitor for sustainable growth",
                        "Consider infrastructure scaling to handle increased load",
                        "Maintain momentum with consistent releases and community engagement"
                    ]
                )
        except Exception as e:
            warnings.warn(f"Error detecting exponential growth in {metric}: {str(e)}")
            
        return None
    
    def _detect_linear_growth(self, df: pd.DataFrame, metric: str) -> Optional[GrowthPattern]:
        """Detect linear growth patterns."""
        try:
            values = df[metric].values
            x = np.arange(len(values))
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Check if linear with good fit
            if r_value ** 2 > 0.85 and p_value < 0.05:
                return GrowthPattern(
                    pattern_type="linear_growth",
                    confidence=r_value ** 2,
                    description=f"Steady linear growth of {slope:.2f} {metric} per day",
                    start_date=pd.to_datetime(df['date'].iloc[0]),
                    end_date=pd.to_datetime(df['date'].iloc[-1]),
                    metrics=[metric],
                    statistics={
                        'daily_increase': slope,
                        'r_squared': r_value ** 2,
                        'p_value': p_value,
                        'total_growth': values[-1] - values[0]
                    },
                    recommendations=[
                        f"Consistent linear growth in {metric} - maintain current strategy",
                        "Consider optimization opportunities to accelerate growth"
                    ]
                )
        except Exception as e:
            warnings.warn(f"Error detecting linear growth in {metric}: {str(e)}")
            
        return None
    
    def _detect_seasonal_patterns(self, df: pd.DataFrame, metric: str) -> List[GrowthPattern]:
        """Detect seasonal or cyclical patterns."""
        patterns = []
        try:
            # Group by day of week and hour
            df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
            df['hour'] = pd.to_datetime(df['date']).dt.hour
            
            # Check for weekly patterns
            weekly_stats = df.groupby('day_of_week')[f'{metric}_growth_rate'].agg(['mean', 'std'])
            weekly_variance = weekly_stats['mean'].var()
            
            if weekly_variance > 0.01:  # Threshold for significant variation
                peak_day = weekly_stats['mean'].idxmax()
                low_day = weekly_stats['mean'].idxmin()
                
                patterns.append(GrowthPattern(
                    pattern_type="weekly_seasonality",
                    confidence=1 - (weekly_variance / (weekly_variance + 0.01)),
                    description=f"Weekly pattern detected - peak on day {peak_day}, low on day {low_day}",
                    start_date=pd.to_datetime(df['date'].min()),
                    end_date=pd.to_datetime(df['date'].max()),
                    metrics=[metric],
                    statistics={
                        'peak_day': peak_day,
                        'low_day': low_day,
                        'variance': weekly_variance,
                        'peak_mean': weekly_stats.loc[peak_day, 'mean'],
                        'low_mean': weekly_stats.loc[low_day, 'mean']
                    },
                    recommendations=[
                        "Optimize release schedule based on weekly patterns",
                        "Plan marketing efforts around peak activity days"
                    ]
                ))
                
        except Exception as e:
            warnings.warn(f"Error detecting seasonal patterns in {metric}: {str(e)}")
            
        return patterns
    
    def _detect_plateau_periods(self, df: pd.DataFrame, metric: str) -> Optional[GrowthPattern]:
        """Detect periods of minimal growth (plateaus)."""
        try:
            # Calculate rolling variance to detect plateaus
            window_size = min(7, len(df) // 4)  # Adaptive window
            if window_size < 2:
                return None
                
            df[f'{metric}_rolling_std'] = df[metric].rolling(window=window_size).std()
            
            # Find periods with low variance
            low_variance_threshold = df[f'{metric}_rolling_std'].quantile(0.25)
            plateau_mask = df[f'{metric}_rolling_std'] <= low_variance_threshold
            
            if plateau_mask.sum() > window_size:
                plateau_start = df[plateau_mask].index[0]
                plateau_end = df[plateau_mask].index[-1]
                
                if plateau_end - plateau_start > window_size:
                    return GrowthPattern(
                        pattern_type="growth_plateau",
                        confidence=1 - (df.loc[plateau_mask, f'{metric}_rolling_std'].mean() / 
                                      df[f'{metric}_rolling_std'].mean()),
                        description=f"Growth plateau detected lasting {(plateau_end - plateau_start + 1)} periods",
                        start_date=pd.to_datetime(df.loc[plateau_start, 'date']),
                        end_date=pd.to_datetime(df.loc[plateau_end, 'date']),
                        metrics=[metric],
                        statistics={
                            'plateau_duration': plateau_end - plateau_start + 1,
                            'avg_variance': df.loc[plateau_mask, f'{metric}_rolling_std'].mean(),
                            'total_variance': df[f'{metric}_rolling_std'].mean()
                        },
                        recommendations=[
                            "Growth plateau detected - consider new initiatives",
                            "Review strategy and identify growth bottlenecks",
                            "Plan feature releases or marketing campaigns to break plateau"
                        ]
                    )
        except Exception as e:
            warnings.warn(f"Error detecting plateaus in {metric}: {str(e)}")
            
        return None
    
    def _detect_acceleration(self, df: pd.DataFrame, metric: str) -> Optional[GrowthPattern]:
        """Detect growth acceleration or deceleration."""
        try:
            growth_rates = df[f'{metric}_growth_rate'].dropna()
            
            if len(growth_rates) < 3:
                return None
                
            # Split data into two halves and compare growth rates
            mid_point = len(growth_rates) // 2
            first_half_mean = growth_rates[:mid_point].mean()
            second_half_mean = growth_rates[mid_point:].mean()
            
            # Calculate acceleration
            acceleration = second_half_mean - first_half_mean
            acceleration_threshold = 0.05  # 5% change threshold
            
            if abs(acceleration) > acceleration_threshold:
                pattern_type = "growth_acceleration" if acceleration > 0 else "growth_deceleration"
                confidence = min(abs(acceleration) / 0.1, 1.0)  # Normalize confidence
                
                return GrowthPattern(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    description=f"Growth {'acceleration' if acceleration > 0 else 'deceleration'} of {acceleration:.3f}",
                    start_date=pd.to_datetime(df['date'].iloc[mid_point]),
                    end_date=pd.to_datetime(df['date'].iloc[-1]),
                    metrics=[metric],
                    statistics={
                        'acceleration': acceleration,
                        'first_half_mean': first_half_mean,
                        'second_half_mean': second_half_mean,
                        'change_percentage': (acceleration / first_half_mean) * 100
                    },
                    recommendations=[
                        "Growth pattern change detected - investigate underlying factors",
                        "Monitor for trend continuation or reversal"
                    ]
                )
        except Exception as e:
            warnings.warn(f"Error detecting acceleration in {metric}: {str(e)}")
            
        return None
    
    def _calculate_baseline_metrics(self) -> None:
        """Calculate baseline metrics from historical data."""
        if len(self.growth_data) < 2:
            return
            
        metrics_data = {}
        
        for metric_name in ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']:
            values = [getattr(d, metric_name) for d in self.growth_data]
            if len(values) > 0:
                metrics_data[metric_name] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values),
                    'growth_rate': (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
                }
                
        self.baseline_metrics = metrics_data
    
    def get_growth_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of growth analysis.
        
        Returns:
            Dictionary containing growth summary statistics
        """
        if not self.growth_data:
            return {"error": "No growth data available"}
            
        summary = {
            'analysis_date': datetime.now().isoformat(),
            'data_period': {
                'start': self.growth_data[0].date.isoformat(),
                'end': self.growth_data[-1].date.isoformat(),
                'duration_days': (self.growth_data[-1].date - self.growth_data[0].date).days
            },
            'patterns_detected': len(self.patterns),
            'baseline_metrics': self.baseline_metrics,
            'pattern_types': list(set(p.pattern_type for p in self.patterns)),
            'recommendations_count': sum(len(p.recommendations) for p in self.patterns)
        }
        
        # Add recent growth rates for key metrics
        recent_data = self.growth_data[-min(7, len(self.growth_data)):]
        
        for metric_name in ['stars', 'forks', 'watchers']:
            if len(recent_data) >= 2:
                current = getattr(recent_data[-1], metric_name)
                previous = getattr(recent_data[-2], metric_name)
                if previous > 0:
                    growth_rate = ((current - previous) / previous) * 100
                    summary[f'{metric_name}_recent_growth_rate'] = growth_rate
        
        return summary