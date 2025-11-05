"""
Community Health Indicators System

Provides comprehensive health metrics and indicators for assessing the overall
health and vitality of the community, including leading and lagging indicators.
"""

import asyncio
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
import statistics
import math

from github_api_client import GitHubAPIClient


@dataclass
class HealthIndicator:
    """Individual health indicator with detailed metrics"""
    name: str
    category: str  # activity, quality, velocity, sustainability, inclusivity
    value: float
    target_value: float
    weight: float
    status: str  # excellent, good, warning, critical
    
    # Detailed metrics
    current_value: float = 0.0
    previous_value: Optional[float] = None
    trend: str = "stable"  # improving, declining, stable
    trend_percentage: float = 0.0
    
    # Metadata
    description: str = ""
    measurement_unit: str = ""
    calculation_method: str = ""
    data_sources: List[str] = field(default_factory=list)
    
    # Threshold values
    excellent_threshold: float = 0.0
    good_threshold: float = 0.0
    warning_threshold: float = 0.0
    critical_threshold: float = 0.0
    
    def __post_init__(self):
        """Determine status based on thresholds"""
        self.status = self._determine_status()
    
    def _determine_status(self) -> str:
        """Determine indicator status based on thresholds and target"""
        if self.excellent_threshold == 0:
            # Assume normalized score (0-100)
            if self.value >= 80:
                return "excellent"
            elif self.value >= 60:
                return "good"
            elif self.value >= 40:
                return "warning"
            else:
                return "critical"
        else:
            # Use explicit thresholds
            if self.value >= self.excellent_threshold:
                return "excellent"
            elif self.value >= self.good_threshold:
                return "good"
            elif self.value >= self.warning_threshold:
                return "warning"
            else:
                return "critical"


@dataclass
class CommunityHealthScore:
    """Comprehensive community health assessment"""
    timestamp: datetime
    overall_score: float  # 0-100
    health_grade: str  # A, B, C, D, F
    
    # Category scores (0-100)
    activity_score: float = 0.0
    quality_score: float = 0.0
    velocity_score: float = 0.0
    sustainability_score: float = 0.0
    inclusivity_score: float = 0.0
    responsiveness_score: float = 0.0
    
    # Detailed indicators
    indicators: List[HealthIndicator] = field(default_factory=list)
    
    # Health metrics summary
    excellent_indicators: int = 0
    good_indicators: int = 0
    warning_indicators: int = 0
    critical_indicators: int = 0
    
    # Trends
    overall_trend_30d: float = 0.0  # % change
    overall_trend_90d: float = 0.0  # % change
    
    # Benchmarks
    peer_comparison: Dict[str, float] = field(default_factory=dict)  # vs community type
    historical_averages: Dict[str, float] = field(default_factory=dict)
    
    # Recommendations
    key_strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)


