"""
Community Engagement Tracking System

This module tracks and analyzes community engagement patterns including
contributor behavior, issue discussions, PR interactions, and community growth.
"""

import asyncio
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
import statistics
import re

import aiohttp
from github_api_client import RepositoryMetrics, GitHubAPIClient


@dataclass
class ContributorProfile:
    """Individual contributor profile and behavior"""
    login: str
    first_contribution_date: datetime
    total_contributions: int
    contribution_types: Dict[str, int]  # code, docs, issues, etc.
    contribution_frequency: float  # contributions per month
    retention_months: int
    last_contribution_date: Optional[datetime] = None
    preferred_languages: List[str] = field(default_factory=list)
    issue_responses: int = 0
    pr_reviews: int = 0
    community_score: float = 0.0


@dataclass
class EngagementMetrics:
    """Community engagement metrics and analysis"""
    repo_owner: str
    repo_name: str
    timestamp: datetime
    
    # Contributor analysis
    total_contributors: int
    active_contributors: int  # contributed in last 30 days
    new_contributors_month: int
    returning_contributors: int
    contributor_retention_rate: float
    
    # Contribution diversity
    code_contributions: int
    documentation_contributions: int
    issue_contributions: int
    discussion_contributions: int
    
    # Response and review metrics
    avg_response_time_hours: float
    avg_review_time_hours: float
    response_rate_percentage: float
    
    # Community health indicators
    contributor_growth_rate: float
    engagement_consistency_score: float
    community_satisfaction_score: float
    
    # Detailed contributor profiles
    contributor_profiles: List[ContributorProfile] = field(default_factory=list)
    top_contributors: List[ContributorProfile] = field(default_factory=list)
    at_risk_contributors: List[ContributorProfile] = field(default_factory=list)


