# Growth Metrics Collection System - API Documentation

## Overview

This document provides comprehensive API documentation for the Growth Metrics Collection System, including all classes, methods, and interfaces available for integration.

## Core Components

### ConfigManager

Centralized configuration management with environment variable support.

```python
from growth_metrics.core.config_manager import ConfigManager

# Initialize
config = ConfigManager('config.yaml')

# Load from file and environment
config.load_from_file('growth_metrics.yaml')
config.load_from_environment()

# Get configuration values
github_token = config.get('github.token')
rate_limit_budget = config.github.rate_limit_budget

# Set configuration values
config.set('github.timeout', 45)

# Validate configuration
errors = config.validate()

# Save configuration
config.save_to_file('updated_config.yaml')
```

**Methods:**
- `load_from_file(file_path)` - Load configuration from YAML/JSON file
- `load_from_environment()` - Load from environment variables
- `get(path, default)` - Get value using dot notation
- `set(path, value)` - Set value using dot notation
- `validate()` - Validate configuration and return errors list
- `save_to_file(file_path)` - Save current configuration

### RateLimiter

GitHub API rate limiting with intelligent backoff and circuit breaker.

```python
from growth_metrics.core.rate_limiter import RateLimiter

# Initialize
rate_limiter = RateLimiter({
    'max_retries': 5,
    'cache_ttl': 300,
    'failure_threshold': 10
})

# Make request with rate limiting
response = rate_limiter.make_request_with_backoff(request_function, *args, **kwargs)

# Check rate limits
stats = rate_limiter.get_stats()
print(f"Remaining requests: {stats['primary_remaining']}")

# Cache responses
cached = rate_limiter.get_cached_response('GET', '/endpoint')
rate_limiter.cache_response('GET', '/endpoint', response_data)
```

**Methods:**
- `make_request_with_backoff(func, *args, **kwargs)` - Execute function with rate limiting
- `check_rate_limits(headers)` - Update rate limit stats from response headers
- `get_stats()` - Get current rate limiting statistics
- `get_cached_response(method, url, params)` - Retrieve cached response
- `cache_response(method, url, data, params)` - Cache response data

### ErrorHandler

Comprehensive error handling with retry logic and categorization.

```python
from growth_metrics.core.error_handler import ErrorHandler, with_error_handling

# Initialize
error_handler = ErrorHandler({'max_retries': 3})

# Execute with error handling
result = error_handler.handle_request_with_retry(function, endpoint='/api/endpoint')

# Use decorator
@with_error_handling({'max_retries': 5})
def api_call():
    return requests.get('https://api.github.com/endpoint')
```

**Methods:**
- `handle_request_with_retry(func, endpoint, *args, **kwargs)` - Execute with retry logic
- `get_error_summary(hours)` - Get error statistics for recent period
- `should_use_fallback(endpoint)` - Determine if fallback strategy needed
- `reset_circuit_breaker(endpoint)` - Manually reset circuit breaker

## API Integration

### GitHubAPIClient

Main client for GitHub API integration with comprehensive data collection.

```python
from growth_metrics.api.github_client import GitHubAPIClient

# Initialize
client = GitHubAPIClient(config)

# Repository information
repo_info = client.get_repository('owner', 'repo')

# Commits
commits = client.get_commits('owner', 'repo', since=datetime(2023, 1, 1))

# Contributors
contributors = client.get_contributors('owner', 'repo')

# Issues and Pull Requests
issues = client.get_issues('owner', 'repo', state='open')
prs = client.get_pull_requests('owner', 'repo')

# Current counts
stars = client.get_stargazers_count('owner', 'repo')
forks = client.get_forks_count('owner', 'repo')

# Batch collection
repositories = [('owner1', 'repo1'), ('owner2', 'repo2')]
results = client.batch_collect_metrics(repositories)
```

