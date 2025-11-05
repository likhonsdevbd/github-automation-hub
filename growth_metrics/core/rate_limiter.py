"""
Rate Limiter for GitHub API Integration
=======================================

Implements rate limit awareness and optimization strategies:
- Primary and secondary rate limit handling
- Exponential backoff with jitter
- Rate budget management
- Request caching and deduplication
- Circuit breaker pattern for resilience
"""

import time
import logging
from typing import Dict, Optional, Any, Callable
from collections import deque
from datetime import datetime, timedelta
import hashlib
import threading

logger = logging.getLogger(__name__)


class RateLimitStats:
    """Track rate limit statistics per endpoint"""
    
    def __init__(self):
        self.primary_remaining = 5000
        self.primary_reset = 0
        self.secondary_remaining = 30
        self.secondary_reset = 0
        self.daily_remaining = 0
        self.daily_reset = 0
        self.requests_this_hour = 0
        self.hour_window_start = datetime.now()
        
    def update_from_headers(self, headers: Dict[str, str]) -> None:
        """Update stats from GitHub API response headers"""
        # Primary rate limit
        if 'x-ratelimit-remaining' in headers:
            self.primary_remaining = int(headers['x-ratelimit-remaining'])
        if 'x-ratelimit-reset' in headers:
            self.primary_reset = int(headers['x-ratelimit-reset'])
            
        # Secondary rate limit
        if 'retry-after' in headers:
            self.secondary_remaining = 0
            self.secondary_reset = time.time() + float(headers['retry-after'])
            
        # Search API rate limit (daily)
        if 'x-ratelimit-remaining' in headers and 'core' in headers.get('x-ratelimit-resource', ''):
            self.daily_remaining = int(headers['x-ratelimit-remaining'])
        if 'x-ratelimit-reset' in headers and 'core' in headers.get('x-ratelimit-resource', ''):
            self.daily_reset = int(headers['x-ratelimit-reset'])
            
    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits"""
        now = datetime.now()
        
        # Reset hourly counter
        if now - self.hour_window_start >= timedelta(hours=1):
            self.requests_this_hour = 0
            self.hour_window_start = now
            
        # Check primary rate limit
        if self.primary_remaining <= 0:
            return False
            
        # Check secondary rate limit
        if self.secondary_remaining <= 0 and time.time() < self.secondary_reset:
            return False
            
        # Check hourly budget (configurable based on workload)
        hourly_budget = self.get_hourly_budget()
        if self.requests_this_hour >= hourly_budget:
            return False
            
        return True
        
    def get_hourly_budget(self) -> int:
        """Get hourly request budget based on workload type"""
        # This would be configurable based on the workload type
        return 2000  # Conservative budget
        
    def record_request(self) -> None:
        """Record that a request was made"""
        self.requests_this_hour += 1
        self.primary_remaining -= 1
        
    def get_wait_time(self) -> float:
        """Get time to wait before making next request"""
        wait_times = []
        
        # Primary rate limit wait time
        if self.primary_remaining <= 0:
            wait_times.append(self.primary_reset - time.time())
            
        # Secondary rate limit wait time
        if self.secondary_remaining <= 0 and time.time() < self.secondary_reset:
            wait_times.append(self.secondary_reset - time.time())
            
        return max(wait_times) if wait_times else 0


class RequestCache:
    """Simple in-memory cache for API responses"""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self.cache = {}
        self.ttl = ttl
        self.lock = threading.Lock()
        
    def _generate_key(self, method: str, url: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key for request"""
        key_data = f"{method.upper()}:{url}:{str(sorted(params.items())) if params else ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    def get(self, method: str, url: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Get cached response if available and not expired"""
        key = self._generate_key(method, url, params)
        
        with self.lock:
            if key in self.cache:
                timestamp, data = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    logger.debug(f"Cache hit for {method} {url}")
                    return data
                else:
                    del self.cache[key]
                    
        return None
        
    def set(self, method: str, url: str, data: Any, params: Dict[str, Any] = None) -> None:
        """Cache response data"""
        key = self._generate_key(method, url, params)
        
        with self.lock:
            self.cache[key] = (time.time(), data)
            
    def clear(self) -> None:
        """Clear all cached data"""
        with self.lock:
            self.cache.clear()


