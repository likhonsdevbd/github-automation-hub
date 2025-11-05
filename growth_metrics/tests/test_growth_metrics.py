"""
Test Suite for Growth Metrics Collection System
===============================================

Comprehensive tests for all components of the growth metrics system.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sqlite3

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.config_manager import ConfigManager
from core.rate_limiter import RateLimiter, RateLimitStats, RequestCache
from core.error_handler import ErrorHandler, ErrorType, ErrorContext
from api.github_client import GitHubAPIClient, RepositoryInfo, CommitInfo, ContributorInfo
from storage.metrics_storage import MetricsDatabase, FileStorage, MetricsStorage
from analytics.growth_analytics import HealthScoreCalculator, TrendAnalyzer, AnomalyDetector


class TestConfigManager(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.yaml')
        
    def test_load_from_dict(self):
        """Test loading configuration from dictionary"""
        config = ConfigManager()
        
        test_config = {
            'github': {'token': 'test_token'},
            'storage': {'backend': 'sqlite'},
            'analytics': {'health_score_weights': {'contributors': 0.5}}
        }
        
        config._load_from_dict(test_config)
        
        self.assertEqual(config.github.token, 'test_token')
        self.assertEqual(config.storage.backend, 'sqlite')
        self.assertEqual(config.analytics.health_score_weights['contributors'], 0.5)
        
    def test_validate(self):
        """Test configuration validation"""
        config = ConfigManager()
        
        # Valid configuration
        config.github.token = 'valid_token'
        config.github.organizations = ['test-org']
        errors = config.validate()
        self.assertEqual(len(errors), 0)
        
        # Invalid configuration
        config.github.token = ''  # Empty token
        errors = config.validate()
        self.assertGreater(len(errors), 0)
        self.assertIn('GitHub token is required', errors)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.rate_limiter = RateLimiter({'max_retries': 3})
        
    def test_rate_limit_stats_update(self):
        """Test updating rate limit stats from headers"""
        stats = RateLimitStats()
        headers = {
            'x-ratelimit-remaining': '4000',
            'x-ratelimit-reset': '1640995200',
            'retry-after': '60'
        }
        
        stats.update_from_headers(headers)
        
        self.assertEqual(stats.primary_remaining, 4000)
        self.assertEqual(stats.primary_reset, 1640995200)
        self.assertEqual(stats.secondary_remaining, 0)
        
    def test_request_cache(self):
        """Test request caching functionality"""
        cache = RequestCache(ttl=300)
        
        # Test cache miss
        result = cache.get('GET', '/test', {})
        self.assertIsNone(result)
        
        # Test cache set and hit
        cache.set('GET', '/test', {'data': 'test'}, {})
        result = cache.get('GET', '/test', {})
        self.assertEqual(result['data'], 'test')
        
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        rate_limiter = RateLimiter({'failure_threshold': 2, 'failure_timeout': 60})
        
        # Initially should be closed
        self.assertFalse(rate_limiter.circuit_breaker_open)
        
        # Record failures to open circuit breaker
        rate_limiter._record_failure()
        rate_limiter._record_failure()
        
        # Circuit breaker should now be open
        self.assertTrue(rate_limiter.circuit_breaker_open)


class TestErrorHandler(unittest.TestCase):
    """Test error handling and retry logic"""
    
    def setUp(self):
        self.error_handler = ErrorHandler({'max_retries': 2})
        
    def test_error_classification(self):
        """Test error classification"""
        classifier = ErrorHandler().error_classifier
        
        # Test rate limit error
        rate_error = Exception("API rate limit exceeded (429)")
        error_type = classifier.classify_error(rate_error)
        self.assertEqual(error_type, ErrorType.RATE_LIMIT)
        
        # Test authentication error
        auth_error = Exception("401 Unauthorized")
        error_type = classifier.classify_error(auth_error)
        self.assertEqual(error_type, ErrorType.AUTHENTICATION)
        
    def test_retry_strategy(self):
        """Test retry strategy calculation"""
        strategy = ErrorHandler().retry_strategy
        
        # Rate limit should respect retry-after
        delay = strategy.calculate_delay(ErrorType.RATE_LIMIT, 0, 30.0)
        self.assertEqual(delay, 30.0)
        
        # Server error should use exponential backoff
        delay = strategy.calculate_delay(ErrorType.SERVER_ERROR, 1)
        self.assertGreater(delay, 1)
        self.assertLess(delay, 3)  # Should be between 1 and 3 seconds


class TestGitHubAPIClient(unittest.TestCase):
    """Test GitHub API client"""
    
    @patch('requests.Session')
    def test_github_client_initialization(self, mock_session):
        """Test GitHub client initialization"""
        config = ConfigManager()
        config.github.token = 'test_token'
        config.github.timeout = 30
        
        client = GitHubAPIClient(config)
        
        # Check that session headers are set correctly
        self.assertEqual(client.session.headers['Authorization'], 'token test_token')
        self.assertEqual(client.session.headers['User-Agent'], 'GrowthMetrics-Collection/1.0')
        
    @patch('requests.Session.request')
    def test_repository_info_structure(self, mock_request):
        """Test repository info data structure"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'full_name': 'owner/repo',
            'private': False,
            'fork': False,
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-01T00:00:00Z',
            'default_branch': 'main',
            'open_issues_count': 10,
            'watchers_count': 100,
            'stargazers_count': 200,
            'forks_count': 50,
            'languages': {'Python': 1000, 'JavaScript': 500},
            'topics': ['python', 'web-development']
        }
        mock_response.headers = {'x-ratelimit-remaining': '5000'}
        mock_request.return_value = mock_response
        
        # Test would require full client setup, this is a simplified test
        # In a real implementation, we would mock the _make_request method


