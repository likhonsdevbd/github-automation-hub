"""
Rate Limiting System for Safe Follow/Unfollow Automation
Enforces 5-10 actions/hour with safety controls
"""
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from queue import PriorityQueue, Queue
import logging
from ..config.settings import ActionType, FollowAutomationConfig

@dataclass
class RateLimitEvent:
    """Track rate limit events for monitoring"""
    timestamp: datetime
    action_type: ActionType
    response_code: int
    retry_after: Optional[int] = None
    handled: bool = False
    
@dataclass
class ActionToken:
    """Represents an action token with metadata"""
    action_type: ActionType
    target_username: str
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0
    retry_count: int = 0
    
class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens if available"""
        with self.lock:
            now = time.time()
            # Refill tokens based on time elapsed
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def available_tokens(self) -> float:
        """Get current available tokens"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            return min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
    
    def time_until_available(self, tokens: int = 1) -> float:
        """Get time until specified tokens are available"""
        if tokens <= 1:
            tokens_needed = 1
        else:
            tokens_needed = tokens
            
        with self.lock:
            if self.tokens >= tokens_needed:
                return 0
            
            tokens_short = tokens_needed - self.tokens
            return tokens_short / self.refill_rate

class RateLimiter:
    """
    Main rate limiter for follow/unfollow automation
    Implements safety-in-depth with multiple control layers
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Token bucket for per-hour limits
        self.hourly_bucket = TokenBucket(
            capacity=config.rate_limit.max_actions_per_hour,
            refill_rate=config.rate_limit.max_actions_per_hour / 3600  # Per second
        )
        
        # Token bucket for per-day limits
        self.daily_bucket = TokenBucket(
            capacity=config.rate_limit.max_actions_per_day,
            refill_rate=config.rate_limit.max_actions_per_day / 86400  # Per day
        )
        
        # Track action history
        self.action_history: List[datetime] = []
        self.lock = threading.Lock()
        
        # Rate limit event tracking
        self.rate_limit_events: List[RateLimitEvent] = []
        
        # Concurrency control
        self.active_actions = 0
        self.max_concurrent = config.rate_limit.max_concurrent_actions
        
        # Cooldown tracking
        self.cooldown_until = None
        
        # Statistics
        self.total_actions = 0
        self.successful_actions = 0
        self.rate_limited_actions = 0
        self.blocked_actions = 0
    
    def can_execute_action(self, action_type: ActionType) -> bool:
        """Check if action can be executed safely"""
        with self.lock:
            # Check cooldown after enforcement
            if self.cooldown_until and datetime.now() < self.cooldown_until:
                self.logger.warning(f"In cooldown until {self.cooldown_until}")
                return False
            
            # Check concurrency limits
            if self.active_actions >= self.max_concurrent:
                return False
            
            # Check token availability
            if not self.hourly_bucket.consume(1):
                return False
            
            if not self.daily_bucket.consume(1):
                return False
            
            # Record action
            self.action_history.append(datetime.now())
            self.active_actions += 1
            self.total_actions += 1
            
            return True
    
    def get_time_until_next_action(self) -> float:
        """Get time until next action can be executed"""
        hourly_wait = self.hourly_bucket.time_until_available(1)
        daily_wait = self.daily_bucket.time_until_available(1)
        return max(hourly_wait, daily_wait)
    
    def record_action_completion(self, success: bool = True, 
                                response_code: Optional[int] = None,
                                retry_after: Optional[int] = None):
        """Record action completion for monitoring"""
        with self.lock:
            self.active_actions = max(0, self.active_actions - 1)
            
            if success:
                self.successful_actions += 1
            
            if response_code in [429, 422]:
                self._handle_enforcement_signal(response_code, retry_after)
            
            # Clean old history
            cutoff = datetime.now() - timedelta(hours=1)
            self.action_history = [t for t in self.action_history if t > cutoff]
    
    def _handle_enforcement_signal(self, response_code: int, retry_after: Optional[int]):
        """Handle rate limit or enforcement signals"""
        event = RateLimitEvent(
            timestamp=datetime.now(),
            action_type=ActionType.FOLLOW,  # Would be determined from context
            response_code=response_code,
            retry_after=retry_after
        )
        
        self.rate_limit_events.append(event)
        self.logger.error(f"Enforcement signal received: {response_code}")
        
        if response_code == 422:
            # Hard stop on validation errors
            self.trigger_cooldown(
                reason="Validation failed - potential spam",
                duration=3600  # 1 hour
            )
            
        elif response_code == 429:
            # Adaptive backoff on rate limits
            wait_time = retry_after * self.config.rate_limit.retry_after_header_multiplier
            self.trigger_cooldown(
                reason="Rate limit exceeded",
                duration=min(wait_time, 1800)  # Max 30 minutes
            )
    
    def trigger_cooldown(self, reason: str, duration: int):
        """Trigger cooldown period"""
        self.cooldown_until = datetime.now() + timedelta(seconds=duration)
        self.logger.warning(f"Cooldown triggered: {reason} for {duration}s")
        
        # Clear any pending cooldown after duration
        threading.Timer(duration, self._clear_cooldown).start()
    
    def _clear_cooldown(self):
        """Clear cooldown period"""
        self.cooldown_until = None
        self.logger.info("Cooldown period ended")
    
    def get_statistics(self) -> Dict:
        """Get rate limiter statistics"""
        with self.lock:
            success_rate = (
                self.successful_actions / max(self.total_actions, 1) * 100
            )
            
            recent_rate = len([
                t for t in self.action_history 
                if t > datetime.now() - timedelta(hours=1)
            ])
            
            return {
                "total_actions": self.total_actions,
                "successful_actions": self.successful_actions,
                "success_rate_percent": round(success_rate, 2),
                "actions_last_hour": recent_rate,
                "active_actions": self.active_actions,
                "rate_limit_events": len(self.rate_limit_events),
                "in_cooldown": self.cooldown_until is not None,
                "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None,
                "hourly_tokens_available": self.hourly_bucket.available_tokens(),
                "daily_tokens_available": self.daily_bucket.available_tokens()
            }

class ActionQueue:
    """Thread-safe queue for managing follow/unfollow actions"""
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Priority queue (higher priority = smaller number)
        self.queue = PriorityQueue(maxsize=config.queue_max_size)
        self.lock = threading.Lock()
        self.processing = False
        
    def add_action(self, action_type: ActionType, username: str, priority: int = 0):
        """Add action to queue"""
        token = ActionToken(
            action_type=action_type,
            target_username=username,
            priority=priority
        )
        
        with self.lock:
            if self.queue.qsize() >= self.config.queue_max_size:
                raise QueueFullError("Action queue is full")
            
            self.queue.put((priority, token))
            self.logger.info(f"Added {action_type.value} action for {username} to queue")
    
    def get_next_action(self) -> Optional[ActionToken]:
        """Get next action from queue"""
        try:
            if not self.queue.empty():
                priority, token = self.queue.get_nowait()
                self.logger.debug(f"Retrieved {token.action_type.value} action for {token.target_username}")
                return token
        except:
            pass
        return None
    
    def size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()
    
    def clear(self):
        """Clear all actions from queue"""
        with self.lock:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except:
                    break
        self.logger.info("Action queue cleared")

class QueueFullError(Exception):
    """Exception raised when queue is full"""
    pass