# Repository Health Monitoring System

A comprehensive health monitoring and analytics system for GitHub repositories that tracks community engagement, code quality, and growth patterns to provide actionable insights and automated alerting.

## 🎯 Overview

This system monitors GitHub repositories to track health metrics, community engagement patterns, and development activity. It provides automated reports, dashboard data, and intelligent alerting to help maintainers understand and improve their repository's health.

### Key Features

- **📊 Health Score Calculation**: Multi-dimensional health scoring based on community engagement, code activity, responsiveness, growth, and sustainability
- **👥 Community Engagement Tracking**: Analyze contributor behavior, retention patterns, and engagement quality
- **🚨 Intelligent Alerting**: Configurable alerts with multiple notification channels (email, Slack, Discord, webhooks)
- **📈 Automated Reporting**: Daily, weekly, and monthly reports with trend analysis and recommendations
- **📋 Dashboard Data Generation**: Structured data for visualization dashboards and KPIs
- **⚡ Real-time Monitoring**: Rapid response to critical health issues with escalation protocols
- **🔒 Rate-limit Aware**: Optimized GitHub API usage with intelligent caching and backoff

## 🏗️ Architecture

The system follows a modular architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub API    │    │  Health Score   │    │  Alert System   │
│   Integration   │───▶│   Calculator    │───▶│  & Notifications│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Community      │    │    Report       │    │    Dashboard    │
│  Engagement     │───▶│   Generator     │───▶│     Data        │
│    Tracker      │    └─────────────────┘    └─────────────────┘
└─────────────────┘                                    
         │                                              
         ▼                                              
┌─────────────────────────────────────────────────────┐
│            Orchestrator & Workflows                  │
└─────────────────────────────────────────────────────┘
```

## 📦 Components

### Core Modules

1. **GitHub API Client** (`src/github_api_client.py`)
   - Rate-limit aware API integration
   - Comprehensive metrics collection
   - Intelligent caching and error handling

2. **Health Score Calculator** (`src/health_score_calculator.py`)
   - Multi-component health scoring (0-100 scale)
   - Weighted algorithm with trend analysis
   - Grade assignment (A+ to F)

3. **Community Engagement Tracker** (`src/community_engagement_tracker.py`)
   - Contributor behavior analysis
   - Retention and growth tracking
   - At-risk contributor identification

4. **Alert System** (`src/alert_system.py`)
   - Configurable alert rules
   - Multi-channel notifications
   - Escalation and deduplication

5. **Report Generator** (`src/report_generator.py`)
   - Automated report creation (Markdown, JSON)
   - Weekly, monthly, and detailed analytics
   - Portfolio-level summaries

6. **Dashboard Data Generator** (`src/dashboard_data_generator.py`)
   - KPI metrics for dashboards
   - Time series data for visualizations
   - Real-time update generation

### Configuration

- **Main Configuration** (`config/config.yaml`)
  - GitHub API settings
  - Health score parameters
  - Alert thresholds
  - Notification channels

- **Alert Rules** (`config/alert_rules.yaml`)
  - Customizable alert conditions
  - Severity levels and escalation
  - Repository-specific overrides

### Automation

- **Daily Health Monitoring** (`workflows/daily-health-monitoring.yaml`)
  - Scheduled daily health checks
  - Report generation and distribution
  - Data collection and storage

- **Real-time Alerts** (`workflows/realtime-health-alerts.yaml`)
  - Rapid response to critical issues
  - Escalation protocols
  - Immediate stakeholder notification

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token with `repo` and `read:org` scopes
- SMTP credentials for email notifications (optional)
- Slack/Discord webhook URLs (optional)

### Installation

1. **Clone and setup the repository:**
   ```bash
   git clone <repository-url>
   cd health_monitoring
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Configure the system:**
   ```bash
   # Copy and edit configuration files
   cp config/config.yaml.example config/config.yaml
   cp config/alert_rules.yaml.example config/alert_rules.yaml
   
   # Edit with your settings
   nano config/config.yaml
   ```

