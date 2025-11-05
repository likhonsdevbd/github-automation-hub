# Community Analytics System

A comprehensive analytics system for tracking community engagement patterns, member lifecycle, retention analysis, and predicting community health trends in GitHub repositories.

## 🚀 Features

### 1. Community Member Lifecycle Tracking
- **New → Active → Veteran progression** analysis
- **Lifecycle stage transitions** monitoring
- **Member risk assessment** and at-risk identification
- **Progression velocity** metrics

### 2. Engagement Scoring Algorithms
- **Multi-dimensional scoring** (contribution, interaction, consistency, community, impact, growth)
- **Individual contributor scores** with detailed breakdowns
- **Community engagement trends** and patterns
- **Peer comparison** and benchmarking

### 3. Community Health Indicators
- **Comprehensive health assessment** across 5 dimensions:
  - Activity (engagement frequency, contribution diversity)
  - Quality (merge rates, review coverage, issue resolution)
  - Velocity (time-to-merge, response times, throughput)
  - Sustainability (contributor diversity, retention, documentation)
  - Inclusivity (first-time contributor engagement, recognition)
- **Health scoring** with A-F grading system
- **Benchmarking** against repository type standards

### 4. Contributor Retention Analysis
- **Cohort analysis** for retention tracking
- **Churn prediction** with risk scoring
- **Retention factor analysis** and recommendations
- **Intervention opportunity** identification

### 5. Social Network Analysis
- **Collaboration network mapping** (co-authorship, reviews, discussions)
- **Centrality analysis** (degree, betweenness, closeness, eigenvector)
- **Community detection** and cluster analysis
- **Network health metrics** and bridge identification

### 6. Engagement Prediction Models
- **Machine learning-powered forecasting** (when scikit-learn available)
- **Statistical trend analysis** (fallback when ML unavailable)
- **Churn risk prediction** for proactive retention
- **Health outlook forecasting** with confidence intervals

## 📦 Installation

### Prerequisites
- Python 3.8+
- GitHub API access token

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Optional Dependencies
For full ML capabilities:
```bash
pip install scikit-learn networkx
```

## 🔧 Quick Start

### Basic Usage

```python
import asyncio
from github_api_client import GitHubAPIClient
from community_analytics.analytics_orchestrator import CommunityAnalyticsOrchestrator

async def analyze_repository():
    # Initialize client and orchestrator
    client = GitHubAPIClient(token="your_github_token")
    orchestrator = CommunityAnalyticsOrchestrator()
    
    # Generate comprehensive analysis
    report = await orchestrator.generate_comprehensive_analysis(
        client=client,
        owner="owner_name",
        repo="repository_name",
        analysis_period_days=180
    )
    
    # Access results
    print(f"Community Score: {report.overall_community_score}")
    print(f"Community Grade: {report.community_grade}")
    print(f"Key Insights: {report.key_insights}")

asyncio.run(analyze_repository())
```

### Focused Analysis

```python
# Lifecycle tracking only
lifecycle_report = await orchestrator.generate_focused_analysis(
    client, owner, repo, "lifecycle"
)

# Health assessment only
health_report = await orchestrator.generate_focused_analysis(
    client, owner, repo, "health"
)

# Retention analysis only
retention_report = await orchestrator.generate_focused_analysis(
    client, owner, repo, "retention"
)
```

## 📊 Detailed Module Usage

### Member Lifecycle Tracker

```python
from community_analytics.core.lifecycle_tracker import MemberLifecycleTracker

tracker = MemberLifecycleTracker(
    inactivity_threshold_days=90,
    new_member_window_days=30,
    active_member_min_contributions=5,
    veteran_member_min_contributions=50
)

# Analyze member progression
lifecycle_metrics = await tracker.analyze_member_lifecycle(
    client, owner, repo, lookback_days=180
)

# Identify promising new members
promising_members = tracker.identify_promising_new_members(limit=10)

# Get lifecycle summary
summary = tracker.get_lifecycle_summary_report()
```

### Engagement Scorer

```python
from community_analytics.core.engagement_scorer import EngagementScorer

scorer = EngagementScorer()

# Calculate engagement scores
engagement_metrics = await scorer.calculate_engagement_scores(
    client, owner, repo, lookback_days=90
)

# Get individual member breakdown
member_score = scorer.get_member_engagement_breakdown("username")

# Compare two members
comparison = scorer.compare_member_engagement("user1", "user2")
```

### Community Health Indicator

```python
from community_analytics.core.health_indicators import CommunityHealthIndicator

health_indicator = CommunityHealthIndicator()

# Calculate health score
health_score = await health_indicator.calculate_community_health(
    client, owner, repo, lookback_days=90, repo_type="small_oss"
)

# Get health summary
summary = health_indicator.get_health_summary_report()
```

### Retention Analyzer

```python
from community_analytics.core.retention_analyzer import RetentionAnalyzer

analyzer = RetentionAnalyzer()

# Analyze retention
retention_metrics = await analyzer.analyze_contributor_retention(
    client, owner, repo, lookback_days=365
)

# Identify retention opportunities
opportunities = analyzer.identify_retention_opportunities(limit=10)

# Get retention summary
summary = analyzer.get_retention_summary_report()
```

