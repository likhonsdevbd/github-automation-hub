"""
Error Handler and Retry Logic
=============================

Comprehensive error handling for GitHub API integration:
- Categorized error types and retry strategies
- Exponential backoff with jitter
- Error reporting and logging
- Automatic recovery mechanisms
- Fallback strategies for degraded functionality
"""

import logging
import time
import functools
import traceback
from typing import Dict, Any, Optional, Callable, Union, Type
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Categorized error types for different handling strategies"""
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE_NOT_FOUND = "resource_not_found"
    VALIDATION = "validation"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_type: ErrorType
    message: str
    status_code: Optional[int] = None
    retry_after: Optional[float] = None
    endpoint: Optional[str] = None
    timestamp: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RetryStrategy:
    """Configurable retry strategies for different error types"""
    
    def __init__(self):
        self.strategies = {
            ErrorType.RATE_LIMIT: {
                'max_retries': 5,
                'base_delay': 2,
                'max_delay': 300,
                'jitter': True,
                'respect_retry_after': True
            },
            ErrorType.SERVER_ERROR: {
                'max_retries': 3,
                'base_delay': 1,
                'max_delay': 60,
                'jitter': True,
                'respect_retry_after': False
            },
            ErrorType.NETWORK_ERROR: {
                'max_retries': 5,
                'base_delay': 0.5,
                'max_delay': 120,
                'jitter': True,
                'respect_retry_after': False
            },
            ErrorType.TIMEOUT: {
                'max_retries': 3,
                'base_delay': 2,
                'max_delay': 60,
                'jitter': True,
                'respect_retry_after': False
            },
            ErrorType.AUTHENTICATION: {
                'max_retries': 0,
                'base_delay': 0,
                'max_delay': 0,
                'jitter': False,
                'respect_retry_after': False
            },
            ErrorType.AUTHORIZATION: {
                'max_retries': 0,
                'base_delay': 0,
                'max_delay': 0,
                'jitter': False,
                'respect_retry_after': False
            },
            ErrorType.RESOURCE_NOT_FOUND: {
                'max_retries': 0,
                'base_delay': 0,
                'max_delay': 0,
                'jitter': False,
                'respect_retry_after': False
            },
            ErrorType.VALIDATION: {
                'max_retries': 0,
                'base_delay': 0,
                'max_delay': 0,
                'jitter': False,
                'respect_retry_after': False
            },
            ErrorType.QUOTA_EXCEEDED: {
                'max_retries': 1,
                'base_delay': 3600,  # 1 hour
                'max_delay': 86400,  # 24 hours
                'jitter': False,
                'respect_retry_after': True
            },
            ErrorType.UNKNOWN: {
                'max_retries': 1,
                'base_delay': 5,
                'max_delay': 60,
                'jitter': True,
                'respect_retry_after': False
            }
        }
    
    def get_strategy(self, error_type: ErrorType) -> Dict[str, Any]:
        """Get retry strategy for error type"""
        return self.strategies.get(error_type, self.strategies[ErrorType.UNKNOWN])
    
    def calculate_delay(self, error_type: ErrorType, retry_count: int, retry_after: Optional[float] = None) -> float:
        """Calculate delay before retry"""
        strategy = self.get_strategy(error_type)
        
        # Respect Retry-After header if provided and strategy allows it
        if retry_after and strategy.get('respect_retry_after', False):
            return max(retry_after, 1)  # Minimum 1 second
            
        # Calculate exponential backoff with jitter
        base_delay = strategy['base_delay']
        max_delay = strategy['max_delay']
        
        if retry_count == 0:
            return 0
            
        delay = min(base_delay * (2 ** retry_count), max_delay)
        
        if strategy.get('jitter', False):
            # Add jitter to prevent thundering herd
            jitter = delay * 0.1 * (time.time() % 1)
            delay += jitter
            
        return delay


class ErrorClassifier:
    """Classify GitHub API errors into error types"""
    
    @staticmethod
    def classify_error(error: Exception, response_data: Optional[Dict[str, Any]] = None) -> ErrorType:
        """Classify error based on exception type and response data"""
        
        error_msg = str(error).lower()
        
        # Authentication errors
        if any(term in error_msg for term in ['401', 'unauthorized', 'authentication']):
            return ErrorType.AUTHENTICATION
            
        # Authorization errors  
        if any(term in error_msg for term in ['403', 'forbidden', 'permission denied']):
            return ErrorType.AUTHORIZATION
            
        # Rate limiting
        if any(term in error_msg for term in ['429', 'rate limit', 'secondary rate limit']):
            return ErrorType.RATE_LIMIT
            
        # Resource not found
        if any(term in error_msg for term in ['404', 'not found']):
            return ErrorType.RESOURCE_NOT_FOUND
            
        # Server errors
        if any(term in error_msg for term in ['500', '502', '503', '504', 'server error', 'gateway']):
            return ErrorType.SERVER_ERROR
            
        # Network errors
        if any(term in error_msg for term in ['connection', 'timeout', 'network']):
            return ErrorType.NETWORK_ERROR
            
        # Validation errors
        if any(term in error_msg for term in ['validation', 'invalid', 'bad request']):
            return ErrorType.VALIDATION
            
        # Quota exceeded
        if any(term in error_msg for term in ['quota', 'limit exceeded', 'api']):
            return ErrorType.QUOTA_EXCEEDED
            
        return ErrorType.UNKNOWN


class ErrorHandler:
    """
    Comprehensive error handler with retry logic and reporting
    
    Provides:
    - Automatic error classification and retry
    - Detailed error logging and reporting
    - Circuit breaker pattern
    - Fallback strategies
    - Recovery tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.retry_strategy = RetryStrategy()
        self.error_classifier = ErrorClassifier()
        
        # Circuit breaker state
        self.failure_counts = {}  # endpoint -> failure count
        self.circuit_breaker_thresholds = self.config.get('circuit_breaker_thresholds', {})
        self.circuit_breaker_timeouts = self.config.get('circuit_breaker_timeouts', {})
        
        # Error tracking
        self.error_history = []
        self.max_history_size = self.config.get('max_error_history', 1000)
        
        # Recovery tracking
        self.recovery_attempts = []
        
    def handle_request_with_retry(self, func: Callable, *args, endpoint: str = None, **kwargs) -> Any:
        """
        Execute function with comprehensive error handling and retry logic
        
        Args:
            func: Function to execute
            *args: Function arguments
            endpoint: Optional endpoint identifier for tracking
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises final exception
            
        Raises:
            Exception: After all retries are exhausted
        """
        
        retry_count = 0
        last_error = None
        endpoint = endpoint or "unknown"
        
        while True:
            try:
                # Check circuit breaker
                if self._is_circuit_breaker_open(endpoint):
                    raise Exception(f"Circuit breaker is open for endpoint: {endpoint}")
                    
                result = func(*args, **kwargs)
                
                # Request succeeded - reset failure count
                if endpoint in self.failure_counts:
                    logger.debug(f"Request succeeded for {endpoint}, resetting failure count")
                    del self.failure_counts[endpoint]
                    
                return result
                
            except Exception as e:
                last_error = e
                
                # Classify error
                error_type = self.error_classifier.classify_error(e)
                retry_after = self._extract_retry_after(e)
                
                # Create error context
                error_context = ErrorContext(
                    error_type=error_type,
                    message=str(e),
                    retry_after=retry_after,
                    endpoint=endpoint,
                    retry_count=retry_count,
                    max_retries=self.retry_strategy.get_strategy(error_type)['max_retries']
                )
                
                # Log error
                self._log_error(error_context)
                
                # Check if we should retry
                if retry_count >= error_context.max_retries:
                    logger.error(f"Max retries ({error_context.max_retries}) exceeded for {endpoint}")
                    self._record_failure(endpoint)
                    break
                    
                # Calculate delay
                delay = self.retry_strategy.calculate_delay(error_type, retry_count, retry_after)
                
                if delay > 0:
                    logger.info(f"Retrying {endpoint} in {delay:.1f}s (attempt {retry_count + 1}/{error_context.max_retries})")
                    time.sleep(delay)
                    
                retry_count += 1
                
        # All retries failed
        self._record_failure(endpoint)
        
        # Store final error for reporting
        if error_context:
            self._add_to_error_history(error_context)
            
        raise last_error
        
    def _extract_retry_after(self, error: Exception) -> Optional[float]:
        """Extract retry-after value from error"""
        error_msg = str(error)
        
        # Look for retry-after in response headers
        if 'retry-after:' in error_msg:
            try:
                return float(error_msg.split('retry-after:')[1].split()[0])
            except (ValueError, IndexError):
                pass
                
        return None
        
    def _log_error(self, error_context: ErrorContext) -> None:
        """Log error with context"""
        
        log_data = {
            'error_type': error_context.error_type.value,
            'message': error_context.message,
            'endpoint': error_context.endpoint,
            'retry_count': error_context.retry_count,
            'timestamp': error_context.timestamp.isoformat()
        }
        
        if error_context.status_code:
            log_data['status_code'] = error_context.status_code
            
        if error_context.retry_after:
            log_data['retry_after'] = error_context.retry_after
            
        logger.error(f"GitHub API Error: {json.dumps(log_data)}", exc_info=True)
        
    def _is_circuit_breaker_open(self, endpoint: str) -> bool:
        """Check if circuit breaker is open for endpoint"""
        if endpoint not in self.failure_counts:
            return False
            
        failure_threshold = self.circuit_breaker_thresholds.get(endpoint, 5)
        timeout = self.circuit_breaker_timeouts.get(endpoint, 300)  # 5 minutes default
        
        return self.failure_counts[endpoint] >= failure_threshold
        
    def _record_failure(self, endpoint: str) -> None:
        """Record failure for circuit breaker"""
        self.failure_counts[endpoint] = self.failure_counts.get(endpoint, 0) + 1
        
        logger.warning(f"Failure recorded for {endpoint}, count: {self.failure_counts[endpoint]}")
        
    def _add_to_error_history(self, error_context: ErrorContext) -> None:
        """Add error to history for analysis"""
        self.error_history.append(error_context)
        
        # Trim history if too large
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
            
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for recent period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            error for error in self.error_history 
            if error.timestamp > cutoff_time
        ]
        
        if not recent_errors:
            return {'total_errors': 0, 'error_types': {}, 'top_endpoints': []}
            
        # Count by error type
        error_types = {}
        for error in recent_errors:
            error_type = error.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        # Count by endpoint
        endpoint_counts = {}
        for error in recent_errors:
            endpoint = error.endpoint or 'unknown'
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
            
        top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_errors': len(recent_errors),
            'error_types': error_types,
            'top_endpoints': top_endpoints,
            'period_hours': hours
        }
        
    def should_use_fallback(self, endpoint: str) -> bool:
        """Determine if fallback strategy should be used"""
        circuit_open = self._is_circuit_breaker_open(endpoint)
        error_summary = self.get_error_summary(hours=1)
        
        # Use fallback if circuit is open or error rate is high
        if circuit_open:
            return True
            
        recent_errors = error_summary['total_errors']
        if recent_errors > 100:  # High error threshold
            logger.warning(f"High error rate detected: {recent_errors} errors in last hour")
            return True
            
        return False
        
    def reset_circuit_breaker(self, endpoint: str) -> None:
        """Manually reset circuit breaker for endpoint"""
        if endpoint in self.failure_counts:
            del self.failure_counts[endpoint]
            logger.info(f"Circuit breaker reset for {endpoint}")


def with_error_handling(config: Dict[str, Any] = None):
    """
    Decorator for automatic error handling and retry logic
    
    Usage:
        @with_error_handling({'max_retries': 3})
        def fetch_data():
            # Your GitHub API call here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(config)
            return handler.handle_request_with_retry(func, *args, endpoint=func.__name__, **kwargs)
        return wrapper
    return decorator


# Utility functions for common error scenarios

def handle_api_response(response_data: Dict[str, Any], expected_fields: list) -> bool:
    """Validate API response has expected fields"""
    for field in expected_fields:
        if field not in response_data:
            logger.warning(f"Missing expected field '{field}' in API response")
            return False
    return True


def extract_error_details(error: Exception) -> Dict[str, Any]:
    """Extract detailed error information for logging"""
    return {
        'type': type(error).__name__,
        'message': str(error),
        'traceback': traceback.format_exc()
    }