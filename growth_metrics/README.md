# Growth Metrics Collection System

A comprehensive system for daily tracking and analysis of GitHub repository growth metrics, implementing the design principles from the Growth Analytics System.

## Overview

This system provides:

- **GitHub API Integration**: Collects commits, stars, forks, issues, PRs, and contributors data
- **Data Storage & Caching**: Efficient storage with SQLite/PostgreSQL support and file backup
- **Historical Analysis**: Trend analysis, forecasting, and anomaly detection
- **Rate Limiting**: Intelligent rate limiting with exponential backoff and circuit breaker
- **Error Handling**: Comprehensive error handling with retry logic and recovery mechanisms

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub API    │    │  Rate Limiter    │    │  Error Handler  │
│   Integration   │◄──►│                  │◄──►│                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────┴─────────┐           │
         │              │   Config Manager   │           │
         │              └───────────────────┘           │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Analytics Engine                                │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐    │
│  │   Health     │ │   Trend      │ │   Community         │    │
│  │   Score      │ │   Analysis   │ │   Engagement        │    │
│  └──────────────┘ └──────────────┘ └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Storage Layer                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐    │
│  │   SQLite/    │ │  File        │ │     Cache           │    │
│  │ PostgreSQL   │ │  Storage     │ │     System          │    │
│  └──────────────┘ └──────────────┘ └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Core Components (`core/`)

- **RateLimiter**: GitHub API rate limiting with exponential backoff
- **ErrorHandler**: Comprehensive error handling and retry logic
- **ConfigManager**: Configuration management with environment support
- **CollectionOrchestrator**: Coordinates daily collection process

### API Integration (`api/`)

- **GitHubAPIClient**: Main GitHub API client for all data collection
- Handles repositories, commits, contributors, issues, and PRs
- Implements efficient pagination and batching
- Rate limit aware and error resilient

### Storage (`storage/`)

- **MetricsStorage**: Unified storage interface
- **MetricsDatabase**: SQLite/PostgreSQL database with optimized schemas
- **FileStorage**: File-based backup storage with compression
- Data retention and cleanup policies

### Analytics (`analytics/`)

- **HealthScoreCalculator**: Repository health scoring based on multiple metrics
- **TrendAnalyzer**: Time series analysis and forecasting
- **AnomalyDetector**: Statistical anomaly detection
- **CommunityEngagementAnalyzer**: Community activity analysis

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# GitHub Configuration
GM_GITHUB_TOKEN=your_github_token_here
GM_GITHUB_TIMEOUT=30
GM_GITHUB_MAX_RETRIES=3
GM_GITHUB_RATE_LIMIT_BUDGET=2000

# Repository targets
GM_GITHUB_ORG=your_organization
GM_GITHUB_REPO=owner/repository

# Storage Configuration  
GM_STORAGE_BACKEND=sqlite
GM_STORAGE_CONNECTION=sqlite:///data/growth_metrics.db
GM_STORAGE_DATA_DIR=./data

# System Configuration
GM_ENVIRONMENT=production
GM_DEBUG=false
GM_LOG_LEVEL=INFO
```

### Configuration File

Create `config/growth_metrics.yaml`:

```yaml
github:
  token: "${GITHUB_TOKEN}"
  timeout: 30
  max_retries: 3
  per_page: 100
  rate_limit_budget: 2000
  repositories:
    - "owner/repository1"
    - "owner/repository2"
  organizations:
    - "your-org"

collection:
  schedule: "0 2 * * *"
  batch_size: 100
  cache_ttl: 300
  enable_caching: true
  enable_rate_limiting: true
  timeout_per_request: 30
  max_concurrent_requests: 5
  historical_days: 365
  snapshot_interval: 24

storage:
  backend: "sqlite"
  connection_string: "sqlite:///data/growth_metrics.db"
  batch_size: 1000
  enable_compression: true
  retention_days: 365
  backup_enabled: true
  backup_interval: 24
  data_directory: "./data"
  create_indexes: true

analytics:
  health_score_weights:
    contributors: 0.30
    pr_throughput: 0.20
    review_velocity: 0.20
    issue_freshness: 0.15
    fork_growth: 0.15
  anomaly_detection_enabled: true
  forecasting_enabled: true
  forecasting_days: 30
  trend_analysis_period: 90
  community_engagement_tracking: true

