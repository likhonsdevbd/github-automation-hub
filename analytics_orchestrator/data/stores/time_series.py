"""
Time series data store implementation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import sqlite3
import threading
from collections import defaultdict
import os


@dataclass
class TimeSeriesEntry:
    """Time series database entry"""
    id: str
    timestamp: datetime
    source: str
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TimeSeriesStore:
    """
    Time series data store using SQLite as backend
    Provides efficient storage and querying of time series data
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize time series store"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.db_path = config.get('db_path', 'data/time_series.db')
        self.db_lock = threading.Lock()
        
        # Cache
        self._cache = {}
        self._cache_size = config.get('cache_size', 1000)
        self._cache_ttl = config.get('cache_ttl', 300)  # 5 minutes
        
        # Statistics
        self._stats = {
            'total_entries': 0,
            'queries_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create main table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS time_series (
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
                
                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON time_series(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON time_series(source)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metric ON time_series(metric_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_timestamp ON time_series(source, timestamp)')
                
                # Create aggregated table for fast queries
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aggregated_series (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        bucket_start DATETIME NOT NULL,
                        bucket_end DATETIME NOT NULL,
                        aggregation_type TEXT NOT NULL,
                        count INTEGER DEFAULT 0,
                        sum_value REAL DEFAULT 0,
                        min_value REAL DEFAULT 0,
                        max_value REAL DEFAULT 0,
                        avg_value REAL DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_agg_source_metric ON aggregated_series(source, metric_name)')
                
                conn.commit()
                
            self.logger.info("Time series database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def initialize(self):
        """Initialize the store"""
        self.logger.info("Initializing time series store")
        # Database is already initialized in __init__
        # This method exists for consistency with other stores
    
    async def is_healthy(self) -> bool:
        """Check if store is healthy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM time_series')
                count = cursor.fetchone()[0]
                return True
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def store_data_point(self, data_point) -> bool:
        """Store a data point"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO time_series 
                        (id, timestamp, source, metric_name, value, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data_point.id,
                        data_point.timestamp,
                        data_point.source,
                        data_point.metric_name,
                        data_point.value,
                        json.dumps(data_point.tags) if data_point.tags else None,
                        json.dumps(data_point.metadata) if data_point.metadata else None
                    ))
                    
                    conn.commit()
                    
                    # Update statistics
                    self._stats['total_entries'] += 1
                    
                    # Update cache
                    cache_key = f"{data_point.source}:{data_point.metric_name}:{data_point.timestamp}"
                    self._cache[cache_key] = data_point
                    
                    # Limit cache size
                    if len(self._cache) > self._cache_size:
                        # Remove oldest entries
                        oldest_keys = sorted(self._cache.keys())[:100]
                        for key in oldest_keys:
                            del self._cache[key]
                    
                    self.logger.debug(f"Stored data point: {data_point.id}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to store data point: {str(e)}")
            return False
    
    async def get_data(self, source: str, start_time: datetime = None, end_time: datetime = None) -> List[TimeSeriesEntry]:
        """Get time series data for a source"""
        try:
            cache_key = f"get_data:{source}:{start_time}:{end_time}"
            
            # Check cache
            if cache_key in self._cache:
                self._stats['cache_hits'] += 1
                return self._cache[cache_key]
            
            self._stats['cache_misses'] += 1
            self._stats['queries_executed'] += 1
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, timestamp, source, metric_name, value, tags, metadata
                    FROM time_series
                    WHERE source = ?
                '''
                params = [source]
                
                if start_time:
                    query += ' AND timestamp >= ?'
                    params.append(start_time)
                
                if end_time:
                    query += ' AND timestamp <= ?'
                    params.append(end_time)
                
                query += ' ORDER BY timestamp DESC LIMIT 1000'
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    entry = TimeSeriesEntry(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        source=row[2],
                        metric_name=row[3],
                        value=row[4],
                        tags=json.loads(row[5]) if row[5] else {},
                        metadata=json.loads(row[6]) if row[6] else {}
                    )
                    results.append(entry)
                
                # Cache results
                self._cache[cache_key] = results
                
                self.logger.debug(f"Retrieved {len(results)} entries for source {source}")
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get data: {str(e)}")
            return []
    
    async def query(self, query: Dict[str, Any]) -> List[TimeSeriesEntry]:
        """Query data based on criteria"""
        try:
            conditions = []
            params = []
            
            # Source filter
            if 'source' in query:
                conditions.append('source = ?')
                params.append(query['source'])
            
            # Metric filter
            if 'metric' in query:
                conditions.append('metric_name = ?')
                params.append(query['metric'])
            
            # Time range filter
            if 'start_time' in query:
                conditions.append('timestamp >= ?')
                params.append(query['start_time'])
            
            if 'end_time' in query:
                conditions.append('timestamp <= ?')
                params.append(query['end_time'])
            
            # Value filter
            if 'min_value' in query:
                conditions.append('value >= ?')
                params.append(query['min_value'])
            
            if 'max_value' in query:
                conditions.append('value <= ?')
                params.append(query['max_value'])
            
            # Tags filter
            if 'tags' in query:
                for tag_key, tag_value in query['tags'].items():
                    conditions.append('tags LIKE ?')
                    params.append(f'%"{tag_key}":"{tag_value}"%')
            
            # Build query
            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            sql_query = f'''
                SELECT id, timestamp, source, metric_name, value, tags, metadata
                FROM time_series
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT 1000
            '''
            
            self._stats['queries_executed'] += 1
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query, params)
                
                results = []
                for row in cursor.fetchall():
                    entry = TimeSeriesEntry(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        source=row[2],
                        metric_name=row[3],
                        value=row[4],
                        tags=json.loads(row[5]) if row[5] else {},
                        metadata=json.loads(row[6]) if row[6] else {}
                    )
                    results.append(entry)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to query data: {str(e)}")
            return []
    
    async def get_aggregated_data(self, source: str, metric: str, 
                                  start_time: datetime, end_time: datetime,
                                  aggregation: str = 'avg', interval: str = '1h') -> List[Dict[str, Any]]:
        """Get aggregated data for a metric"""
        try:
            # Parse interval
            if interval == '1h':
                bucket_size = 3600  # seconds
            elif interval == '1d':
                bucket_size = 86400  # seconds
            else:
                bucket_size = 3600  # default to 1 hour
            
            # Calculate buckets
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Group data into buckets
                cursor.execute('''
                    SELECT 
                        (strftime('%s', timestamp) / ?) * ? as bucket_start,
                        COUNT(*) as count,
                        SUM(value) as sum_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        AVG(value) as avg_value
                    FROM time_series
                    WHERE source = ? AND metric_name = ? 
                          AND timestamp >= ? AND timestamp <= ?
                    GROUP BY bucket_start
                    ORDER BY bucket_start
                ''', (bucket_size, bucket_size, source, metric, start_time, end_time))
                
                results = []
                for row in cursor.fetchall():
                    bucket_start = datetime.fromtimestamp(row[0])
                    bucket_end = datetime.fromtimestamp(row[0] + bucket_size)
                    
                    result = {
                        'bucket_start': bucket_start,
                        'bucket_end': bucket_end,
                        'count': row[1],
                        'sum': row[2],
                        'min': row[3],
                        'max': row[4],
                        'avg': row[5]
                    }
                    
                    # Apply aggregation function
                    if aggregation == 'sum':
                        result['value'] = row[2]
                    elif aggregation == 'min':
                        result['value'] = row[3]
                    elif aggregation == 'max':
                        result['value'] = row[4]
                    else:  # avg or other
                        result['value'] = row[5]
                    
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get aggregated data: {str(e)}")
            return []
    
    async def cleanup_expired(self, cutoff_time: datetime):
        """Clean up expired data"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Delete expired entries
                    cursor.execute('''
                        DELETE FROM time_series 
                        WHERE timestamp < ?
                    ''', (cutoff_time,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        self.logger.info(f"Cleaned up {deleted_count} expired time series entries")
                    
                    # Clean up cache
                    expired_cache_keys = []
                    for key, entry in self._cache.items():
                        if hasattr(entry, 'timestamp') and entry.timestamp < cutoff_time:
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
                
                # Get total entries
                cursor.execute('SELECT COUNT(*) FROM time_series')
                total_entries = cursor.fetchone()[0]
                
                # Get entries by source
                cursor.execute('''
                    SELECT source, COUNT(*) 
                    FROM time_series 
                    GROUP BY source 
                    ORDER BY COUNT(*) DESC
                ''')
                by_source = dict(cursor.fetchall())
                
                # Get entries by metric
                cursor.execute('''
                    SELECT metric_name, COUNT(*) 
                    FROM time_series 
                    GROUP BY metric_name 
                    ORDER BY COUNT(*) DESC
                ''')
                by_metric = dict(cursor.fetchall())
                
                return {
                    'total_entries': total_entries,
                    'by_source': by_source,
                    'by_metric': by_metric,
                    'cache_stats': self._stats.copy(),
                    'cache_size': len(self._cache),
                    'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return {}
    
    async def shutdown(self):
        """Shutdown the store"""
        self.logger.info("Shutting down time series store")
        # Close database connection (SQLite doesn't need explicit close)
        # Clean up cache
        self._cache.clear()
    
    async def export_data(self, source: str = None, format: str = 'json') -> str:
        """Export data to file"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"data/export_time_series_{timestamp}.{format}"
            
            # Query data
            if source:
                data = await self.get_data(source)
            else:
                # Get all data (limited for performance)
                data = await self.query({'start_time': datetime.utcnow() - timedelta(days=7)})
            
            if format == 'json':
                # Export as JSON
                export_data = []
                for entry in data:
                    export_data.append({
                        'id': entry.id,
                        'timestamp': entry.timestamp.isoformat(),
                        'source': entry.source,
                        'metric_name': entry.metric_name,
                        'value': entry.value,
                        'tags': entry.tags,
                        'metadata': entry.metadata
                    })
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Exported {len(data)} entries to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {str(e)}")
            raise


if __name__ == "__main__":
    # Example usage
    import asyncio
    from datetime import datetime, timedelta
    
    async def main():
        # Initialize store
        store = TimeSeriesStore({'db_path': 'test_time_series.db'})
        await store.initialize()
        
        # Create sample data
        from core.data_pipeline import DataPoint, create_data_point
        
        # Store some data points
        for i in range(10):
            data_point = create_data_point(
                f'metric_{i % 3}',
                i * 1.5,
                'test_source',
                tags={'host': 'server1'}
            )
            await store.store_data_point(data_point)
            await asyncio.sleep(0.1)  # Small delay
        
        # Query data
        data = await store.get_data('test_source')
        print(f"Retrieved {len(data)} data points")
        
        # Get statistics
        stats = await store.get_statistics()
        print(f"Store statistics: {stats}")
        
        # Cleanup
        await store.shutdown()
        
        # Remove test database
        import os
        if os.path.exists('test_time_series.db'):
            os.remove('test_time_series.db')
    
    asyncio.run(main())