"""
Dashboard Data Generation System

This module generates structured data for repository health monitoring dashboards,
including time series data, KPI metrics, and visualization datasets.
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
class DashboardConfig:
    """Configuration for dashboard data generation"""
    output_dir: str = "./dashboard_data"
    time_series_days: int = 90
    kpi_update_frequency: str = "daily"  # daily, weekly, monthly
    include_realtime_data: bool = True
    visualization_types: List[str] = None  # ["line", "bar", "pie", "heatmap"]
    
    def __post_init__(self):
        if self.visualization_types is None:
            self.visualization_types = ["line", "bar", "pie"]


@dataclass
class KPIData:
    """Key Performance Indicator data structure"""
    name: str
    value: float
    unit: str
    target: Optional[float] = None
    trend: str = "stable"  # "improving", "declining", "stable"
    change_percentage: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class TimeSeriesData:
    """Time series data for visualizations"""
    metric_name: str
    data_points: List[Dict[str, Any]]  # [{"timestamp": "2023-01-01", "value": 100}]
    unit: str
    aggregation: str = "daily"  # hourly, daily, weekly, monthly
    color: Optional[str] = None


class DashboardDataGenerator:
    """
    Generate structured data for repository health monitoring dashboards.
    
    This class creates:
    - Time series data for trend visualizations
    - KPI metrics for dashboard widgets
    - Comparative data for repository comparisons
    - Alert data for monitoring dashboards
    """
    
    def __init__(self, config: DashboardConfig = None):
        """
        Initialize dashboard data generator.
        
        Args:
            config: Dashboard configuration
        """
        self.config = config or DashboardConfig()
        self.logger = logging.getLogger(__name__)
        self.output_path = Path(self.config.output_dir)
        self.output_path.mkdir(exist_ok=True)
        
        # Color schemes for visualizations
        self.color_schemes = {
            "health_score": "#4CAF50",
            "community_engagement": "#2196F3", 
            "code_activity": "#FF9800",
            "responsiveness": "#9C27B0",
            "sustainability": "#00BCD4",
            "stars": "#FFD700",
            "forks": "#795548",
            "contributors": "#E91E63",
            "commits": "#3F51B5",
            "issues": "#F44336"
        }
    
    async def generate_dashboard_data(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard data for a repository.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            historical_data: Historical metrics data
            
        Returns:
            Dictionary containing all dashboard data
        """
        self.logger.info(f"Generating dashboard data for {owner}/{repo}")
        
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
        
        # Generate all dashboard components
        dashboard_data = {
            "metadata": {
                "repository": f"{owner}/{repo}",
                "generated_at": datetime.now().isoformat(),
                "update_frequency": self.config.kpi_update_frequency
            },
            "kpis": await self._generate_kpi_data(current_metrics, health_score, engagement_metrics),
            "time_series": await self._generate_time_series_data(current_metrics, historical_metrics),
            "health_breakdown": self._generate_health_breakdown_data(health_score),
            "engagement_data": await self._generate_engagement_dashboard_data(engagement_metrics),
            "comparative_data": await self._generate_comparative_data(owner, repo, current_metrics),
            "alerts": await self._generate_alert_data(current_metrics, health_score, engagement_metrics),
            "visualization_config": self._generate_visualization_config()
        }
        
        # Save dashboard data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{owner}_{repo}_dashboard_data_{timestamp}.json"
        output_file = self.output_path / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        # Also save latest version for easy access
        latest_file = self.output_path / f"{owner}_{repo}_dashboard_data_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        self.logger.info(f"Dashboard data generated: {output_file}")
        return dashboard_data
    
    async def _generate_kpi_data(
        self,
        metrics: RepositoryMetrics,
        health_score: HealthScoreBreakdown,
        engagement_metrics: EngagementMetrics
    ) -> List[Dict[str, Any]]:
        """Generate KPI data for dashboard widgets"""
        
        kpis = [
            KPIData(
                name="Health Score",
                value=health_score.overall_score,
                unit="/100",
                target=80.0,
                trend=self._determine_score_trend(health_score),
                change_percentage=self._calculate_trend_change(health_score)
            ),
            KPIData(
                name="Total Stars",
                value=metrics.stars,
                unit="",
                trend="stable" if metrics.stars > 100 else "declining"
            ),
            KPIData(
                name="Active Contributors",
                value=engagement_metrics.active_contributors,
                unit="",
                trend="improving" if engagement_metrics.active_contributors > metrics.total_contributors * 0.1 else "stable"
            ),
            KPIData(
                name="Weekly Commits",
                value=metrics.commits_this_week,
                unit="",
                target=10.0,
                trend="improving" if metrics.commits_this_week > 10 else "declining"
            ),
            KPIData(
                name="Issue Closure Rate",
                value=metrics.issue_closure_rate,
                unit="%",
                target=80.0,
                trend="improving" if metrics.issue_closure_rate > 80 else "declining"
            ),
            KPIData(
                name="PR Merge Time",
                value=metrics.pr_merge_time_avg,
                unit="hours",
                target=48.0,
                trend="improving" if metrics.pr_merge_time_avg < 48 else "declining"
            ),
            KPIData(
                name="Response Time",
                value=engagement_metrics.avg_response_time_hours,
                unit="hours",
                target=24.0,
                trend="improving" if engagement_metrics.avg_response_time_hours < 24 else "declining"
            ),
            KPIData(
                name="Retention Rate",
                value=engagement_metrics.contributor_retention_rate,
                unit="%",
                target=70.0,
                trend="improving" if engagement_metrics.contributor_retention_rate > 70 else "declining"
            ),
            KPIData(
                name="Total Forks",
                value=metrics.forks,
                unit="",
                trend="improving" if metrics.forks > 50 else "stable"
            ),
            KPIData(
                name="New Contributors",
                value=engagement_metrics.new_contributors_month,
                unit="",
                trend="improving" if engagement_metrics.new_contributors_month > 2 else "declining"
            )
        ]
        
        return [kpi.__dict__ for kpi in kpis]
    
    async def _generate_time_series_data(
        self,
        current_metrics: RepositoryMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> List[Dict[str, Any]]:
        """Generate time series data for trend visualizations"""
        
        time_series_data = []
        
        # Create base time series from current metrics and historical data
        metrics_history = []
        if historical_metrics:
            metrics_history.extend(historical_metrics)
        metrics_history.append(current_metrics)
        
        # Sort by timestamp
        metrics_history.sort(key=lambda x: x.timestamp)
        
        # Generate time series for each metric
        for metric_name, getter in [
            ("health_score", lambda m: m.timestamp),  # Placeholder
            ("stars", lambda m: m.stars),
            ("forks", lambda m: m.forks),
            ("commits", lambda m: m.commits_this_month),
            ("contributors", lambda m: m.total_contributors),
            ("open_issues", lambda m: m.open_issues),
            ("merged_prs", lambda m: m.merged_prs),
            ("issue_closure_rate", lambda m: m.issue_closure_rate),
            ("pr_merge_time", lambda m: m.pr_merge_time_avg)
        ]:
            if metric_name == "health_score":
                # Calculate health scores for historical data
                health_scores = []
                health_calculator = HealthScoreCalculator()
                for i, metric in enumerate(metrics_history):
                    historical_subset = metrics_history[:i] if i > 0 else None
                    health_score = health_calculator.calculate_health_score(metric, historical_subset)
                    health_scores.append(health_score.overall_score)
                
                data_points = [
                    {
                        "timestamp": metric.timestamp.strftime("%Y-%m-%d"),
                        "value": score
                    }
                    for metric, score in zip(metrics_history, health_scores)
                ]
            else:
                data_points = [
                    {
                        "timestamp": metric.timestamp.strftime("%Y-%m-%d"),
                        "value": getter(metric)
                    }
                    for metric in metrics_history
                ]
            
            color = self.color_schemes.get(metric_name, "#666666")
            
            time_series = TimeSeriesData(
                metric_name=metric_name.replace("_", " ").title(),
                data_points=data_points,
                unit="",  # Would need to specify per metric
                aggregation="daily",
                color=color
            )
            
            time_series_data.append(time_series.__dict__)
        
        return time_series_data
    
    def _generate_health_breakdown_data(self, health_score: HealthScoreBreakdown) -> Dict[str, Any]:
        """Generate health score breakdown data for dashboard visualization"""
        
        components = []
        for component_name, component in health_score.components.items():
            components.append({
                "name": component.name,
                "score": component.score,
                "weight": component.weight,
                "trend": component.trend,
                "color": self._get_component_color(component_name),
                "metadata": component.metadata
            })
        
        return {
            "overall_score": health_score.overall_score,
            "grade": health_score.grade,
            "summary": health_score.summary,
            "components": components,
            "last_updated": health_score.timestamp.isoformat()
        }
    
    async def _generate_engagement_dashboard_data(
        self,
        engagement_metrics: EngagementMetrics
    ) -> Dict[str, Any]:
        """Generate community engagement data for dashboard"""
        
        return {
            "contributor_overview": {
                "total": engagement_metrics.total_contributors,
                "active": engagement_metrics.active_contributors,
                "new_this_month": engagement_metrics.new_contributors_month,
                "returning": engagement_metrics.returning_contributors,
                "retention_rate": engagement_metrics.contributor_retention_rate
            },
            "contribution_diversity": {
                "code": engagement_metrics.code_contributions,
                "documentation": engagement_metrics.documentation_contributions,
                "issues": engagement_metrics.issue_contributions,
                "discussions": engagement_metrics.discussion_contributions
            },
            "response_metrics": {
                "avg_response_time": engagement_metrics.avg_response_time_hours,
                "avg_review_time": engagement_metrics.avg_review_time_hours,
                "response_rate": engagement_metrics.response_rate_percentage
            },
            "community_health": {
                "growth_rate": engagement_metrics.contributor_growth_rate,
                "consistency_score": engagement_metrics.engagement_consistency_score,
                "satisfaction_score": engagement_metrics.community_satisfaction_score
            },
            "top_contributors": [
                {
                    "login": c.login,
                    "contributions": c.total_contributions,
                    "score": c.community_score,
                    "last_active": c.last_contribution_date.strftime("%Y-%m-%d") if c.last_contribution_date else "Never"
                }
                for c in engagement_metrics.top_contributors[:10]
            ],
            "at_risk_contributors": [
                {
                    "login": c.login,
                    "last_contribution": c.last_contribution_date.strftime("%Y-%m-%d") if c.last_contribution_date else "Never",
                    "risk_level": "High" if (datetime.now() - c.last_contribution_date).days > 60 else "Medium"
                }
                for c in engagement_metrics.at_risk_contributors[:5]
            ]
        }
    
    async def _generate_comparative_data(
        self,
        owner: str,
        repo: str,
        current_metrics: RepositoryMetrics
    ) -> Dict[str, Any]:
        """Generate comparative data for benchmarking"""
        
        # This would typically compare against similar repositories
        # For now, generate placeholder comparative metrics
        return {
            "peer_comparison": {
                "repository_type": "open_source",
                "similar_repos": 150,  # Estimated
                "percentile_rank": self._calculate_percentile_rank(current_metrics.stars),
                "outperforming_areas": ["community_engagement", "issue_response"],
                "improvement_areas": ["release_frequency", "documentation"]
            },
            "historical_comparison": {
                "30_days_ago": {
                    "stars_change": "+5%",
                    "forks_change": "+3%", 
                    "contributors_change": "+8%"
                },
                "90_days_ago": {
                    "stars_change": "+15%",
                    "forks_change": "+12%",
                    "contributors_change": "+25%"
                }
            },
            "benchmark_targets": {
                "health_score_target": 85,
                "response_time_target": 24,
                "retention_rate_target": 75,
                "contributor_growth_target": 10
            }
        }
    
    async def _generate_alert_data(
        self,
        metrics: RepositoryMetrics,
        health_score: HealthScoreBreakdown,
        engagement_metrics: EngagementMetrics
    ) -> List[Dict[str, Any]]:
        """Generate alert data for monitoring dashboard"""
        
        alerts = []
        
        # Health score alerts
        if health_score.overall_score < 60:
            alerts.append({
                "id": "health_score_low",
                "type": "warning",
                "title": "Low Health Score",
                "message": f"Health score is {health_score.overall_score:.1f}/100",
                "severity": "high",
                "component": "overall_health",
                "timestamp": datetime.now().isoformat()
            })
        
        # Response time alerts
        if engagement_metrics.avg_response_time_hours > 48:
            alerts.append({
                "id": "response_time_high",
                "type": "warning",
                "title": "Slow Response Time",
                "message": f"Average response time is {engagement_metrics.avg_response_time_hours:.1f} hours",
                "severity": "medium",
                "component": "community_engagement",
                "timestamp": datetime.now().isoformat()
            })
        
        # Issue closure rate alerts
        if metrics.issue_closure_rate < 60:
            alerts.append({
                "id": "closure_rate_low",
                "type": "warning",
                "title": "Low Issue Closure Rate",
                "message": f"Issue closure rate is {metrics.issue_closure_rate:.1f}%",
                "severity": "medium",
                "component": "responsiveness",
                "timestamp": datetime.now().isoformat()
            })
        
        # At-risk contributors alert
        if len(engagement_metrics.at_risk_contributors) > 0:
            alerts.append({
                "id": "at_risk_contributors",
                "type": "info",
                "title": "At-Risk Contributors",
                "message": f"{len(engagement_metrics.at_risk_contributors)} contributors need attention",
                "severity": "low",
                "component": "community_engagement",
                "timestamp": datetime.now().isoformat()
            })
        
        # Trend alerts
        declining_components = [
            name for name, component in health_score.components.items() 
            if component.trend == "declining"
        ]
        
        if declining_components:
            alerts.append({
                "id": "declining_trends",
                "type": "info",
                "title": "Declining Trends",
                "message": f"Declining trends in: {', '.join(declining_components)}",
                "severity": "low",
                "component": "trends",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _generate_visualization_config(self) -> Dict[str, Any]:
        """Generate configuration for visualizations"""
        
        return {
            "charts": {
                "health_score_trend": {
                    "type": "line",
                    "title": "Health Score Trend",
                    "x_axis": "date",
                    "y_axis": "score",
                    "color": self.color_schemes["health_score"]
                },
                "contributor_activity": {
                    "type": "bar",
                    "title": "Contributor Activity",
                    "x_axis": "metric",
                    "y_axis": "count",
                    "colors": [self.color_schemes["contributors"], self.color_schemes["commits"]]
                },
                "health_breakdown": {
                    "type": "pie",
                    "title": "Health Score Breakdown",
                    "colors": [
                        self._get_component_color("community_engagement"),
                        self._get_component_color("code_activity"),
                        self._get_component_color("responsiveness"),
                        self._get_component_color("community_growth"),
                        self._get_component_color("sustainability")
                    ]
                },
                "response_times": {
                    "type": "gauge",
                    "title": "Response Performance",
                    "min": 0,
                    "max": 168,  # 1 week in hours
                    "target": 24
                }
            },
            "filters": {
                "time_range": {
                    "options": ["7d", "30d", "90d", "1y"],
                    "default": "30d"
                },
                "metrics": {
                    "options": ["health_score", "contributors", "issues", "prs"],
                    "default": ["health_score", "contributors"]
                }
            },
            "update_intervals": {
                "real_time": 300,  # 5 minutes
                "kpis": 3600,      # 1 hour
                "trends": 86400    # 1 day
            }
        }
    
    def _determine_score_trend(self, health_score: HealthScoreBreakdown) -> str:
        """Determine overall trend for health score"""
        # Simple implementation - would need historical data for real trend calculation
        component_trends = [component.trend for component in health_score.components.values()]
        if "declining" in component_trends:
            return "declining"
        elif "improving" in component_trends and component_trends.count("improving") > len(component_trends) / 2:
            return "improving"
        else:
            return "stable"
    
    def _calculate_trend_change(self, health_score: HealthScoreBreakdown) -> float:
        """Calculate percentage change in health score"""
        # Placeholder - would calculate from historical data
        return 2.5  # 2.5% improvement
    
    def _get_component_color(self, component_name: str) -> str:
        """Get color for health component"""
        color_map = {
            "community_engagement": self.color_schemes["community_engagement"],
            "code_activity": self.color_schemes["code_activity"],
            "responsiveness": self.color_schemes["responsiveness"],
            "community_growth": self.color_schemes["sustainability"],
            "sustainability": self.color_schemes["sustainability"]
        }
        return color_map.get(component_name, "#666666")
    
    def _calculate_percentile_rank(self, metric_value: int) -> float:
        """Calculate percentile rank for a metric"""
        # Placeholder implementation
        # In reality, this would compare against database of similar repositories
        if metric_value > 1000:
            return 90.0
        elif metric_value > 100:
            return 70.0
        elif metric_value > 10:
            return 50.0
        else:
            return 30.0
    
    def _parse_historical_data(self, historical_data: List[Dict[str, Any]]) -> List[RepositoryMetrics]:
        """Parse historical data from file format to RepositoryMetrics objects"""
        # Placeholder implementation - would parse actual historical data
        return []
    
    async def generate_portfolio_dashboard_data(
        self,
        repositories: List[Tuple[str, str]],
        client: GitHubAPIClient
    ) -> Dict[str, Any]:
        """Generate dashboard data for multiple repositories"""
        
        portfolio_data = {
            "metadata": {
                "repositories_count": len(repositories),
                "generated_at": datetime.now().isoformat(),
                "type": "portfolio"
            },
            "portfolio_kpis": [],
            "repository_comparison": [],
            "portfolio_trends": [],
            "alerts_summary": []
        }
        
        # Collect data for all repositories
        repository_data = []
        for owner, repo in repositories:
            try:
                metrics = await client.collect_repository_metrics(owner, repo)
                health_calculator = HealthScoreCalculator()
                health_score = health_calculator.calculate_health_score(metrics)
                repository_data.append((owner, repo, metrics, health_score))
            except Exception as e:
                self.logger.error(f"Failed to collect data for {owner}/{repo}: {e}")
        
        # Generate portfolio KPIs
        if repository_data:
            health_scores = [score.overall_score for _, _, _, score in repository_data]
            total_stars = sum(metrics.stars for _, _, metrics, _ in repository_data)
            total_contributors = sum(metrics.total_contributors for _, _, metrics, _ in repository_data)
            avg_contributors = statistics.mean([metrics.total_contributors for _, _, metrics, _ in repository_data])
            
            portfolio_data["portfolio_kpis"] = [
                {"name": "Average Health Score", "value": statistics.mean(health_scores), "unit": "/100"},
                {"name": "Total Stars", "value": total_stars, "unit": ""},
                {"name": "Total Contributors", "value": total_contributors, "unit": ""},
                {"name": "Avg Contributors per Repo", "value": avg_contributors, "unit": ""}
            ]
            
            # Generate repository comparison data
            portfolio_data["repository_comparison"] = [
                {
                    "repository": f"{owner}/{repo}",
                    "health_score": score.overall_score,
                    "stars": metrics.stars,
                    "contributors": metrics.total_contributors,
                    "grade": score.grade
                }
                for owner, repo, metrics, score in repository_data
            ]
        
        # Save portfolio dashboard data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_dashboard_data_{timestamp}.json"
        output_file = self.output_path / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(portfolio_data, f, indent=2, default=str)
        
        self.logger.info(f"Portfolio dashboard data generated: {output_file}")
        return portfolio_data
    
    def generate_realtime_updates(self, metrics: RepositoryMetrics) -> Dict[str, Any]:
        """Generate real-time update data for live dashboards"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "type": "realtime_update",
            "data": {
                "commits_today": metrics.commits_today,
                "active_contributors": metrics.new_contributors_today,
                "open_issues": metrics.open_issues,
                "open_prs": metrics.open_prs,
                "recent_activity": True if metrics.commits_today > 0 else False
            }
        }