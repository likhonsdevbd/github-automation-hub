"""
Repository Health Score Calculation System

This module implements algorithms to calculate repository health scores
based on multiple indicators including community engagement, code quality,
activity patterns, and responsiveness metrics.
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import math

import numpy as np
from scipy import stats
from github_api_client import RepositoryMetrics


@dataclass
class HealthScoreComponent:
    """Individual health score component"""
    name: str
    score: float  # 0-100
    weight: float  # 0-1
    normalized_value: float  # 0-1 normalized metric
    trend: str  # "improving", "stable", "declining"
    metadata: Dict[str, Any]


@dataclass
class HealthScoreBreakdown:
    """Complete health score breakdown"""
    overall_score: float  # 0-100
    grade: str  # A+, A, B+, B, C+, C, D+, D, F
    timestamp: datetime
    components: Dict[str, HealthScoreComponent]
    recommendations: List[str]
    summary: str


class HealthScoreCalculator:
    """
    Repository health score calculator using weighted components.
    
    Health score is calculated based on:
    - Community engagement (30%)
    - Code activity (25%)
    - Responsiveness (20%)
    - Community growth (15%)
    - Sustainability (10%)
    """
    
    # Component weights for overall health score
    COMPONENT_WEIGHTS = {
        "community_engagement": 0.30,
        "code_activity": 0.25,
        "responsiveness": 0.20,
        "community_growth": 0.15,
        "sustainability": 0.10
    }
    
    # Component sub-metrics weights
    SUB_METRICS_WEIGHTS = {
        "community_engagement": {
            "issue_response_time": 0.30,
            "contributor_diversity": 0.25,
            "discussion_activity": 0.20,
            "release_frequency": 0.15,
            "documentation_quality": 0.10
        },
        "code_activity": {
            "commit_frequency": 0.40,
            "pr_merge_rate": 0.35,
            "code_churn": 0.15,
            "test_coverage": 0.10
        },
        "responsiveness": {
            "issue_closure_rate": 0.40,
            "pr_review_speed": 0.35,
            "maintenance_frequency": 0.25
        },
        "community_growth": {
            "new_contributors": 0.50,
            "retention_rate": 0.30,
            "star_growth": 0.20
        },
        "sustainability": {
            "dependency_health": 0.40,
            "security_posture": 0.30,
            "documentation_coverage": 0.30
        }
    }
    
    def __init__(self, repository_baselines: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Initialize health score calculator.
        
        Args:
            repository_baselines: Historical baselines for normalization
        """
        self.logger = logging.getLogger(__name__)
        self.baselines = repository_baselines or {}
        self.trend_window_days = 30
        self.historical_window_days = 90
        
    def calculate_health_score(
        self,
        current_metrics: RepositoryMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> HealthScoreBreakdown:
        """
        Calculate comprehensive health score breakdown.
        
        Args:
            current_metrics: Current repository metrics
            historical_metrics: Historical metrics for trend analysis
            
        Returns:
            HealthScoreBreakdown with detailed breakdown
        """
        self.logger.info(f"Calculating health score for {current_metrics.repo_owner}/{current_metrics.repo_name}")
        
        # Calculate component scores
        components = {}
        
        # Community Engagement Score
        community_score = self._calculate_community_engagement_score(
            current_metrics, historical_metrics
        )
        components["community_engagement"] = community_score
        
        # Code Activity Score
        activity_score = self._calculate_code_activity_score(
            current_metrics, historical_metrics
        )
        components["code_activity"] = activity_score
        
        # Responsiveness Score
        responsiveness_score = self._calculate_responsiveness_score(
            current_metrics, historical_metrics
        )
        components["responsiveness"] = responsiveness_score
        
        # Community Growth Score
        growth_score = self._calculate_community_growth_score(
            current_metrics, historical_metrics
        )
        components["community_growth"] = growth_score
        
        # Sustainability Score
        sustainability_score = self._calculate_sustainability_score(
            current_metrics, historical_metrics
        )
        components["sustainability"] = sustainability_score
        
        # Calculate overall score
        overall_score = sum(
            component.score * self.COMPONENT_WEIGHTS[component_name]
            for component_name, component in components.items()
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(components, current_metrics)
        
        # Generate summary
        summary = self._generate_summary(overall_score, components)
        
        # Determine grade
        grade = self._calculate_grade(overall_score)
        
        return HealthScoreBreakdown(
            overall_score=overall_score,
            grade=grade,
            timestamp=current_metrics.timestamp,
            components=components,
            recommendations=recommendations,
            summary=summary
        )
    
    def _calculate_community_engagement_score(
        self,
        metrics: RepositoryMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> HealthScoreComponent:
        """Calculate community engagement score"""
        
        # Issue response time (lower is better)
        issue_response_score = self._normalize_metric(
            metrics.issue_response_time_avg,
            baseline_key="issue_response_time",
            lower_is_better=True,
            target_value=24,  # 24 hours target
            max_value=168  # 1 week maximum acceptable
        )
        
        # Contributor diversity (based on unique contributors)
        diversity_score = self._normalize_contributor_diversity(metrics.total_contributors)
        
        # Discussion activity (placeholder - would need Discussions API)
        discussion_score = self._normalize_discussion_activity(metrics.discussions_count)
        
        # Release frequency
        release_score = self._normalize_release_frequency(
            metrics.releases_count,
            historical_metrics
        )
        
        # Documentation quality (placeholder - would need file analysis)
        docs_score = 75.0  # Neutral score for now
        
        # Calculate weighted component score
        weights = self.SUB_METRICS_WEIGHTS["community_engagement"]
        component_score = (
            issue_response_score * weights["issue_response_time"] +
            diversity_score * weights["contributor_diversity"] +
            discussion_score * weights["discussion_activity"] +
            release_score * weights["release_frequency"] +
            docs_score * weights["documentation_quality"]
        )
        
        # Determine trend
        trend = self._calculate_trend("community_engagement", historical_metrics)
        
        return HealthScoreComponent(
            name="Community Engagement",
            score=component_score,
            weight=self.COMPONENT_WEIGHTS["community_engagement"],
            normalized_value=component_score / 100,
            trend=trend,
            metadata={
                "issue_response_time": metrics.issue_response_time_avg,
                "contributor_diversity": diversity_score,
                "discussion_activity": metrics.discussions_count,
                "release_frequency": metrics.releases_count,
                "documentation_quality": docs_score
            }
        )
    
    def _calculate_code_activity_score(
        self,
        metrics: RepositoryMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> HealthScoreComponent:
        """Calculate code activity score"""
        
        # Commit frequency (normalized by time period)
        commit_score = self._normalize_commit_frequency(
            metrics.commits_this_month,
            historical_metrics
        )
        
        # PR merge rate
        total_prs = metrics.merged_prs + metrics.open_prs + metrics.closed_prs
        merge_rate = (metrics.merged_prs / max(1, total_prs)) * 100
        merge_score = self._normalize_metric(
            merge_rate,
            baseline_key="pr_merge_rate",
            lower_is_better=False,
            target_value=80,  # 80% merge rate target
            max_value=100
        )
        
        # Code churn (placeholder - would need diff analysis)
        churn_score = 70.0  # Neutral score
        
        # Test coverage (placeholder - would need coverage data)
        coverage_score = 75.0  # Neutral score
        
        # Calculate weighted component score
        weights = self.SUB_METRICS_WEIGHTS["code_activity"]
        component_score = (
            commit_score * weights["commit_frequency"] +
            merge_score * weights["pr_merge_rate"] +
            churn_score * weights["code_churn"] +
            coverage_score * weights["test_coverage"]
        )
        
        # Determine trend
        trend = self._calculate_trend("code_activity", historical_metrics)
        
        return HealthScoreComponent(
            name="Code Activity",
            score=component_score,
            weight=self.COMPONENT_WEIGHTS["code_activity"],
            normalized_value=component_score / 100,
            trend=trend,
            metadata={
                "commit_frequency": metrics.commits_this_month,
                "pr_merge_rate": merge_rate,
                "code_churn": churn_score,
                "test_coverage": coverage_score
            }
        )
    
    def _calculate_responsiveness_score(
        self,
        metrics: RepositoryMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> HealthScoreComponent:
        """Calculate responsiveness score"""
        
        # Issue closure rate
        closure_score = self._normalize_metric(
            metrics.issue_closure_rate,
            baseline_key="issue_closure_rate",
            lower_is_better=False,
            target_value=80,  # 80% closure rate target
            max_value=100
        )
        
        # PR review speed
        review_score = self._normalize_metric(
            metrics.pr_merge_time_avg,
            baseline_key="pr_review_speed",
            lower_is_better=True,
            target_value=72,  # 72 hours target
            max_value=168  # 1 week maximum
        )
        
        # Maintenance frequency (based on recent commits)
        maintenance_score = self._normalize_metric(
            metrics.commits_this_week,
            baseline_key="maintenance_frequency",
            lower_is_better=False,
            target_value=10,  # 10 commits per week target
            max_value=50
        )
        
        # Calculate weighted component score
        weights = self.SUB_METRICS_WEIGHTS["responsiveness"]
        component_score = (
            closure_score * weights["issue_closure_rate"] +
            review_score * weights["pr_review_speed"] +
            maintenance_score * weights["maintenance_frequency"]
        )
        
        # Determine trend
        trend = self._calculate_trend("responsiveness", historical_metrics)
        
        return HealthScoreComponent(
            name="Responsiveness",
            score=component_score,
            weight=self.COMPONENT_WEIGHTS["responsiveness"],
            normalized_value=component_score / 100,
            trend=trend,
            metadata={
                "issue_closure_rate": metrics.issue_closure_rate,
                "pr_review_speed": metrics.pr_merge_time_avg,
                "maintenance_frequency": metrics.commits_this_week
            }
        )
    
    def _calculate_community_growth_score(
        self,
        metrics: RepositoryMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> HealthScoreComponent:
        """Calculate community growth score"""
        
        # New contributors
        new_contributors_score = self._normalize_metric(
            metrics.new_contributors_month,
            baseline_key="new_contributors",
            lower_is_better=False,
            target_value=5,  # 5 new contributors per month target
            max_value=20
        )
        
        # Retention rate (placeholder - would need contributor tracking)
        retention_score = 75.0  # Neutral score
        
        # Star growth (normalized growth rate)
        star_growth_score = self._normalize_star_growth(
            metrics.stars,
            historical_metrics
        )
        
        # Calculate weighted component score
        weights = self.SUB_METRICS_WEIGHTS["community_growth"]
        component_score = (
            new_contributors_score * weights["new_contributors"] +
            retention_score * weights["retention_rate"] +
            star_growth_score * weights["star_growth"]
        )
        
        # Determine trend
        trend = self._calculate_trend("community_growth", historical_metrics)
        
        return HealthScoreComponent(
            name="Community Growth",
            score=component_score,
            weight=self.COMPONENT_WEIGHTS["community_growth"],
            normalized_value=component_score / 100,
            trend=trend,
            metadata={
                "new_contributors": metrics.new_contributors_month,
                "retention_rate": retention_score,
                "star_growth": star_growth_score
            }
        )
    
    def _calculate_sustainability_score(
        self,
        metrics: RepositoryMetrics,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> HealthScoreComponent:
        """Calculate sustainability score"""
        
        # Dependency health (placeholder - would need dependency analysis)
        dependency_score = 75.0  # Neutral score
        
        # Security posture (placeholder - would need security scan data)
        security_score = 80.0  # Good baseline
        
        # Documentation coverage (placeholder - would need file analysis)
        docs_score = 70.0  # Acceptable baseline
        
        # Calculate component score
        weights = self.SUB_METRICS_WEIGHTS["sustainability"]
        component_score = (
            dependency_score * weights["dependency_health"] +
            security_score * weights["security_posture"] +
            docs_score * weights["documentation_coverage"]
        )
        
        # Determine trend
        trend = self._calculate_trend("sustainability", historical_metrics)
        
        return HealthScoreComponent(
            name="Sustainability",
            score=component_score,
            weight=self.COMPONENT_WEIGHTS["sustainability"],
            normalized_value=component_score / 100,
            trend=trend,
            metadata={
                "dependency_health": dependency_score,
                "security_posture": security_score,
                "documentation_coverage": docs_score
            }
        )
    
    def _normalize_metric(
        self,
        value: float,
        baseline_key: str,
        lower_is_better: bool,
        target_value: float,
        max_value: float
    ) -> float:
        """
        Normalize a metric to 0-100 scale based on target and max values.
        
        Args:
            value: Raw metric value
            baseline_key: Key for historical baseline lookup
            lower_is_better: Whether lower values are better
            target_value: Target value for optimal score
            max_value: Maximum value before score reaches 0
            
        Returns:
            Normalized score (0-100)
        """
        if value == 0 and not lower_is_better:
            return 0.0
        
        if lower_is_better:
            # For metrics where lower is better (e.g., response time)
            if value <= target_value:
                return 100.0
            elif value >= max_value:
                return 0.0
            else:
                # Linear interpolation between target and max
                return 100.0 - ((value - target_value) / (max_value - target_value)) * 100.0
        else:
            # For metrics where higher is better
            if value >= target_value:
                return 100.0
            elif value <= 0:
                return 0.0
            else:
                # Linear interpolation between 0 and target
                return (value / target_value) * 100.0
    
    def _normalize_contributor_diversity(self, total_contributors: int) -> float:
        """Normalize contributor diversity score"""
        # Sigmoid function to reward growth but with diminishing returns
        # 1 contributor = ~20 points, 10 contributors = ~80 points, 50+ contributors = ~98 points
        normalized = 100 / (1 + math.exp(-0.1 * (total_contributors - 10)))
        return min(100.0, max(0.0, normalized))
    
    def _normalize_discussion_activity(self, discussions_count: int) -> float:
        """Normalize discussion activity score"""
        # Based on number of active discussions
        if discussions_count == 0:
            return 30.0  # Low score for no discussions
        elif discussions_count < 5:
            return 60.0
        elif discussions_count < 15:
            return 80.0
        elif discussions_count < 30:
            return 90.0
        else:
            return 95.0
    
    def _normalize_release_frequency(
        self,
        releases_count: int,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> float:
        """Normalize release frequency score"""
        if historical_metrics:
            # Calculate average monthly releases over historical period
            monthly_releases = [m.releases_count / max(1, (datetime.now() - m.timestamp).days / 30) 
                              for m in historical_metrics if (datetime.now() - m.timestamp).days > 0]
            avg_releases = statistics.mean(monthly_releases) if monthly_releases else 0
            
            # Score based on consistency and frequency
            if avg_releases >= 2:  # 2+ releases per month
                return 100.0
            elif avg_releases >= 1:  # 1 release per month
                return 85.0
            elif avg_releases >= 0.5:  # 1 release every 2 months
                return 70.0
            elif avg_releases >= 0.25:  # 1 release every 4 months
                return 50.0
            else:
                return 30.0
        else:
            # Fallback based on total releases
            if releases_count >= 12:
                return 100.0
            elif releases_count >= 6:
                return 80.0
            elif releases_count >= 3:
                return 60.0
            elif releases_count >= 1:
                return 40.0
            else:
                return 20.0
    
    def _normalize_commit_frequency(
        self,
        commits_per_month: int,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> float:
        """Normalize commit frequency score"""
        if historical_metrics:
            # Calculate average monthly commits
            monthly_commits = [m.commits_this_month for m in historical_metrics[-12:]]  # Last 12 data points
            avg_commits = statistics.mean(monthly_commits) if monthly_commits else commits_per_month
            
            # Score based on consistency and frequency
            if avg_commits >= 50:  # Very active
                return 100.0
            elif avg_commits >= 30:  # Active
                return 85.0
            elif avg_commits >= 15:  # Moderate
                return 70.0
            elif avg_commits >= 5:  # Low activity
                return 50.0
            else:
                return 30.0
        else:
            # Fallback scoring
            if commits_per_month >= 50:
                return 100.0
            elif commits_per_month >= 30:
                return 85.0
            elif commits_per_month >= 15:
                return 70.0
            elif commits_per_month >= 5:
                return 50.0
            else:
                return 30.0
    
    def _normalize_star_growth(
        self,
        current_stars: int,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> float:
        """Normalize star growth score"""
        if historical_metrics and len(historical_metrics) >= 2:
            # Calculate growth rate
            old_stars = historical_metrics[-1].stars if historical_metrics else 0
            growth_rate = (current_stars - old_stars) / max(1, old_stars) * 100
            
            # Score based on growth rate
            if growth_rate >= 20:  # 20%+ growth
                return 100.0
            elif growth_rate >= 10:  # 10-20% growth
                return 85.0
            elif growth_rate >= 5:  # 5-10% growth
                return 70.0
            elif growth_rate >= 0:  # 0-5% growth
                return 60.0
            else:
                return 30.0  # Negative growth
        else:
            # Fallback based on total stars
            if current_stars >= 1000:
                return 100.0
            elif current_stars >= 500:
                return 80.0
            elif current_stars >= 100:
                return 60.0
            elif current_stars >= 10:
                return 40.0
            else:
                return 20.0
    
    def _calculate_trend(
        self,
        component_name: str,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> str:
        """Calculate trend direction for a component"""
        if not historical_metrics or len(historical_metrics) < 3:
            return "stable"
        
        # For simplicity, we'll analyze the trend of the overall score
        # In a real implementation, you'd track component-specific historical data
        recent_scores = [90, 85, 80]  # Placeholder - would need actual component history
        
        if len(recent_scores) >= 3:
            # Calculate trend using linear regression
            x = np.arange(len(recent_scores))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_scores)
            
            if slope > 2:  # Increasing trend
                return "improving"
            elif slope < -2:  # Decreasing trend
                return "declining"
            else:
                return "stable"
        
        return "stable"
    
    def _generate_recommendations(
        self,
        components: Dict[str, HealthScoreComponent],
        metrics: RepositoryMetrics
    ) -> List[str]:
        """Generate actionable recommendations based on health score breakdown"""
        recommendations = []
        
        # Community Engagement recommendations
        community_component = components.get("community_engagement")
        if community_component and community_component.score < 60:
            if metrics.issue_response_time_avg > 48:
                recommendations.append("Improve issue response time by assigning dedicated triage volunteers")
            if metrics.total_contributors < 5:
                recommendations.append("Focus on attracting new contributors through 'good first issue' labels")
            if metrics.releases_count < 2:
                recommendations.append("Establish regular release schedule to maintain community engagement")
        
        # Code Activity recommendations
        activity_component = components.get("code_activity")
        if activity_component and activity_component.score < 60:
            if metrics.commits_this_month < 10:
                recommendations.append("Increase development activity to maintain momentum")
            total_prs = metrics.merged_prs + metrics.open_prs + metrics.closed_prs
            merge_rate = (metrics.merged_prs / max(1, total_prs)) * 100
            if merge_rate < 60:
                recommendations.append("Review and streamline PR process to improve merge rates")
        
        # Responsiveness recommendations
        responsiveness_component = components.get("responsiveness")
        if responsiveness_component and responsiveness_component.score < 60:
            if metrics.issue_closure_rate < 60:
                recommendations.append("Implement systematic issue triage and closure process")
            if metrics.pr_merge_time_avg > 96:  # 4 days
                recommendations.append("Reduce PR review time by adding more reviewers or implementing review rotation")
        
        # Community Growth recommendations
        growth_component = components.get("community_growth")
        if growth_component and growth_component.score < 60:
            if metrics.new_contributors_month == 0:
                recommendations.append("Launch contributor onboarding program to attract new maintainers")
        
        # Sustainability recommendations
        sustainability_component = components.get("sustainability")
        if sustainability_component and sustainability_component.score < 60:
            recommendations.append("Conduct dependency audit and security review")
            recommendations.append("Improve documentation coverage and organization")
        
        return recommendations
    
    def _generate_summary(
        self,
        overall_score: float,
        components: Dict[str, HealthScoreComponent]
    ) -> str:
        """Generate human-readable summary of health score"""
        if overall_score >= 90:
            summary = "Excellent repository health with strong community engagement and active development."
        elif overall_score >= 80:
            summary = "Good repository health with active community and regular development activity."
        elif overall_score >= 70:
            summary = "Fair repository health. Some areas need attention for sustained growth."
        elif overall_score >= 60:
            summary = "Moderate repository health with several improvement opportunities."
        elif overall_score >= 40:
            summary = "Below-average repository health requiring immediate attention."
        else:
            summary = "Poor repository health with critical issues requiring urgent action."
        
        # Add component-specific insights
        lowest_component = min(components.values(), key=lambda c: c.score)
        if lowest_component.score < 50:
            summary += f" Primary concern: {lowest_component.name.lower()}."
        
        return summary
    
    def _calculate_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 65:
            return "D+"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def calculate_grade_distribution(
        self,
        health_scores: List[float]
    ) -> Dict[str, int]:
        """Calculate grade distribution for multiple repositories"""
        distribution = {"A+": 0, "A": 0, "B+": 0, "B": 0, "C+": 0, "C": 0, "D+": 0, "D": 0, "F": 0}
        
        for score in health_scores:
            grade = self._calculate_grade(score)
            distribution[grade] += 1
        
        return distribution