system:
  environment: "production"
  debug: false
  log_level: "INFO"
  metrics_enabled: true
  telemetry_enabled: true
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd code/automation-hub/growth_metrics
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup configuration**:
   ```bash
   cp config/config_template.yaml config/growth_metrics.yaml
   # Edit config/growth_metrics.yaml with your settings
   ```

4. **Set up environment variables**:
   ```bash
   export GM_GITHUB_TOKEN=your_token_here
   ```

## Usage

### Command Line Usage

Run daily collection:
```bash
python -m growth_metrics.core.collection_orchestrator
```

### GitHub Actions Workflows

The system includes pre-configured GitHub Actions workflows:

1. **Daily Collection**: `workflows/daily-metrics-collection.yaml`
   - Runs daily at 2:00 AM UTC
   - Collects metrics for configured repositories
   - Handles errors and rate limits

2. **Health Analysis**: `workflows/health-analysis.yaml`
   - Weekly health analysis
   - Generates health reports as GitHub issues
   - Trend analysis and anomaly detection

### Python API Usage

```python
from growth_metrics.core.collection_orchestrator import DailyMetricsCollector
from growth_metrics.analytics.growth_analytics import GrowthAnalyticsEngine

# Initialize collector
collector = DailyMetricsCollector('config/growth_metrics.yaml')

# Run collection
summary = collector.run_daily_collection()

# Run analytics
analytics = GrowthAnalyticsEngine()
results = analytics.analyze_repository_growth(current_metrics, historical_data)
```

## Rate Limiting Strategy

The system implements a conservative rate limiting strategy based on GitHub's API limits:

- **Primary Rate Limit**: 5,000 requests/hour
- **Secondary Rate Limit**: ~30 requests/5 minutes for search operations
- **Search API**: Daily quotas for complex searches

**Budget Allocation**:
- Light workload: 100-500 requests/hour (1-3 repos)
- Moderate workload: 1,000-3,000 requests/hour (multiple repos)
- Heavy workload: 3,000-4,500 requests/hour (org-level collection)

## Health Score Calculation

The repository health score is calculated using weighted components:

- **Contributors (30%)**: Unique monthly contributors and retention
- **PR Throughput (20%)**: Opened and merged PRs per period
- **Review Velocity (20%)**: Median time-to-merge for PRs
- **Issue Freshness (15%)**: Mean age of open issues
- **Fork Growth (15%)**: Experimentation and future contributor pool

Scores are normalized against project history and benchmarked against peers.

## Data Retention

- **Metrics Snapshots**: Daily snapshots retained for configurable period (default: 365 days)
- **Commit History**: Retained for 90 days (configurable)
- **Cache**: 5-minute TTL for API responses
- **Logs**: Configurable retention with automatic cleanup

## Monitoring and Alerting

The system provides:

- **Rate Limit Monitoring**: Tracks API usage and remaining quotas
- **Error Tracking**: Categorized error types with retry statistics
- **Collection Health**: Success rates and performance metrics
- **Anomaly Detection**: Statistical detection of unusual patterns

## Security

- **Token Management**: Uses GitHub's automatic `GITHUB_TOKEN`
- **Least Privilege**: Minimal required permissions
- **Secure Storage**: Encrypted configuration and secure credential handling
- **Input Validation**: Sanitizes all inputs and validates configurations

## Troubleshooting

### Common Issues

1. **Rate Limit Exceeded**:
   - Check rate limit status: `python -c "from growth_metrics.api.github_client import GitHubAPIClient; client = GitHubAPIClient(); print(client.get_rate_limit_info())"`
   - Adjust `rate_limit_budget` in configuration
   - Increase collection interval

2. **Authentication Failures**:
   - Verify `GITHUB_TOKEN` is set correctly
   - Check token has required permissions
   - Ensure token hasn't expired

3. **Database Errors**:
   - Check `data/` directory permissions
   - Verify storage configuration
   - Run cleanup if database is corrupted

### Logging

Logs are written to:
- Console output (INFO level)
- `logs/growth_metrics_collection.log` (detailed logs)
- `logs/collection_summary_YYYYMMDD_HHMMSS.json` (collection summaries)

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure rate limiting compliance
5. Test with multiple repository configurations

## License

This project is licensed under the MIT License.

## References

- [GitHub API Rate Limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Growth Analytics System Design](../analytics_system_design/growth_analytics_system.md)