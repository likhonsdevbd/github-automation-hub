#!/usr/bin/env python3
"""
Test Suite for Follow Automation System
Validates all components and integrations
"""

import os
import sys
import unittest
import tempfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add automation modules to path
sys.path.append(str(Path(__file__).parent))

from config.settings import FollowAutomationConfig, ActionType
from config.templates import ConfigTemplate, ConfigValidator
from core.rate_limiter import RateLimiter, TokenBucket, ActionQueue
from scheduling.timing_system import HumanLikeScheduler, CircadianModifier, JitterGenerator
from queue.queue_manager import FollowQueue, Prioritizer
from detection.follow_back_detector import FollowBackDetector
from tracking.roi_optimizer import MetricsCollector, ROICalculator

class TestTokenBucket(unittest.TestCase):
    """Test token bucket rate limiter"""
    
    def test_initial_state(self):
        """Test initial token bucket state"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        self.assertEqual(bucket.capacity, 10)
        self.assertEqual(bucket.refill_rate, 1.0)
        self.assertEqual(bucket.tokens, 10)
    
    def test_consume_tokens(self):
        """Test token consumption"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        # Should be able to consume tokens
        self.assertTrue(bucket.consume(5))
        self.assertEqual(bucket.tokens, 5)
        
        # Should not be able to exceed capacity
        self.assertTrue(bucket.consume(10))  # Refills first
        self.assertTrue(bucket.consume(15))  # Should still work due to refill
    
    def test_available_tokens(self):
        """Test available token calculation"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        self.assertEqual(bucket.available_tokens(), 10)

class TestRateLimiter(unittest.TestCase):
    """Test rate limiter functionality"""
    
    def setUp(self):
        """Set up test configuration"""
        self.config = FollowAutomationConfig()
        self.config.rate_limit.max_actions_per_hour = 6
        self.rate_limiter = RateLimiter(self.config)
    
    def test_action_execution_limits(self):
        """Test action execution rate limiting"""
        # Should allow initial actions
        for i in range(6):
            result = self.rate_limiter.can_execute_action(ActionType.FOLLOW)
            self.assertTrue(result)
        
        # Should block after reaching limit
        result = self.rate_limiter.can_execute_action(ActionType.FOLLOW)
        self.assertFalse(result)
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        # Execute some actions
        self.rate_limiter.can_execute_action(ActionType.FOLLOW)
        self.rate_limiter.record_action_completion(True, 200)
        
        stats = self.rate_limiter.get_statistics()
        self.assertEqual(stats["total_actions"], 1)
        self.assertEqual(stats["successful_actions"], 1)
        self.assertEqual(stats["success_rate_percent"], 100.0)

class TestHumanLikeScheduler(unittest.TestCase):
    """Test human-like timing system"""
    
    def setUp(self):
        """Set up scheduler"""
        self.config = FollowAutomationConfig()
        self.scheduler = HumanLikeScheduler(self.config)
    
    def test_delay_calculation(self):
        """Test delay calculation with different contexts"""
        delay = self.scheduler.calculate_next_delay(ActionType.FOLLOW, 1.0)
        
        # Should be within reasonable bounds
        self.assertGreaterEqual(delay, 5.0)
        self.assertLessEqual(delay, 120.0)
    
    def test_circadian_modifier(self):
        """Test circadian rhythm modifiers"""
        # Test peak hours (9 AM)
        mult_9am = CircadianModifier.get_activity_multiplier(9, 1)  # Tuesday
        self.assertGreaterEqual(mult_9am, 0.8)
        
        # Test low activity hours (2 AM)
        mult_2am = CircadianModifier.get_activity_multiplier(2, 1)
        self.assertLessEqual(mult_2am, 0.4)
    
    def test_jitter_generation(self):
        """Test jitter generation with different distributions"""
        jitter_gen = JitterGenerator(self.config)
        
        # Test uniform jitter
        delay = jitter_gen.generate_delay(10.0, None, "uniform")
        self.assertIsInstance(delay, float)
        self.assertGreater(delay, 0)

class TestQueueManager(unittest.TestCase):
    """Test queue management system"""
    
    def setUp(self):
        """Set up queue"""
        self.config = FollowAutomationConfig()
        self.queue = FollowQueue(self.config)
    
    def test_action_addition(self):
        """Test adding actions to queue"""
        item_id = self.queue.add_action(ActionType.FOLLOW, "testuser")
        self.assertIsNotNone(item_id)
        
        stats = self.queue.get_queue_stats()
        self.assertEqual(stats["queue_size"], 1)
    
    def test_prioritization(self):
        """Test target prioritization"""
        prioritizer = Prioritizer(self.config)
        
        # High relevance context
        high_relevance = {
            "public_repos": 20,
            "followers": 1000,
            "following": 500,
            "last_active_days": 5,
            "shared_repos": ["repo1"]
        }
        
        score, priority = prioritizer.prioritize_target("testuser", high_relevance)
        self.assertGreater(score, 2.0)
        self.assertIsNotNone(priority)

class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def test_template_configurations(self):
        """Test different configuration templates"""
        # Test conservative config
        conservative = ConfigTemplate.conservative_config()
        self.assertEqual(conservative.rate_limit.max_actions_per_hour, 5)
        
        # Test balanced config
        balanced = ConfigTemplate.balanced_config()
        self.assertEqual(balanced.rate_limit.max_actions_per_hour, 8)
        
        # Test active config
        active = ConfigTemplate.active_config()
        self.assertEqual(active.rate_limit.max_actions_per_hour, 10)
    
    def test_configuration_validation(self):
        """Test configuration safety validation"""
        # Safe configuration
        safe_config = ConfigTemplate.conservative_config()
        assessment = ConfigValidator.validate_config_safety(safe_config)
        self.assertIn("safety_assessment", assessment)
        
        # Risky configuration
        risky_config = FollowAutomationConfig()
        risky_config.rate_limit.max_actions_per_hour = 15  # Too high
        assessment = ConfigValidator.validate_config_safety(risky_config)
        self.assertGreater(len(assessment["rate_limits"]), 0)

class TestMetricsCollection(unittest.TestCase):
    """Test metrics collection and ROI calculation"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.config = FollowAutomationConfig()
        self.metrics_collector = MetricsCollector(self.config, self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_metrics_recording(self):
        """Test recording action metrics"""
        from tracking.roi_optimizer import ActionMetrics
        
        metrics = ActionMetrics(
            timestamp=datetime.now(),
            action_type=ActionType.FOLLOW,
            target_username="testuser",
            success=True,
            response_code=200,
            relevance_score=3.5
        )
        
        self.metrics_collector.record_action(metrics)
        
        # Verify recording
        recent_metrics = self.metrics_collector.get_recent_metrics(hours=1)
        self.assertEqual(len(recent_metrics), 1)
        self.assertEqual(recent_metrics[0].target_username, "testuser")
    
    def test_roi_calculation(self):
        """Test ROI calculation"""
        # Add some test data
        from tracking.roi_optimizer import ActionMetrics
        
        for i in range(5):
            metrics = ActionMetrics(
                timestamp=datetime.now(),
                action_type=ActionType.FOLLOW,
                target_username=f"user{i}",
                success=True,
                response_code=200
            )
            self.metrics_collector.record_action(metrics)
        
        # Calculate ROI
        roi_calculator = ROICalculator(self.config, self.metrics_collector)
        roi_result = roi_calculator.calculate_roi(1)  # 1 day
        
        self.assertEqual(roi_result.total_actions, 5)
        self.assertEqual(roi_result.successful_actions, 5)
        self.assertEqual(roi_result.success_rate, 100.0)

class TestIntegration(unittest.TestCase):
    """Integration tests for full system"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Mock environment for testing
        os.environ["GITHUB_TOKEN"] = "test_token"
        
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.config = FollowAutomationConfig()
        self.config.rate_limit.max_actions_per_hour = 6
    
    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)
    
    @patch('requests.Session')
    def test_full_workflow(self, mock_session):
        """Test complete workflow from action to tracking"""
        from main_orchestrator import FollowAutomationOrchestrator
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_session.return_value.get.return_value = mock_response
        mock_session.return_value.request.return_value = mock_response
        
        # Test with conservative configuration
        orchestrator = FollowAutomationOrchestrator()
        
        # Add follow action
        success = orchestrator.add_follow_action("testuser", {
            "public_repos": 10,
            "followers": 1000,
            "activity_level": "high"
        })
        self.assertTrue(success)
        
        # Verify queue state
        stats = orchestrator.get_system_status()
        self.assertEqual(stats['components']['queue']['queue_size'], 1)

class TestPerformance(unittest.TestCase):
    """Performance and stress tests"""
    
    def test_queue_performance(self):
        """Test queue performance with many items"""
        config = FollowAutomationConfig()
        config.queue_max_size = 10000
        queue = FollowQueue(config)
        
        # Add many items
        for i in range(1000):
            queue.add_action(ActionType.FOLLOW, f"user{i}")
        
        stats = queue.get_queue_stats()
        self.assertEqual(stats["queue_size"], 1000)
    
    def test_rate_limiter_performance(self):
        """Test rate limiter with rapid requests"""
        config = FollowAutomationConfig()
        config.rate_limit.max_actions_per_hour = 100
        rate_limiter = RateLimiter(config)
        
        # Simulate rapid requests
        allowed = 0
        for i in range(50):
            if rate_limiter.can_execute_action(ActionType.FOLLOW):
                allowed += 1
                rate_limiter.record_action_completion(True, 200)
        
        # Should respect rate limits
        self.assertLessEqual(allowed, 50)

def run_all_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTokenBucket,
        TestRateLimiter,
        TestHumanLikeScheduler,
        TestQueueManager,
        TestConfiguration,
        TestMetricsCollection,
        TestIntegration,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

def run_specific_test(test_name):
    """Run specific test"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromName(test_name))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_performance_tests():
    """Run only performance tests"""
    return run_specific_test('TestPerformance')

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Follow Automation System")
    parser.add_argument("--test", help="Run specific test")
    parser.add_argument("--performance", action="store_true", 
                       help="Run performance tests only")
    parser.add_argument("--all", action="store_true",
                       help="Run all tests")
    
    args = parser.parse_args()
    
    try:
        if args.performance:
            print("Running performance tests...")
            success = run_performance_tests()
        elif args.test:
            print(f"Running test: {args.test}")
            success = run_specific_test(args.test)
        else:
            print("Running all tests...")
            success = run_all_tests()
        
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest run interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)