class TestMetricsStorage(unittest.TestCase):
    """Test metrics storage functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_metrics.db')
        
    def test_database_initialization(self):
        """Test database table creation"""
        db = MetricsDatabase(self.db_path)
        
        # Check that database file exists
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check that we can connect and query tables
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'repositories', 'commits', 'contributors', 
                'issues', 'pull_requests', 'metrics_snapshots'
            ]
            
            for table in expected_tables:
                self.assertIn(table, tables)
                
    def test_file_storage(self):
        """Test file-based storage"""
        storage = FileStorage(self.temp_dir, compress=True)
        
        test_data = {
            'repository': 'test/repo',
            'timestamp': datetime.now().isoformat(),
            'metrics': {'stars': 100, 'forks': 10}
        }
        
        # Save data
        file_path = storage.save_metrics_batch(test_data)
        
        # Check file exists and has correct extension
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith('.gz'))
        
        # Load data back
        loaded_data = storage.load_metrics_batch(file_path)
        self.assertEqual(loaded_data['repository'], 'test/repo')
        self.assertEqual(loaded_data['metrics']['stars'], 100)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)


class TestAnalytics(unittest.TestCase):
    """Test analytics and health scoring"""
    
    def setUp(self):
        self.health_calculator = HealthScoreCalculator()
        self.trend_analyzer = TrendAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        
    def test_health_score_calculation(self):
        """Test health score calculation"""
        # Create sample metrics data
        metrics_data = {
            'contributors_count': 25,
            'prs_opened': 10,
            'prs_merged': 8,
            'avg_time_to_merge_hours': 24,
            'issues': [
                {'state': 'open', 'created_at': '2023-01-01T00:00:00Z'},
                {'state': 'open', 'created_at': '2023-01-02T00:00:00Z'}
            ],
            'forks_count': 15
        }
        
        health_score = self.health_calculator.calculate_health_score(metrics_data)
        
        # Check that all components are calculated
        self.assertIsInstance(health_score.contributors_score, float)
        self.assertIsInstance(health_score.pr_throughput_score, float)
        self.assertIsInstance(health_score.review_velocity_score, float)
        self.assertIsInstance(health_score.issue_freshness_score, float)
        self.assertIsInstance(health_score.fork_growth_score, float)
        self.assertIsInstance(health_score.overall_score, float)
        
        # Overall score should be weighted average
        expected_overcome = (
            health_score.contributors_score * 0.30 +
            health_score.pr_throughput_score * 0.20 +
            health_score.review_velocity_score * 0.20 +
            health_score.issue_freshness_score * 0.15 +
            health_score.fork_growth_score * 0.15
        )
        
        self.assertAlmostEqual(health_score.overall_score, expected_overcome, places=5)
        
    def test_trend_analysis(self):
        """Test trend analysis functionality"""
        # Create sample time series data
        sample_data = []
        for i in range(30):
            sample_data.append({
                'snapshot_date': (datetime.now() - timedelta(days=30-i)).isoformat(),
                'stargazers_count': 1000 + i * 10 + (i % 7) * 5,  # Trend + seasonality
                'forks_count': 100 + i * 2,
                'commits_count': max(0, 5 + (i % 3) - 1)  # Some variation
            })
        
        trends = self.trend_analyzer.analyze_trends(sample_data)
        
        # Should detect trends for numeric metrics
        self.assertGreater(len(trends), 0)
        
        for trend in trends:
            self.assertIn(trend.metric_name, ['stargazers_count', 'forks_count', 'commits_count'])
            self.assertIn(trend.trend_direction, ['increasing', 'decreasing', 'stable'])
            self.assertGreaterEqual(trend.trend_strength, 0)
            self.assertLessEqual(trend.trend_strength, 1)
            
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        # Create sample data with an anomaly
        sample_data = []
        base_value = 100
        
        for i in range(20):
            if i == 10:  # Insert anomaly
                value = base_value * 3  # Big spike
            else:
                value = base_value + (i - 10) * 2 + (i % 3)
                
            sample_data.append({
                'snapshot_date': (datetime.now() - timedelta(days=20-i)).isoformat(),
                'test_metric': value
            })
        
        anomalies = self.anomaly_detector.detect_anomalies(sample_data, ['test_metric'])
        
        # Should detect the anomaly
        test_metric_anomalies = [a for a in anomalies if a.metric_name == 'test_metric']
        self.assertGreater(len(test_metric_anomalies), 0)
        
        anomaly = test_metric_anomalies[0]
        self.assertEqual(anomaly.anomaly_type, 'spike')
        self.assertEqual(anomaly.severity, 'medium')  # Depends on z-score


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'integration_config.yaml')
        
    def test_end_to_end_workflow(self):
        """Test complete workflow from config to analytics"""
        # Create minimal configuration
        config_data = {
            'github': {
                'token': 'test_token',
                'timeout': 30,
                'repositories': ['test/repo']
            },
            'collection': {
                'batch_size': 10,
                'enable_caching': True
            },
            'storage': {
                'backend': 'sqlite',
                'connection_string': f'sqlite:///{os.path.join(self.temp_dir, "test.db")}'
            },
            'analytics': {
                'health_score_weights': {
                    'contributors': 0.30,
                    'pr_throughput': 0.20,
                    'review_velocity': 0.20,
                    'issue_freshness': 0.15,
                    'fork_growth': 0.15
                }
            }
        }
        
        import yaml
        with open(self.config_file, 'w') as f:
            yaml.dump(config_data, f)
            
        # Test configuration loading
        config = ConfigManager(self.config_file)
        self.assertEqual(config.github.token, 'test_token')
        self.assertEqual(len(config.github.repositories), 1)
        
        # Test storage initialization
        storage = MetricsStorage(config.get_effective_config()['storage'])
        self.assertIsNotNone(storage)
        
        # Test analytics initialization
        from analytics.growth_analytics import GrowthAnalyticsEngine
        analytics = GrowthAnalyticsEngine(config.get_effective_config()['analytics'])
        self.assertIsNotNone(analytics)
        
        # Test health score calculation with sample data
        sample_metrics = {
            'contributors_count': 10,
            'prs_opened': 5,
            'prs_merged': 4,
            'avg_time_to_merge_hours': 48,
            'issues': [{'state': 'open', 'created_at': '2023-01-01T00:00:00Z'}],
            'forks_count': 20
        }
        
        health_score = analytics.health_calculator.calculate_health_score(sample_metrics)
        self.assertIsInstance(health_score.overall_score, float)
        self.assertGreaterEqual(health_score.overall_score, 0)
        self.assertLessEqual(health_score.overall_score, 1)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)


def create_test_suite():
    """Create and return test suite"""
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestConfigManager,
        TestRateLimiter,
        TestErrorHandler,
        TestGitHubAPIClient,
        TestMetricsStorage,
        TestAnalytics,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
        
    return test_suite


if __name__ == '__main__':
    # Run tests
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)