class CommunityEngagementTracker:
    """
    Track and analyze community engagement patterns.
    
    This class provides comprehensive tracking of community interactions,
    contributor behavior, and engagement trends.
    """
    
    def __init__(self, engagement_window_days: int = 90):
        """
        Initialize community engagement tracker.
        
        Args:
            engagement_window_days: Window for engagement analysis
        """
        self.engagement_window_days = engagement_window_days
        self.logger = logging.getLogger(__name__)
        
        # Engagement patterns
        self.contribution_patterns = defaultdict(list)
        self.response_time_patterns = defaultdict(list)
        self.contributor_lifecycle = {}
        
    async def analyze_community_engagement(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> EngagementMetrics:
        """
        Perform comprehensive community engagement analysis.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            historical_metrics: Historical data for trend analysis
            
        Returns:
            EngagementMetrics with comprehensive analysis
        """
        self.logger.info(f"Analyzing community engagement for {owner}/{repo}")
        
        # Collect engagement data
        contributors_data, issues_data, prs_data, discussions_data = await asyncio.gather(
            self._collect_contributor_data(client, owner, repo),
            self._collect_issues_data(client, owner, repo),
            self._collect_prs_data(client, owner, repo),
            self._collect_discussions_data(client, owner, repo),
            return_exceptions=True
        )
        
        # Handle potential exceptions
        contributors_data = contributors_data if not isinstance(contributors_data, Exception) else []
        issues_data = issues_data if not isinstance(issues_data, Exception) else []
        prs_data = prs_data if not isinstance(prs_data, Exception) else []
        discussions_data = discussions_data if not isinstance(discussions_data, Exception) else []
        
        # Analyze contributor behavior
        contributor_profiles = await self._analyze_contributor_profiles(
            contributors_data, issues_data, prs_data
        )
        
        # Calculate engagement metrics
        engagement_metrics = await self._calculate_engagement_metrics(
            contributor_profiles, issues_data, prs_data, discussions_data
        )
        
        # Identify at-risk contributors
        at_risk_contributors = self._identify_at_risk_contributors(contributor_profiles)
        
        # Generate community insights
        top_contributors = self._identify_top_contributors(contributor_profiles)
        
        return EngagementMetrics(
            repo_owner=owner,
            repo_name=repo,
            timestamp=datetime.now(),
            total_contributors=len(contributor_profiles),
            active_contributors=len([c for c in contributor_profiles if self._is_recently_active(c)]),
            new_contributors_month=self._count_new_contributors(contributor_profiles),
            returning_contributors=self._count_returning_contributors(contributor_profiles),
            contributor_retention_rate=self._calculate_retention_rate(contributor_profiles),
            code_contributions=sum(c.total_contributions for c in contributor_profiles),
            documentation_contributions=sum(c.contribution_types.get("docs", 0) for c in contributor_profiles),
            issue_contributions=sum(c.contribution_types.get("issues", 0) for c in contributor_profiles),
            discussion_contributions=sum(c.contribution_types.get("discussions", 0) for c in contributor_profiles),
            avg_response_time_hours=self._calculate_avg_response_time(issues_data),
            avg_review_time_hours=self._calculate_avg_review_time(prs_data),
            response_rate_percentage=self._calculate_response_rate(issues_data),
            contributor_growth_rate=self._calculate_growth_rate(contributor_profiles, historical_metrics),
            engagement_consistency_score=self._calculate_engagement_consistency(contributor_profiles),
            community_satisfaction_score=self._calculate_satisfaction_score(contributor_profiles),
            contributor_profiles=contributor_profiles,
            top_contributors=top_contributors,
            at_risk_contributors=at_risk_contributors
        )
    
    async def _collect_contributor_data(self, client: GitHubAPIClient, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Collect contributor data from GitHub API"""
        try:
            contributors = await client.get_contributors(owner, repo)
            return contributors
        except Exception as e:
            self.logger.error(f"Failed to collect contributor data: {e}")
            return []
    
    async def _collect_issues_data(self, client: GitHubAPIClient, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Collect issues data for engagement analysis"""
        try:
            issues = await client.get_issues(owner, repo, state="all", since=datetime.now() - timedelta(days=self.engagement_window_days))
            return issues
        except Exception as e:
            self.logger.error(f"Failed to collect issues data: {e}")
            return []
    
    async def _collect_prs_data(self, client: GitHubAPIClient, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Collect PR data for engagement analysis"""
        try:
            prs = await client.get_pull_requests(owner, repo, state="all")
            return prs
        except Exception as e:
            self.logger.error(f"Failed to collect PRs data: {e}")
            return []
    
    async def _collect_discussions_data(self, client: GitHubAPIClient, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Collect discussions data (placeholder - would need separate API call)"""
        # Placeholder for discussions API - return empty for now
        return []
    
    async def _analyze_contributor_profiles(
        self,
        contributors: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        prs: List[Dict[str, Any]]
    ) -> List[ContributorProfile]:
        """Analyze individual contributor profiles and behavior"""
        profiles = []
        
        # Group contributions by user
        user_contributions = defaultdict(lambda: {
            "commits": 0,
            "issues": 0,
            "prs": 0,
            "first_contribution": None,
            "last_contribution": None,
            "languages": set()
        })
        
        # Process commits
        for contributor in contributors:
            login = contributor.get("login")
            if login:
                user_contributions[login]["commits"] = contributor.get("contributions", 0)
        
        # Process issues (would need issue comments data for full analysis)
        for issue in issues:
            author = issue.get("user", {}).get("login")
            if author:
                user_contributions[author]["issues"] += 1
                if user_contributions[author]["first_contribution"] is None:
                    user_contributions[author]["first_contribution"] = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
                user_contributions[author]["last_contribution"] = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
        
        # Process PRs
        for pr in prs:
            author = pr.get("user", {}).get("login")
            if author:
                user_contributions[author]["prs"] += 1
                if user_contributions[author]["first_contribution"] is None:
                    user_contributions[author]["first_contribution"] = datetime.fromisoformat(pr["created_at"].replace('Z', '+00:00'))
                user_contributions[author]["last_contribution"] = datetime.fromisoformat(pr["created_at"].replace('Z', '+00:00'))
        
        # Build contributor profiles
        for login, contributions in user_contributions.items():
            profile = self._build_contributor_profile(login, contributions)
            profiles.append(profile)
        
        return profiles
    
    def _build_contributor_profile(self, login: str, contributions: Dict[str, Any]) -> ContributorProfile:
        """Build individual contributor profile"""
        first_contribution = contributions["first_contribution"] or datetime.now() - timedelta(days=30)
        last_contribution = contributions["last_contribution"] or datetime.now()
        
        # Calculate contribution frequency
        months_active = max(1, (last_contribution - first_contribution).days / 30)
        total_contributions = contributions["commits"] + contributions["issues"] + contributions["prs"]
        contribution_frequency = total_contributions / months_active
        
        # Calculate retention
        now = datetime.now()
        months_since_last = (now - last_contribution).days / 30
        retention_months = max(0, 12 - months_since_last)  # Assume 12 month max retention window
        
        # Contribution types
        contribution_types = {
            "code": contributions["commits"],
            "issues": contributions["issues"],
            "prs": contributions["prs"]
        }
        
        # Community score (weighted combination of factors)
        community_score = self._calculate_community_score(contributions)
        
        return ContributorProfile(
            login=login,
            first_contribution_date=first_contribution,
            total_contributions=total_contributions,
            contribution_types=contribution_types,
            contribution_frequency=contribution_frequency,
            retention_months=retention_months,
            last_contribution_date=last_contribution,
            community_score=community_score
        )
    
    def _calculate_community_score(self, contributions: Dict[str, Any]) -> float:
        """Calculate community engagement score for a contributor"""
        # Factors: diversity of contributions, consistency, recency
        diversity_score = min(100, len([k for k, v in contributions.items() if k != "languages" and v > 0]) * 25)
        volume_score = min(100, (contributions["commits"] + contributions["issues"] + contributions["prs"]) * 2)
        recency_score = 100 if contributions["last_contribution"] and (datetime.now() - contributions["last_contribution"]).days < 30 else 50
        
        return (diversity_score + volume_score + recency_score) / 3
    
    async def _calculate_engagement_metrics(
        self,
        profiles: List[ContributorProfile],
        issues: List[Dict[str, Any]],
        prs: List[Dict[str, Any]],
        discussions: List[Dict[str, Any]]
    ) -> EngagementMetrics:
        """Calculate comprehensive engagement metrics"""
        # This method would be called by the main analyze_community_engagement method
        # Return placeholder for now - actual calculation happens in the main method
        return EngagementMetrics(
            repo_owner="",
            repo_name="",
            timestamp=datetime.now(),
            total_contributors=0,
            active_contributors=0,
            new_contributors_month=0,
            returning_contributors=0,
            contributor_retention_rate=0.0,
            code_contributions=0,
            documentation_contributions=0,
            issue_contributions=0,
            discussion_contributions=0,
            avg_response_time_hours=0.0,
            avg_review_time_hours=0.0,
            response_rate_percentage=0.0,
            contributor_growth_rate=0.0,
            engagement_consistency_score=0.0,
            community_satisfaction_score=0.0
        )
    
    def _is_recently_active(self, profile: ContributorProfile) -> bool:
        """Check if contributor is recently active"""
        if not profile.last_contribution_date:
            return False
        return (datetime.now() - profile.last_contribution_date).days < 30
    
    def _count_new_contributors(self, profiles: List[ContributorProfile]) -> int:
        """Count contributors who started in the last month"""
        one_month_ago = datetime.now() - timedelta(days=30)
        return len([p for p in profiles if p.first_contribution_date >= one_month_ago])
    
    def _count_returning_contributors(self, profiles: List[ContributorProfile]) -> int:
        """Count returning contributors (not new, but active)"""
        one_month_ago = datetime.now() - timedelta(days=30)
        return len([
            p for p in profiles 
            if p.first_contribution_date < one_month_ago and self._is_recently_active(p)
        ])
    
    def _calculate_retention_rate(self, profiles: List[ContributorProfile]) -> float:
        """Calculate contributor retention rate"""
        if not profiles:
            return 0.0
        
        # Retention rate = contributors active in last 30 days / total contributors
        active_count = len([p for p in profiles if self._is_recently_active(p)])
        return (active_count / len(profiles)) * 100
    
    def _calculate_avg_response_time(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate average response time to issues"""
        response_times = []
        for issue in issues:
            if issue.get("comments", 0) > 0:
                # Placeholder calculation - would need actual comment timestamps
                created = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
                # Assume 24 hour average response time for now
                response_times.append(24.0)
        
        return statistics.mean(response_times) if response_times else 0.0
    
    def _calculate_avg_review_time(self, prs: List[Dict[str, Any]]) -> float:
        """Calculate average PR review time"""
        review_times = []
        for pr in prs:
            if pr.get("merged_at"):
                created = datetime.fromisoformat(pr["created_at"].replace('Z', '+00:00'))
                merged = datetime.fromisoformat(pr["merged_at"].replace('Z', '+00:00'))
                review_time = (merged - created).total_seconds() / 3600  # hours
                review_times.append(review_time)
        
        return statistics.mean(review_times) if review_times else 0.0
    
    def _calculate_response_rate(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate issue response rate"""
        if not issues:
            return 0.0
        
        responded_issues = len([issue for issue in issues if issue.get("comments", 0) > 0])
        return (responded_issues / len(issues)) * 100
    
    def _calculate_growth_rate(
        self,
        profiles: List[ContributorProfile],
        historical_metrics: Optional[List[RepositoryMetrics]] = None
    ) -> float:
        """Calculate contributor growth rate"""
        if not historical_metrics:
            return 0.0
        
        # Calculate monthly growth rate
        current_count = len([p for p in profiles])
        if len(historical_metrics) >= 2:
            previous_count = len([p for p in profiles if p.first_contribution_date < historical_metrics[-1].timestamp])
            growth_rate = ((current_count - previous_count) / max(1, previous_count)) * 100
            return growth_rate
        
        return 0.0
    
    def _calculate_engagement_consistency(self, profiles: List[ContributorProfile]) -> float:
        """Calculate engagement consistency score"""
        if not profiles:
            return 0.0
        
        # Consistency based on contribution frequency variance
        frequencies = [p.contribution_frequency for p in profiles if p.contribution_frequency > 0]
        if not frequencies:
            return 0.0
        
        if len(frequencies) == 1:
            return 100.0
        
        mean_freq = statistics.mean(frequencies)
        variance = statistics.variance(frequencies)
        coefficient_of_variation = (variance ** 0.5) / max(0.1, mean_freq)
        
        # Lower CV = more consistent engagement
        consistency_score = max(0, 100 - (coefficient_of_variation * 50))
        return consistency_score
    
    def _calculate_satisfaction_score(self, profiles: List[ContributorProfile]) -> float:
        """Calculate community satisfaction score based on contributor behavior"""
        if not profiles:
            return 0.0
        
        # Factors indicating satisfaction: retention, contribution diversity, frequency
        retention_scores = [min(100, (p.retention_months / 12) * 100) for p in profiles]
        diversity_scores = [min(100, len([k for k, v in p.contribution_types.items() if v > 0]) * 33) for p in profiles]
        frequency_scores = [min(100, p.contribution_frequency * 10) for p in profiles]
        
        # Calculate weighted average
        all_scores = [r * 0.4 + d * 0.3 + f * 0.3 for r, d, f in zip(retention_scores, diversity_scores, frequency_scores)]
        return statistics.mean(all_scores)
    
    def _identify_top_contributors(self, profiles: List[ContributorProfile]) -> List[ContributorProfile]:
        """Identify top contributors based on community score and contribution quality"""
        # Sort by community score and recency
        scored_profiles = []
        for profile in profiles:
            # Boost score for recent activity
            recency_boost = 0
            if profile.last_contribution_date:
                days_since = (datetime.now() - profile.last_contribution_date).days
                if days_since < 7:
                    recency_boost = 20
                elif days_since < 30:
                    recency_boost = 10
            
            final_score = profile.community_score + recency_boost
            scored_profiles.append((profile, final_score))
        
        # Sort by final score and return top 10
        scored_profiles.sort(key=lambda x: x[1], reverse=True)
        return [profile for profile, _ in scored_profiles[:10]]
    
    def _identify_at_risk_contributors(self, profiles: List[ContributorProfile]) -> List[ContributorProfile]:
        """Identify contributors who might be at risk of leaving"""
        at_risk = []
        
        for profile in profiles:
            risk_factors = 0
            
            # No recent activity
            if profile.last_contribution_date:
                days_since = (datetime.now() - profile.last_contribution_date).days
                if days_since > 60:
                    risk_factors += 2
                elif days_since > 30:
                    risk_factors += 1
            
            # Low contribution diversity
            diversity = len([k for k, v in profile.contribution_types.items() if v > 0])
            if diversity == 1:
                risk_factors += 1
            
            # Declining contribution frequency
            if profile.contribution_frequency < 1:
                risk_factors += 1
            
            # Low retention
            if profile.retention_months < 3:
                risk_factors += 1
            
            # Flag as at-risk if 2+ risk factors
            if risk_factors >= 2:
                at_risk.append(profile)
        
        return at_risk
    
    def generate_engagement_report(self, metrics: EngagementMetrics) -> Dict[str, Any]:
        """Generate comprehensive engagement report"""
        report = {
            "summary": {
                "total_contributors": metrics.total_contributors,
                "active_contributors": metrics.active_contributors,
                "retention_rate": f"{metrics.contributor_retention_rate:.1f}%",
                "growth_rate": f"{metrics.contributor_growth_rate:.1f}%"
            },
            "top_contributors": [
                {
                    "login": c.login,
                    "contributions": c.total_contributions,
                    "community_score": f"{c.community_score:.1f}",
                    "last_active": c.last_contribution_date.strftime("%Y-%m-%d") if c.last_contribution_date else "Never"
                }
                for c in metrics.top_contributors[:5]
            ],
            "at_risk_contributors": [
                {
                    "login": c.login,
                    "risk_factors": [
                        "No recent activity" if (datetime.now() - c.last_contribution_date).days > 30 else "",
                        "Limited diversity" if len([k for k, v in c.contribution_types.items() if v > 0]) == 1 else "",
                        "Low frequency" if c.contribution_frequency < 1 else ""
                    ],
                    "last_contribution": c.last_contribution_date.strftime("%Y-%m-%d") if c.last_contribution_date else "Never"
                }
                for c in metrics.at_risk_contributors[:5]
            ],
            "recommendations": self._generate_engagement_recommendations(metrics)
        }
        
        return report
    
    def _generate_engagement_recommendations(self, metrics: EngagementMetrics) -> List[str]:
        """Generate actionable recommendations for improving engagement"""
        recommendations = []
        
        if metrics.contributor_retention_rate < 50:
            recommendations.append("Implement contributor retention program with regular check-ins")
        
        if metrics.new_contributors_month < metrics.total_contributors * 0.1:
            recommendations.append("Increase new contributor onboarding efforts")
        
        if metrics.avg_response_time_hours > 48:
            recommendations.append("Establish faster issue response protocols")
        
        if len(metrics.at_risk_contributors) > metrics.total_contributors * 0.2:
            recommendations.append("Reach out to at-risk contributors with personalized engagement")
        
        if metrics.engagement_consistency_score < 60:
            recommendations.append("Encourage more consistent contribution patterns")
        
        if len(metrics.top_contributors) < 5:
            recommendations.append("Recognize and retain top contributors")
        
        return recommendations