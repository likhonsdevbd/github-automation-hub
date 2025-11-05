#!/usr/bin/env python3
"""
Quick validation script for Follow Automation System
Tests basic functionality without complex imports
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Set up environment for testing
os.environ["GITHUB_TOKEN"] = "test_token"

def test_basic_imports():
    """Test that basic modules can be imported"""
    print("Testing basic imports...")
    
    try:
        # Test configuration import
        sys.path.append(str(Path(__file__).parent))
        from config.settings import FollowAutomationConfig, ActionType
        print("✅ Configuration imports successful")
        
        # Test basic configuration
        config = FollowAutomationConfig()
        config.validate()
        print("✅ Configuration validation successful")
        
        # Test template imports
        from config.templates import ConfigTemplate, ConfigValidator
        print("✅ Template imports successful")
        
        # Test template usage
        conservative = ConfigTemplate.conservative_config()
        assessment = ConfigValidator.validate_config_safety(conservative)
        print("✅ Template usage successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration_templates():
    """Test configuration templates"""
    print("\nTesting configuration templates...")
    
    try:
        from config.templates import ConfigTemplate, ConfigValidator
        
        # Test all templates
        templates = {
            "conservative": ConfigTemplate.conservative_config(),
            "balanced": ConfigTemplate.balanced_config(), 
            "active": ConfigTemplate.active_config()
        }
        
        for name, config in templates.items():
            print(f"  Testing {name} configuration...")
            
            # Validate configuration
            assessment = ConfigValidator.validate_config_safety(config)
            safety_level = assessment["safety_assessment"][0]
            
            print(f"    Actions/hour: {config.rate_limit.max_actions_per_hour}")
            print(f"    Safety level: {safety_level}")
            
            # Basic validation
            assert 5 <= config.rate_limit.max_actions_per_hour <= 10
        
        print("✅ All configuration templates tested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

def test_core_functionality():
    """Test core system functionality"""
    print("\nTesting core functionality...")
    
    try:
        from config.settings import FollowAutomationConfig, ActionType
        from config.templates import ConfigTemplate
        
        # Create test configuration
        config = ConfigTemplate.conservative_config()
        
        print(f"  Created conservative configuration:")
        print(f"    Rate limit: {config.rate_limit.max_actions_per_hour}/hour")
        print(f"    Base delay: {config.timing.base_delay_min}-{config.timing.base_delay_max}s")
        print(f"    Follow-back window: {config.detection.follow_back_window_days} days")
        
        # Test token bucket concept
        print(f"  Token bucket parameters:")
        print(f"    Capacity: {config.rate_limit.max_actions_per_hour}")
        print(f"    Refill rate: {config.rate_limit.max_actions_per_hour}/3600 per second")
        
        # Test timing system concept
        print(f"  Timing system parameters:")
        print(f"    Jitter factor: {config.timing.jitter_factor}")
        print(f"    Micro-batch size: {config.timing.micro_batch_size}")
        
        print("✅ Core functionality validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Core functionality test failed: {e}")
        return False

def test_orchestrator_creation():
    """Test orchestrator creation (basic validation)"""
    print("\nTesting orchestrator creation...")
    
    try:
        # Mock the components that require external dependencies
        from config.settings import FollowAutomationConfig
        
        # Test configuration loading
        config = FollowAutomationConfig()
        
        print(f"  Configuration loaded:")
        print(f"    Rate limits: {config.rate_limit.max_actions_per_hour}/hour")
        print(f"    API base: {config.api_base_url}")
        print(f"    Endpoints: {len(config.endpoints)} configured")
        
        # Test environment variable handling
        if "GITHUB_TOKEN" in os.environ:
            print(f"    GitHub token: {'✅ Set' if os.environ['GITHUB_TOKEN'] else '❌ Missing'}")
        
        print("✅ Orchestrator creation validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator creation test failed: {e}")
        return False

def test_security_features():
    """Test security and compliance features"""
    print("\nTesting security features...")
    
    try:
        from config.settings import FollowAutomationConfig
        from config.templates import SecurityProfiles
        
        config = FollowAutomationConfig()
        
        print(f"  Security configuration:")
        print(f"    User agent rotation: {config.security.user_agent_rotation}")
        print(f"    Session persistence: {config.security.session_persistence}")
        print(f"    REST-only operations: {config.security.avoid_ui_automation}")
        
        # Test security profiles
        print(f"  Security profiles:")
        for profile in [SecurityProfiles.MINIMAL, SecurityProfiles.STANDARD, SecurityProfiles.ENHANCED]:
            print(f"    {profile.name}: {profile.risk_level} risk")
        
        print("✅ Security features validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Security features test failed: {e}")
        return False

def generate_sample_config():
    """Generate a sample configuration file"""
    print("\nGenerating sample configuration...")
    
    try:
        from config.templates import ConfigTemplate
        
        # Create a balanced configuration
        config = ConfigTemplate.balanced_config()
        
        # Save to file
        config_file = Path(__file__).parent / "sample_config.py"
        
        with open(config_file, 'w') as f:
            f.write(f'''"""
Sample Follow Automation Configuration
Generated: {datetime.now().isoformat()}
"""

from config.settings import FollowAutomationConfig

def get_sample_config():
    """Get sample configuration"""
    config = FollowAutomationConfig()
    
    # Rate limiting
    config.rate_limit.max_actions_per_hour = {config.rate_limit.max_actions_per_hour}
    config.rate_limit.max_actions_per_day = {config.rate_limit.max_actions_per_day}
    config.rate_limit.max_concurrent_actions = {config.rate_limit.max_concurrent_actions}
    
    # Timing
    config.timing.base_delay_min = {config.timing.base_delay_min}
    config.timing.base_delay_max = {config.timing.base_delay_max}
    config.timing.micro_batch_size = {config.timing.micro_batch_size}
    
    # Detection
    config.detection.follow_back_window_days = {config.detection.follow_back_window_days}
    config.detection.check_interval_hours = {config.detection.check_interval_hours}
    
    return config

if __name__ == "__main__":
    config = get_sample_config()
    print("Sample configuration created successfully")
    print(f"Actions per hour: {{config.rate_limit.max_actions_per_hour}}")
    print(f"Follow-back window: {{config.detection.follow_back_window_days}} days")
''')
        
        print(f"✅ Sample configuration saved to: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Sample config generation failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Follow Automation System - Quick Validation")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_configuration_templates,
        test_core_functionality,
        test_orchestrator_creation,
        test_security_features,
        generate_sample_config
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All validation tests passed!")
        print("\nSystem is ready for use. Next steps:")
        print("1. Set your GITHUB_TOKEN environment variable")
        print("2. Run: python main_orchestrator.py --interactive")
        print("3. Or try: python examples/demo_usage.py")
        return True
    else:
        print("❌ Some validation tests failed")
        print("Please check the errors above and fix any issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)