class RateLimiter:
    """
    Rate limiter with intelligent backoff and caching for GitHub API calls
    
    Implements the design principles from the growth analytics system:
    - Conservative request budgets
    - Exponential backoff with jitter
    - Request deduplication and caching
    - Circuit breaker pattern
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.stats = RateLimitStats()
        self.cache = RequestCache(ttl=self.config.get('cache_ttl', 300))
        
        # Circuit breaker state
        self.circuit_breaker_open = False
        self.circuit_breaker_last_failure = 0
        self.failure_threshold = self.config.get('failure_threshold', 10)
        self.failure_timeout = self.config.get('failure_timeout', 60)
        
        # Request tracking
        self.request_times = deque(maxlen=1000)
        self.lock = threading.Lock()
        
    def check_rate_limits(self, headers: Dict[str, str]) -> None:
        """Update rate limit stats from API response"""
        self.stats.update_from_headers(headers)
        
    def wait_if_needed(self) -> bool:
        """
        Wait if rate limits require it
        Returns True if we can proceed, False if we should skip the request
        """
        wait_time = self.stats.get_wait_time()
        
        if wait_time > 0:
            logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
            return True
            
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            return False
            
        return True
        
    def make_request_with_backoff(self, request_func: Callable, *args, **kwargs) -> Any:
        """
        Make request with exponential backoff and circuit breaker
        """
        max_retries = self.config.get('max_retries', 5)
        base_delay = self.config.get('base_delay', 1)
        max_delay = self.config.get('max_delay', 300)
        
        for attempt in range(max_retries + 1):
            try:
                # Check if we can make the request
                if not self.wait_if_needed():
                    raise Exception("Circuit breaker is open or rate limits exceeded")
                    
                # Record request time
                with self.lock:
                    self.request_times.append(time.time())
                    
                result = request_func(*args, **kwargs)
                
                # Check circuit breaker - request succeeded
                if self.circuit_breaker_open:
                    self.circuit_breaker_open = False
                    logger.info("Circuit breaker recovered")
                    
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Rate limit error
                if any(term in error_msg for term in ['429', 'rate limit', 'secondary rate limit']):
                    wait_time = self._extract_wait_time(e)
                    if wait_time:
                        logger.warning(f"Rate limit error, waiting {wait_time} seconds")
                        time.sleep(wait_time)
                        continue
                        
                # Server error (5xx) - retry
                elif any(term in error_msg for term in ['500', '502', '503', '504', 'gateway']):
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        # Add jitter to prevent thundering herd
                        delay += delay * 0.1 * (time.time() % 1)
                        logger.warning(f"Server error, retrying in {delay:.1f} seconds (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                        
                # Circuit breaker
                self._record_failure()
                raise e
                
        # All retries failed
        self._record_failure()
        raise Exception(f"Request failed after {max_retries} retries")
        
    def _extract_wait_time(self, error: Exception) -> Optional[float]:
        """Extract wait time from rate limit error message"""
        error_msg = str(error)
        
        # Look for Retry-After header value
        if 'retry-after:' in error_msg:
            try:
                return float(error_msg.split('retry-after:')[1].split()[0])
            except (ValueError, IndexError):
                pass
                
        # Look for numeric values in parentheses
        import re
        matches = re.findall(r'\((\d+(?:\.\d+)?)s?\)', error_msg)
        if matches:
            return float(matches[0])
            
        return None
        
    def _record_failure(self) -> None:
        """Record failure for circuit breaker"""
        self.circuit_breaker_last_failure = time.time()
        
        # Count recent failures
        recent_failures = sum(
            1 for t in list(self.request_times)[-50:] 
            if time.time() - t < 300  # Last 5 minutes
        )
        
        if recent_failures >= self.failure_threshold:
            self.circuit_breaker_open = True
            logger.error(f"Circuit breaker opened due to {recent_failures} failures")
            
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker should be open"""
        if not self.circuit_breaker_open:
            return False
            
        # Check if enough time has passed to try again
        if time.time() - self.circuit_breaker_last_failure > self.failure_timeout:
            self.circuit_breaker_open = False
            logger.info("Circuit breaker timeout expired, allowing requests")
            return False
            
        return True
        
    def get_cached_response(self, method: str, url: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Get cached response if available"""
        return self.cache.get(method, url, params)
        
    def cache_response(self, method: str, url: str, data: Any, params: Dict[str, Any] = None) -> None:
        """Cache response data"""
        self.cache.set(method, url, data, params)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limit statistics"""
        return {
            'primary_remaining': self.stats.primary_remaining,
            'primary_reset': self.stats.primary_reset,
            'secondary_remaining': self.stats.secondary_remaining,
            'requests_this_hour': self.stats.requests_this_hour,
            'circuit_breaker_open': self.circuit_breaker_open,
            'cache_size': len(self.cache.cache)
        }
        
    def clear_cache(self) -> None:
        """Clear request cache"""
        self.cache.clear()
        
    def get_request_rate(self) -> float:
        """Get current request rate (requests per minute)"""
        now = time.time()
        
        # Count requests in the last minute
        recent_requests = sum(
            1 for t in list(self.request_times) 
            if now - t < 60
        )
        
        return recent_requests / 60.0