3. **Set environment variables:**
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   export EMAIL_USERNAME="your_email@example.com"
   export EMAIL_PASSWORD="your_email_password"
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
   ```

### Basic Usage

**Run health monitoring for specific repositories:**
```bash
python scripts/health_monitor.py \
  --repositories "owner1/repo1,owner2/repo2" \
  --config config/config.yaml \
  --alert-rules config/alert_rules.yaml \
  --output-dir ./data \
  --reports-dir ./reports
```

**Monitor repositories from file:**
```bash
echo -e "owner1/repo1\nowner2/repo2\nowner3/repo3" > repos.txt
python scripts/health_monitor.py \
  --repositories "$(cat repos.txt)" \
  --config config/config.yaml
```

**Generate reports without alerts:**
```bash
python scripts/health_monitor.py \
  --repositories "owner/repo" \
  --config config/config.yaml \
  --skip-alerts
```

### GitHub Actions Setup

1. **Add secrets to your repository:**
   - `GITHUB_TOKEN`: Personal access token
   - `HEALTH_CONFIG`: Base64-encoded config.yaml content
   - `ALERT_RULES_CONFIG`: Base64-encoded alert_rules.yaml content
   - `EMAIL_USERNAME`, `EMAIL_PASSWORD`: Email credentials
   - `SLACK_WEBHOOK_URL`: Slack webhook URL

2. **Enable workflows:**
   - The workflows are automatically triggered daily at 2 AM UTC
   - Manual triggering available via GitHub Actions UI

## ⚙️ Configuration

### Health Score Components

The health score is calculated using weighted components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Community Engagement | 30% | Issue response, contributor diversity, discussion activity |
| Code Activity | 25% | Commit frequency, PR merge rate, code churn |
| Responsiveness | 20% | Issue closure rate, PR review speed, maintenance frequency |
| Community Growth | 15% | New contributors, retention rate, star growth |
| Sustainability | 10% | Dependency health, security posture, documentation coverage |

### Alert Rules

Common alert types include:

- **Health Score Alerts**: Triggered when overall health score drops below thresholds
- **Response Time Alerts**: When average issue/PR response times exceed targets
- **Activity Alerts**: When commit activity, issue closure rates, or contributor metrics decline
- **Engagement Alerts**: When new contributors stop or community satisfaction drops

### Notification Channels

Configure multiple notification channels:

- **Email**: SMTP-based email notifications
- **Slack**: Webhook integration for team channels
- **Discord**: Webhook integration for community servers
- **Webhooks**: Generic HTTP webhooks for custom integrations
- **GitHub Issues**: Automatic issue creation for tracking

## 📊 Health Score Details

### Scoring Methodology

The health score (0-100) is calculated using:

1. **Normalization**: Metrics are normalized to 0-1 scale using historical baselines
2. **Weighting**: Each component contributes proportionally to overall score
3. **Grading**: Final scores map to letter grades (A+ to F)

### Score Interpretation

| Grade | Score Range | Description | Action Required |
|-------|-------------|-------------|-----------------|
| A+ | 95-100 | Excellent | Maintain current practices |
| A | 90-94 | Very Good | Minor optimizations |
| B+ | 85-89 | Good | Address specific areas |
| B | 80-84 | Fair | Improvement needed |
| C+ | 75-79 | Below Average | Significant attention required |
| C | 70-74 | Poor | Major improvements needed |
| D+ | 65-69 | Very Poor | Critical issues to address |
| D | 60-64 | Critical | Urgent action required |
| F | 0-59 | Failing | Complete overhaul needed |

## 📈 Dashboard Integration

The system generates structured data for integration with various dashboard solutions:

### KPI Metrics

- Health Score (0-100)
- Community Engagement Score
- Response Time (hours)
- Issue Closure Rate (%)
- Contributor Retention (%)
- Star Growth Rate
- Fork Activity

### Time Series Data

- Daily/weekly/monthly trends
- Historical comparisons
- Seasonal patterns
- Anomaly detection

### Visualization Types

- Line charts for trends
- Bar charts for comparisons
- Pie charts for component breakdown
- Gauge charts for real-time metrics

## 🔧 Advanced Usage

### Custom Health Score Weights

Modify component weights in `config/config.yaml`:

```yaml
health_score:
  weights:
    community_engagement: 0.35  # Increased weight
    code_activity: 0.20        # Decreased weight
    responsiveness: 0.25       # Increased weight
    community_growth: 0.10     # Maintained
    sustainability: 0.10       # Maintained
