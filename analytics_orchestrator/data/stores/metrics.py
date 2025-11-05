"""
Metrics data store implementation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import sqlite3
import threading
import os


@dataclass
class MetricEntry:
    """Metric database entry"""
    id: str
    timestamp: datetime
    source: str
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsStore:
    """
    Metrics data store for aggregated metrics and statistics
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize metrics store"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.db_path = config.get('db_path', 'data/metrics.db')
        self.db_lock = threading.Lock()
        
        # Cache for metrics summaries
        self._cache = {}
        self._cache_size = config.get('cache_size', 500)
        self._cache_ttl = config.get('cache_ttl', 600)  # 10 minutes
        
        # Statistics
        self._stats = {
            'total_metrics': 0,
            'queries_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for metrics"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id TEXT PRIMARY KEY,
                        timestamp DATETIME NOT NULL,
                        source TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        tags TEXT,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create aggregated metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aggregated_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        time_period TEXT NOT NULL,
                        aggregation_type TEXT NOT NULL,
                        count INTEGER DEFAULT 0,
                        sum_value REAL DEFAULT 0,
                        min_value REAL DEFAULT 0,
                        max_value REAL DEFAULT 0,
                        avg_value REAL DEFAULT 0,
                        p95_value REAL DEFAULT 0,
                        p99_value REAL DEFAULT 0,
                        first_timestamp DATETIME,
                        last_timestamp DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create health scores table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS health_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        component_name TEXT,
                        score REAL NOT NULL,
                        grade TEXT NOT NULL,
                        metrics_data TEXT,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_source ON metrics(source)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_source_timestamp ON metrics(source, timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_health_source ON health_scores(source)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_health_timestamp ON health_scores(timestamp)')
                
                conn.commit()
                
            self.logger.info("Metrics database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics database: {str(e)}")
            raise
    
    async def initialize(self):
        """Initialize the store"""
        self.logger.info("Initializing metrics store")
        # Database is already initialized in __init__
    
    async def is_healthy(self) -> bool:
        """Check if store is healthy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM metrics')
                count = cursor.fetchone()[0]
                return True
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def store_metrics(self, source: str, metrics_data: Dict[str, Any]) -> bool:
        """Store metrics data"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Store individual metrics
                    if 'metrics' in metrics_data:
                        for metric_name, value in metrics_data['metrics'].items():
                            cursor.execute('''
                                INSERT INTO metrics 
                                (id, timestamp, source, metric_name, value, tags, metadata)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                f"{source}_{metric_name}_{datetime.utcnow().timestamp()}",
                                datetime.utcnow(),
                                source,
                                metric_name,
                                float(value) if isinstance(value, (int, float, str)) else 0,
                                json.dumps({'category': 'aggregated'}),
                                json.dumps(metrics_data)
                            ))
                    
                    # Store aggregated data
                    cursor.execute('''
                        INSERT INTO aggregated_metrics
                        (source, metric_name, time_period, aggregation_type, count, sum_value, 
                         min_value, max_value, avg_value, first_timestamp, last_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        source,
                        metrics_data.get('batch_id', 'unknown'),
                        'batch',
                        'sum',
                        metrics_data.get('data_points_count', 0),
                        metrics_data.get('data_points_count', 0),
                        metrics_data.get('data_points_count', 0),
                        metrics_data.get('data_points_count', 0),
                        metrics_data.get('data_points_count', 0) if metrics_data.get('data_points_count') else 0,
                        metrics_data.get('timestamp'),
                        metrics_data.get('timestamp')
                    ))
                    
                    conn.commit()
                    
                    # Update statistics
                    self._stats['total_metrics'] += 1
                    
                    self.logger.debug(f"Stored metrics for source: {source}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {str(e)}")
            return False
    
    async def store_health_score(self, source: str, component_name: str, 
                                 score: float, grade: str, metrics_data: Dict[str, Any]) -> bool:
        """Store health score"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO health_scores
                        (source, component_name, score, grade, metrics_data, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        source,
                        component_name,
                        score,
                        grade,
                        json.dumps(metrics_data),
                        datetime.utcnow()
                    ))
                    
                    conn.commit()
                    self.logger.debug(f"Stored health score for {source}:{component_name} = {score}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to store health score: {str(e)}")
            return False
    
    async def get_summary(self, source: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for a source"""
        try:
            cache_key = f"summary:{source}:{hours}"
            
            # Check cache
            if cache_key in self._cache:
                self._stats['cache_hits'] += 1
                return self._cache[cache_key]
            
            self._stats['cache_misses'] += 1
            self._stats['queries_executed'] += 1
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recent metrics
                cursor.execute('''
                    SELECT metric_name, COUNT(*), AVG(value), MIN(value), MAX(value)
                    FROM metrics
                    WHERE source = ? AND timestamp >= ?
                    GROUP BY metric_name
                    ORDER BY metric_name
                ''', (source, cutoff_time))
                
                metrics_summary = {}
                for row in cursor.fetchall():
                    metrics_summary[row[0]] = {
                        'count': row[1],
                        'avg': round(row[2], 2) if row[2] else 0,
                        'min': row[3],
                        'max': row[4],
                        'trend': 'stable'  # Simplified trend
                    }
                
                # Get health scores
                cursor.execute('''
                    SELECT component_name, score, grade, timestamp
                    FROM health_scores
                    WHERE source = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (source, cutoff_time))
                
                health_scores = []
                for row in cursor.fetchall():
                    health_scores.append({
                        'component': row[0],
                        'score': row[1],
                        'grade': row[2],
                        'timestamp': row[3]
                    })
                
                # Get aggregated data
                cursor.execute('''
                    SELECT metric_name, SUM(count), AVG(avg_value), MIN(min_value), MAX(max_value)
                    FROM aggregated_metrics
                    WHERE source = ? AND first_timestamp >= ?
                    GROUP BY metric_name
                ''', (source, cutoff_time))
                
                aggregated_summary = {}
                for row in cursor.fetchall():
                    aggregated_summary[row[0]] = {
                        'total_count': row[1],
                        'avg_value': round(row[2], 2) if row[2] else 0,
                        'min_value': row[3],
                        'max_value': row[4]
                    }
                
                summary = {
                    'source': source,
                    'time_period_hours': hours,
                    'generated_at': datetime.utcnow().isoformat(),
                    'metrics_summary': metrics_summary,
                    'health_scores': health_scores,
                    'aggregated_summary': aggregated_summary,
                    'total_metrics_count': len(metrics_summary)
                }
                
                # Cache the result
                self._cache[cache_key] = summary
                
                # Limit cache size
                if len(self._cache) > self._cache_size:
                    # Remove oldest entries
                    oldest_keys = sorted(self._cache.keys())[:50]
                    for key in oldest_keys:
                        del self._cache[key]
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Failed to get summary: {str(e)}")
            return {}
    
    async def get_health_scores(self, source: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health scores"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT source, component_name, score, grade, metrics_data, timestamp
                    FROM health_scores
                    WHERE timestamp >= ?
                '''
                params = [cutoff_time]
                
                if source:
                    query += ' AND source = ?'
                    params.append(source)
                
                query += ' ORDER BY timestamp DESC'
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'source': row[0],
                        'component': row[1],
                        'score': row[2],
                        'grade': row[3],
                        'metrics_data': json.loads(row[4]) if row[4] else {},
                        'timestamp': row[5]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get health scores: {str(e)}")
            return []
    
    async def get_trend_analysis(self, source: str, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Get trend analysis for a specific metric"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get daily aggregated values
                cursor.execute('''
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as count,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value
                    FROM metrics
                    WHERE source = ? AND metric_name = ? AND timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (source, metric_name, cutoff_time))
                
                daily_data = []
                for row in cursor.fetchall():
                    daily_data.append({
                        'date': row[0],
                        'count': row[1],
                        'avg': round(row[2], 2) if row[2] else 0,
                        'min': row[3],
                        'max': row[4]
                    })
                
                # Calculate trend
                if len(daily_data) >= 2:
                    first_avg = daily_data[0]['avg']
                    last_avg = daily_data[-1]['avg']
                    
                    if last_avg > first_avg * 1.1:
                        trend = 'increasing'
                    elif last_avg < first_avg * 0.9:
                        trend = 'decreasing'
                    else:
                        trend = 'stable'
                else:
                    trend = 'insufficient_data'
                
                return {
                    'source': source,
                    'metric_name': metric_name,
                    'period_days': days,
                    'trend': trend,
                    'data_points': len(daily_data),
                    'daily_data': daily_data,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get trend analysis: {str(e)}")
            return {}
    
    async def get_component_metrics(self, component_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics for a specific component"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get component health scores
                cursor.execute('''
                    SELECT source, score, grade, timestamp
                    FROM health_scores
                    WHERE component_name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (component_name, cutoff_time))
                
                latest_health = None
                row = cursor.fetchone()
                if row:
                    latest_health = {
                        'source': row[0],
                        'score': row[1],
                        'grade': row[2],
                        'timestamp': row[3]
                    }
                
                # Get aggregated metrics for component
                cursor.execute('''
                    SELECT metric_name, SUM(count), AVG(avg_value), MIN(min_value), MAX(max_value)
                    FROM aggregated_metrics
                    WHERE source LIKE ? AND first_timestamp >= ?
                    GROUP BY metric_name
                ''', (f'%{component_name}%', cutoff_time))
                
                component_metrics = {}
                for row in cursor.fetchall():
                    component_metrics[row[0]] = {
                        'total_count': row[1],
                        'avg_value': round(row[2], 2) if row[2] else 0,
                        'min_value': row[3],
                        'max_value': row[4]
                    }
                
                return {
                    'component_name': component_name,
                    'latest_health': latest_health,
                    'metrics': component_metrics,
                    'period_hours': hours,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get component metrics: {str(e)}")
            return {}
    
    async def cleanup_expired(self, cutoff_time: datetime):
        """Clean up expired data"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Clean up old metrics
                    cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_time,))
                    deleted_metrics = cursor.rowcount
                    
                    # Clean up old health scores
                    cursor.execute('DELETE FROM health_scores WHERE timestamp < ?', (cutoff_time,))
                    deleted_health = cursor.rowcount
                    
                    # Clean up old aggregated metrics
                    cursor.execute('DELETE FROM aggregated_metrics WHERE last_timestamp < ?', (cutoff_time,))
                    deleted_aggregated = cursor.rowcount
                    
                    conn.commit()
                    
                    total_deleted = deleted_metrics + deleted_health + deleted_aggregated
                    if total_deleted > 0:
                        self.logger.info(f"Cleaned up {total_deleted} expired metric entries")
                    
                    # Clean up cache
                    expired_cache_keys = []
                    for key in self._cache.keys():
                        if ':' in key:
                            parts = key.split(':')
                            if len(parts) >= 2:
                                # This is a simplified cache cleanup
                                # In production, you'd want to track cache entry timestamps
                                expired_cache_keys.append(key)
                    
                    for key in expired_cache_keys:
                        del self._cache[key]
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired data: {str(e)}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get basic counts
                cursor.execute('SELECT COUNT(*) FROM metrics')
                total_metrics = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM health_scores')
                total_health_scores = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM aggregated_metrics')
                total_aggregated = cursor.fetchone()[0]
                
                # Get sources
                cursor.execute('SELECT DISTINCT source FROM metrics')
                sources = [row[0] for row in cursor.fetchall()]
                
                # Get recent activity
                recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                cursor.execute('SELECT COUNT(*) FROM metrics WHERE timestamp >= ?', (recent_cutoff,))
                recent_metrics = cursor.fetchone()[0]
                
                return {
                    'total_metrics': total_metrics,
                    'total_health_scores': total_health_scores,
                    'total_aggregated': total_aggregated,
                    'sources': sources,
                    'sources_count': len(sources),
                    'recent_metrics_24h': recent_metrics,
                    'cache_stats': self._stats.copy(),
                    'cache_size': len(self._cache),
                    'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return {}
    
    async def shutdown(self):
        """Shutdown the store"""
        self.logger.info("Shutting down metrics store")
        self._cache.clear()


if __name__ == "__main__":
    # Example usage
    import asyncio
    from datetime import datetime, timedelta
    
    async def main():
        # Initialize store
        store = MetricsStore({'db_path': 'test_metrics.db'})
        await store.initialize()
        
        # Store some metrics
        metrics_data = {
            'batch_id': 'test_batch_1',
            'data_points_count': 100,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'response_time': 45.2,
                'throughput': 1200,
                'error_rate': 0.02
            }
        }
        
        await store.store_metrics('api_service', metrics_data)
        
        # Store health score
        await store.store_health_score('api_service', 'health_monitor', 85.5, 'B+', {'details': 'good performance'})
        
        # Get summary
        summary = await store.get_summary('api_service', 24)
        print(f"Summary: {summary}")
        
        # Get health scores
        health_scores = await store.get_health_scores('api_service')
        print(f"Health scores: {health_scores}")
        
        # Get statistics
        stats = await store.get_statistics()
        print(f"Store statistics: {stats}")
        
        # Cleanup
        await store.shutdown()
        
        # Remove test database
        import os
        if os.path.exists('test_metrics.db'):
            os.remove('test_metrics.db')
    
    asyncio.run(main())