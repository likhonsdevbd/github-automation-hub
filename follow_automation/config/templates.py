"""
Configuration Templates and Utilities
Provides template configurations for different use cases
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import time
from .settings import FollowAutomationConfig, ActionType, RateLimitConfig, TimingConfig, DetectionConfig, SecurityConfig, TrackingConfig

class ConfigTemplate:
    """Configuration templates for different automation scenarios"""
    
    @staticmethod
    def conservative_config() -> FollowAutomationConfig:
        """Ultra-conservative configuration (5 actions/hour)"""
        config = FollowAutomationConfig()
        
        # Conservative rate limits
        config.rate_limit.max_actions_per_hour = 5
        config.rate_limit.max_actions_per_day = 80
        config.rate_limit.cooldown_after_enforcement = 7200  # 2 hours
        
        # Extended delays
        config.timing.base_delay_min = 15.0
        config.timing.base_delay_max = 60.0
        config.timing.micro_batch_size = 1
        
        # Extended detection window
        config.detection.follow_back_window_days = 14
        config.detection.check_interval_hours = 24
        
        return config
    
    @staticmethod
    def balanced_config() -> FollowAutomationConfig:
        """Balanced configuration (8 actions/hour) - Recommended"""
        config = FollowAutomationConfig()
        
        # Balanced rate limits
        config.rate_limit.max_actions_per_hour = 8
        config.rate_limit.max_actions_per_day = 150
        config.rate_limit.cooldown_after_enforcement = 3600  # 1 hour
        
        # Moderate delays
        config.timing.base_delay_min = 8.0
        config.timing.base_delay_max = 35.0
        config.timing.micro_batch_size = 2
        
        # Standard detection window
        config.detection.follow_back_window_days = 7
        config.detection.check_interval_hours = 12
        
        return config
    
    @staticmethod
    def active_config() -> FollowAutomationConfig:
        """More active configuration (10 actions/hour) - Higher risk"""
        config = FollowAutomationConfig()
        
        # Active rate limits
        config.rate_limit.max_actions_per_hour = 10
        config.rate_limit.max_actions_per_day = 200
        config.rate_limit.cooldown_after_enforcement = 1800  # 30 minutes
        
        # Faster delays
        config.timing.base_delay_min = 5.0
        config.timing.base_delay_max = 25.0
        config.timing.micro_batch_size = 3
        
        # Quicker detection
        config.detection.follow_back_window_days = 5
        config.detection.check_interval_hours = 6
        
        return config

@dataclass
class SecurityProfile:
    """Security profile configuration"""
    name: str
    risk_level: str  # low, medium, high
    user_agent_rotation: bool = True
    session_persistence: bool = True
    proxy_usage: bool = False
    custom_headers: Dict[str, str] = None

class SecurityProfiles:
    """Predefined security profiles"""
    
    MINIMAL = SecurityProfile(
        name="minimal",
        risk_level="low",
        user_agent_rotation=False,
        session_persistence=True,
        proxy_usage=False
    )
    
    STANDARD = SecurityProfile(
        name="standard",
        risk_level="medium",
        user_agent_rotation=True,
        session_persistence=True,
        proxy_usage=False
    )
    
    ENHANCED = SecurityProfile(
        name="enhanced",
        risk_level="medium",
        user_agent_rotation=True,
        session_persistence=True,
        proxy_usage=True,
        custom_headers={
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate"
        }
    )

@dataclass
class TargetProfile:
    """Profile configuration for different target types"""
    name: str
    priority_multiplier: float
    max_daily_actions: int
    relevance_threshold: float
    activity_requirements: Dict[str, float]

class TargetProfiles:
    """Predefined target profiles for different strategies"""
    
    COLLABORATORS = TargetProfile(
        name="collaborators",
        priority_multiplier=2.0,
        max_daily_actions=10,
        relevance_threshold=0.8,
        activity_requirements={
            "min_recent_commits": 5,
            "min_shared_repos": 1,
            "min_follower_ratio": 0.5
        }
    )
    
    ACTIVE_DEVELOPERS = TargetProfile(
        name="active_developers", 
        priority_multiplier=1.5,
        max_daily_actions=15,
        relevance_threshold=0.6,
        activity_requirements={
            "min_recent_activity_days": 30,
            "min_public_repos": 3,
            "min_followers": 100
        }
    )
    
    GENERAL_NETWORK = TargetProfile(
        name="general_network",
        priority_multiplier=1.0,
        max_daily_actions=20,
        relevance_threshold=0.4,
        activity_requirements={
            "min_public_repos": 1,
            "min_followers": 50
        }
    )

class ConfigValidator:
    """Validates configuration settings for safety"""
    
    @staticmethod
    def validate_rate_limits(config: FollowAutomationConfig) -> List[str]:
        """Validate rate limiting settings"""
        warnings = []
        
        if config.rate_limit.max_actions_per_hour > 10:
            warnings.append("High action rate may increase detection risk")
        
        if config.rate_limit.max_actions_per_hour > config.rate_limit.max_actions_per_day / 24:
            warnings.append("Hourly rate exceeds daily average")
        
        if config.rate_limit.max_concurrent_actions > 1:
            warnings.append("Concurrent actions increase detection risk")
        
        return warnings
    
    @staticmethod
    def validate_timing(config: FollowAutomationConfig) -> List[str]:
        """Validate timing settings"""
        warnings = []
        
        if config.timing.base_delay_min < 5.0:
            warnings.append("Very short delays may appear automated")
        
        if config.timing.base_delay_max < config.timing.base_delay_min * 2:
            warnings.append("Limited delay variation may look mechanical")
        
        if config.timing.micro_batch_size > 3:
            warnings.append("Large micro-batches may appear automated")
        
        return warnings
    
    @staticmethod
    def validate_detection(config: FollowAutomationConfig) -> List[str]:
        """Validate detection settings"""
        warnings = []
        
        if config.detection.follow_back_window_days < 5:
            warnings.append("Very short follow-back window may miss reciprocation")
        
        if config.detection.check_interval_hours > 24:
            warnings.append("Infrequent detection may miss timely unfollow opportunities")
        
        return warnings
    
    @classmethod
    def validate_config_safety(cls, config: FollowAutomationConfig) -> Dict[str, List[str]]:
        """Comprehensive safety validation"""
        results = {
            "rate_limits": cls.validate_rate_limits(config),
            "timing": cls.validate_timing(config),
            "detection": cls.validate_detection(config)
        }
        
        # Overall safety assessment
        total_warnings = sum(len(warnings) for warnings in results.values())
        if total_warnings == 0:
            results["safety_assessment"] = ["Configuration appears safe"]
        elif total_warnings <= 2:
            results["safety_assessment"] = ["Configuration has minor risk factors"]
        else:
            results["safety_assessment"] = ["Configuration has elevated risk factors"]
        
        return results

class ConfigGenerator:
    """Generate configurations for specific use cases"""
    
    @staticmethod
    def generate_work_hours_config() -> FollowAutomationConfig:
        """Generate configuration that only operates during work hours"""
        config = FollowAutomationConfig()
        
        # Active during business hours (9 AM - 5 PM, Monday-Friday)
        # This would need to be implemented in the scheduler
        config.timing.circadian_modifier = True
        
        # Reduce activity during off-hours
        config.rate_limit.max_actions_per_hour = 3  # Very conservative off-hours
        
        return config
    
    @staticmethod
    def generate_international_config() -> FollowAutomationConfig:
        """Generate configuration optimized for international usage"""
        config = FollowAutomationConfig()
        
        # More conservative rates for international operations
        config.rate_limit.max_actions_per_hour = 6
        config.rate_limit.cooldown_after_enforcement = 7200  # 2 hours
        
        # Enhanced security
        config.security.user_agent_rotation = True
        config.security.session_persistence = True
        
        return config
    
    @staticmethod
    def generate_organization_config(org_name: str) -> FollowAutomationConfig:
        """Generate configuration for organization-specific automation"""
        config = FollowAutomationConfig()
        
        # Higher priorities for organization members
        config.detection.relevance_threshold = 0.2  # Lower threshold for org members
        
        # More aggressive follow-back detection for organizational network
        config.detection.follow_back_window_days = 5
        
        return config

def print_config_assessment(config: FollowAutomationConfig):
    """Print configuration assessment"""
    print("\nConfiguration Safety Assessment:")
    print("=" * 50)
    
    assessment = ConfigValidator.validate_config_safety(config)
    
    for category, warnings in assessment.items():
        if category != "safety_assessment":
            print(f"\n{category.title()} Concerns:")
            if warnings:
                for warning in warnings:
                    print(f"  ⚠️  {warning}")
            else:
                print("  ✅ No concerns detected")
    
    print(f"\nOverall Assessment:")
    for assessment_msg in assessment["safety_assessment"]:
        print(f"  {assessment_msg}")

def create_custom_config_scenario():
    """Create a custom configuration for a specific scenario"""
    print("\nCustom Configuration Generator")
    print("=" * 40)
    
    # Get user preferences
    action_rate = input("Actions per hour (5-10): ").strip()
    target_profile = input("Target profile (collaborators/active_developers/general_network): ").strip()
    
    # Start with appropriate template
    if action_rate and int(action_rate) <= 6:
        config = ConfigTemplate.conservative_config()
    elif action_rate and int(action_rate) >= 9:
        config = ConfigTemplate.active_config()
    else:
        config = ConfigTemplate.balanced_config()
    
    # Apply custom settings
    if action_rate:
        config.rate_limit.max_actions_per_hour = int(action_rate)
    
    # Apply security profile
    if target_profile == "collaborators":
        config.detection.relevance_threshold = 0.8
    elif target_profile == "general_network":
        config.detection.relevance_threshold = 0.3
    
    print(f"\nGenerated custom configuration:")
    print(f"  Actions per hour: {config.rate_limit.max_actions_per_hour}")
    print(f"  Micro-batch size: {config.timing.micro_batch_size}")
    print(f"  Follow-back window: {config.detection.follow_back_window_days} days")
    print(f"  Relevance threshold: {config.detection.relevance_threshold}")
    
    return config

if __name__ == "__main__":
    # Demo different configurations
    print("Follow Automation Configuration Templates")
    print("=" * 50)
    
    # Show template configurations
    conservative = ConfigTemplate.conservative_config()
    balanced = ConfigTemplate.balanced_config()
    active = ConfigTemplate.active_config()
    
    print(f"\nConservative (5/hour):")
    print_config_assessment(conservative)
    
    print(f"\nBalanced (8/hour):")
    print_config_assessment(balanced)
    
    print(f"\nActive (10/hour):")
    print_config_assessment(active)
    
    # Interactive configuration generator
    try:
        custom_config = create_custom_config_scenario()
        print("\nCustom configuration generated successfully!")
    except KeyboardInterrupt:
        print("\nConfiguration generation cancelled.")