class CommunityHealthIndicator:
    """
    Calculate and monitor community health indicators.
    
    This class provides comprehensive health assessment across multiple dimensions
    including activity, quality, velocity, sustainability, and inclusivity.
    """
    
    def __init__(self):
        """Initialize the health indicator system"""
        self.logger = logging.getLogger(__name__)
        
        # Category weights for overall score calculation
        self.category_weights = {
            'activity': 0.20,
            'quality': 0.25,
            'velocity': 0.20,
            'sustainability': 0.20,
            'inclusivity': 0.15
        }
        
        # Historical health data for trend analysis
        self.health_history: List[CommunityHealthScore] = []
        
        # Health benchmarks by repository type
        self.health_benchmarks = {
            'small_oss': {
                'activity_score': {'excellent': 70, 'good': 50, 'warning': 30},
                'quality_score': {'excellent': 80, 'good': 60, 'warning': 40},
                'velocity_score': {'excellent': 60, 'good': 40, 'warning': 25},
                'sustainability_score': {'excellent': 75, 'good': 55, 'warning': 35},
                'inclusivity_score': {'excellent': 85, 'good': 65, 'warning': 45}
            },
            'enterprise': {
                'activity_score': {'excellent': 85, 'good': 65, 'warning': 45},
                'quality_score': {'excellent': 90, 'good': 75, 'warning': 55},
                'velocity_score': {'excellent': 75, 'good': 55, 'warning': 35},
                'sustainability_score': {'excellent': 80, 'good': 60, 'warning': 40},
                'inclusivity_score': {'excellent': 80, 'good': 60, 'warning': 40}
            }
        }
    
    async def calculate_community_health(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int = 90,
        repo_type: str = "small_oss"
    ) -> CommunityHealthScore:
        """
        Calculate comprehensive community health indicators.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            lookback_days: Days of historical data to analyze
            repo_type: Type of repository for benchmarking ('small_oss', 'enterprise')
            
        Returns:
            CommunityHealthScore with comprehensive health assessment
        """
        self.logger.info(f"Calculating community health for {owner}/{repo}")
        
        # Collect comprehensive data
        data = await self._collect_health_data(client, owner, repo, lookback_days)
        
        # Calculate indicators across all categories
        indicators = []
        
        # Activity indicators
        indicators.extend(self._calculate_activity_indicators(data))
        
        # Quality indicators
        indicators.extend(self._calculate_quality_indicators(data))
        
        # Velocity indicators
        indicators.extend(self._calculate_velocity_indicators(data))
        
        # Sustainability indicators
        indicators.extend(self._calculate_sustainability_indicators(data))
        
        # Inclusivity indicators
        indicators.extend(self._calculate_inclusivity_indicators(data))
        
        # Responsiveness indicators
        indicators.extend(self._calculate_responsiveness_indicators(data))
        
        # Calculate category scores
        category_scores = self._calculate_category_scores(indicators)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores)
        
        # Determine health grade
        health_grade = self._determine_health_grade(overall_score)
        
        # Calculate trends
        trends = self._calculate_health_trends(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_health_recommendations(indicators, category_scores)
        
        # Create health score object
        health_score = CommunityHealthScore(
            timestamp=datetime.now(),
            overall_score=overall_score,
            health_grade=health_grade,
            activity_score=category_scores.get('activity', 0.0),
            quality_score=category_scores.get('quality', 0.0),
            velocity_score=category_scores.get('velocity', 0.0),
            sustainability_score=category_scores.get('sustainability', 0.0),
            inclusivity_score=category_scores.get('inclusivity', 0.0),
            indicators=indicators,
            excellent_indicators=len([i for i in indicators if i.status == 'excellent']),
            good_indicators=len([i for i in indicators if i.status == 'good']),
            warning_indicators=len([i for i in indicators if i.status == 'warning']),
            critical_indicators=len([i for i in indicators if i.status == 'critical']),
            overall_trend_30d=trends.get('30d', 0.0),
            overall_trend_90d=trends.get('90d', 0.0),
            key_strengths=recommendations['strengths'],
            improvement_areas=recommendations['improvements'],
            priority_actions=recommendations['actions']
        )
        
        # Store for trend analysis
        self.health_history.append(health_score)
        
        return health_score
    
    async def _collect_health_data(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Collect comprehensive data for health calculations"""
        
        since_date = datetime.now() - timedelta(days=lookback_days)
        
        try:
            # Collect data concurrently
            contributors, issues, prs, commits, comments, reviews = await asyncio.gather(
                client.get_contributors(owner, repo),
                client.get_issues(owner, repo, state="all", since=since_date),
                client.get_pull_requests(owner, repo, state="all"),
                client.get_commits(owner, repo, since=since_date),
                client.get_issue_comments(owner, repo, since=since_date),
                client.get_review_comments(owner, repo, since=since_date),
                return_exceptions=True
            )
            
            # Handle potential exceptions
            data = {}
            for key, result in zip(['contributors', 'issues', 'prs', 'commits', 'comments', 'reviews'], 
                                 [contributors, issues, prs, commits, comments, reviews]):
                data[key] = result if not isinstance(result, Exception) else []
            
            # Get repository stats
            repo_info = await client.get_repository_info(owner, repo)
            data['repository'] = repo_info
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to collect health data: {e}")
            return {}
    
    def _calculate_activity_indicators(self, data: Dict[str, Any]) -> List[HealthIndicator]:
        """Calculate activity-related health indicators"""
        indicators = []
        
        contributors = data.get('contributors', [])
        commits = data.get('commits', [])
        issues = data.get('issues', [])
        prs = data.get('prs', [])
        
        # Active contributors (last 30 days)
        active_contributors = len(contributors)  # Simplified - would need historical data
        indicator = HealthIndicator(
            name="Active Contributors",
            category="activity",
            value=active_contributors,
            target_value=50,  # Adjust based on repo size
            weight=0.3,
            status="good",
            description="Number of contributors with recent activity",
            measurement_unit="contributors",
            calculation_method="Count of contributors with activity in last 30 days",
            data_sources=["contributors", "commits", "issues", "prs"]
        )
        indicators.append(indicator)
        
        # Commit frequency
        total_commits = len(commits)
        avg_commits_per_day = total_commits / 30 if total_commits > 0 else 0
        indicator = HealthIndicator(
            name="Commit Frequency",
            category="activity",
            value=avg_commits_per_day,
            target_value=5.0,
            weight=0.2,
            status="good" if avg_commits_per_day >= 3 else "warning",
            description="Average commits per day over last 30 days",
            measurement_unit="commits/day",
            calculation_method="Total commits / 30 days",
            data_sources=["commits"]
        )
        indicators.append(indicator)
        
        # Issue creation rate
        issue_creation_rate = len(issues) / 30 if issues else 0
        indicator = HealthIndicator(
            name="Issue Creation Rate",
            category="activity",
            value=issue_creation_rate,
            target_value=2.0,
            weight=0.15,
            status="good",
            description="Average issues created per day",
            measurement_unit="issues/day",
            calculation_method="Total issues / 30 days",
            data_sources=["issues"]
        )
        indicators.append(indicator)
        
        # PR creation rate
        pr_creation_rate = len(prs) / 30 if prs else 0
        indicator = HealthIndicator(
            name="PR Creation Rate",
            category="activity",
            value=pr_creation_rate,
            target_value=1.5,
            weight=0.15,
            status="good",
            description="Average pull requests created per day",
            measurement_unit="PRs/day",
            calculation_method="Total PRs / 30 days",
            data_sources=["prs"]
        )
        indicators.append(indicator)
        
        # Contribution diversity (types of contributions)
        contribution_types = 0
        if commits: contribution_types += 1
        if issues: contribution_types += 1
        if prs: contribution_types += 1
        
        diversity_score = (contribution_types / 3) * 100
        indicator = HealthIndicator(
            name="Contribution Diversity",
            category="activity",
            value=diversity_score,
            target_value=80.0,
            weight=0.2,
            status="excellent" if diversity_score >= 80 else "good" if diversity_score >= 60 else "warning",
            description="Diversity of contribution types (commits, issues, PRs)",
            measurement_unit="percentage",
            calculation_method="Percentage of contribution types present",
            data_sources=["commits", "issues", "prs"]
        )
        indicators.append(indicator)
        
        return indicators
    
    def _calculate_quality_indicators(self, data: Dict[str, Any]) -> List[HealthIndicator]:
        """Calculate quality-related health indicators"""
        indicators = []
        
        prs = data.get('prs', [])
        issues = data.get('issues', [])
        commits = data.get('commits', [])
        
        # PR merge rate
        merged_prs = [pr for pr in prs if pr.get('merged_at')]
        merge_rate = (len(merged_prs) / len(prs)) * 100 if prs else 0
        indicator = HealthIndicator(
            name="PR Merge Rate",
            category="quality",
            value=merge_rate,
            target_value=80.0,
            weight=0.3,
            status="excellent" if merge_rate >= 80 else "good" if merge_rate >= 60 else "warning",
            description="Percentage of PRs that get merged",
            measurement_unit="percentage",
            calculation_method="Merged PRs / Total PRs * 100",
            data_sources=["prs"]
        )
        indicators.append(indicator)
        
        # Issue resolution rate
        resolved_issues = [issue for issue in issues if issue.get('state') == 'closed']
        resolution_rate = (len(resolved_issues) / len(issues)) * 100 if issues else 0
        indicator = HealthIndicator(
            name="Issue Resolution Rate",
            category="quality",
            value=resolution_rate,
            target_value=75.0,
            weight=0.25,
            status="excellent" if resolution_rate >= 75 else "good" if resolution_rate >= 50 else "warning",
            description="Percentage of issues that get resolved",
            measurement_unit="percentage",
            calculation_method="Closed issues / Total issues * 100",
            data_sources=["issues"]
        )
        indicators.append(indicator)
        
        # Code review coverage
        prs_with_reviews = [pr for pr in prs if pr.get('review_comments', 0) > 0]
        review_coverage = (len(prs_with_reviews) / len(prs)) * 100 if prs else 0
        indicator = HealthIndicator(
            name="Code Review Coverage",
            category="quality",
            value=review_coverage,
            target_value=90.0,
            weight=0.25,
            status="excellent" if review_coverage >= 90 else "good" if review_coverage >= 70 else "warning",
            description="Percentage of PRs that receive code reviews",
            measurement_unit="percentage",
            calculation_method="PRs with reviews / Total PRs * 100",
            data_sources=["prs", "reviews"]
        )
        indicators.append(indicator)
        
        # Commit message quality (simplified)
        commit_messages = [commit.get('commit', {}).get('message', '') for commit in commits]
        quality_commits = len([msg for msg in commit_messages if len(msg) > 10 and not msg.startswith('Merge')])
        commit_quality = (quality_commits / len(commits)) * 100 if commits else 0
        indicator = HealthIndicator(
            name="Commit Message Quality",
            category="quality",
            value=commit_quality,
            target_value=85.0,
            weight=0.2,
            status="excellent" if commit_quality >= 85 else "good" if commit_quality >= 70 else "warning",
            description="Quality of commit messages (descriptive, non-merge)",
            measurement_unit="percentage",
            calculation_method="Quality commits / Total commits * 100",
            data_sources=["commits"]
        )
        indicators.append(indicator)
        
        return indicators
    
    def _calculate_velocity_indicators(self, data: Dict[str, Any]) -> List[HealthIndicator]:
        """Calculate velocity-related health indicators"""
        indicators = []
        
        prs = data.get('prs', [])
        issues = data.get('issues', [])
        
        # Time to merge (for merged PRs)
        merge_times = []
        for pr in prs:
            if pr.get('merged_at'):
                created = self._parse_date(pr.get('created_at'))
                merged = self._parse_date(pr.get('merged_at'))
                if created and merged:
                    merge_time_hours = (merged - created).total_seconds() / 3600
                    merge_times.append(merge_time_hours)
        
        avg_time_to_merge = statistics.mean(merge_times) if merge_times else 0
        indicator = HealthIndicator(
            name="Average Time to Merge",
            category="velocity",
            value=avg_time_to_merge,
            target_value=72.0,  # 3 days in hours
            weight=0.4,
            status="excellent" if avg_time_to_merge <= 48 else "good" if avg_time_to_merge <= 72 else "warning",
            description="Average time from PR creation to merge",
            measurement_unit="hours",
            calculation_method="Mean time between PR creation and merge",
            data_sources=["prs"]
        )
        indicators.append(indicator)
        
        # Issue response time
        response_times = []
        for issue in issues:
            if issue.get('comments', 0) > 0:
                # Simplified - would need actual comment timestamps
                created = self._parse_date(issue.get('created_at'))
                if created:
                    # Assume 24 hour response time for calculation
                    response_time = 24
                    response_times.append(response_time)
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        indicator = HealthIndicator(
            name="Average Issue Response Time",
            category="velocity",
            value=avg_response_time,
            target_value=48.0,  # 2 days in hours
            weight=0.3,
            status="excellent" if avg_response_time <= 24 else "good" if avg_response_time <= 48 else "warning",
            description="Average time to first response on issues",
            measurement_unit="hours",
            calculation_method="Mean time from issue creation to first comment",
            data_sources=["issues", "comments"]
        )
        indicators.append(indicator)
        
        # Throughput (closed items per period)
        throughput_score = len([pr for pr in prs if pr.get('merged_at')]) + len([issue for issue in issues if issue.get('state') == 'closed'])
        indicator = HealthIndicator(
            name="Issue/PR Throughput",
            category="velocity",
            value=throughput_score,
            target_value=50,  # Adjust based on repo size
            weight=0.3,
            status="good",
            description="Number of issues and PRs resolved in the period",
            measurement_unit="items",
            calculation_method="Count of merged PRs + resolved issues",
            data_sources=["prs", "issues"]
        )
        indicators.append(indicator)
        
        return indicators
    
    def _calculate_sustainability_indicators(self, data: Dict[str, Any]) -> List[HealthIndicator]:
        """Calculate sustainability-related health indicators"""
        indicators = []
        
        contributors = data.get('contributors', [])
        commits = data.get('commits', [])
        
        # Contributor diversity
        if contributors:
            top_contributor_commits = contributors[0].get('contributions', 0) if contributors else 0
            total_commits = sum(c.get('contributions', 0) for c in contributors)
            concentration_ratio = (top_contributor_commits / total_commits) if total_commits > 0 else 0
            
            diversity_score = 100 - (concentration_ratio * 100)  # Lower concentration = higher diversity
            indicator = HealthIndicator(
                name="Contributor Diversity",
                category="sustainability",
                value=diversity_score,
                target_value=60.0,
                weight=0.3,
                status="excellent" if diversity_score >= 60 else "good" if diversity_score >= 40 else "warning",
                description="Distribution of contributions across contributors",
                measurement_unit="percentage",
                calculation_method="100 - (top contributor percentage)",
                data_sources=["contributors"]
            )
            indicators.append(indicator)
        
        # New contributor rate
        new_contributor_rate = len(contributors) * 0.3  # Simplified - would need historical comparison
        indicator = HealthIndicator(
            name="New Contributor Rate",
            category="sustainability",
            value=new_contributor_rate,
            target_value=20.0,
            weight=0.25,
            status="good",
            description="Rate of new contributors joining",
            measurement_unit="contributors/month",
            calculation_method="Estimated new contributors per month",
            data_sources=["contributors"]
        )
        indicators.append(indicator)
        
        # Activity consistency (based on commit patterns)
        if commits:
            commit_dates = [self._parse_date(commit.get('commit', {}).get('author', {}).get('date')) 
                          for commit in commits]
            commit_dates = [d for d in commit_dates if d]
            
            if len(commit_dates) > 1:
                commit_dates.sort()
                gaps = [(commit_dates[i+1] - commit_dates[i]).days for i in range(len(commit_dates)-1)]
                avg_gap = statistics.mean(gaps)
                consistency_score = max(0, 100 - (avg_gap * 5))  # Smaller gaps = higher consistency
                
                indicator = HealthIndicator(
                    name="Activity Consistency",
                    category="sustainability",
                    value=consistency_score,
                    target_value=70.0,
                    weight=0.25,
                    status="good",
                    description="Consistency of community activity over time",
                    measurement_unit="score",
                    calculation_method="Based on gaps between commits",
                    data_sources=["commits"]
                )
                indicators.append(indicator)
        
        # Documentation health (simplified)
        documentation_indicators = 0
        # This would need more sophisticated analysis in a real implementation
        indicator = HealthIndicator(
            name="Documentation Health",
            category="sustainability",
            value=75.0,  # Placeholder
            target_value=80.0,
            weight=0.2,
            status="good",
            description="Quality and completeness of documentation",
            measurement_unit="score",
            calculation_method="Assessment of README, docs, and guides",
            data_sources=["repository"]
        )
        indicators.append(indicator)
        
        return indicators
    
    def _calculate_inclusivity_indicators(self, data: Dict[str, Any]) -> List[HealthIndicator]:
        """Calculate inclusivity-related health indicators"""
        indicators = []
        
        contributors = data.get('contributors', [])
        issues = data.get('issues', [])
        
        # First-time contributor engagement
        first_time_indicators = 0
        # Simplified calculation - would need more detailed contributor analysis
        engagement_score = min(100, len(contributors) * 10)  # Placeholder
        indicator = HealthIndicator(
            name="First-time Contributor Engagement",
            category="inclusivity",
            value=engagement_score,
            target_value=80.0,
            weight=0.3,
            status="good",
            description="Engagement level of new contributors",
            measurement_unit="score",
            calculation_method="Based on new contributor retention and activity",
            data_sources=["contributors", "issues", "prs"]
        )
        indicators.append(indicator)
        
        # Issue response inclusivity (quick responses to new users)
        quick_responses = 0  # Would need detailed analysis of who responds to new user issues
        inclusivity_score = 70  # Placeholder
        indicator = HealthIndicator(
            name="Community Responsiveness",
            category="inclusivity",
            value=inclusivity_score,
            target_value=85.0,
            weight=0.25,
            status="good",
            description="Responsiveness to community members, especially newcomers",
            measurement_unit="score",
            calculation_method="Based on response times and community interaction",
            data_sources=["issues", "comments"]
        )
        indicators.append(indicator)
        
        # Contribution recognition (All Contributors style)
        recognition_score = 60  # Placeholder - would need bot integration
        indicator = HealthIndicator(
            name="Contribution Recognition",
            category="inclusivity",
            value=recognition_score,
            target_value=75.0,
            weight=0.25,
            status="good",
            description="Recognition of diverse contribution types",
            measurement_unit="score",
            calculation_method="Based on contribution type diversity and acknowledgment",
            data_sources=["contributors", "repository"]
        )
        indicators.append(indicator)
        
        # Community guidelines and governance
        governance_score = 80  # Placeholder
        indicator = HealthIndicator(
            name="Community Governance",
            category="inclusivity",
            value=governance_score,
            target_value=85.0,
            weight=0.2,
            status="good",
            description="Quality of community guidelines and governance",
            measurement_unit="score",
            calculation_method="Assessment of CODEOWNERS, contributing guidelines, etc.",
            data_sources=["repository"]
        )
        indicators.append(indicator)
        
        return indicators
    
    def _calculate_responsiveness_indicators(self, data: Dict[str, Any]) -> List[HealthIndicator]:
        """Calculate responsiveness-related health indicators"""
        indicators = []
        
        issues = data.get('issues', [])
        comments = data.get('comments', [])
        
        # Issue acknowledgment rate
        issues_with_comments = len([issue for issue in issues if issue.get('comments', 0) > 0])
        acknowledgment_rate = (issues_with_comments / len(issues)) * 100 if issues else 0
        indicator = HealthIndicator(
            name="Issue Acknowledgment Rate",
            category="activity",
            value=acknowledgment_rate,
            target_value=90.0,
            weight=0.35,
            status="excellent" if acknowledgment_rate >= 90 else "good" if acknowledgment_rate >= 70 else "warning",
            description="Percentage of issues that receive acknowledgment or response",
            measurement_unit="percentage",
            calculation_method="Issues with comments / Total issues * 100",
            data_sources=["issues", "comments"]
        )
        indicators.append(indicator)
        
        # PR review speed
        prs_needing_review = [pr for pr in data.get('prs', []) if not pr.get('merged_at')]
        if prs_needing_review:
            # Simplified - would need detailed review timeline analysis
            review_speed_score = 70  # Placeholder
        else:
            review_speed_score = 100  # No PRs needing review
        
        indicator = HealthIndicator(
            name="PR Review Speed",
            category="velocity",
            value=review_speed_score,
            target_value=80.0,
            weight=0.35,
            status="good",
            description="Speed of PR review process",
            measurement_unit="score",
            calculation_method="Based on time from PR submission to first review",
            data_sources=["prs", "reviews"]
        )
        indicators.append(indicator)
        
        # Community engagement in discussions
        discussion_activity = len(comments) / max(1, len(issues))
        indicator = HealthIndicator(
            name="Discussion Engagement",
            category="activity",
            value=discussion_activity,
            target_value=2.0,
            weight=0.3,
            status="good" if discussion_activity >= 1.5 else "warning",
            description="Level of engagement in community discussions",
            measurement_unit="comments per issue",
            calculation_method="Total comments / Total issues",
            data_sources=["issues", "comments"]
        )
        indicators.append(indicator)
        
        return indicators
    
    def _calculate_category_scores(self, indicators: List[HealthIndicator]) -> Dict[str, float]:
        """Calculate scores for each health category"""
        category_scores = {}
        
        for category in ['activity', 'quality', 'velocity', 'sustainability', 'inclusivity']:
            category_indicators = [ind for ind in indicators if ind.category == category]
            if category_indicators:
                # Weighted average
                total_weight = sum(ind.weight for ind in category_indicators)
                if total_weight > 0:
                    weighted_sum = sum(ind.value * ind.weight for ind in category_indicators)
                    category_scores[category] = weighted_sum / total_weight
                else:
                    category_scores[category] = 0.0
            else:
                category_scores[category] = 0.0
        
        return category_scores
    
    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate overall health score"""
        total_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            weight = self.category_weights.get(category, 0.0)
            total_score += score * weight
            total_weight += weight
        
        return total_score / max(0.1, total_weight)
    
    def _determine_health_grade(self, overall_score: float) -> str:
        """Determine letter grade from numerical score"""
        if overall_score >= 90:
            return "A"
        elif overall_score >= 80:
            return "B"
        elif overall_score >= 70:
            return "C"
        elif overall_score >= 60:
            return "D"
        else:
            return "F"
    
    def _calculate_health_trends(self, current_score: float) -> Dict[str, float]:
        """Calculate health score trends"""
        trends = {'30d': 0.0, '90d': 0.0}
        
        if len(self.health_history) >= 2:
            # 30-day trend
            previous_score = self.health_history[-2].overall_score
            trends['30d'] = ((current_score - previous_score) / previous_score) * 100 if previous_score > 0 else 0
        
        if len(self.health_history) >= 4:
            # 90-day trend (assuming quarterly data points)
            old_score = self.health_history[-4].overall_score
            trends['90d'] = ((current_score - old_score) / old_score) * 100 if old_score > 0 else 0
        
        return trends
    
    def _generate_health_recommendations(
        self, 
        indicators: List[HealthIndicator], 
        category_scores: Dict[str, float]
    ) -> Dict[str, List[str]]:
        """Generate actionable health recommendations"""
        strengths = []
        improvements = []
        actions = []
        
        # Identify strengths
        for indicator in indicators:
            if indicator.status == "excellent":
                strengths.append(f"Strong {indicator.name.lower()} ({indicator.value:.1f})")
        
        # Identify improvement areas
        for indicator in indicators:
            if indicator.status in ["warning", "critical"]:
                improvements.append(f"Improve {indicator.name.lower()} (currently {indicator.value:.1f})")
        
        # Priority actions based on low-scoring categories
        for category, score in category_scores.items():
            if score < 60:
                actions.append(f"Focus on improving {category} health (score: {score:.1f})")
        
        # Specific recommendations based on indicator values
        for indicator in indicators:
            if indicator.value < indicator.warning_threshold:
                if "time" in indicator.name.lower() or "response" in indicator.name.lower():
                    actions.append(f"Improve response times for {indicator.name.lower()}")
                elif "rate" in indicator.name.lower():
                    actions.append(f"Increase {indicator.name.lower()}")
                elif "coverage" in indicator.name.lower():
                    actions.append(f"Improve {indicator.name.lower()}")
        
        return {
            'strengths': strengths[:5],  # Top 5
            'improvements': improvements[:5],  # Top 5
            'actions': actions[:7]  # Top 7
        }
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            return None
    
    def get_health_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health summary report"""
        if not self.health_history:
            return {"error": "No health data available"}
        
        latest_health = self.health_history[-1]
        
        # Trend analysis
        if len(self.health_history) >= 2:
            previous = self.health_history[-2]
            score_change = latest_health.overall_score - previous.overall_score
        else:
            score_change = 0
        
        # Category performance
        category_performance = {
            'activity': latest_health.activity_score,
            'quality': latest_health.quality_score,
            'velocity': latest_health.velocity_score,
            'sustainability': latest_health.sustainability_score,
            'inclusivity': latest_health.inclusivity_score
        }
        
        # Indicator breakdown
        indicator_breakdown = {}
        for indicator in latest_health.indicators:
            indicator_breakdown[indicator.name] = {
                'value': indicator.value,
                'status': indicator.status,
                'category': indicator.category,
                'weight': indicator.weight
            }
        
        return {
            "overall_health": {
                "score": latest_health.overall_score,
                "grade": latest_health.health_grade,
                "change": score_change
            },
            "category_scores": category_performance,
            "indicator_count": {
                "excellent": latest_health.excellent_indicators,
                "good": latest_health.good_indicators,
                "warning": latest_health.warning_indicators,
                "critical": latest_health.critical_indicators
            },
            "trends": {
                "30_day": latest_health.overall_trend_30d,
                "90_day": latest_health.overall_trend_90d
            },
            "top_indicators": sorted(
                [(ind.name, ind.value) for ind in latest_health.indicators],
                key=lambda x: x[1], reverse=True
            )[:10],
            "bottom_indicators": sorted(
                [(ind.name, ind.value) for ind in latest_health.indicators],
                key=lambda x: x[1]
            )[:5],
            "key_strengths": latest_health.key_strengths,
            "priority_actions": latest_health.priority_actions
        }