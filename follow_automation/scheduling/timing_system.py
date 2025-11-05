"""
Human-Like Timing System with Randomization
Implements jittered delays and circadian rhythm modifiers
"""
import time
import random
import math
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging
from ..config.settings import FollowAutomationConfig, ActionType

@dataclass
class TimingContext:
    """Context for timing decisions"""
    action_type: ActionType
    time_of_day: int  # Hour of day (0-23)
    day_of_week: int  # 0=Monday, 6=Sunday
    last_action_time: Optional[datetime] = None
    consecutive_actions: int = 0
    has_enforcement_signal: bool = False

class CircadianModifier:
    """Modifies timing based on circadian rhythms"""
    
    # Activity levels by hour (0-24)
    # Higher values = more activity (shorter delays)
    ACTIVITY_CURVE = {
        0: 0.3,   # Midnight
        1: 0.2,   # 1 AM
        2: 0.2,   # 2 AM
        3: 0.2,   # 3 AM
        4: 0.3,   # 4 AM
        5: 0.4,   # 5 AM
        6: 0.6,   # 6 AM
        7: 0.8,   # 7 AM
        8: 1.0,   # 8 AM - Peak
        9: 1.0,   # 9 AM - Peak
        10: 0.9,  # 10 AM
        11: 0.9,  # 11 AM
        12: 0.8,  # Noon
        13: 0.8,  # 1 PM
        14: 0.7,  # 2 PM
        15: 0.7,  # 3 PM
        16: 0.8,  # 4 PM
        17: 0.9,  # 5 PM
        18: 0.7,  # 6 PM
        19: 0.6,  # 7 PM
        20: 0.5,  # 8 PM
        21: 0.4,  # 9 PM
        22: 0.4,  # 10 PM
        23: 0.3,  # 11 PM
    }
    
    # Weekend modifiers (lower activity)
    WEEKEND_MODIFIER = {
        5: 0.7,  # Friday evening
        6: 0.5,  # Saturday
        0: 0.5,  # Sunday
    }
    
    @classmethod
    def get_activity_multiplier(cls, hour: int, day_of_week: int) -> float:
        """Get activity multiplier based on time and day"""
        base = cls.ACTIVITY_CURVE.get(hour, 0.5)
        
        # Apply weekend modifier
        if day_of_week >= 5:  # Weekend
            if day_of_week == 5:  # Friday
                weekend_multiplier = cls.WEEKEND_MODIFIER.get(hour, 0.6)
            else:  # Saturday/Sunday
                weekend_multiplier = cls.WEEKEND_MODIFIER.get(day_of_week, 0.5)
            base *= weekend_multiplier
        
        return max(0.1, min(1.0, base))

class JitterGenerator:
    """Generate randomized delays for human-like timing"""
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Statistical distributions for different scenarios
        self.distributions = {
            "uniform": self._uniform_jitter,
            "log_normal": self._log_normal_jitter,
            "weibull": self._weibull_jitter,
            "adaptive": self._adaptive_jitter
        }
    
    def _uniform_jitter(self, base_delay: float) -> float:
        """Uniform distribution with ±jitter factor"""
        jitter_range = base_delay * self.config.timing.jitter_factor
        return random.uniform(
            base_delay - jitter_range,
            base_delay + jitter_range
        )
    
    def _log_normal_jitter(self, base_delay: float) -> float:
        """Log-normal distribution (realistic for human behavior)"""
        # Convert to log space
        mu = math.log(base_delay)
        sigma = math.log(1 + self.config.timing.jitter_factor)
        
        # Generate log-normal sample
        return random.lognormvariate(mu, sigma)
    
    def _weibull_jitter(self, base_delay: float) -> float:
        """Weibull distribution (good for burst patterns)"""
        # Shape parameter (1.5 for mild positive skew)
        k = 1.5
        # Scale parameter based on base delay
        lam = base_delay / math.gamma(1 + 1/k)
        
        return random.weibullvariate(k, lam)
    
    def _adaptive_jitter(self, base_delay: float, context: TimingContext) -> float:
        """Adaptive jitter based on context and recent behavior"""
        base = self._log_normal_jitter(base_delay)
        
        # Apply consecutive action penalty
        if context.consecutive_actions > 0:
            consecutive_penalty = min(context.consecutive_actions * 0.2, 1.0)
            base *= (1 + consecutive_penalty)
        
        # Apply enforcement signal penalty
        if context.has_enforcement_signal:
            enforcement_penalty = 3.0  # Triple delay after enforcement
            base *= enforcement_penalty
        
        # Cap the maximum delay to prevent runaway
        return min(base, base_delay * 5)
    
    def generate_delay(self, base_delay: float, context: TimingContext,
                      distribution: str = "adaptive") -> float:
        """Generate jittered delay"""
        if distribution not in self.distributions:
            self.logger.warning(f"Unknown distribution {distribution}, using adaptive")
            distribution = "adaptive"
        
        return self.distributions[distribution](base_delay, context)

