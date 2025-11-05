#!/usr/bin/env python3
"""
Example Usage Script for Growth Metrics Collection System
=========================================================

This script demonstrates how to use the growth metrics collection system
for daily tracking, health analysis, and trend reporting.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import json

# Add the package to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.collection_orchestrator import DailyMetricsCollector
from analytics.growth_analytics import GrowthAnalyticsEngine
from storage.metrics_storage import MetricsStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('example_usage.log')
    ]
)

logger = logging.getLogger(__name__)


def setup_example_config():
    """Setup example configuration for demonstration"""
    
    config_data = {
        'github': {
            'token': os.getenv('GITHUB_TOKEN', ''),  # Set this environment variable
            'timeout': 30,
            'max_retries': 3,
            'per_page': 100,
            'rate_limit_budget': 1000,  # Lower for example
            'repositories': [
                # Add your repositories here for testing
                # 'owner/repo-name'
            ],
            'organizations': [
                # Add organizations here for testing
                # 'your-org-name'
            ]
        },
        'collection': {
            'batch_size': 50,  # Smaller batch for example
            'cache_ttl': 300,
            'enable_caching': True,
            'enable_rate_limiting': True,
            'max_concurrent_requests': 3,  # Lower concurrency for example
            'historical_days': 30,  # Shorter history for example
            'snapshot_interval': 24
        },
        'storage': {
            'backend': 'sqlite',
            'connection_string': 'sqlite:///example_growth_metrics.db',
            'data_directory': './example_data',
            'enable_compression': True,
            'retention_days': 30,  # Shorter retention for example
            'backup_enabled': False,
            'create_indexes': True
        },
        'analytics': {
            'health_score_weights': {
                'contributors': 0.30,
                'pr_throughput': 0.20,
                'review_velocity': 0.20,
                'issue_freshness': 0.15,
                'fork_growth': 0.15
            },
            'anomaly_detection_enabled': True,
            'forecasting_enabled': True,
            'forecasting_days': 14,  # Shorter forecast for example
            'trend_analysis_period': 30,
            'community_engagement_tracking': True
        },
        'system': {
            'environment': 'development',
            'debug': True,
            'log_level': 'DEBUG',
            'metrics_enabled': True
        }
    }
    
    # Create directories
    os.makedirs('example_config', exist_ok=True)
    os.makedirs('example_data', exist_ok=True)
    os.makedirs('example_logs', exist_ok=True)
    
    # Save configuration
    import yaml
    with open('example_config/growth_metrics.yaml', 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    logger.info("Example configuration created at example_config/growth_metrics.yaml")


def demonstrate_basic_collection():
    """Demonstrate basic metrics collection"""
    
    logger.info("=== Demonstrating Basic Metrics Collection ===")
    
    try:
        # Initialize collector
        collector = DailyMetricsCollector('example_config/growth_metrics.yaml')
        
        # For demo purposes, add a test repository if none configured
        if not collector.repos_to_collect:
            # Add a well-known open source repo for testing
            test_repo = ("microsoft", "vscode")  # Public repository for testing
            collector.repos_to_collect.append(test_repo)
            logger.info(f"Added test repository: {test_repo[0]}/{test_repo[1]}")
        
        # Run collection
        summary = collector.run_daily_collection()
        
        logger.info("Collection Summary:")
        logger.info(f"  Status: {summary['status']}")
        logger.info(f"  Duration: {summary.get('performance_statistics', {}).get('duration_formatted', 'N/A')}")
        logger.info(f"  Repositories: {summary.get('repository_statistics', {}).get('total_repositories', 0)}")
        logger.info(f"  Success Rate: {summary.get('repository_statistics', {}).get('success_rate', 0):.1%}")
        
        if summary.get('collection_errors'):
            logger.warning(f"Errors encountered: {len(summary['collection_errors'])}")
            for error in summary['collection_errors'][:3]:  # Show first 3 errors
                logger.warning(f"  - {error}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Basic collection failed: {e}")
        return None


def demonstrate_analytics():
    """Demonstrate analytics and health scoring"""
    
    logger.info("=== Demonstrating Analytics and Health Scoring ===")
    
    try:
        # Initialize components
        config = ConfigManager('example_config/growth_metrics.yaml')
        analytics = GrowthAnalyticsEngine(config.get_effective_config()['analytics'])
        storage = MetricsStorage(config.get_effective_config()['storage'])
        
        # Get sample repository data
        test_repo = ("microsoft", "vscode")
        owner, name = test_repo
        
        # Get historical data
        historical_data = storage.get_repository_history(owner, name, days=30)
        
        if not historical_data:
            logger.info("No historical data found. Running quick collection...")
            collector = DailyMetricsCollector('example_config/growth_metrics.yaml')
            collector.repos_to_collect = [test_repo]
            results = collector.collect_repository_metrics(owner, name)
            
            # Convert to storage format
            sample_metrics = results.to_dict()
            sample_metrics['calculated_metrics'] = calculate_sample_metrics(results)
        else:
            sample_metrics = historical_data[-1]  # Most recent
        
        # Run comprehensive analysis
        analysis_results = analytics.analyze_repository_growth(
            current_metrics=sample_metrics,
            historical_data=historical_data
        )
        
        # Display results
        logger.info(f"Analysis Results for {test_repo[0]}/{test_repo[1]}:")
        
        # Health score
        health_score = analysis_results.get('health_score', {})
        if health_score:
            logger.info(f"  Overall Health Score: {health_score.get('overall_score', 0):.2f}")
            logger.info(f"    Contributors Score: {health_score.get('contributors_score', 0):.2f}")
            logger.info(f"    PR Throughput Score: {health_score.get('pr_throughput_score', 0):.2f}")
            logger.info(f"    Review Velocity Score: {health_score.get('review_velocity_score', 0):.2f}")
            logger.info(f"    Issue Freshness Score: {health_score.get('issue_freshness_score', 0):.2f}")
            logger.info(f"    Fork Growth Score: {health_score.get('fork_growth_score', 0):.2f}")
        
        # Trends
        trends = analysis_results.get('trend_analysis', [])
        logger.info(f"  Trends Analyzed: {len(trends)} metrics")
        for trend in trends[:3]:  # Show first 3 trends
            logger.info(f"    {trend['metric_name']}: {trend['trend_direction']} "
                       f"(strength: {trend['trend_strength']:.2f}, growth: {trend['growth_rate']:.1f}%)")
        
        # Anomalies
        anomalies = analysis_results.get('anomalies', [])
        if anomalies:
            logger.info(f"  Anomalies Detected: {len(anomalies)}")
            for anomaly in anomalies[:3]:  # Show first 3 anomalies
                logger.info(f"    {anomaly['severity']} {anomaly['anomaly_type']} in {anomaly['metric_name']}")
        else:
            logger.info("  No anomalies detected")
        
        # Community engagement
        engagement = analysis_results.get('community_engagement', {})
        if engagement:
            logger.info(f"  Community Activity Score: {engagement.get('community_activity_score', 0):.2f}")
            logger.info(f"  Total Contributors: {engagement.get('total_contributors', 0)}")
        
        # Recommendations
        recommendations = analysis_results.get('recommendations', [])
        if recommendations:
            logger.info("  Top Recommendations:")
            for rec in recommendations[:3]:  # Show first 3 recommendations
                logger.info(f"    - {rec}")
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Analytics demonstration failed: {e}")
        return None


def calculate_sample_metrics(repo_metrics):
    """Calculate sample metrics for demonstration"""
    
    metrics_data = repo_metrics.metrics_data
    
    calculated = {
        'total_commits': len(metrics_data.get('commits', [])),
        'active_contributors': len(set(c.author_login for c in metrics_data.get('commits', []) if c.author_login)),
        'total_additions': sum(c.additions for c in metrics_data.get('commits', [])),
        'total_deletions': sum(c.deletions for c in metrics_data.get('commits', [])),
        'open_issues': len([i for i in metrics_data.get('issues', []) if i.state == 'open']),
        'closed_issues': len([i for i in metrics_data.get('issues', []) if i.state == 'closed']),
        'open_prs': len([pr for pr in metrics_data.get('pull_requests', []) if pr.state == 'open']),
        'merged_prs': len([pr for pr in metrics_data.get('pull_requests', []) if pr.state == 'merged'])
    }
    
    # Add current stats
    current_stats = metrics_data.get('current_stats', {})
    calculated.update(current_stats)
    
    return calculated


def demonstrate_trend_analysis():
    """Demonstrate trend analysis capabilities"""
    
    logger.info("=== Demonstrating Trend Analysis ===")
    
    try:
        # Create sample time series data for demonstration
        import numpy as np
        from datetime import datetime, timedelta
        
        # Generate 30 days of sample data
        dates = [(datetime.now() - timedelta(days=x)).date() for x in range(30, 0, -1)]
        
        # Simulate growth in different metrics
        sample_data = []
        for i, date in enumerate(dates):
            sample_record = {
                'snapshot_date': date.isoformat(),
                'stargazers_count': 1000 + i * 10 + np.random.normal(0, 5),
                'forks_count': 100 + i * 2 + np.random.normal(0, 2),
                'contributors_count': 5 + int(i * 0.1) + np.random.randint(-1, 2),
                'commits_count': max(0, np.random.poisson(3)),
                'prs_opened': max(0, np.random.poisson(2)),
                'issues_opened': max(0, np.random.poisson(5)),
                'issues_closed': max(0, np.random.poisson(4))
            }
            sample_data.append(sample_record)
        
        # Initialize analytics
        config = ConfigManager('example_config/growth_metrics.yaml')
        analytics = GrowthAnalyticsEngine(config.get_effective_config()['analytics'])
        
        # Analyze trends
        trends = analytics.trend_analyzer.analyze_trends(sample_data)
        
        logger.info(f"Trend Analysis Results ({len(trends)} metrics):")
        for trend in trends:
            logger.info(f"  {trend.metric_name}:")
            logger.info(f"    Direction: {trend.trend_direction}")
            logger.info(f"    Strength: {trend.trend_strength:.2f}")
            logger.info(f"    Growth Rate: {trend.growth_rate:.1f}% per period")
            logger.info(f"    Seasonality: {'Detected' if trend.seasonality_detected else 'None'}")
            logger.info(f"    Confidence: {trend.confidence:.2f}")
            if trend.forecast_values:
                logger.info(f"    Forecast (next 7 days): {[f'{v:.1f}' for v in trend.forecast_values[:3]]}")
        
        # Detect anomalies
        anomalies = analytics.anomaly_detector.detect_anomalies(sample_data)
        
        logger.info(f"\nAnomaly Detection Results ({len(anomalies)} anomalies):")
        for anomaly in anomalies:
            logger.info(f"  {anomaly.metric_name}: {anomaly.anomaly_type} ({anomaly.severity})")
            logger.info(f"    Value: {anomaly.value:.1f}, Expected: {anomaly.expected_value:.1f}")
            logger.info(f"    Date: {anomaly.date.strftime('%Y-%m-%d')}")
            logger.info(f"    Description: {anomaly.description}")
        
        return {
            'trends': [t.__dict__ for t in trends],
            'anomalies': [a.__dict__ for a in anomalies]
        }
        
    except Exception as e:
        logger.error(f"Trend analysis demonstration failed: {e}")
        return None


def save_example_results(results, filename):
    """Save example results to JSON file"""
    
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")


def main():
    """Main demonstration function"""
    
    print("Growth Metrics Collection System - Example Usage")
    print("=" * 60)
    
    # Setup
    logger.info("Setting up example configuration...")
    setup_example_config()
    
    # Check for GitHub token
    if not os.getenv('GITHUB_TOKEN'):
        print("\n⚠️  Warning: GITHUB_TOKEN environment variable not set.")
        print("   Some features will be limited. For full functionality:")
        print("   export GITHUB_TOKEN=your_token_here")
        print("   (Token needs 'repo' and 'read:org' permissions)\n")
    
    # Demonstrate features
    print("\n1. Basic Metrics Collection")
    collection_results = demonstrate_basic_collection()
    
    print("\n2. Analytics and Health Scoring")
    analytics_results = demonstrate_analytics()
    
    print("\n3. Trend Analysis and Anomaly Detection")
    trend_results = demonstrate_trend_analysis()
    
    # Save results
    if collection_results:
        save_example_results(collection_results, 'example_logs/collection_example.json')
    
    if analytics_results:
        save_example_results(analytics_results, 'example_logs/analytics_example.json')
        
    if trend_results:
        save_example_results(trend_results, 'example_logs/trends_example.json')
    
    print("\n" + "=" * 60)
    print("Example usage completed successfully!")
    print("\nFiles created:")
    print("  - example_config/growth_metrics.yaml (configuration)")
    print("  - example_logs/collection_example.json (collection results)")
    print("  - example_logs/analytics_example.json (analytics results)")
    print("  - example_logs/trends_example.json (trend analysis results)")
    print("  - example_growth_metrics.db (SQLite database)")
    print("\nTo run the actual collection system:")
    print("  export GITHUB_TOKEN=your_token")
    print("  python -m growth_metrics.core.collection_orchestrator")


if __name__ == '__main__':
    main()