**Methods:**
- `get_repository(owner, repo)` - Get repository information
- `get_commits(owner, repo, since, until, branch)` - Get commits for date range
- `get_contributors(owner, repo, include_anonymous)` - Get contributors
- `get_issues(owner, repo, state, since, labels)` - Get issues
- `get_pull_requests(owner, repo, state)` - Get pull requests
- `get_stargazers_count(owner, repo)` - Get current star count
- `get_forks_count(owner, repo)` - Get current fork count
- `batch_collect_metrics(repositories, start_date, end_date)` - Batch collection

**Data Structures:**
- `RepositoryInfo` - Repository metadata and statistics
- `CommitInfo` - Individual commit information
- `ContributorInfo` - Contributor details and contributions
- `IssueInfo` - Issue metadata and state
- `PRInfo` - Pull request information and metrics

## Storage Layer

### MetricsStorage

Unified storage interface supporting multiple backends.

```python
from growth_metrics.storage.metrics_storage import MetricsStorage

# Initialize with configuration
storage = MetricsStorage({
    'backend': 'sqlite',
    'connection_string': 'sqlite:///growth_metrics.db',
    'retention_days': 365
})

# Save repository data
storage.save_repository_data(repo_metrics)

# Retrieve historical data
history = storage.get_repository_history('owner', 'repo', days=30)

# Cleanup old data
cleanup_stats = storage.cleanup_old_data()
```

**Methods:**
- `save_repository_data(repo_metrics)` - Save complete repository metrics
- `get_repository_history(owner, name, days)` - Get historical metrics
- `cleanup_old_data()` - Clean up data based on retention policy

### MetricsDatabase

SQLite database with optimized schemas and indexing.

```python
from growth_metrics.storage.metrics_storage import MetricsDatabase

# Initialize database
db = MetricsDatabase('growth_metrics.db', create_indexes=True)

# Insert data
db.insert_repository(repo_data)
db.insert_commits(commits_data)
db.insert_contributors(contributors_data)

# Query data
snapshot = db.get_repository_snapshot('owner', 'repo', date)
history = db.get_repository_history('owner', 'repo', days=30)
metrics = db.get_repository_metrics('owner', 'repo', start_date, end_date)
```

**Methods:**
- `insert_repository(data)` - Insert repository information
- `insert_commits(data)` - Insert commit records in batch
- `insert_contributors(data)` - Insert contributor records
- `insert_issues(data)` - Insert issue records
- `insert_pull_requests(data)` - Insert PR records
- `insert_metrics_snapshot(data)` - Insert daily snapshot
- `get_repository_snapshot(owner, repo, date)` - Get snapshot for specific date
- `get_repository_history(owner, repo, days)` - Get historical data
- `get_repository_metrics(owner, repo, start_date, end_date)` - Get aggregated metrics
- `cleanup_old_data(retention_days)` - Clean up old records

### FileStorage

File-based storage with compression support.

```python
from growth_metrics.storage.metrics_storage import FileStorage

# Initialize
storage = FileStorage('./data', compress=True)

# Save to file
file_path = storage.save_metrics_batch(metrics_data, date=datetime.now())

# Load from file
data = storage.load_metrics_batch(file_path)

# List files
files = storage.list_metrics_files(start_date, end_date)
```

**Methods:**
- `save_metrics_batch(data, date)` - Save metrics to compressed file
- `load_metrics_batch(file_path)` - Load metrics from file
- `list_metrics_files(start_date, end_date)` - List files in date range

## Analytics Engine

### GrowthAnalyticsEngine

Main analytics engine combining all analysis components.

```python
from growth_metrics.analytics.growth_analytics import GrowthAnalyticsEngine

# Initialize
analytics = GrowthAnalyticsEngine(config)

# Analyze repository
results = analytics.analyze_repository_growth(current_metrics, historical_data)

# Get performance benchmark
benchmark = analytics.get_performance_benchmark(repository_data, peer_repositories)
```