class HumanLikeScheduler:
    """
    Main human-like timing scheduler
    Manages delays, micro-batching, and circadian rhythms
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.jitter_gen = JitterGenerator(config)
        self.last_action_time = None
        self.consecutive_actions = 0
        self.micro_batch_count = 0
        
        # Track action patterns to avoid detection
        self.action_patterns: List[datetime] = []
        self.max_pattern_history = 1000
    
    def calculate_next_delay(self, action_type: ActionType, 
                           recent_success_rate: float = 1.0) -> float:
        """Calculate next delay with full context"""
        
        # Get current timing context
        now = datetime.now()
        context = TimingContext(
            action_type=action_type,
            time_of_day=now.hour,
            day_of_week=now.weekday(),
            last_action_time=self.last_action_time,
            consecutive_actions=self.consecutive_actions,
            has_enforcement_signal=recent_success_rate < 0.8
        )
        
        # Base delay calculation
        base_delay = self._calculate_base_delay(action_type)
        
        # Apply circadian modifier
        activity_mult = CircadianModifier.get_activity_multiplier(
            now.hour, now.weekday()
        )
        base_delay /= activity_mult  # More active = shorter delays
        
        # Apply success rate modifier
        success_mult = 1.0 + (1.0 - recent_success_rate) * 2.0
        base_delay *= success_mult
        
        # Generate jittered delay
        delay = self.jitter_gen.generate_delay(base_delay, context)
        
        # Ensure minimum delay
        delay = max(self.config.timing.base_delay_min, delay)
        
        self.logger.debug(f"Calculated delay: {delay:.1f}s (base: {base_delay:.1f}s, "
                         f"activity: {activity_mult:.2f}, success: {recent_success_rate:.2f})")
        
        return delay
    
    def _calculate_base_delay(self, action_type: ActionType) -> float:
        """Calculate base delay for action type"""
        if action_type == ActionType.FOLLOW:
            # Follows need more conservative timing
            return random.uniform(
                self.config.timing.base_delay_min * 2,
                self.config.timing.base_delay_max * 1.5
            )
        else:  # UNFOLLOW
            # Unfollows can be slightly faster but still conservative
            return random.uniform(
                self.config.timing.base_delay_min,
                self.config.timing.base_delay_max
            )
    
    def should_start_micro_batch(self) -> bool:
        """Determine if we should start a micro-batch"""
        return (
            self.micro_batch_count == 0 or
            self.micro_batch_count >= self.config.timing.micro_batch_size
        )
    
    def record_action_execution(self, action_type: ActionType, success: bool):
        """Record action execution for pattern analysis"""
        now = datetime.now()
        self.action_patterns.append(now)
        
        if self.last_action_time:
            time_diff = (now - self.last_action_time).total_seconds()
            self.logger.debug(f"Action interval: {time_diff:.1f}s")
        
        # Update consecutive counter
        if success:
            self.consecutive_actions += 1
            self.micro_batch_count += 1
        else:
            self.consecutive_actions = 0
            self.micro_batch_count = 0
        
        self.last_action_time = now
        
        # Clean old patterns
        cutoff = now - timedelta(hours=24)
        self.action_patterns = [
            t for t in self.action_patterns if t > cutoff
        ][:self.max_pattern_history]
        
        # Check for suspicious patterns
        self._check_suspicious_patterns()
    
    def _check_suspicious_patterns(self):
        """Check for patterns that look automated"""
        if len(self.action_patterns) < 10:
            return
        
        # Check for too-regular intervals
        intervals = []
        for i in range(1, len(self.action_patterns)):
            diff = (self.action_patterns[i] - self.action_patterns[i-1]).total_seconds()
            intervals.append(diff)
        
        if len(intervals) >= 5:
            # Check coefficient of variation (should be > 0.3 for human-like)
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = math.sqrt(variance)
            cv = std_dev / mean_interval if mean_interval > 0 else 0
            
            if cv < 0.3:
                self.logger.warning(f"Low variability detected (CV: {cv:.3f}). "
                                  "Increasing randomization.")
                # Increase jitter factor temporarily
                self.jitter_gen.jitter_factor *= 1.5
    
    def reset_micro_batch(self):
        """Reset micro-batch counter"""
        self.micro_batch_count = 0
    
    def get_current_pattern_stats(self) -> dict:
        """Get current action pattern statistics"""
        if not self.action_patterns:
            return {"pattern_length": 0}
        
        now = datetime.now()
        recent_actions = [
            t for t in self.action_patterns 
            if t > now - timedelta(hours=1)
        ]
        
        if len(recent_actions) < 2:
            return {"pattern_length": len(recent_actions)}
        
        # Calculate statistics
        intervals = [
            (recent_actions[i] - recent_actions[i-1]).total_seconds()
            for i in range(1, len(recent_actions))
        ]
        
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_interval if mean_interval > 0 else 0
        
        return {
            "pattern_length": len(recent_actions),
            "mean_interval_seconds": round(mean_interval, 2),
            "std_dev_seconds": round(std_dev, 2),
            "coefficient_variation": round(cv, 3),
            "consecutive_actions": self.consecutive_actions,
            "micro_batch_count": self.micro_batch_count,
            "time_since_last_action": (
                now - self.action_patterns[-1]
            ).total_seconds() if self.action_patterns else None
        }

class TimingValidator:
    """Validate timing patterns for safety"""
    
    @staticmethod
    def validate_delay(delay: float, context: dict) -> Tuple[bool, str]:
        """Validate if delay is safe"""
        reasons = []
        
        # Check minimum delay
        if delay < 5.0:
            reasons.append("Delay too short")
        
        # Check maximum delay (avoid very long delays that might timeout)
        if delay > 300:  # 5 minutes
            reasons.append("Delay too long")
        
        # Check for regular intervals
        if "intervals" in context:
            intervals = context["intervals"]
            if len(intervals) >= 5:
                cv = TimingValidator._calculate_coefficient_variation(intervals)
                if cv < 0.2:
                    reasons.append("Too regular intervals")
        
        return len(reasons) == 0, "; ".join(reasons)
    
    @staticmethod
    def _calculate_coefficient_variation(values: List[float]) -> float:
        """Calculate coefficient of variation"""
        if not values:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        return std_dev / mean if mean > 0 else 0