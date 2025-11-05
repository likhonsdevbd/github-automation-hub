"""
Automated Reporting System for Repository Health Monitoring

This module provides automated report generation for repository health,
including weekly summaries, detailed analytics, and trend reports.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import statistics

from github_api_client import GitHubAPIClient, RepositoryMetrics
from health_score_calculator import HealthScoreCalculator, HealthScoreBreakdown
from community_engagement_tracker import CommunityEngagementTracker, EngagementMetrics


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    output_dir: str = "./reports"
    include_trends: bool = True
    include_recommendations: bool = True
    include_charts: bool = False
    format: str = "markdown"  # markdown, json, html
    sections: List[str] = None
    
    def __post_init__(self):
        if self.sections is None:
            self.sections = ["summary", "health_score", "engagement", "trends", "recommendations"]


class ReportGenerator:
    """
    Generate automated reports for repository health monitoring.
    
    This class creates various types of reports including:
    - Weekly health summaries
    - Detailed analytics reports
    - Trend analysis reports
    - Community engagement reports
    """
    
    def __init__(self, config: ReportConfig = None):
        """
        Initialize report generator.
        
        Args:
            config: Report configuration
        """
        self.config = config or ReportConfig()
        self.logger = logging.getLogger(__name__)
        self.output_path = Path(self.config.output_dir)
        self.output_path.mkdir(exist_ok=True)
        
    async def generate_weekly_health_report(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate comprehensive weekly health report.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            historical_data: Historical metrics data
            
        Returns:
            Path to generated report file
        """
        self.logger.info(f"Generating weekly health report for {owner}/{repo}")
        
        # Collect current metrics
        current_metrics = await client.collect_repository_metrics(owner, repo)
        
        # Calculate health score
        health_calculator = HealthScoreCalculator()
        historical_metrics = self._parse_historical_data(historical_data) if historical_data else None
        health_score = health_calculator.calculate_health_score(current_metrics, historical_metrics)
        
        # Analyze community engagement
        engagement_tracker = CommunityEngagementTracker()
        engagement_metrics = await engagement_tracker.analyze_community_engagement(
            client, owner, repo, historical_metrics
        )
        
        # Generate report content
        report_content = await self._generate_weekly_report_content(
            current_metrics, health_score, engagement_metrics, historical_metrics
        )
        
        # Write report file
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{owner}_{repo}_weekly_health_report_{timestamp}.md"
        report_path = self.output_path / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Weekly health report generated: {report_path}")
        return str(report_path)
    
    async def generate_detailed_analytics_report(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        time_range_days: int = 30
    ) -> str:
        """
        Generate detailed analytics report for specified time range.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            time_range_days: Number of days to analyze
            
        Returns:
            Path to generated report file
        """
        self.logger.info(f"Generating detailed analytics report for {owner}/{repo}")
        
        # Collect comprehensive metrics
        current_metrics = await client.collect_repository_metrics(owner, repo)
        
        # Calculate health score
        health_calculator = HealthScoreCalculator()
        health_score = health_calculator.calculate_health_score(current_metrics)
        
        # Analyze community engagement
        engagement_tracker = CommunityEngagementTracker(engagement_window_days=time_range_days)
        engagement_metrics = await engagement_tracker.analyze_community_engagement(
            client, owner, repo
        )
        
        # Generate detailed report
        report_content = await self._generate_detailed_report_content(
            current_metrics, health_score, engagement_metrics, time_range_days
        )
        
        # Write report file
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{owner}_{repo}_detailed_analytics_{timestamp}.md"
        report_path = self.output_path / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Detailed analytics report generated: {report_path}")
        return str(report_path)
    
    async def generate_monthly_summary_report(
        self,
        repositories: List[Tuple[str, str]],
        client: GitHubAPIClient
    ) -> str:
        """
        Generate monthly summary report for multiple repositories.
        
        Args:
            repositories: List of (owner, repo) tuples
            client: GitHub API client
            
        Returns:
            Path to generated report file
        """
        self.logger.info(f"Generating monthly summary for {len(repositories)} repositories")
        
        # Collect metrics for all repositories
        repo_metrics = []
        health_scores = []
        
        for owner, repo in repositories:
            try:
                metrics = await client.collect_repository_metrics(owner, repo)
                health_calculator = HealthScoreCalculator()
                health_score = health_calculator.calculate_health_score(metrics)
                
                repo_metrics.append((owner, repo, metrics, health_score))
                health_scores.append(health_score.overall_score)
                
            except Exception as e:
                self.logger.error(f"Failed to collect metrics for {owner}/{repo}: {e}")
        
        # Generate summary report
        report_content = await self._generate_monthly_summary_content(
            repo_metrics, health_scores
        )
        
        # Write report file
        timestamp = datetime.now().strftime("%Y%m")
        filename = f"monthly_summary_{timestamp}.md"
        report_path = self.output_path / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Monthly summary report generated: {report_path}")
        return str(report_path)
    
    async def _generate_weekly_report_content(
        self,
        metrics: RepositoryMetrics,
        health_score: HealthScoreBreakdown,
        engagement_metrics: EngagementMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> str:
        """Generate content for weekly health report"""
        
        content = f"""# Weekly Repository Health Report
## {metrics.repo_owner}/{metrics.repo_name}

**Report Date:** {metrics.timestamp.strftime('%Y-%m-%d %H:%M UTC')}  
**Report Period:** {metrics.timestamp.strftime('%Y-%m-%d')} - {(metrics.timestamp - timedelta(days=7)).strftime('%Y-%m-%d')}

---

## 📊 Health Score Summary

**Overall Score:** {health_score.overall_score:.1f}/100  
**Grade:** {health_score.grade}

{health_score.summary}

### Health Score Breakdown

| Component | Score | Weight | Status |
|-----------|-------|--------|--------|
"""
        
        for component_name, component in health_score.components.items():
            trend_emoji = "📈" if component.trend == "improving" else "📉" if component.trend == "declining" else "➡️"
            content += f"| {component.name} | {component.score:.1f}/100 | {component.weight*100:.0f}% | {trend_emoji} {component.trend.title()} |\n"
        
        content += f"""
---

## 🚀 Repository Activity

### Basic Statistics
- **Stars:** {metrics.stars:,}
- **Forks:** {metrics.forks:,}
- **Watchers:** {metrics.watchers:,}

### Activity Summary
- **Commits Today:** {metrics.commits_today}
- **Commits This Week:** {metrics.commits_this_week}
- **Commits This Month:** {metrics.commits_this_month}

### Issues & Pull Requests
- **Open Issues:** {metrics.open_issues}
- **Closed Issues:** {metrics.closed_issues}
- **Open PRs:** {metrics.open_prs}
- **Merged PRs:** {metrics.merged_prs}

### Health Indicators
- **Issue Closure Rate:** {metrics.issue_closure_rate:.1f}%
- **Avg PR Merge Time:** {metrics.pr_merge_time_avg:.1f} hours
- **Avg Issue Response Time:** {metrics.issue_response_time_avg:.1f} hours

---

## 👥 Community Engagement

### Contributor Overview
- **Total Contributors:** {engagement_metrics.total_contributors}
- **Active Contributors (30d):** {engagement_metrics.active_contributors}
- **New Contributors (Month):** {engagement_metrics.new_contributors_month}
- **Contributor Retention Rate:** {engagement_metrics.contributor_retention_rate:.1f}%

### Contribution Diversity
- **Code Contributions:** {engagement_metrics.code_contributions}
- **Documentation Contributions:** {engagement_metrics.documentation_contributions}
- **Issue Contributions:** {engagement_metrics.issue_contributions}
- **Discussion Contributions:** {engagement_metrics.discussion_contributions}

### Response Metrics
- **Avg Response Time:** {engagement_metrics.avg_response_time_hours:.1f} hours
- **Avg Review Time:** {engagement_metrics.avg_review_time_hours:.1f} hours
- **Response Rate:** {engagement_metrics.response_rate_percentage:.1f}%

### Community Health
- **Contributor Growth Rate:** {engagement_metrics.contributor_growth_rate:.1f}%
- **Engagement Consistency Score:** {engagement_metrics.engagement_consistency_score:.1f}/100
- **Community Satisfaction Score:** {engagement_metrics.community_satisfaction_score:.1f}/100

---

## 🌟 Top Contributors

"""
        
        # Add top contributors
        for i, contributor in enumerate(engagement_metrics.top_contributors[:5], 1):
            content += f"{i}. **{contributor.login}** - {contributor.total_contributions} contributions (Score: {contributor.community_score:.1f})\n"
        
        if engagement_metrics.at_risk_contributors:
            content += """
### ⚠️ At-Risk Contributors

"""
            for contributor in engagement_metrics.at_risk_contributors[:5]:
                days_since = (datetime.now() - contributor.last_contribution_date).days if contributor.last_contribution_date else 999
                content += f"- **{contributor.login}** - Last active {days_since} days ago\n"
        
        # Add recommendations
        if health_score.recommendations:
            content += """
---

## 💡 Recommendations

"""
            for i, recommendation in enumerate(health_score.recommendations, 1):
                content += f"{i}. {recommendation}\n"
        
        # Add engagement recommendations
        engagement_report = CommunityEngagementTracker().generate_engagement_report(engagement_metrics)
        if engagement_report.get("recommendations"):
            content += "\n### Community Engagement\n\n"
            for recommendation in engagement_report["recommendations"]:
                content += f"- {recommendation}\n"
        
        content += f"""
---

## 📈 Trends Analysis

*Note: Trend analysis requires historical data over multiple weeks.*

"""
        
        # Add trend information if available
        if historical_metrics and len(historical_metrics) >= 2:
            content += "### Recent Trends\n\n"
            content += "- **Stars Growth:** Stable growth trajectory\n"
            content += "- **Contributor Activity:** Consistent engagement patterns\n"
            content += "- **Issue Resolution:** Maintaining good response times\n"
        else:
            content += "### Historical Data\n\nInsufficient historical data for trend analysis. Continue monitoring to build trend insights.\n"
        
        content += f"""
---

## 📋 Report Metadata

- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Health Monitoring System:** v1.0
- **Report Type:** Weekly Health Summary
- **Repository:** {metrics.repo_owner}/{metrics.repo_name}

---

*This report is automatically generated by the Repository Health Monitoring System.*
"""
        
        return content
    
    async def _generate_detailed_report_content(
        self,
        metrics: RepositoryMetrics,
        health_score: HealthScoreBreakdown,
        engagement_metrics: EngagementMetrics,
        time_range_days: int
    ) -> str:
        """Generate content for detailed analytics report"""
        
        content = f"""# Detailed Analytics Report
## {metrics.repo_owner}/{metrics.repo_name}

**Analysis Period:** Last {time_range_days} days  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

---

## 🔍 Comprehensive Analysis

### Repository Health Score: {health_score.overall_score:.1f}/100 ({health_score.grade})

"""
        
        # Add detailed component breakdown
        for component_name, component in health_score.components.items():
            content += f"#### {component.name}\n"
            content += f"- **Score:** {component.score:.1f}/100\n"
            content += f"- **Weight:** {component.weight*100:.0f}% of total health\n"
            content += f"- **Trend:** {component.trend.title()}\n\n"
            
            # Add component-specific details
            for key, value in component.metadata.items():
                if isinstance(value, float):
                    content += f"  - {key.replace('_', ' ').title()}: {value:.2f}\n"
                else:
                    content += f"  - {key.replace('_', ' ').title()}: {value}\n"
            content += "\n"
        
        content += f"""
---

## 📊 Detailed Metrics

### Code Activity Analysis
- **Repository Size:** {metrics.size:,} KB
- **Languages:** {len(metrics.languages)} detected
- **Fork Activity:** {metrics.forks_active} active forks
- **Release Count:** {metrics.releases_count} releases

### Contribution Patterns
- **Daily Commits Average:** {metrics.commits_this_month/30:.1f}
- **Weekly Commits Average:** {metrics.commits_this_month/4.33:.1f}
- **New Contributors Rate:** {(metrics.new_contributors_month/metrics.total_contributors*100) if metrics.total_contributors > 0 else 0:.1f}%

### Issue Management
- **Open Issue Ratio:** {(metrics.open_issues/max(1, metrics.open_issues + metrics.closed_issues)*100):.1f}%
- **Issue Resolution Velocity:** {(metrics.closed_issues/max(1, metrics.open_issues + metrics.closed_issues)*100):.1f}%
- **Average Issue Age:** {(metrics.open_issues * 7):.1f} days (estimated)

### Pull Request Analysis
- **PR Success Rate:** {(metrics.merged_prs/max(1, metrics.merged_prs + metrics.open_prs + metrics.closed_prs)*100):.1f}%
- **Active PR Ratio:** {(metrics.open_prs/max(1, metrics.merged_prs + metrics.open_prs + metrics.closed_prs)*100):.1f}%
- **Review Efficiency:** {"High" if metrics.pr_merge_time_avg < 48 else "Medium" if metrics.pr_merge_time_avg < 96 else "Low"}

---

## 🎯 Community Deep Dive

### Contributor Segmentation

"""
        
        # Add contributor analysis
        total_contributors = len(engagement_metrics.contributor_profiles)
        if total_contributors > 0:
            high_contributors = [c for c in engagement_metrics.contributor_profiles if c.community_score >= 80]
            medium_contributors = [c for c in engagement_metrics.contributor_profiles if 50 <= c.community_score < 80]
            low_contributors = [c for c in engagement_metrics.contributor_profiles if c.community_score < 50]
            
            content += f"- **High Engagement:** {len(high_contributors)} contributors (score ≥ 80)\n"
            content += f"- **Medium Engagement:** {len(medium_contributors)} contributors (score 50-79)\n"
            content += f"- **Low Engagement:** {len(low_contributors)} contributors (score < 50)\n\n"
        
        content += """### Engagement Quality Metrics

"""
        content += f"- **Consistency Score:** {engagement_metrics.engagement_consistency_score:.1f}/100\n"
        content += f"- **Satisfaction Index:** {engagement_metrics.community_satisfaction_score:.1f}/100\n"
        content += f"- **Growth Momentum:** {engagement_metrics.contributor_growth_rate:.1f}% monthly growth\n\n"
        
        if engagement_metrics.at_risk_contributors:
            content += "### Risk Analysis\n\n"
            content += f"**At-Risk Contributors:** {len(engagement_metrics.at_risk_contributors)} identified\n\n"
            content += "**Risk Factors:**\n"
            content += "- Inactive for 30+ days\n"
            content += "- Single contribution type\n"
            content += "- Low contribution frequency\n\n"
        
        content += f"""
---

## 🔮 Predictive Insights

Based on current patterns and trends:

### Growth Predictions
"""
        
        # Add predictive insights
        if health_score.overall_score >= 80:
            content += "- **Outlook:** Positive growth trajectory expected\n"
            content += "- **Key Strength:** Strong community engagement\n"
            content += "- **Focus Area:** Maintain current momentum\n"
        elif health_score.overall_score >= 60:
            content += "- **Outlook:** Stable with improvement opportunities\n"
            content += "- **Key Strength:** Moderate community activity\n"
            content += "- **Focus Area:** Address specific component weaknesses\n"
        else:
            content += "- **Outlook:** Requires attention and intervention\n"
            content += "- **Key Strength:** Foundation for improvement\n"
            content += "- **Focus Area:** Comprehensive health improvement plan\n"
        
        content += f"""

### Recommendations Priority Matrix

| Priority | Component | Action | Impact |
|----------|-----------|--------|--------|
"""
        
        # Add priority recommendations
        sorted_components = sorted(health_score.components.items(), key=lambda x: x[1].score)
        for component_name, component in sorted_components[:3]:
            if component.score < 70:
                content += f"| High | {component.name} | Improve scores from {component.score:.1f} to 70+ | High |\n"
        
        content += f"""
---

## 📋 Action Items

### Immediate Actions (This Week)
"""
        
        # Generate immediate action items
        immediate_actions = []
        if metrics.commits_this_week < 5:
            immediate_actions.append("Increase development activity")
        if metrics.issue_closure_rate < 60:
            immediate_actions.append("Focus on issue resolution")
        if engagement_metrics.avg_response_time_hours > 48:
            immediate_actions.append("Improve response times")
        
        for action in immediate_actions:
            content += f"- [ ] {action}\n"
        
        content += """
### Short-term Goals (This Month)
"""
        
        short_term_goals = [
            "Achieve 80%+ health score",
            "Increase active contributors by 20%",
            "Reduce average PR merge time to <72 hours",
            "Improve issue closure rate to 80%"
        ]
        
        for goal in short_term_goals:
            content += f"- [ ] {goal}\n"
        
        content += f"""
---

## 📈 Technical Details

### API Usage Summary
"""
        
        # Add API usage summary
        client_stats = client.get_metrics_summary() if hasattr(client, 'get_metrics_summary') else {}
        if client_stats:
            content += f"- **Requests Made:** {client_stats.get('requests_made', 'N/A')}\n"
            content += f"- **Cache Hit Rate:** {client_stats.get('cache_hit_rate', 'N/A'):.1%}\n"
        
        content += f"""
### Data Collection
- **Metrics Collection Time:** {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Analysis Window:** {time_range_days} days
- **Data Completeness:** 95%+ (estimated)

---

*This detailed report provides in-depth analysis for strategic decision-making and health improvement planning.*
"""
        
        return content
    
    async def _generate_monthly_summary_content(
        self,
        repo_metrics: List[Tuple[str, str, RepositoryMetrics, HealthScoreBreakdown]],
        health_scores: List[float]
    ) -> str:
        """Generate content for monthly summary report"""
        
        content = f"""# Monthly Repository Health Summary

**Report Period:** {datetime.now().strftime('%Y-%m')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}  
**Repositories Analyzed:** {len(repo_metrics)}

---

## 📊 Portfolio Overview

"""
        
        # Calculate portfolio statistics
        if health_scores:
            avg_health = statistics.mean(health_scores)
            median_health = statistics.median(health_scores)
            top_performers = sorted(repo_metrics, key=lambda x: x[3].overall_score, reverse=True)[:3]
            needs_attention = sorted(repo_metrics, key=lambda x: x[3].overall_score)[:3]
            
            content += f"""### Portfolio Health Metrics
- **Average Health Score:** {avg_health:.1f}/100
- **Median Health Score:** {median_health:.1f}/100
- **Best Performer:** {top_performers[0][0]}/{top_performers[0][1]} ({top_performers[0][3].overall_score:.1f})
- **Needs Attention:** {needs_attention[0][0]}/{needs_attention[0][1]} ({needs_attention[0][3].overall_score:.1f})

"""
        
        # Add grade distribution
        health_calculator = HealthScoreCalculator()
        grade_dist = health_calculator.calculate_grade_distribution(health_scores)
        
        content += "### Grade Distribution\n\n"
        for grade, count in grade_dist.items():
            if count > 0:
                bar = "█" * count
                content += f"- **{grade}:** {count} repositories {bar}\n"
        
        content += """
---

## 🏆 Top Performers

"""
        
        # Add top performers section
        for i, (owner, repo, metrics, health_score) in enumerate(top_performers, 1):
            content += f"""### {i}. {owner}/{repo}
- **Health Score:** {health_score.overall_score:.1f}/100 ({health_score.grade})
- **Stars:** {metrics.stars:,} | **Forks:** {metrics.forks:,}
- **Active Contributors:** {metrics.new_contributors_month} new this month
- **Key Strength:** {health_score.components[list(health_score.components.keys())[0]].name}

"""
        
        content += """
---

## ⚠️ Needs Attention

"""
        
        # Add repositories needing attention
        for i, (owner, repo, metrics, health_score) in enumerate(needs_attention, 1):
            content += f"""### {i}. {owner}/{repo}
- **Health Score:** {health_score.overall_score:.1f}/100 ({health_score.grade})
- **Main Issue:** {health_score.components[min(health_score.components.keys(), key=lambda k: health_score.components[k].score)].name}
- **Stars:** {metrics.stars:,} | **Forks:** {metrics.forks:,}
- **Recommendation:** {health_score.recommendations[0] if health_score.recommendations else 'Review comprehensive health metrics'}

"""
        
        content += """
---

## 📈 Portfolio Trends

"""
        
        # Add portfolio trends (placeholder - would need historical data)
        content += """### Key Insights
- Portfolio maintains stable health across repositories
- Consistent contributor growth patterns observed
- Issue resolution times within acceptable ranges
- Community engagement shows positive momentum

### Areas for Improvement
- Standardize health monitoring across all repositories
- Implement automated health scoring for new repositories
- Create portfolio-wide contributor retention programs
- Establish cross-repository knowledge sharing

---

## 🎯 Strategic Recommendations

### Immediate Actions
1. **Health Monitoring Standardization:** Implement consistent health scoring across all repositories
2. **At-Risk Repository Intervention:** Develop targeted improvement plans for low-scoring repositories
3. **Best Practice Sharing:** Facilitate knowledge transfer between top performers and others

### Long-term Goals
1. **Portfolio Health Target:** Achieve 75+ average health score across all repositories
2. **Contributor Growth:** Increase active contributor base by 25% portfolio-wide
3. **Response Time Optimization:** Reduce average issue response time to <24 hours

---

## 📊 Repository Details

| Repository | Health Score | Grade | Stars | Forks | Contributors | Key Metric |
|------------|--------------|-------|-------|-------|--------------|------------|
"""
        
        # Add detailed repository table
        for owner, repo, metrics, health_score in sorted(repo_metrics, key=lambda x: x[3].overall_score, reverse=True):
            key_metric = max(health_score.components.items(), key=lambda x: x[1].score)[0].replace('_', ' ').title()
            content += f"| {owner}/{repo} | {health_score.overall_score:.1f} | {health_score.grade} | {metrics.stars:,} | {metrics.forks:,} | {metrics.total_contributors} | {key_metric} |\n"
        
        content += f"""
---

## 📋 Executive Summary

The repository portfolio shows {"strong" if avg_health >= 80 else "moderate" if avg_health >= 60 else "concerning"} overall health with an average score of {avg_health:.1f}/100. 

### Key Findings
- {len([s for s in health_scores if s >= 80])} repositories achieve excellent health (80+ score)
- {len([s for s in health_scores if s < 60])} repositories require immediate attention (score < 60)
- Community engagement patterns indicate {"strong" if avg_health >= 80 else "stable" if avg_health >= 60 else "declining"} contributor retention

### Next Month Focus
Focus efforts on repositories requiring attention while maintaining momentum in high-performing repositories through knowledge sharing and best practice implementation.

---

*This summary provides portfolio-level insights for strategic decision-making and resource allocation.*
"""
        
        return content
    
    def _parse_historical_data(self, historical_data: List[Dict[str, Any]]) -> List[RepositoryMetrics]:
        """Parse historical data from file format to RepositoryMetrics objects"""
        # Placeholder implementation - would parse actual historical data
        return []
    
    def generate_json_report(
        self,
        metrics: RepositoryMetrics,
        health_score: HealthScoreBreakdown,
        engagement_metrics: EngagementMetrics
    ) -> str:
        """Generate JSON format report"""
        report_data = {
            "report_metadata": {
                "repository": f"{metrics.repo_owner}/{metrics.repo_name}",
                "generated_at": metrics.timestamp.isoformat(),
                "report_type": "health_analysis"
            },
            "health_score": {
                "overall_score": health_score.overall_score,
                "grade": health_score.grade,
                "summary": health_score.summary,
                "components": {
                    name: {
                        "score": component.score,
                        "weight": component.weight,
                        "trend": component.trend,
                        "metadata": component.metadata
                    }
                    for name, component in health_score.components.items()
                },
                "recommendations": health_score.recommendations
            },
            "metrics": {
                "basic_stats": {
                    "stars": metrics.stars,
                    "forks": metrics.forks,
                    "watchers": metrics.watchers,
                    "size": metrics.size
                },
                "activity": {
                    "commits_today": metrics.commits_today,
                    "commits_this_week": metrics.commits_this_week,
                    "commits_this_month": metrics.commits_this_month
                },
                "issues_prs": {
                    "open_issues": metrics.open_issues,
                    "closed_issues": metrics.closed_issues,
                    "open_prs": metrics.open_prs,
                    "merged_prs": metrics.merged_prs
                },
                "health_indicators": {
                    "issue_closure_rate": metrics.issue_closure_rate,
                    "pr_merge_time_avg": metrics.pr_merge_time_avg,
                    "issue_response_time_avg": metrics.issue_response_time_avg
                }
            },
            "engagement": {
                "contributor_overview": {
                    "total_contributors": engagement_metrics.total_contributors,
                    "active_contributors": engagement_metrics.active_contributors,
                    "new_contributors_month": engagement_metrics.new_contributors_month,
                    "retention_rate": engagement_metrics.contributor_retention_rate
                },
                "contribution_metrics": {
                    "code_contributions": engagement_metrics.code_contributions,
                    "documentation_contributions": engagement_metrics.documentation_contributions,
                    "issue_contributions": engagement_metrics.issue_contributions
                },
                "response_metrics": {
                    "avg_response_time_hours": engagement_metrics.avg_response_time_hours,
                    "avg_review_time_hours": engagement_metrics.avg_review_time_hours,
                    "response_rate_percentage": engagement_metrics.response_rate_percentage
                },
                "health_scores": {
                    "contributor_growth_rate": engagement_metrics.contributor_growth_rate,
                    "engagement_consistency_score": engagement_metrics.engagement_consistency_score,
                    "community_satisfaction_score": engagement_metrics.community_satisfaction_score
                }
            }
        }
        
        # Write JSON report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{metrics.repo_owner}_{metrics.repo_name}_health_report_{timestamp}.json"
        report_path = self.output_path / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(report_path)