**Methods:**
- `analyze_repository_growth(current_metrics, historical_data)` - Comprehensive analysis
- `get_performance_benchmark(repo_data, peer_repos)` - Compare against peers

### HealthScoreCalculator

Repository health scoring based on multiple weighted components.

```python
from growth_metrics.analytics.growth_analytics import HealthScoreCalculator

# Initialize with custom weights
weights = {
    'contributors': 0.30,
    'pr_throughput': 0.20,
    'review_velocity': 0.20,
    'issue_freshness': 0.15,
    'fork_growth': 0.15
}
calculator = HealthScoreCalculator(weights)

# Calculate health score
health_score = calculator.calculate_health_score(metrics_data, historical_data)
```

**Methods:**
- `calculate_health_score(metrics_data, historical_data)` - Calculate comprehensive health score

**Returns:**
- `HealthScoreComponents` dataclass with individual scores and overall score

### TrendAnalyzer

Time series analysis and forecasting capabilities.

```python
from growth_metrics.analytics.growth_analytics import TrendAnalyzer

analyzer = TrendAnalyzer()

# Analyze trends
trends = analyzer.analyze_trends(metrics_data)

# Single metric analysis
trend = analyzer._analyze_single_trend(metrics_data, 'stargazers_count')
```

**Methods:**
- `analyze_trends(data, metric_names)` - Analyze trends for multiple metrics
- `detect_seasonality(values)` - Detect seasonal patterns
- `generate_simple_forecast(values, dates, periods)` - Generate linear forecast

**Returns:**
- `TrendAnalysis` dataclass with direction, strength, growth rate, and forecast

### AnomalyDetector

Statistical anomaly detection using multiple methods.

```python
from growth_metrics.analytics.growth_analytics import AnomalyDetector

detector = AnomalyDetector()

# Detect anomalies
anomalies = detector.detect_anomalies(metrics_data, metric_names)

# Analyze single metric
metric_anomalies = detector._detect_metric_anomalies(metrics_data, 'stargazers_count')
```

**Methods:**
- `detect_anomalies(data, metric_names)` - Detect anomalies in multiple metrics
- `detect_seasonality(values)` - Detect seasonal patterns
- `classify_anomaly_type(value, values, index)` - Classify anomaly type
- `calculate_severity(score)` - Calculate severity level

**Returns:**
- `AnomalyDetection` dataclass with type, score, value, expected value, and description

### CommunityEngagementAnalyzer

Community engagement and activity analysis.

```python
from growth_metrics.analytics.growth_analytics import CommunityEngagementAnalyzer

analyzer = CommunityEngagementAnalyzer()

# Analyze engagement
engagement = analyzer.analyze_engagement(metrics_data)
```

**Methods:**
- `analyze_engagement(metrics_data)` - Comprehensive engagement analysis
- `calculate_contribution_diversity(data)` - Diversity of contribution types
- `calculate_contributor_retention(data)` - Contributor retention rate
- `calculate_issue_response_time(data)` - Issue response metrics
- `calculate_pr_review_velocity(data)` - PR review velocity
- `calculate_community_score(analysis)` - Overall community score

**Returns:**
- Dictionary with contribution diversity, retention, response times, and overall score

## Daily Collection Orchestrator

### DailyMetricsCollector

Orchestrates the complete daily collection process.

```python
from growth_metrics.core.collection_orchestrator import DailyMetricsCollector

# Initialize
collector = DailyMetricsCollector('config.yaml')

# Setup collection targets
collector.setup_collection_targets()

# Run collection
summary = collector.run_daily_collection()

# Single repository collection
repo_metrics = collector.collect_repository_metrics('owner', 'repo')

# Batch collection
results = collector.collect_metrics_batch(max_concurrent=5)
```

