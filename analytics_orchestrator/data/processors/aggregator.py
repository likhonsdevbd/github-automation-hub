"""
Data aggregation processor for analytics pipeline
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
from collections import defaultdict, Counter


@dataclass
class AggregationResult:
    """Aggregation result structure"""
    metric_name: str
    source: str
    count: int
    sum_value: float
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    std_dev: float
    percentiles: Dict[str, float]
    trend: str
    timestamp: datetime


class DataAggregator:
    """
    Data aggregation processor that groups and summarizes data points
    """
    
    def __init__(self):
        """Initialize data aggregator"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Data aggregator initialized")
    
    async def aggregate(self, data_points: List) -> Dict[str, Any]:
        """
        Aggregate a list of data points
        
        Args:
            data_points: List of data point objects
            
        Returns:
            Dictionary containing aggregated metrics
        """
        try:
            if not data_points:
                return {}
            
            # Group data points by metric name and source
            grouped_data = self._group_data_points(data_points)
            
            # Aggregate each group
            aggregated_metrics = {}
            
            for (metric_name, source), points in grouped_data.items():
                try:
                    result = await self._aggregate_metric_group(metric_name, source, points)
                    aggregated_metrics[f"{source}_{metric_name}"] = {
                        'count': result.count,
                        'sum': result.sum_value,
                        'min': result.min_value,
                        'max': result.max_value,
                        'avg': result.avg_value,
                        'median': result.median_value,
                        'std_dev': result.std_dev,
                        'percentiles': result.percentiles,
                        'trend': result.trend,
                        'timestamp': result.timestamp.isoformat()
                    }
                except Exception as e:
                    self.logger.error(f"Failed to aggregate {metric_name} for {source}: {str(e)}")
                    continue
            
            self.logger.debug(f"Aggregated {len(data_points)} data points into {len(aggregated_metrics)} metrics")
            return aggregated_metrics
            
        except Exception as e:
            self.logger.error(f"Data aggregation failed: {str(e)}")
            return {}
    
    def _group_data_points(self, data_points: List) -> Dict[tuple, List]:
        """Group data points by metric name and source"""
        grouped = defaultdict(list)
        
        for point in data_points:
            # Handle different data point types
            if hasattr(point, 'metric_name') and hasattr(point, 'source'):
                key = (point.metric_name, point.source)
                grouped[key].append(point)
            elif isinstance(point, dict):
                key = (point.get('metric_name', 'unknown'), point.get('source', 'unknown'))
                grouped[key].append(point)
        
        return dict(grouped)
    
    async def _aggregate_metric_group(self, metric_name: str, source: str, points: List) -> AggregationResult:
        """Aggregate a group of data points for a specific metric and source"""
        try:
            # Extract values (handle different data point formats)
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
                elif isinstance(point, dict):
                    try:
                        value = float(point.get('value', 0))
                        values.append(value)
                        timestamps.append(point.get('timestamp', datetime.utcnow()))
                    except (ValueError, TypeError):
                        continue
            
            if not values:
                raise ValueError("No valid numeric values found")
            
            # Calculate basic statistics
            count = len(values)
            sum_value = sum(values)
            min_value = min(values)
            max_value = max(values)
            avg_value = sum_value / count
            
            # Calculate advanced statistics
            try:
                median_value = statistics.median(values)
                std_dev = statistics.stdev(values) if count > 1 else 0.0
            except statistics.StatisticsError:
                median_value = avg_value
                std_dev = 0.0
            
            # Calculate percentiles
            sorted_values = sorted(values)
            percentiles = self._calculate_percentiles(sorted_values)
            
            # Determine trend
            trend = self._calculate_trend(values, timestamps)
            
            return AggregationResult(
                metric_name=metric_name,
                source=source,
                count=count,
                sum_value=sum_value,
                min_value=min_value,
                max_value=max_value,
                avg_value=avg_value,
                median_value=median_value,
                std_dev=std_dev,
                percentiles=percentiles,
                trend=trend,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to aggregate metric group {metric_name}:{source}: {str(e)}")
            raise
    
    def _calculate_percentiles(self, sorted_values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for a sorted list of values"""
        if not sorted_values:
            return {}
        
        n = len(sorted_values)
        percentiles = {}
        
        # Common percentiles
        percentile_values = [25, 50, 75, 90, 95, 99]
        
        for p in percentile_values:
            try:
                if p == 50:  # median
                    value = statistics.median(sorted_values)
                else:
                    index = (p / 100.0) * (n - 1)
                    if index.is_integer():
                        value = sorted_values[int(index)]
                    else:
                        lower_index = int(index)
                        upper_index = lower_index + 1
                        weight = index - lower_index
                        value = sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
                
                percentiles[f'p{p}'] = round(value, 2)
            except Exception as e:
                self.logger.debug(f"Failed to calculate percentile {p}: {str(e)}")
                percentiles[f'p{p}'] = 0.0
        
        return percentiles
    
    def _calculate_trend(self, values: List[float], timestamps: List[datetime]) -> str:
        """Calculate trend direction from values and timestamps"""
        try:
            if len(values) < 3:
                return 'insufficient_data'
            
            # Sort by timestamp
            sorted_data = sorted(zip(timestamps, values), key=lambda x: x[0])
            sorted_values = [v for _, v in sorted_data]
            
            # Calculate linear regression slope
            n = len(sorted_values)
            x_values = list(range(n))
            
            # Calculate slope
            sum_x = sum(x_values)
            sum_y = sum(sorted_values)
            sum_xy = sum(x * y for x, y in zip(x_values, sorted_values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Determine trend based on slope and relative change
            if abs(slope) < 0.01:  # Very small slope
                trend = 'stable'
            elif slope > 0:
                # Positive trend, check magnitude
                if slope > 0.1:
                    trend = 'increasing_fast'
                elif slope > 0.05:
                    trend = 'increasing'
                else:
                    trend = 'increasing_slow'
            else:
                # Negative trend
                if slope < -0.1:
                    trend = 'decreasing_fast'
                elif slope < -0.05:
                    trend = 'decreasing'
                else:
                    trend = 'decreasing_slow'
            
            return trend
            
        except Exception as e:
            self.logger.debug(f"Failed to calculate trend: {str(e)}")
            return 'error'
    
    async def aggregate_by_time_window(self, data_points: List, window_size: str = '1h') -> Dict[str, Any]:
        """
        Aggregate data points by time windows
        
        Args:
            data_points: List of data point objects
            window_size: Time window size ('1h', '1d', '1w')
            
        Returns:
            Dictionary containing time-windowed aggregations
        """
        try:
            if not data_points:
                return {}
            
            # Parse window size
            window_seconds = self._parse_window_size(window_size)
            
            # Group data by time windows
            windowed_groups = self._group_by_time_window(data_points, window_seconds)
            
            # Aggregate each time window
            aggregated_metrics = {}
            
            for window_start, points in windowed_groups.items():
                window_key = window_start.strftime('%Y-%m-%d_%H-%M-%S')
                
                # Aggregate points in this window
                window_metrics = await self.aggregate(points)
                
                for metric_name, metrics in window_metrics.items():
                    full_key = f"{window_key}_{metric_name}"
                    aggregated_metrics[full_key] = {
                        'window_start': window_start.isoformat(),
                        'window_size': window_size,
                        **metrics
                    }
            
            self.logger.debug(f"Time-windowed aggregation completed for {len(windowed_groups)} windows")
            return aggregated_metrics
            
        except Exception as e:
            self.logger.error(f"Time-windowed aggregation failed: {str(e)}")
            return {}
    
    def _parse_window_size(self, window_size: str) -> int:
        """Parse window size string to seconds"""
        window_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '2h': 7200,
            '6h': 21600,
            '12h': 43200,
            '1d': 86400,
            '1w': 604800,
            '1M': 2592000  # 30 days approximation
        }
        
        return window_map.get(window_size, 3600)  # Default to 1 hour
    
    def _group_by_time_window(self, data_points: List, window_seconds: int) -> Dict[datetime, List]:
        """Group data points by time windows"""
        windowed = defaultdict(list)
        
        for point in data_points:
            # Get timestamp
            if hasattr(point, 'timestamp'):
                timestamp = point.timestamp
            elif isinstance(point, dict):
                timestamp = point.get('timestamp', datetime.utcnow())
            else:
                timestamp = datetime.utcnow()
            
            # Calculate window start
            timestamp_seconds = int(timestamp.timestamp())
            window_start_seconds = (timestamp_seconds // window_seconds) * window_seconds
            window_start = datetime.fromtimestamp(window_start_seconds)
            
            windowed[window_start].append(point)
        
        return dict(windowed)
    
    async def aggregate_by_tags(self, data_points: List, tag_keys: List[str] = None) -> Dict[str, Any]:
        """
        Aggregate data points by tag combinations
        
        Args:
            data_points: List of data point objects
            tag_keys: List of tag keys to group by
            
        Returns:
            Dictionary containing tag-based aggregations
        """
        try:
            if not data_points:
                return {}
            
            # Group by tags
            tagged_groups = self._group_by_tags(data_points, tag_keys or [])
            
            # Aggregate each tag group
            aggregated_metrics = {}
            
            for tag_combination, points in tagged_groups.items():
                # Create tag key
                tag_key = '_'.join(f"{k}={v}" for k, v in tag_combination.items())
                
                # Aggregate points in this tag group
                group_metrics = await self.aggregate(points)
                
                for metric_name, metrics in group_metrics.items():
                    full_key = f"{tag_key}_{metric_name}"
                    aggregated_metrics[full_key] = {
                        'tags': tag_combination,
                        **metrics
                    }
            
            self.logger.debug(f"Tag-based aggregation completed for {len(tagged_groups)} tag combinations")
            return aggregated_metrics
            
        except Exception as e:
            self.logger.error(f"Tag-based aggregation failed: {str(e)}")
            return {}
    
    def _group_by_tags(self, data_points: List, tag_keys: List[str]) -> Dict[tuple, List]:
        """Group data points by tag combinations"""
        tagged = defaultdict(list)
        
        for point in data_points:
            # Get tags
            if hasattr(point, 'tags') and point.tags:
                tags = point.tags
            elif isinstance(point, dict):
                tags = point.get('tags', {})
            else:
                tags = {}
            
            # Extract tag combination
            tag_combination = tuple(
                (key, tags.get(key, 'unknown')) for key in tag_keys
            )
            
            tagged[tag_combination].append(point)
        
        return dict(tagged)
    
    async def calculate_rate_metrics(self, data_points: List) -> Dict[str, Any]:
        """Calculate rate-based metrics from data points"""
        try:
            if not data_points:
                return {}
            
            # Group by metric name and source
            grouped_data = self._group_data_points(data_points)
            rate_metrics = {}
            
            for (metric_name, source), points in grouped_data.items():
                try:
                    # Sort by timestamp
                    sorted_points = sorted(points, key=lambda x: x.timestamp if hasattr(x, 'timestamp') else datetime.utcnow())
                    
                    if len(sorted_points) < 2:
                        continue
                    
                    # Calculate rates
                    total_time = (sorted_points[-1].timestamp - sorted_points[0].timestamp).total_seconds()
                    
                    if total_time > 0:
                        # Events per second
                        events_per_second = len(points) / total_time
                        
                        # Events per minute
                        events_per_minute = events_per_second * 60
                        
                        # Events per hour
                        events_per_hour = events_per_minute * 60
                        
                        rate_metrics[f"{source}_{metric_name}_rates"] = {
                            'events_per_second': round(events_per_second, 4),
                            'events_per_minute': round(events_per_minute, 2),
                            'events_per_hour': round(events_per_hour, 2),
                            'total_events': len(points),
                            'time_period_seconds': total_time,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                
                except Exception as e:
                    self.logger.error(f"Failed to calculate rate metrics for {metric_name}:{source}: {str(e)}")
                    continue
            
            return rate_metrics
            
        except Exception as e:
            self.logger.error(f"Rate metrics calculation failed: {str(e)}")
            return {}
    
    async def calculate_health_metrics(self, data_points: List) -> Dict[str, Any]:
        """Calculate health and quality metrics from data points"""
        try:
            if not data_points:
                return {}
            
            grouped_data = self._group_data_points(data_points)
            health_metrics = {}
            
            for (metric_name, source), points in grouped_data.items():
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
                        continue
                    
                    # Calculate quality metrics
                    total_points = len(points)
                    valid_points = len(values)
                    quality_score = (valid_points / total_points) * 100 if total_points > 0 else 0
                    
                    # Calculate consistency metrics
                    avg_value = statistics.mean(values)
                    std_dev = statistics.stdev(values) if len(values) > 1 else 0
                    consistency_score = 100 - (std_dev / avg_value * 100) if avg_value > 0 else 100
                    
                    # Data freshness
                    latest_timestamp = max(
                        point.timestamp for point in points 
                        if hasattr(point, 'timestamp')
                    )
                    current_time = datetime.utcnow()
                    freshness_minutes = (current_time - latest_timestamp).total_seconds() / 60
                    
                    health_metrics[f"{source}_{metric_name}_health"] = {
                        'quality_score': round(quality_score, 2),
                        'consistency_score': round(max(0, consistency_score), 2),
                        'data_freshness_minutes': round(freshness_minutes, 2),
                        'total_points': total_points,
                        'valid_points': valid_points,
                        'invalid_points': total_points - valid_points,
                        'avg_value': round(avg_value, 2),
                        'std_deviation': round(std_dev, 2),
                        'latest_timestamp': latest_timestamp.isoformat(),
                        'timestamp': current_time.isoformat()
                    }
                
                except Exception as e:
                    self.logger.error(f"Failed to calculate health metrics for {metric_name}:{source}: {str(e)}")
                    continue
            
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"Health metrics calculation failed: {str(e)}")
            return {}


if __name__ == "__main__":
    # Example usage
    import asyncio
    from datetime import datetime, timedelta
    
    async def main():
        # Create sample data points
        from core.data_pipeline import create_data_point
        
        data_points = []
        base_time = datetime.utcnow() - timedelta(hours=2)
        
        for i in range(100):
            data_points.append(create_data_point(
                'response_time',
                50 + (i % 20) * 2 + (i * 0.1),
                'api_service',
                tags={'endpoint': 'users', 'method': 'GET'},
                timestamp=base_time + timedelta(minutes=i)
            ))
        
        # Initialize aggregator
        aggregator = DataAggregator()
        
        # Test basic aggregation
        print("Testing basic aggregation...")
        result = await aggregator.aggregate(data_points[:10])
        print(f"Aggregation result: {result}")
        
        # Test time window aggregation
        print("\nTesting time window aggregation...")
        window_result = await aggregator.aggregate_by_time_window(data_points, '1h')
        print(f"Time window result: {window_result}")
        
        # Test rate metrics
        print("\nTesting rate metrics...")
        rate_result = await aggregator.calculate_rate_metrics(data_points)
        print(f"Rate metrics result: {rate_result}")
        
        # Test health metrics
        print("\nTesting health metrics...")
        health_result = await aggregator.calculate_health_metrics(data_points)
        print(f"Health metrics result: {health_result}")
    
    asyncio.run(main())