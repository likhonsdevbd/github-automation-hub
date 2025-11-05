"""
Sample Follow Automation Configuration
Generated: 2025-11-06T07:20:16.924934
"""

from config.settings import FollowAutomationConfig

def get_sample_config():
    """Get sample configuration"""
    config = FollowAutomationConfig()
    
    # Rate limiting
    config.rate_limit.max_actions_per_hour = 8
    config.rate_limit.max_actions_per_day = 150
    config.rate_limit.max_concurrent_actions = 1
    
    # Timing
    config.timing.base_delay_min = 8.0
    config.timing.base_delay_max = 35.0
    config.timing.micro_batch_size = 2
    
    # Detection
    config.detection.follow_back_window_days = 7
    config.detection.check_interval_hours = 12
    
    return config

if __name__ == "__main__":
    config = get_sample_config()
    print("Sample configuration created successfully")
    print(f"Actions per hour: {config.rate_limit.max_actions_per_hour}")
    print(f"Follow-back window: {config.detection.follow_back_window_days} days")