### Social Network Analyzer

```python
from community_analytics.core.network_analyzer import SocialNetworkAnalyzer

network_analyzer = SocialNetworkAnalyzer()

# Analyze social network
network_analysis = await network_analyzer.analyze_social_network(
    client, owner, repo, lookback_days=180
)

# Identify collaboration opportunities
opportunities = network_analyzer.identify_collaboration_opportunities(limit=10)

# Get network summary
summary = network_analyzer.get_network_summary_report()
```

### Prediction Engine

```python
from community_analytics.models.prediction_engine import EngagementPredictionEngine

prediction_engine = EngagementPredictionEngine()

# Predict engagement trends
forecast = await prediction_engine.predict_engagement_trend(
    historical_metrics, prediction_days=30
)

# Assess churn risk
churn_assessment = await prediction_engine.assess_churn_risk(
    contributor_profiles
)

# Predict community health
health_prediction = await prediction_engine.predict_community_health(
    current_metrics, historical_trends
)
```

## 📈 Understanding Results

### Community Analytics Report Structure

```python
class CommunityAnalyticsReport:
    timestamp: datetime
    repository: str
    analysis_period_days: int
    
    # Executive Summary
    overall_community_score: float  # 0-100
    community_grade: str  # A+, A, B+, etc.
    key_insights: List[str]
    priority_recommendations: List[str]
    
    # Detailed Analysis Results
    lifecycle_analysis: Dict[str, Any]
    engagement_analysis: Dict[str, Any]
    health_analysis: Dict[str, Any]
    retention_analysis: Dict[str, Any]
    network_analysis: Dict[str, Any]
    
    # Predictive Insights
    predictions: Dict[str, Any]
    
    # Action Items
    immediate_actions: List[Dict[str, str]]
    long_term_strategies: List[Dict[str, str]]
```

### Health Score Breakdown

The community health score is calculated across 5 dimensions:

- **Activity (20%)**: Contribution frequency, diversity, and consistency
- **Quality (25%)**: Code quality metrics, review coverage, issue resolution
- **Velocity (20%)**: Response times, time-to-merge, throughput
- **Sustainability (20%)**: Contributor diversity, retention, documentation
- **Inclusivity (15%)**: New contributor engagement, recognition, governance

### Engagement Score Components

Individual engagement scores include:

- **Contribution Score (30%)**: Code, documentation, issue contributions
- **Interaction Score (20%)**: Reviews, comments, collaborations
- **Consistency Score (15%)**: Regular activity patterns
- **Community Score (15%)**: Mentoring, helping others, discussions
- **Impact Score (15%)**: Merged PRs, resolved issues
- **Growth Score (5%)**: Improvement over time

## ⚙️ Configuration

### Configuration File

The system uses `config/config.yaml` for configuration:

```yaml
# Example configuration
lifecycle_tracker:
  inactivity_threshold_days: 90
  new_member_window_days: 30
  active_member_min_contributions: 5
  veteran_member_min_contributions: 50

health_indicators:
  category_weights:
    activity: 0.20
    quality: 0.25
    velocity: 0.20
    sustainability: 0.20
    inclusivity: 0.15
```

### Environment Variables

```bash
# GitHub API
GITHUB_TOKEN=your_personal_access_token

# Optional: External services
SLACK_WEBHOOK_URL=your_slack_webhook
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email
EMAIL_PASSWORD=your_password
```

## 🔍 API Reference

### Main Orchestrator Methods

#### `generate_comprehensive_analysis()`
Generates a complete community analytics report.

**Parameters:**
- `client`: GitHub API client
- `owner`: Repository owner
- `repo`: Repository name
- `analysis_period_days`: Analysis period (default: 180)

**Returns:** `CommunityAnalyticsReport`

#### `generate_focused_analysis()`
Generates analysis for a specific area.

**Parameters:**
- `client`: GitHub API client
- `owner`: Repository owner
- `repo`: Repository name
- `analysis_type`: Type of analysis ('lifecycle', 'engagement', 'health', 'retention', 'network')
- `**kwargs`: Additional parameters

**Returns:** Dict containing analysis results

### Data Models

#### Lifecycle Metrics
```python
@dataclass
class LifecycleMetrics:
    total_members: int
    new_members: int
    active_members: int
    veteran_members: int
    at_risk_members: int
    retention_rate_3_months: float
    retention_rate_6_months: float
    retention_rate_12_months: float
    monthly_churn_rate: float
    predicted_lost_next_month: int
```

#### Engagement Metrics
```python
@dataclass
class CommunityEngagementScore:
    total_engagement_score: float
    contribution_engagement: float
    interaction_engagement: float
    consistency_engagement: float
    community_engagement: float
    impact_engagement: float
    growth_engagement: float
    highly_engaged_count: int
    moderately_engaged_count: int
    low_engagement_count: int
```

