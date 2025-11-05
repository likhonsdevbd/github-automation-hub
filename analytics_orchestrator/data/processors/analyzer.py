"""
Data analysis processor for analytics pipeline
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import statistics
import math
from collections import defaultdict, deque


class AnalysisType(Enum):
    """Analysis type enumeration"""
    TREND = "trend"
    ANOMALY = "anomaly"
    PATTERN = "pattern"
    CORRELATION = "correlation"
    FORECAST = "forecast"
    STATISTICAL = "statistical"
    PERFORMANCE = "performance"


@dataclass
class AnalysisResult:
    """Analysis result structure"""
    analysis_type: AnalysisType
    metric_name: str
    source: str
    result: Dict[str, Any]
    confidence: float
    timestamp: datetime
    processing_time: float


class DataAnalyzer:
    """
    Data analysis processor that performs various analytical operations on data points
    """
    
    def __init__(self):
        """Initialize data analyzer"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Data analyzer initialized")
        
        # Analysis functions
        self.analysis_functions = {
            AnalysisType.TREND: self._analyze_trends,
            AnalysisType.ANOMALY: self._detect_anomalies,
            AnalysisType.PATTERN: self._detect_patterns,
            AnalysisType.CORRELATION: self._analyze_correlation,
            AnalysisType.FORECAST: self._forecast_values,
            AnalysisType.STATISTICAL: self._statistical_analysis,
            AnalysisType.PERFORMANCE: self._performance_analysis
        }
        
        # Anomaly detection parameters
        self.anomaly_params = {
            'z_score_threshold': 3.0,
            'iqr_multiplier': 1.5,
            'window_size': 10,
            'min_points': 5
        }
        
        # Trend analysis parameters
        self.trend_params = {
            'min_points': 3,
            'trend_threshold': 0.1,
            'seasonality_period': 24  # hours
        }
    
    async def analyze(self, data_points: List) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on data points
        
        Args:
            data_points: List of data point objects
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            if not data_points:
                return {}
            
            start_time = datetime.utcnow()
            analysis_results = {}
            
            # Group data by metric and source
            grouped_data = self._group_data_points(data_points)
            
            # Perform different types of analysis
            for (metric_name, source), points in grouped_data.items():
                try:
                    # Trend analysis
                    trend_result = await self._analyze_trends(metric_name, source, points)
                    if trend_result:
                        analysis_results[f"{source}_{metric_name}_trend"] = trend_result
                    
                    # Anomaly detection
                    anomaly_result = await self._detect_anomalies(metric_name, source, points)
                    if anomaly_result:
                        analysis_results[f"{source}_{metric_name}_anomalies"] = anomaly_result
                    
                    # Pattern detection
                    pattern_result = await self._detect_patterns(metric_name, source, points)
                    if pattern_result:
                        analysis_results[f"{source}_{metric_name}_patterns"] = pattern_result
                    
                    # Statistical analysis
                    stats_result = await self._statistical_analysis(metric_name, source, points)
                    if stats_result:
                        analysis_results[f"{source}_{metric_name}_stats"] = stats_result
                    
                    # Performance analysis
                    performance_result = await self._performance_analysis(metric_name, source, points)
                    if performance_result:
                        analysis_results[f"{source}_{metric_name}_performance"] = performance_result
                    
                except Exception as e:
                    self.logger.error(f"Analysis failed for {metric_name}:{source}: {str(e)}")
                    continue
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            analysis_results['_processing_info'] = {
                'processing_time_seconds': processing_time,
                'data_points_analyzed': len(data_points),
                'analysis_count': len(analysis_results) - 1,  # Exclude processing info
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.debug(f"Analyzed {len(data_points)} data points in {processing_time:.2f} seconds")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Data analysis failed: {str(e)}")
            return {}
    
    def _group_data_points(self, data_points: List) -> Dict[Tuple[str, str], List]:
        """Group data points by metric name and source"""
        grouped = defaultdict(list)
        
        for point in data_points:
            if hasattr(point, 'metric_name') and hasattr(point, 'source'):
                key = (point.metric_name, point.source)
                grouped[key].append(point)
            elif isinstance(point, dict):
                key = (point.get('metric_name', 'unknown'), point.get('source', 'unknown'))
                grouped[key].append(point)
        
        return dict(grouped)
    
    async def _analyze_trends(self, metric_name: str, source: str, points: List) -> Optional[Dict[str, Any]]:
        """Analyze trends in data points"""
        try:
            if len(points) < self.trend_params['min_points']:
                return None
            
            # Extract values and timestamps
            values = []
            timestamps = []
            
            for point in points:
                if hasattr(point, 'value') and hasattr(point, 'timestamp'):
                    try:
                        value = float(point.value)
                        values.append(value)
                        timestamps.append(point.timestamp)
                    except (ValueError, TypeError):
                        continue
            
            if len(values) < self.trend_params['min_points']:
                return None
            
            # Calculate trend
            trend_result = self._calculate_trend_analysis(values, timestamps)
            
            return {
                'trend_direction': trend_result['direction'],
                'trend_strength': trend_result['strength'],
                'slope': trend_result['slope'],
                'r_squared': trend_result['r_squared'],
                'change_rate': trend_result['change_rate'],
                'confidence': trend_result['confidence'],
                'data_points_count': len(values),
                'analysis_type': 'trend',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Trend analysis failed for {metric_name}:{source}: {str(e)}")
            return None
    
    def _calculate_trend_analysis(self, values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Calculate detailed trend analysis"""
        try:
            # Sort by timestamp
            sorted_data = sorted(zip(timestamps, values), key=lambda x: x[0])
            sorted_values = [v for _, v in sorted_data]
            
            # Calculate linear regression
            n = len(sorted_values)
            x_values = list(range(n))
            
            # Calculate regression coefficients
            sum_x = sum(x_values)
            sum_y = sum(sorted_values)
            sum_xy = sum(x * y for x, y in zip(x_values, sorted_values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # Calculate R-squared
            y_mean = sum_y / n
            ss_tot = sum((y - y_mean) ** 2 for y in sorted_values)
            ss_res = sum((sorted_values[i] - (slope * x_values[i] + intercept)) ** 2 for i in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Determine trend direction and strength
            abs_slope = abs(slope)
            
            if abs_slope < 0.01:
                direction = 'stable'
                strength = 'very_weak'
            elif slope > 0:
                if abs_slope < 0.05:
                    direction = 'increasing'
                    strength = 'weak'
                elif abs_slope < 0.1:
                    direction = 'increasing'
                    strength = 'moderate'
                else:
                    direction = 'increasing'
                    strength = 'strong'
            else:
                if abs_slope < 0.05:
                    direction = 'decreasing'
                    strength = 'weak'
                elif abs_slope < 0.1:
                    direction = 'decreasing'
                    strength = 'moderate'
                else:
                    direction = 'decreasing'
                    strength = 'strong'
            
            # Calculate change rate
            if len(sorted_values) > 1:
                first_value = sorted_values[0]
                last_value = sorted_values[-1]
                change_rate = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
            else:
                change_rate = 0
            
            # Calculate confidence based on R-squared and data points
            confidence = min(1.0, r_squared * (len(values) / 10.0))
            
            return {
                'direction': direction,
                'strength': strength,
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_squared,
                'change_rate': change_rate,
                'confidence': confidence
            }
            
        except Exception as e:
            self.logger.debug(f"Trend calculation failed: {str(e)}")
            return {
                'direction': 'unknown',
                'strength': 'unknown',
                'slope': 0,
                'r_squared': 0,
                'change_rate': 0,
                'confidence': 0
            }
    
    async def _detect_anomalies(self, metric_name: str, source: str, points: List) -> Optional[Dict[str, Any]]:
        """Detect anomalies in data points"""
        try:
            if len(points) < self.anomaly_params['min_points']:
                return None
            
            # Extract values
            values = []
            for point in points:
                if hasattr(point, 'value'):
                    try:
                        values.append(float(point.value))
                    except (ValueError, TypeError):
                        continue
            
            if len(values) < self.anomaly_params['min_points']:
                return None
            
            # Anomaly detection methods
            anomalies = {
                'z_score_anomalies': [],
                'iqr_anomalies': [],
                'statistical_anomalies': []
            }
            
            # Z-score anomaly detection
            if len(values) > 1:
                mean_val = statistics.mean(values)
                std_val = statistics.stdev(values)
                
                if std_val > 0:
                    for i, value in enumerate(values):
                        z_score = abs((value - mean_val) / std_val)
                        if z_score > self.anomaly_params['z_score_threshold']:
                            anomalies['z_score_anomalies'].append({
                                'index': i,
                                'value': value,
                                'z_score': z_score,
                                'timestamp': points[i].timestamp if hasattr(points[i], 'timestamp') else None
                            })
            
            # IQR anomaly detection
            if len(values) >= 4:
                sorted_values = sorted(values)
                q1_idx = len(sorted_values) // 4
                q3_idx = 3 * len(sorted_values) // 4
                
                q1 = sorted_values[q1_idx]
                q3 = sorted_values[q3_idx]
                iqr = q3 - q1
                
                lower_bound = q1 - self.anomaly_params['iqr_multiplier'] * iqr
                upper_bound = q3 + self.anomaly_params['iqr_multiplier'] * iqr
                
                for i, value in enumerate(values):
                    if value < lower_bound or value > upper_bound:
                        anomalies['iqr_anomalies'].append({
                            'index': i,
                            'value': value,
                            'bounds': {'lower': lower_bound, 'upper': upper_bound},
                            'timestamp': points[i].timestamp if hasattr(points[i], 'timestamp') else None
                        })
            
            # Statistical anomaly detection (rolling statistics)
            window_size = self.anomaly_params['window_size']
            if len(values) >= window_size:
                rolling_stats = []
                for i in range(len(values) - window_size + 1):
                    window = values[i:i + window_size]
                    rolling_stats.append({
                        'index': i + window_size // 2,
                        'mean': statistics.mean(window),
                        'std': statistics.stdev(window) if len(window) > 1 else 0,
                        'value': values[i + window_size // 2]
                    })
                
                for stat in rolling_stats:
                    if stat['std'] > 0:
                        z_score = abs((stat['value'] - stat['mean']) / stat['std'])
                        if z_score > self.anomaly_params['z_score_threshold']:
                            anomalies['statistical_anomalies'].append({
                                'index': stat['index'],
                                'value': stat['value'],
                                'z_score': z_score,
                                'rolling_mean': stat['mean'],
                                'rolling_std': stat['std'],
                                'timestamp': points[stat['index']].timestamp if hasattr(points[stat['index']], 'timestamp') else None
                            })
            
            # Remove duplicates between methods
            all_anomaly_indices = set()
            for method_anomalies in anomalies.values():
                for anomaly in method_anomalies:
                    all_anomaly_indices.add(anomaly['index'])
            
            return {
                'total_anomalies': len(all_anomaly_indices),
                'anomaly_indices': list(all_anomaly_indices),
                'anomaly_details': anomalies,
                'data_points_count': len(values),
                'anomaly_rate': len(all_anomaly_indices) / len(values),
                'detection_methods': ['z_score', 'iqr', 'rolling_statistics'],
                'analysis_type': 'anomaly',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Anomaly detection failed for {metric_name}:{source}: {str(e)}")
            return None
    
    async def _detect_patterns(self, metric_name: str, source: str, points: List) -> Optional[Dict[str, Any]]:
        """Detect patterns in data points"""
        try:
            if len(points) < 5:
                return None
            
            # Extract values
            values = []
            timestamps = []
            
            for point in points:
                if hasattr(point, 'value') and hasattr(point, 'timestamp'):
                    try:
                        value = float(point.value)
                        values.append(value)
                        timestamps.append(point.timestamp)
                    except (ValueError, TypeError):
                        continue
            
            if len(values) < 5:
                return None
            
            patterns = {
                'cyclical_patterns': {},
                'sequential_patterns': {},
                'distribution_patterns': {}
            }
            
            # Detect cyclical patterns
            if len(values) >= 24:  # Need enough data points
                # Simple periodicity detection
                for period in [4, 8, 12, 24]:  # Different period lengths
                    if len(values) >= period * 2:
                        correlation = self._calculate_periodic_correlation(values, period)
                        if abs(correlation) > 0.5:  # Threshold for meaningful correlation
                            patterns['cyclical_patterns'][f'period_{period}'] = {
                                'correlation': correlation,
                                'strength': 'strong' if abs(correlation) > 0.8 else 'moderate'
                            }
            
            # Detect sequential patterns
            if len(values) >= 3:
                # Check for monotonic sequences
                increasing_count = 0
                decreasing_count = 0
                
                for i in range(1, len(values)):
                    if values[i] > values[i-1]:
                        increasing_count += 1
                    elif values[i] < values[i-1]:
                        decreasing_count += 1
                
                total_changes = increasing_count + decreasing_count
                if total_changes > 0:
                    increasing_ratio = increasing_count / total_changes
                    if increasing_ratio > 0.8:
                        patterns['sequential_patterns']['monotonic_increasing'] = {
                            'strength': 'strong',
                            'ratio': increasing_ratio
                        }
                    elif increasing_ratio < 0.2:
                        patterns['sequential_patterns']['monotonic_decreasing'] = {
                            'strength': 'strong',
                            'ratio': 1 - increasing_ratio
                        }
            
            # Detect distribution patterns
            if len(values) > 1:
                try:
                    mean_val = statistics.mean(values)
                    median_val = statistics.median(values)
                    
                    if abs(mean_val - median_val) / mean_val < 0.1:
                        patterns['distribution_patterns']['normal_distribution'] = {
                            'mean': mean_val,
                            'median': median_val,
                            'symmetry': 'high'
                        }
                    else:
                        patterns['distribution_patterns']['skewed_distribution'] = {
                            'mean': mean_val,
                            'median': median_val,
                            'skewness': 'positive' if mean_val > median_val else 'negative'
                        }
                except:
                    pass
            
            return {
                'patterns_detected': len(patterns['cyclical_patterns']) + len(patterns['sequential_patterns']) + len(patterns['distribution_patterns']),
                'patterns': patterns,
                'data_points_count': len(values),
                'analysis_type': 'pattern',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Pattern detection failed for {metric_name}:{source}: {str(e)}")
            return None
    
    def _calculate_periodic_correlation(self, values: List[float], period: int) -> float:
        """Calculate correlation for a specific period"""
        try:
            if len(values) < period * 2:
                return 0.0
            
            # Create two series with the given period offset
            series1 = values[:len(values)//2]
            series2 = values[period:period + len(series1)]
            
            if len(series1) != len(series2) or len(series1) == 0:
                return 0.0
            
            # Calculate correlation
            mean1 = statistics.mean(series1)
            mean2 = statistics.mean(series2)
            
            numerator = sum((x - mean1) * (y - mean2) for x, y in zip(series1, series2))
            sum_sq1 = sum((x - mean1) ** 2 for x in series1)
            sum_sq2 = sum((y - mean2) ** 2 for y in series2)
            
            denominator = math.sqrt(sum_sq1 * sum_sq2)
            
            return numerator / denominator if denominator != 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def _statistical_analysis(self, metric_name: str, source: str, points: List) -> Optional[Dict[str, Any]]:
        """Perform statistical analysis"""
        try:
            # Extract values
            values = []
            for point in points:
                if hasattr(point, 'value'):
                    try:
                        values.append(float(point.value))
                    except (ValueError, TypeError):
                        continue
            
            if not values:
                return None
            
            # Calculate comprehensive statistics
            stats = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'sum': sum(values)
            }
            
            if len(values) > 1:
                stats.update({
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'mode': statistics.mode(values) if len(set(values)) < len(values) else None,
                    'std_dev': statistics.stdev(values),
                    'variance': statistics.variance(values)
                })
                
                # Percentiles
                sorted_values = sorted(values)
                n = len(sorted_values)
                stats['percentiles'] = {
                    'p25': sorted_values[int(0.25 * n)],
                    'p50': sorted_values[int(0.50 * n)],
                    'p75': sorted_values[int(0.75 * n)],
                    'p90': sorted_values[int(0.90 * n)],
                    'p95': sorted_values[int(0.95 * n)],
                    'p99': sorted_values[int(0.99 * n)]
                }
            else:
                stats.update({
                    'mean': values[0],
                    'median': values[0],
                    'std_dev': 0.0,
                    'variance': 0.0,
                    'percentiles': {}
                })
            
            # Additional metrics
            stats['range'] = stats['max'] - stats['min']
            stats['coefficient_of_variation'] = (stats['std_dev'] / stats['mean']) if stats['mean'] != 0 else 0
            
            # Distribution analysis
            if len(values) > 2:
                mean_val = stats['mean']
                skewness = sum((x - mean_val) ** 3 for x in values) / (len(values) * stats['std_dev'] ** 3) if stats['std_dev'] > 0 else 0
                
                if abs(skewness) < 0.5:
                    stats['distribution'] = 'approximately_normal'
                elif skewness > 0.5:
                    stats['distribution'] = 'right_skewed'
                else:
                    stats['distribution'] = 'left_skewed'
            else:
                stats['distribution'] = 'insufficient_data'
            
            return {
                'statistics': stats,
                'analysis_type': 'statistical',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Statistical analysis failed for {metric_name}:{source}: {str(e)}")
            return None
    
    async def _performance_analysis(self, metric_name: str, source: str, points: List) -> Optional[Dict[str, Any]]:
        """Analyze performance characteristics"""
        try:
            # Extract values
            values = []
            timestamps = []
            
            for point in points:
                if hasattr(point, 'value') and hasattr(point, 'timestamp'):
                    try:
                        value = float(point.value)
                        values.append(value)
                        timestamps.append(point.timestamp)
                    except (ValueError, TypeError):
                        continue
            
            if not values:
                return None
            
            performance = {}
            
            # Stability analysis
            if len(values) > 1:
                # Calculate coefficient of variation
                mean_val = statistics.mean(values)
                std_val = statistics.stdev(values)
                cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
                
                performance['stability'] = {
                    'coefficient_of_variation': cv,
                    'stability_rating': 'high' if cv < 10 else 'medium' if cv < 25 else 'low'
                }
            
            # Reliability analysis (based on anomaly rate)
            anomaly_result = await self._detect_anomalies(metric_name, source, points)
            if anomaly_result:
                anomaly_rate = anomaly_result['anomaly_rate']
                performance['reliability'] = {
                    'anomaly_rate': anomaly_rate,
                    'reliability_rating': 'high' if anomaly_rate < 0.05 else 'medium' if anomaly_rate < 0.15 else 'low'
                }
            
            # Trend analysis
            if len(values) > 2:
                trend_result = await self._analyze_trends(metric_name, source, points)
                if trend_result:
                    performance['trend'] = {
                        'direction': trend_result['trend_direction'],
                        'strength': trend_result['trend_strength'],
                        'slope': trend_result['slope']
                    }
            
            # Performance summary
            performance['summary'] = {
                'average_value': statistics.mean(values) if values else 0,
                'performance_rating': 'good',
                'recommendations': []
            }
            
            # Generate recommendations
            if performance.get('stability', {}).get('stability_rating') == 'low':
                performance['summary']['recommendations'].append('Consider investigating high variability in values')
            
            if performance.get('reliability', {}).get('reliability_rating') == 'low':
                performance['summary']['recommendations'].append('High anomaly rate detected - review system stability')
            
            return {
                'performance': performance,
                'data_points_count': len(values),
                'analysis_type': 'performance',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Performance analysis failed for {metric_name}:{source}: {str(e)}")
            return None
    
    async def _analyze_correlation(self, metric_name: str, source: str, points: List) -> Optional[Dict[str, Any]]:
        """Analyze correlation between metrics (placeholder)"""
        # This would require multiple metrics for correlation analysis
        # Placeholder implementation
        return None
    
    async def _forecast_values(self, metric_name: str, source: str, points: List) -> Optional[Dict[str, Any]]:
        """Forecast future values (placeholder)"""
        # This would implement forecasting algorithms like ARIMA, linear regression, etc.
        # Placeholder implementation
        return None
    
    async def get_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of all analysis results"""
        try:
            summary = {
                'total_analyses': len(analysis_results) - 1,  # Exclude processing info
                'analysis_types': {},
                'key_findings': [],
                'recommendations': [],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Count analysis types
            for key, result in analysis_results.items():
                if key.startswith('_'):
                    continue
                
                if isinstance(result, dict) and 'analysis_type' in result:
                    analysis_type = result['analysis_type']
                    if analysis_type not in summary['analysis_types']:
                        summary['analysis_types'][analysis_type] = 0
                    summary['analysis_types'][analysis_type] += 1
            
            # Extract key findings
            for key, result in analysis_results.items():
                if key.startswith('_'):
                    continue
                
                # Trend findings
                if 'trend' in result and isinstance(result, dict):
                    trend_data = result.get('trend', {})
                    if trend_data.get('trend_strength') == 'strong':
                        summary['key_findings'].append(f"Strong {trend_data.get('trend_direction', 'unknown')} trend detected in {key}")
                
                # Anomaly findings
                if 'anomalies' in result and isinstance(result, dict):
                    anomaly_data = result.get('anomalies', {})
                    if anomaly_data.get('anomaly_rate', 0) > 0.1:
                        summary['key_findings'].append(f"High anomaly rate ({anomaly_data.get('anomaly_rate', 0):.2%}) detected in {key}")
                
                # Performance findings
                if 'performance' in result and isinstance(result, dict):
                    performance_data = result.get('performance', {})
                    if performance_data.get('reliability', {}).get('reliability_rating') == 'low':
                        summary['recommendations'].append(f"Low reliability detected in {key} - investigate system issues")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get analysis summary: {str(e)}")
            return {}


if __name__ == "__main__":
    # Example usage
    import asyncio
    from datetime import datetime, timedelta
    
    async def main():
        # Create sample data points
        from core.data_pipeline import create_data_point
        
        # Generate sample data with trends and anomalies
        data_points = []
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        # Normal values with slight upward trend
        for i in range(50):
            value = 100 + i * 2 + (i % 10)  # Upward trend with some variation
            if i == 25 or i == 45:  # Add anomalies
                value += 50
            data_points.append(create_data_point(
                'response_time',
                value,
                'api_service',
                tags={'endpoint': '/api/users'},
                timestamp=base_time + timedelta(minutes=i)
            ))
        
        # Initialize analyzer
        analyzer = DataAnalyzer()
        
        # Perform analysis
        print("Performing data analysis...")
        results = await analyzer.analyze(data_points)
        
        print(f"Analysis completed with {len(results)} results")
        for key, result in results.items():
            print(f"\n{key}:")
            if isinstance(result, dict):
                for subkey, subvalue in result.items():
                    print(f"  {subkey}: {subvalue}")
        
        # Get analysis summary
        print("\nGetting analysis summary...")
        summary = await analyzer.get_analysis_summary(results)
        print(f"Summary: {summary}")
    
    asyncio.run(main())