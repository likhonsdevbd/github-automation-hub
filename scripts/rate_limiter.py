"""
Rate Limiter - Conservative, compliant rate limiting for GitHub automation.

Implements safety-first rate limiting with:
- ≤24 actions/hour default limit
- Exponential backoff on 429 errors
- Hard stops on 422 errors
- Jittered pacing for human-like behavior
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class RateLimitBucket:
    """Represents a rate limit bucket with refill mechanism."""
    capacity: int
    tokens: int
    refill_rate: float  # tokens per second
    last_refill: datetime
    
    def __post_init__(self):
        self.tokens = self.capacity


class RateLimiter:
    """
    Conservative rate limiter implementing safety-first controls.
    
    Default configuration:
    - 24 actions/hour total (20-30 range from architecture)
    - Separate buckets for follow/unfollow operations
    - Exponential backoff on rate limit errors
    - Jittered delays for human-like behavior
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize rate limit buckets
        self.buckets = {
            'follow': RateLimitBucket(
                capacity=config.get('max_actions_per_hour', 24),
                tokens=config.get('max_actions_per_hour', 24),
                refill_rate=config.get('max_actions_per_hour', 24) / 3600,  # per second
                last_refill=datetime.now()
            ),
            'unfollow': RateLimitBucket(
                capacity=config.get('max_actions_per_hour', 24),
                tokens=config.get('max_actions_per_hour', 24),
                refill_rate=config.get('max_actions_per_hour', 24) / 3600,
                last_refill=datetime.now()
            ),
            'api_calls': RateLimitBucket(
                capacity=config.get('max_api_calls_per_hour', 5000),
                tokens=config.get('max_api_calls_per_hour', 5000),
                refill_rate=config.get('max_api_calls_per_hour', 5000) / 3600,
                last_refill=datetime.now()
            )
        }
        
        # Backoff state
        self.backoff_until: Optional[datetime] = None
        self.backoff_multiplier = 1.0
        
        # Statistics
        self.stats = {
            'total_actions': 0,
            'rate_limited_actions': 0,
            'backoff_events': 0,
            'last_action_time': None
        }
    
    def can_execute_action(self, action_type: str) -> bool:
        """
        Check if an action can be executed within rate limits.
        
        Args:
            action_type: Type of action ('follow', 'unfollow', 'api_call')
            
        Returns:
            bool: True if action can be executed
        """
        self._refill_buckets()
        
        if self.backoff_until and datetime.now() < self.backoff_until:
            return False
        
        bucket = self.buckets.get(action_type)
        if not bucket:
            self.logger.warning(f"Unknown action type: {action_type}")
            return False
        
        if bucket.tokens >= 1:
            return True
        
        self.stats['rate_limited_actions'] += 1
        return False
    
    def execute_with_delay(self, action_type: str, base_delay: float = None) -> float:
        """
        Execute action with appropriate delay based on safety requirements.
        
        Args:
            action_type: Type of action
            base_delay: Base delay in seconds
            
        Returns:
            float: Actual delay applied
        """
        if not base_delay:
            base_delay = self.config.get('base_delay_seconds', 150)  # 2.5 minutes default
        
        # Calculate jittered delay
        delay = self._calculate_jittered_delay(base_delay, action_type)
        
        # Add additional safety delays for consecutive actions
        if self.stats['last_action_time']:
            time_since_last = (datetime.now() - self.stats['last_action_time']).total_seconds()
            min_gap = self.config.get('min_gap_between_actions', 180)  # 3 minutes
            if time_since_last < min_gap:
                additional_delay = min_gap - time_since_last
                delay = max(delay, additional_delay)
        
        self.logger.debug(f"Applying {delay:.1f}s delay for {action_type} action")
        time.sleep(delay)
        
        return delay
    
    def record_action(self, action_type: str):
        """Record that an action was executed."""
        self._refill_buckets()
        
        bucket = self.buckets.get(action_type)
        if bucket and bucket.tokens >= 1:
            bucket.tokens -= 1
            self.stats['total_actions'] += 1
            self.stats['last_action_time'] = datetime.now()
            
            self.logger.debug(f"Recorded {action_type} action. Tokens remaining: {bucket.tokens}")
    
    def record_api_call(self):
        """Record an API call."""
        self._refill_buckets()
        
        bucket = self.buckets['api_calls']
        if bucket.tokens >= 1:
            bucket.tokens -= 1
    
    def handle_rate_limit_hit(self, response_headers: Dict[str, str] = None):
        """
        Handle rate limit exceeded (429) with exponential backoff.
        
        Args:
            response_headers: GitHub API response headers
        """
        self.stats['backoff_events'] += 1
        
        # Calculate backoff duration
        backoff_duration = self._calculate_backoff_duration(response_headers)
        
        self.backoff_until = datetime.now() + timedelta(seconds=backoff_duration)
        self.backoff_multiplier = min(self.backoff_multiplier * 2, 300)  # Cap at 5 minutes
        
        self.logger.warning(f"Rate limit hit. Backing off for {backoff_duration:.1f} seconds")
    
    def handle_validation_error(self):
        """
        Handle validation/spam signal (422) - should trigger emergency stop.
        This method exists for API consistency but should typically
        trigger an immediate halt in the automation manager.
        """
        self.logger.error("422 validation error - automation should be halted")
        self.backoff_until = datetime.now() + timedelta(hours=1)
        self.backoff_multiplier = min(self.backoff_multiplier * 2, 3600)  # Cap at 1 hour
    
    def get_remaining_calls(self) -> int:
        """Get remaining API calls in current window."""
        self._refill_buckets()
        return self.buckets['api_calls'].tokens
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive rate limiter status."""
        self._refill_buckets()
        
        return {
            'buckets': {
                name: {
                    'capacity': bucket.capacity,
                    'tokens': bucket.tokens,
                    'refill_rate_per_hour': bucket.refill_rate * 3600
                }
                for name, bucket in self.buckets.items()
            },
            'backoff': {
                'active': self.backoff_until and datetime.now() < self.backoff_until,
                'until': self.backoff_until.isoformat() if self.backoff_until else None,
                'multiplier': self.backoff_multiplier
            },
            'stats': self.stats,
            'compliance': self._assess_compliance()
        }
    
    def _refill_buckets(self):
        """Refill tokens in all buckets based on elapsed time."""
        now = datetime.now()
        
        for bucket in self.buckets.values():
            elapsed = (now - bucket.last_refill).total_seconds()
            if elapsed > 0:
                tokens_to_add = elapsed * bucket.refill_rate
                bucket.tokens = min(bucket.capacity, bucket.tokens + tokens_to_add)
                bucket.last_refill = now
    
    def _calculate_jittered_delay(self, base_delay: float, action_type: str) -> float:
        """
        Calculate jittered delay for human-like behavior.
        
        Uses a combination of uniform and log-normal distributions
        to avoid predictable patterns.
        """
        # Base jitter factor (20-40% variability)
        jitter_factor = random.uniform(0.8, 1.4)
        
        # Add random extra delay (log-normal for realistic variability)
        log_delay = random.lognormvariate(
            mean=0.0,  # log-normal with mean 0
            sigma=0.5  # standard deviation
        ) * base_delay * 0.1
        
        total_delay = base_delay * jitter_factor + log_delay
        
        # Apply action-type specific adjustments
        if action_type == 'follow':
            # Slightly longer delays for follow actions (more sensitive)
            total_delay *= random.uniform(1.1, 1.3)
        elif action_type == 'unfollow':
            # Shorter delays for unfollow (less sensitive)
            total_delay *= random.uniform(0.9, 1.1)
        
        # Apply backoff multiplier if in backoff period
        if self.backoff_until and datetime.now() < self.backoff_until:
            total_delay *= self.backoff_multiplier
        
        # Ensure minimum delay
        min_delay = self.config.get('min_delay_seconds', 60)
        return max(total_delay, min_delay)
    
    def _calculate_backoff_duration(self, response_headers: Dict[str, str] = None) -> float:
        """
        Calculate backoff duration based on GitHub headers or exponential backoff.
        
        Args:
            response_headers: GitHub API response headers
            
        Returns:
            float: Backoff duration in seconds
        """
        # Check for Retry-After header (GitHub's preferred method)
        if response_headers and 'Retry-After' in response_headers:
            try:
                retry_after = int(response_headers['Retry-After'])
                return max(retry_after, 60)  # Minimum 60 seconds
            except (ValueError, TypeError):
                pass
        
        # Use rate limit reset header if available
        if response_headers and 'X-RateLimit-Reset' in response_headers:
            try:
                reset_time = int(response_headers['X-RateLimit-Reset'])
                current_time = int(time.time())
                return max(reset_time - current_time, 60)
            except (ValueError, TypeError):
                pass
        
        # Fall back to exponential backoff
        return min(60 * self.backoff_multiplier, 3600)  # Cap at 1 hour
    
    def _assess_compliance(self) -> Dict[str, Any]:
        """Assess compliance based on rate limiting statistics."""
        if self.stats['total_actions'] == 0:
            return {'status': 'no_data'}
        
        rate_limited_ratio = self.stats['rate_limited_actions'] / self.stats['total_actions']
        backoff_ratio = self.stats['backoff_events'] / self.stats['total_actions']
        
        issues = []
        if rate_limited_ratio > 0.3:
            issues.append('high_rate_limiting')
        if backoff_ratio > 0.1:
            issues.append('frequent_backoff')
        if self.backoff_until and datetime.now() < self.backoff_until:
            issues.append('currently_in_backoff')
        
        return {
            'status': 'compliant' if not issues else 'issues_detected',
            'issues': issues,
            'rate_limited_ratio': rate_limited_ratio,
            'backoff_ratio': backoff_ratio,
            'total_actions': self.stats['total_actions']
        }