#### Health Metrics
```python
@dataclass
class CommunityHealthScore:
    overall_score: float  # 0-100
    health_grade: str  # A, B, C, D, F
    activity_score: float
    quality_score: float
    velocity_score: float
    sustainability_score: float
    inclusivity_score: float
    excellent_indicators: int
    good_indicators: int
    warning_indicators: int
    critical_indicators: int
```

## 🤝 Contributing

### Development Setup

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
4. Run tests:
   ```bash
   pytest tests/
   ```

### Adding New Analytics Modules

1. Create a new module in the `core/` directory
2. Implement the analysis interface
3. Add configuration options in `config/config.yaml`
4. Update the orchestrator to include the new module
5. Add tests for the new module
6. Update documentation

### Code Style

- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive docstrings
- Include unit tests for all public methods
- Use meaningful variable and function names

## 📝 Examples

### Example 1: Community Health Dashboard

```python
async def create_health_dashboard():
    client = GitHubAPIClient(token=token)
    orchestrator = CommunityAnalyticsOrchestrator()
    
    # Analyze multiple repositories
    repos = ["owner1/repo1", "owner2/repo2", "owner3/repo3"]
    
    results = []
    for repo in repos:
        owner, repo_name = repo.split("/")
        report = await orchestrator.generate_comprehensive_analysis(
            client, owner, repo_name
        )
        results.append({
            'repository': repo,
            'health_score': report.overall_community_score,
            'grade': report.community_grade,
            'key_issues': report.health_analysis.get('critical_indicators', 0)
        })
    
    # Sort by health score
    results.sort(key=lambda x: x['health_score'], reverse=True)
    
    return results
```

### Example 2: Churn Risk Alert System

```python
async def check_churn_risk():
    client = GitHubAPIClient(token=token)
    orchestrator = CommunityAnalyticsOrchestrator()
    
    # Get retention analysis
    retention_report = await orchestrator.generate_focused_analysis(
        client, owner, repo, "retention"
    )
    
    # Check for high-risk contributors
    high_risk = retention_report.get('high_risk_contributors', [])
    
    if len(high_risk) > 5:
        # Send alert
        send_alert(f"High churn risk: {len(high_risk)} contributors at risk")
        
        # Generate intervention plan
        intervention_plan = generate_intervention_plan(high_risk)
        
        return intervention_plan
    
    return None
```

### Example 3: Engagement Trend Analysis

```python
async def analyze_engagement_trends():
    client = GitHubAPIClient(token=token)
    orchestrator = CommunityAnalyticsOrchestrator()
    
    # Get predictions
    report = await orchestrator.generate_comprehensive_analysis(
        client, owner, repo
    )
    
    # Analyze engagement forecast
    predictions = report.predictions
    if 'engagement_forecast' in predictions:
        forecast = predictions['engagement_forecast']
        
        trend = forecast['overall_trend']
        confidence = forecast['model_confidence']
        
        if trend == 'declining' and confidence > 0.7:
            # Generate action plan for declining engagement
            action_plan = generate_engagement_recovery_plan(forecast)
            return action_plan
    
    return None
```

## 🛡️ Rate Limiting and Best Practices

### GitHub API Rate Limits

The system is designed to respect GitHub API rate limits:

- **Conservative request pacing** to stay well below limits
- **Automatic backoff** on 429 responses
- **Caching** to avoid redundant API calls
- **Batch processing** where possible

### Recommended Usage

```python
# Configure for your use case
orchestrator = CommunityAnalyticsOrchestrator()

# For daily monitoring (light usage)
daily_report = await orchestrator.generate_focused_analysis(
    client, owner, repo, "health", lookback_days=7
)

# For weekly deep analysis
weekly_report = await orchestrator.generate_comprehensive_analysis(
    client, owner, repo, analysis_period_days=90
)

# For monthly strategic review
monthly_report = await orchestrator.generate_comprehensive_analysis(
    client, owner, repo, analysis_period_days=180
)
```

## 📊 Sample Output

### Community Health Report

```json
{
  "overall_community_score": 73.5,
  "community_grade": "B",
  "key_insights": [
    "Community showing stable engagement patterns",
    "Good retention rate but needs improvement in inclusivity"
  ],
  "health_analysis": {
    "activity_score": 78.2,
    "quality_score": 81.5,
    "velocity_score": 69.8,
    "sustainability_score": 72.1,
    "inclusivity_score": 65.4,
    "critical_indicators": 0,
    "warning_indicators": 2
  },
  "priority_recommendations": [
    "Improve first-time contributor onboarding",
    "Increase community engagement activities"
  ]
}
```

## 🆘 Troubleshooting

### Common Issues

1. **Rate Limit Exceeded**
   ```
   Solution: Increase delay between requests or reduce analysis frequency
   ```

2. **Insufficient Data**
   ```
   Solution: Increase lookback_days parameter for more historical data
   ```

3. **Memory Usage**
   ```
   Solution: Process repositories in smaller batches or increase analysis period
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all analytics operations will show detailed logs
```

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- Built on top of the existing community engagement tracking system
- Inspired by GitHub's repository insights and community health metrics
- Incorporates best practices from open source community management

---

For more detailed documentation, see the `docs/` directory or visit our [wiki](link-to-wiki).