```

### Custom Alert Rules

Add custom alerts in `config/alert_rules.yaml`:

```yaml
alert_rules:
  - name: "High Security Vulnerabilities"
    id: "security_vulns"
    type: "security_vulnerability"
    severity: "high"
    condition:
      metric: "security.scan_results"
      operator: "gt"
      threshold: 5
    time_window: "24h"
    notifications:
      email: true
      slack: true
```

### Repository-specific Configuration

Override settings per repository:

```yaml
notification_overrides:
  repository_overrides:
    "critical-project":
      critical_alerts:
        email: true
        slack: true
        discord: true
```

### Real-time Monitoring

Enable real-time updates:

```bash
python scripts/health_monitor.py \
  --repositories "owner/repo" \
  --realtime \
  --config config/config.yaml
```

## 🔍 Monitoring and Maintenance

### Health Checks

Regularly check system health:

```bash
# View system status
python -c "from src.alert_system import AlertSystem; print(AlertSystem().get_alert_summary())"

# Check API rate limits
python -c "from src.github_api_client import GitHubAPIClient; import asyncio; client = GitHubAPIClient('token'); print(client.get_metrics_summary())"
```

### Data Management

- **Retention**: Historical data kept for 90 days by default
- **Cleanup**: Automated cleanup of old data and logs
- **Backup**: Regular backup of configuration and reports

### Performance Tuning

- **Caching**: Enable API response caching to reduce GitHub API calls
- **Concurrency**: Adjust concurrent repository processing limits
- **Rate Limiting**: Monitor and adjust GitHub API rate limit settings

## 🚨 Troubleshooting

### Common Issues

**GitHub API Rate Limiting:**
```
Error: Rate limit exceeded
```
- Solution: Increase rate limit buffer, reduce concurrent requests, enable caching

**Authentication Errors:**
```
Error: Bad credentials
```
- Solution: Verify GITHUB_TOKEN has correct scopes and is valid

**Email Notifications Failing:**
```
Error: SMTP authentication failed
```
- Solution: Check email credentials and SMTP server settings

**Workflow Failures:**
```
Error: Workflow failed with exit code 1
```
- Solution: Check workflow logs for specific error details

### Debug Mode

Enable verbose logging:

```bash
python scripts/health_monitor.py \
  --repositories "owner/repo" \
  --verbose \
  --config config/config.yaml
```

### Log Analysis

Check logs for detailed information:

```bash
# View recent logs
tail -f logs/health_monitor.log

# Search for specific errors
grep ERROR logs/health_monitor.log | tail -20

# Check alert-related logs
grep -i alert logs/health_monitor.log
```

## 🤝 Contributing

### Development Setup

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

2. **Run tests:**
   ```bash
   pytest tests/
   pytest tests/ --cov=src/
   ```

3. **Code formatting:**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   ```

### Adding New Features

1. **Health Score Components**: Extend `HealthScoreCalculator`
2. **Alert Types**: Add new `AlertType` enum values and rules
3. **Notifications**: Implement new notification channels
4. **Reports**: Add new report types to `ReportGenerator`

## 📚 API Reference

### Core Classes

#### `GitHubAPIClient`
```python
async with GitHubAPIClient(token) as client:
    metrics = await client.collect_repository_metrics(owner, repo)
```

#### `HealthScoreCalculator`
```python
calculator = HealthScoreCalculator()
health_score = calculator.calculate_health_score(metrics, historical_data)
```

#### `AlertSystem`
```python
alert_system = AlertSystem(notification_config)
alerts = await alert_system.check_repository_health(client, owner, repo)
```

### Configuration Reference

See `config/config.yaml.example` and `config/alert_rules.yaml.example` for complete configuration options.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join GitHub Discussions for questions and ideas
- **Security**: Report security issues via private channels

## 🎉 Acknowledgments

This system is inspired by repository health monitoring best practices and community feedback. Key influences include:

- GitHub's repository insights and analytics
- Open source community health metrics (CHAOSS project)
- DevOps monitoring and alerting patterns
- Community engagement and retention research

---

**Built with ❤️ for healthier open source communities**