**Methods:**
- `setup_collection_targets()` - Setup repositories from configuration
- `collect_repository_metrics(owner, repo, start_date, end_date)` - Collect for single repo
- `collect_metrics_batch(max_concurrent)` - Concurrent collection for all repos
- `process_and_store_metrics()` - Process and store collected data
- `run_daily_collection()` - Complete daily collection workflow
- `cleanup_old_data()` - Clean up old data
- `get_collection_status()` - Get current collection status

**Returns:**
- Dictionary with collection summary, statistics, and errors

## Workflow Templates

### GitHub Actions Workflows

**Daily Metrics Collection** (`workflows/daily-metrics-collection.yaml`):
- Scheduled daily at 2:00 AM UTC
- Configurable repository targets
- Rate limit aware processing
- Comprehensive error handling
- Artifact upload for logs and data

**Health Analysis** (`workflows/health-analysis.yaml`):
- Weekly health score calculation
- Trend analysis and anomaly detection
- Automatic GitHub issue creation for reports
- Benchmark comparison

## Configuration Structure

### Environment Variables

```bash
# Required
GM_GITHUB_TOKEN=your_token_here

# Optional
GM_GITHUB_TIMEOUT=30
GM_GITHUB_MAX_RETRIES=3
GM_GITHUB_RATE_LIMIT_BUDGET=2000
GM_STORAGE_BACKEND=sqlite
GM_STORAGE_CONNECTION=sqlite:///growth_metrics.db
GM_ENVIRONMENT=production
GM_LOG_LEVEL=INFO
```

### Configuration File Format

```yaml
github:
  token: "${GITHUB_TOKEN}"
  timeout: 30
  max_retries: 3
  repositories:
    - "owner/repo1"
    - "owner/repo2"
  organizations:
    - "your-org"

collection:
  schedule: "0 2 * * *"
  batch_size: 100
  enable_caching: true
  max_concurrent_requests: 5

storage:
  backend: "sqlite"
  connection_string: "sqlite:///growth_metrics.db"
  retention_days: 365

analytics:
  health_score_weights:
    contributors: 0.30
    pr_throughput: 0.20
    review_velocity: 0.20
    issue_freshness: 0.15
    fork_growth: 0.15
```

## Error Types

The system categorizes errors for different handling strategies:

- `RATE_LIMIT` - GitHub API rate limiting (429 errors)
- `AUTHENTICATION` - Authentication failures (401 errors)
- `AUTHORIZATION` - Permission errors (403 errors)
- `RESOURCE_NOT_FOUND` - 404 errors
- `SERVER_ERROR` - Server errors (5xx)
- `NETWORK_ERROR` - Network connectivity issues
- `TIMEOUT` - Request timeouts
- `VALIDATION` - Input validation errors
- `QUOTA_EXCEEDED` - API quota exceeded

## Rate Limiting

The system implements a comprehensive rate limiting strategy:

**Budget Allocation:**
- Light workload: 100-500 requests/hour
- Moderate workload: 1,000-3,000 requests/hour
- Heavy workload: 3,000-4,500 requests/hour

**Retry Strategy:**
- Exponential backoff with jitter
- Respect Retry-After headers
- Circuit breaker pattern for resilience
- Request caching to reduce redundant calls

## Health Score Calculation

The health score is a weighted average of five components:

1. **Contributors (30%)**: Monthly contributors and retention
2. **PR Throughput (20%)**: Open/merged PRs ratio
3. **Review Velocity (20%)**: Median time-to-merge
4. **Issue Freshness (15%)**: Mean age of open issues
5. **Fork Growth (15%)**: Community experimentation

Scores are normalized 0-1 with 1 being excellent health.

## Data Retention

- **Daily Snapshots**: Retained for configurable period (default: 365 days)
- **Commit History**: Retained for 90 days
- **API Response Cache**: 5-minute TTL
- **Error Logs**: Retained with automatic cleanup

This API documentation covers all major components and interfaces. For implementation examples, see the `examples/` directory and test suite in `tests/`.