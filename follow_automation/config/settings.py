"""
Follow/Unfollow Automation System Configuration
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"

@dataclass
class RateLimitConfig:
    """Safe rate limiting configuration (5-10 actions/hour)"""
    max_actions_per_hour: int = 8  # Balanced default (within 5-10 range)
    max_actions_per_day: int = 300  # ~8% of daily activity
    max_concurrent_actions: int = 1  # No parallel actions
    cooldown_after_enforcement: int = 3600  # 1 hour after 422/429
    retry_after_header_multiplier: float = 1.5  # Be conservative with Retry-After
    
@dataclass
class TimingConfig:
    """Human-like timing with randomization"""
    base_delay_min: float = 5.0  # 5 seconds minimum
    base_delay_max: float = 30.0  # 30 seconds maximum
    jitter_factor: float = 0.3  # 30% randomization
    circadian_modifier: bool = True  # Adjust for time of day
    micro_batch_size: int = 3  # Max 1-3 actions per burst
    
@dataclass
class DetectionConfig:
    """Follow-back detection settings"""
    follow_back_window_days: int = 7
    check_interval_hours: int = 12
    max_list_size: int = 1000  # Pagination limit
    relevance_threshold: float = 0.3
    
@dataclass
class SecurityConfig:
    """Anti-detection and security settings"""
    use_proxies: bool = False
    proxy_rotation: bool = False
    user_agent_rotation: bool = True
    session_persistence: bool = True
    avoid_ui_automation: bool = True  # REST-only per design
    max_proxies: int = 5
    proxy_test_timeout: int = 10
    
@dataclass
class TrackingConfig:
    """Success tracking and ROI optimization"""
    track_follow_back_ratio: bool = True
    track_action_success_rate: bool = True
    track_rate_limit_events: bool = True
    roi_calculation_period_days: int = 30
    minimum_data_points: int = 10
    
class FollowAutomationConfig:
    """Main configuration class"""
    
    def __init__(self):
        self.rate_limit = RateLimitConfig()
        self.timing = TimingConfig()
        self.detection = DetectionConfig()
        self.security = SecurityConfig()
        self.tracking = TrackingConfig()
        
        # API endpoints (GitHub REST API)
        self.api_base_url = "https://api.github.com"
        self.endpoints = {
            "followers": "/user/followers",
            "following": "/user/following",
            "check_follow": "/user/following/{username}",
            "follow": "/user/following/{username}",
            "unfollow": "/user/following/{username}",
            "rate_limit": "/rate_limit"
        }
        
        # Required scopes
        self.required_scopes = ["user:follow"]  # Least privilege
        
        # Queue management
        self.queue_max_size = 1000
        self.queue_cleanup_interval = 86400  # 24 hours
        
        # Logging
        self.log_level = "INFO"
        self.audit_log_retention_days = 30
        self.minimal_data_retention = True
        
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not 5 <= self.rate_limit.max_actions_per_hour <= 10:
            raise ValueError("Rate limit must be 5-10 actions/hour for safety")
        
        if self.rate_limit.max_concurrent_actions > 1:
            raise ValueError("No parallel actions allowed for safety")
        
        if self.detection.follow_back_window_days < 7:
            raise ValueError("Follow-back window must be at least 7 days")
        
        return True
    
    def get_env_config(self):
        """Load configuration from environment variables"""
        # Token configuration
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        
        # Proxy configuration (optional)
        proxy_list = os.getenv("PROXY_LIST")
        if proxy_list:
            self.security.use_proxies = True
            self.security.proxy_list = proxy_list.split(",")
        
        # Override rate limits from environment
        if os.getenv("MAX_ACTIONS_PER_HOUR"):
            self.rate_limit.max_actions_per_hour = int(os.getenv("MAX_ACTIONS_PER_HOUR"))
        
        return self

# Global configuration instance
config = FollowAutomationConfig()