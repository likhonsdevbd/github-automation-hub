"""
Cache store implementation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import sqlite3
import threading
import os
import hashlib
import time


@dataclass
class CacheEntry:
    """Cache entry structure"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)


class CacheStore:
    """
    High-performance cache store with multiple backend options
    Supports memory, SQLite, and Redis backends
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cache store"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.backend = config.get('type', 'memory')
        self.default_ttl = config.get('ttl', 3600)  # 1 hour
        self.max_size = config.get('max_size', 1000)
        self.cleanup_interval = config.get('cleanup_interval', 300)  # 5 minutes
        
        # Backend-specific configuration
        self.db_path = config.get('db_path', 'data/cache.db')
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
        self.redis_namespace = config.get('redis_namespace', 'analytics_cache')
        
        # Internal state
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._access_lock = threading.RLock()
        self._cleanup_task = None
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'expired_cleanups': 0
        }
        
        # Initialize backend
        self._init_backend()
    
    def _init_backend(self):
        """Initialize the cache backend"""
        if self.backend == 'memory':
            self._init_memory_backend()
        elif self.backend == 'sqlite':
            self._init_sqlite_backend()
        elif self.backend == 'redis':
            self._init_redis_backend()
        else:
            raise ValueError(f"Unsupported cache backend: {self.backend}")
    
    def _init_memory_backend(self):
        """Initialize in-memory cache backend"""
        self.logger.info("Initializing memory cache backend")
        self.memory_lock = threading.RLock()
    
    def _init_sqlite_backend(self):
        """Initialize SQLite cache backend"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        expires_at DATETIME NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)')
                
                conn.commit()
                
            self.logger.info("SQLite cache backend initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite cache: {str(e)}")
            raise
    
    def _init_redis_backend(self):
        """Initialize Redis cache backend"""
        try:
            import redis.asyncio as redis
            
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.logger.info("Redis cache backend initialized")
            
        except ImportError:
            self.logger.warning("Redis client not available, falling back to memory cache")
            self.backend = 'memory'
            self._init_memory_backend()
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis cache: {str(e)}")
            # Fall back to memory cache
            self.backend = 'memory'
            self._init_memory_backend()
    
    async def initialize(self):
        """Initialize the cache store"""
        self.logger.info("Initializing cache store")
        
        # Start cleanup task
        if self.backend == 'memory':
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def is_healthy(self) -> bool:
        """Check if store is healthy"""
        try:
            if self.backend == 'memory':
                return True
            elif self.backend == 'sqlite':
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM cache')
                    return True
            elif self.backend == 'redis':
                if hasattr(self, 'redis_client'):
                    await self.redis_client.ping()
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Cache health check failed: {str(e)}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            if self.backend == 'memory':
                return await self._get_memory(key, default)
            elif self.backend == 'sqlite':
                return await self._get_sqlite(key, default)
            elif self.backend == 'redis':
                return await self._get_redis(key, default)
            else:
                return default
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {str(e)}")
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            if self.backend == 'memory':
                return await self._set_memory(key, value, ttl)
            elif self.backend == 'sqlite':
                return await self._set_sqlite(key, value, ttl)
            elif self.backend == 'redis':
                return await self._set_redis(key, value, ttl)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.backend == 'memory':
                return await self._delete_memory(key)
            elif self.backend == 'sqlite':
                return await self._delete_sqlite(key)
            elif self.backend == 'redis':
                return await self._delete_redis(key)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.backend == 'memory':
                with self.memory_lock:
                    return key in self._memory_cache
            elif self.backend == 'sqlite':
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1 FROM cache WHERE key = ? AND expires_at > ?', (key, datetime.utcnow()))
                    return cursor.fetchone() is not None
            elif self.backend == 'redis':
                if hasattr(self, 'redis_client'):
                    return await self.redis_client.exists(f"{self.redis_namespace}:{key}") > 0
            return False
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.backend == 'memory':
                with self.memory_lock:
                    self._memory_cache.clear()
            elif self.backend == 'sqlite':
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM cache')
                    conn.commit()
            elif self.backend == 'redis':
                if hasattr(self, 'redis_client'):
                    await self.redis_client.delete(f"{self.redis_namespace}:*")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        results = {}
        for key in keys:
            results[key] = await self.get(key)
        return results
    
    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        success = True
        for key, value in items.items():
            if not await self.set(key, value, ttl):
                success = False
        return success
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self._stats.copy()
        
        if self.backend == 'memory':
            with self.memory_lock:
                stats['total_entries'] = len(self._memory_cache)
                stats['memory_usage_mb'] = self._calculate_memory_usage()
        
        return stats
    
    async def cleanup_expired(self):
        """Clean up expired entries"""
        try:
            if self.backend == 'memory':
                await self._cleanup_memory()
            elif self.backend == 'sqlite':
                await self._cleanup_sqlite()
            elif self.backend == 'redis':
                await self._cleanup_redis()
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {str(e)}")
    
    # Memory backend implementations
    async def _get_memory(self, key: str, default: Any = None) -> Any:
        """Get from memory cache"""
        with self.memory_lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if entry.expires_at > datetime.utcnow():
                    # Update access statistics
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()
                    self._stats['hits'] += 1
                    return entry.value
                else:
                    # Expired, remove it
                    del self._memory_cache[key]
                    self._stats['expired_cleanups'] += 1
            
            self._stats['misses'] += 1
            return default
    
    async def _set_memory(self, key: str, value: Any, ttl: int) -> bool:
        """Set in memory cache"""
        with self.memory_lock:
            # Check if we need to evict entries
            if len(self._memory_cache) >= self.max_size:
                await self._evict_memory_entries()
            
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            self._memory_cache[key] = entry
            self._stats['sets'] += 1
            return True
    
    async def _delete_memory(self, key: str) -> bool:
        """Delete from memory cache"""
        with self.memory_lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                self._stats['deletes'] += 1
                return True
            return False
    
    async def _cleanup_memory(self):
        """Clean up expired memory entries"""
        with self.memory_lock:
            current_time = datetime.utcnow()
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if entry.expires_at <= current_time
            ]
            
            for key in expired_keys:
                del self._memory_cache[key]
                self._stats['expired_cleanups'] += 1
    
    async def _evict_memory_entries(self):
        """Evict entries when cache is full"""
        with self.memory_lock:
            # Sort by last accessed time (LRU)
            sorted_entries = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Evict 10% of entries
            evict_count = max(1, len(sorted_entries) // 10)
            for key, _ in sorted_entries[:evict_count]:
                del self._memory_cache[key]
                self._stats['evictions'] += 1
    
    def _calculate_memory_usage(self) -> float:
        """Calculate memory usage in MB"""
        import sys
        total_size = 0
        for entry in self._memory_cache.values():
            total_size += sys.getsizeof(entry.value)
            total_size += sys.getsizeof(entry)
        return total_size / (1024 * 1024)
    
    # SQLite backend implementations
    async def _get_sqlite(self, key: str, default: Any = None) -> Any:
        """Get from SQLite cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT value, access_count FROM cache 
                WHERE key = ? AND expires_at > ?
            ''', (key, datetime.utcnow()))
            
            row = cursor.fetchone()
            if row:
                # Update access statistics
                cursor.execute('''
                    UPDATE cache 
                    SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP 
                    WHERE key = ?
                ''', (key,))
                conn.commit()
                
                self._stats['hits'] += 1
                return json.loads(row[0])
            else:
                self._stats['misses'] += 1
                return default
    
    async def _set_sqlite(self, key: str, value: Any, ttl: int) -> bool:
        """Set in SQLite cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cache 
                    (key, value, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    key,
                    json.dumps(value, default=str),
                    datetime.utcnow(),
                    expires_at
                ))
                
                conn.commit()
                self._stats['sets'] += 1
                return True
        except Exception as e:
            self.logger.error(f"SQLite cache set error: {str(e)}")
            return False
    
    async def _delete_sqlite(self, key: str) -> bool:
        """Delete from SQLite cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self._stats['deletes'] += 1
                    return True
            return False
        except Exception as e:
            self.logger.error(f"SQLite cache delete error: {str(e)}")
            return False
    
    async def _cleanup_sqlite(self):
        """Clean up expired SQLite entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cache WHERE expires_at <= ?', (datetime.utcnow(),))
                cleaned = cursor.rowcount
                conn.commit()
                
                if cleaned > 0:
                    self._stats['expired_cleanups'] += cleaned
                    self.logger.debug(f"Cleaned {cleaned} expired SQLite cache entries")
        except Exception as e:
            self.logger.error(f"SQLite cleanup error: {str(e)}")
    
    # Redis backend implementations
    async def _get_redis(self, key: str, default: Any = None) -> Any:
        """Get from Redis cache"""
        if not hasattr(self, 'redis_client'):
            return default
        
        try:
            full_key = f"{self.redis_namespace}:{key}"
            value = await self.redis_client.get(full_key)
            
            if value is not None:
                self._stats['hits'] += 1
                return json.loads(value)
            else:
                self._stats['misses'] += 1
                return default
        except Exception as e:
            self.logger.error(f"Redis cache get error: {str(e)}")
            return default
    
    async def _set_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set in Redis cache"""
        if not hasattr(self, 'redis_client'):
            return False
        
        try:
            full_key = f"{self.redis_namespace}:{key}"
            serialized_value = json.dumps(value, default=str)
            
            await self.redis_client.setex(full_key, ttl, serialized_value)
            self._stats['sets'] += 1
            return True
        except Exception as e:
            self.logger.error(f"Redis cache set error: {str(e)}")
            return False
    
    async def _delete_redis(self, key: str) -> bool:
        """Delete from Redis cache"""
        if not hasattr(self, 'redis_client'):
            return False
        
        try:
            full_key = f"{self.redis_namespace}:{key}"
            deleted = await self.redis_client.delete(full_key)
            
            if deleted > 0:
                self._stats['deletes'] += 1
                return True
            return False
        except Exception as e:
            self.logger.error(f"Redis cache delete error: {str(e)}")
            return False
    
    async def _cleanup_redis(self):
        """Clean up expired Redis entries (automatic with TTL)"""
        # Redis handles expiration automatically with TTL
        # This method is a no-op but kept for interface consistency
        pass
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task for memory backend"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired()
            except Exception as e:
                self.logger.error(f"Error in periodic cache cleanup: {str(e)}")
    
    async def shutdown(self):
        """Shutdown the cache store"""
        self.logger.info("Shutting down cache store")
        
        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close Redis connection
        if self.backend == 'redis' and hasattr(self, 'redis_client'):
            await self.redis_client.close()
        
        # Clear memory cache
        if self.backend == 'memory':
            with self.memory_lock:
                self._memory_cache.clear()


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        # Test memory cache
        print("Testing memory cache...")
        cache = CacheStore({'type': 'memory', 'ttl': 10, 'max_size': 100})
        await cache.initialize()
        
        # Set and get
        await cache.set('test_key', {'data': 'test_value'}, 30)
        value = await cache.get('test_key')
        print(f"Retrieved value: {value}")
        
        # Stats
        stats = await cache.get_stats()
        print(f"Cache stats: {stats}")
        
        # Cleanup
        await cache.shutdown()
        
        # Test SQLite cache
        print("\nTesting SQLite cache...")
        cache = CacheStore({'type': 'sqlite', 'db_path': 'test_cache.db', 'ttl': 10})
        await cache.initialize()
        
        await cache.set('sqlite_key', {'data': 'sqlite_value'}, 30)
        value = await cache.get('sqlite_key')
        print(f"Retrieved value: {value}")
        
        await cache.shutdown()
        
        # Remove test database
        import os
        if os.path.exists('test_cache.db'):
            os.remove('test_cache.db')
    
    asyncio.run(main())