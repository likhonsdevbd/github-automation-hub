"""
Community Engagement Scoring System

Calculates comprehensive engagement scores for individual members and the community
as a whole, incorporating multiple dimensions of contribution and interaction patterns.
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
class EngagementScore:
    """Individual engagement score breakdown"""
    login: str
    total_score: float
    
    # Component scores (0-100)
    contribution_score: float = 0.0
    interaction_score: float = 0.0
    consistency_score: float = 0.0
    community_score: float = 0.0
    impact_score: float = 0.0
    growth_score: float = 0.0
    
    # Detailed metrics
    total_contributions: int = 0
    total_interactions: int = 0
    contribution_types: Dict[str, int] = field(default_factory=dict)
    interaction_types: Dict[str, int] = field(default_factory=dict)
    
    # Raw data
    first_activity_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    active_days: int = 0
    streak_days: int = 0
    contribution_frequency: float = 0.0
    
    # Impact metrics
    commits_merged: int = 0
    reviews_given: int = 0
    issues_responded: int = 0
    discussions_started: int = 0
    help_provided_count: int = 0
    
    # Peer recognition
    mentioned_by_others: int = 0
    collaborations: int = 0
    
    def __post_init__(self):
        """Ensure all scores are in valid range"""
        self.total_score = min(100.0, max(0.0, self.total_score))
        self.contribution_score = min(100.0, max(0.0, self.contribution_score))
        self.interaction_score = min(100.0, max(0.0, self.interaction_score))
        self.consistency_score = min(100.0, max(0.0, self.consistency_score))
        self.community_score = min(100.0, max(0.0, self.community_score))
        self.impact_score = min(100.0, max(0.0, self.impact_score))
        self.growth_score = min(100.0, max(0.0, self.growth_score))


@dataclass 
class CommunityEngagementScore:
    """Aggregate community engagement metrics"""
    timestamp: datetime
    total_engagement_score: float  # Community-wide engagement (0-100)
    
    # Engagement dimensions
    contribution_engagement: float = 0.0
    interaction_engagement: float = 0.0
    consistency_engagement: float = 0.0
    community_engagement: float = 0.0
    impact_engagement: float = 0.0
    growth_engagement: float = 0.0
    
    # Member distribution
    highly_engaged_count: int = 0  # Score >= 80
    moderately_engaged_count: int = 0  # Score 50-79
    low_engagement_count: int = 0  # Score < 50
    new_active_members: int = 0
    
    # Activity metrics
    avg_contribution_frequency: float = 0.0
    avg_active_days_per_month: float = 0.0
    community_health_index: float = 0.0
    
    # Engagement trends
    engagement_trend_30d: float = 0.0  # % change vs 30 days ago
    engagement_trend_90d: float = 0.0  # % change vs 90 days ago
    
    # Top contributors by dimension
    top_contributors: Dict[str, List[str]] = field(default_factory=dict)
    
    # Engagement patterns
    peak_activity_hours: List[int] = field(default_factory=list)
    peak_activity_days: List[int] = field(default_factory=list)
    contribution_distribution: Dict[str, int] = field(default_factory=dict)


class EngagementScorer:
    """
    Calculate comprehensive engagement scores for community members.
    
    This class provides multi-dimensional engagement scoring that considers
    contributions, interactions, consistency, community building, impact, and growth.
    """
    
    def __init__(self):
        """Initialize the engagement scorer"""
        self.logger = logging.getLogger(__name__)
        
        # Scoring weights (can be adjusted based on community priorities)
        self.weights = {
            'contribution': 0.30,  # Code, documentation, issues, etc.
            'interaction': 0.20,   # Reviews, comments, discussions
            'consistency': 0.15,   # Regular activity patterns
            'community': 0.15,     # Mentoring, helping others
            'impact': 0.15,        # Merged PRs, resolved issues
            'growth': 0.05         # Improvement over time
        }
        
        # Score baselines for normalization
        self.baselines = {
            'contribution': {'excellent': 100, 'good': 70, 'average': 40},
            'interaction': {'excellent': 80, 'good': 50, 'average': 25},
            'consistency': {'excellent': 90, 'good': 60, 'average': 30},
            'community': {'excellent': 75, 'good': 45, 'average': 20},
            'impact': {'excellent': 85, 'good': 55, 'average': 30},
            'growth': {'excellent': 95, 'good': 65, 'average': 35}
        }
        
        # Historical scores for trend calculation
        self.score_history: Dict[str, List[Tuple[datetime, EngagementScore]]] = defaultdict(list)
    
    async def calculate_engagement_scores(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int = 90
    ) -> CommunityEngagementScore:
        """
        Calculate engagement scores for all community members.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name  
            lookback_days: Days of historical data to analyze
            
        Returns:
            CommunityEngagementScore with aggregate metrics
        """
        self.logger.info(f"Calculating engagement scores for {owner}/{repo}")
        
        # Collect comprehensive activity data
        activity_data = await self._collect_activity_data(client, owner, repo, lookback_days)
        
        # Calculate individual engagement scores
        individual_scores = []
        for member_data in self._process_member_activity(activity_data):
            score = self._calculate_individual_score(member_data)
            individual_scores.append(score)
            self.score_history[score.login].append((datetime.now(), score))
        
        # Calculate community engagement metrics
        community_score = self._calculate_community_score(individual_scores)
        
        return community_score
    
    async def _collect_activity_data(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Collect comprehensive activity data for engagement scoring"""
        
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
            
            # Get collaborators for each member
            collaborators = await self._get_collaborator_network(client, owner, repo)
            data['collaborators'] = collaborators
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to collect activity data: {e}")
            return {}
    
    async def _get_collaborator_network(
        self, 
        client: GitHubAPIClient, 
        owner: str, 
        repo: str
    ) -> Dict[str, Set[str]]:
        """Get collaborator network to calculate collaboration scores"""
        collaborators = defaultdict(set)
        
        try:
            # Get all PRs to find co-authors
            prs = await client.get_pull_requests(owner, repo, state="all")
            
            for pr in prs:
                if pr.get('merged_at'):
                    # Get commits for this PR to find co-authors
                    pr_commits = await client.get_pr_commits(owner, repo, pr['number'])
                    
                    authors = set()
                    for commit in pr_commits:
                        author_login = commit.get('author', {}).get('login')
                        if author_login:
                            authors.add(author_login)
                    
                    # Add collaboration relationships
                    for author1 in authors:
                        for author2 in authors:
                            if author1 != author2:
                                collaborators[author1].add(author2)
                                collaborators[author2].add(author1)
        
        except Exception as e:
            self.logger.warning(f"Could not collect collaborator network: {e}")
        
        return dict(collaborators)
    
    def _process_member_activity(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw activity data into member-centric format"""
        member_activities = defaultdict(lambda: {
            'commits': [],
            'issues': [],
            'prs': [],
            'comments': [],
            'reviews': [],
            'collaborators': set()
        })
        
        # Process commits
        for commit in activity_data.get('commits', []):
            author = commit.get('author', {})
            login = author.get('login')
            if login:
                member_activities[login]['commits'].append(commit)
        
        # Process issues
        for issue in activity_data.get('issues', []):
            author = issue.get('user', {})
            login = author.get('login')
            if login:
                member_activities[login]['issues'].append(issue)
        
        # Process PRs
        for pr in activity_data.get('prs', []):
            author = pr.get('user', {})
            login = author.get('login')
            if login:
                member_activities[login]['prs'].append(pr)
        
        # Process comments
        for comment in activity_data.get('comments', []):
            author = comment.get('user', {})
            login = author.get('login')
            if login:
                member_activities[login]['comments'].append(comment)
        
        # Process reviews
        for review in activity_data.get('reviews', []):
            author = review.get('user', {})
            login = author.get('login')
            if login:
                member_activities[login]['reviews'].append(review)
        
        # Add collaborator information
        collaborators = activity_data.get('collaborators', {})
        for member, collabs in collaborators.items():
            member_activities[member]['collaborators'] = collabs
        
        return dict(member_activities)
    
    def _calculate_individual_score(self, member_data: Dict[str, Any]) -> EngagementScore:
        """Calculate comprehensive engagement score for a single member"""
        
        login = list(member_data.keys())[0] if member_data else "unknown"
        activities = member_data.get(login, {})
        
        # Extract basic metrics
        commits = activities.get('commits', [])
        issues = activities.get('issues', [])
        prs = activities.get('prs', [])
        comments = activities.get('comments', [])
        reviews = activities.get('reviews', [])
        collaborators = activities.get('collaborators', set())
        
        # Calculate component scores
        contribution_score = self._calculate_contribution_score(commits, issues, prs)
        interaction_score = self._calculate_interaction_score(comments, reviews, collaborators)
        consistency_score = self._calculate_consistency_score(commits, issues, prs, comments)
        community_score = self._calculate_community_score(issues, comments, reviews, collaborators)
        impact_score = self._calculate_impact_score(prs, issues)
        growth_score = self._calculate_growth_score(login, commits, issues, prs)
        
        # Calculate total score
        total_score = (
            contribution_score * self.weights['contribution'] +
            interaction_score * self.weights['interaction'] +
            consistency_score * self.weights['consistency'] +
            community_score * self.weights['community'] +
            impact_score * self.weights['impact'] +
            growth_score * self.weights['growth']
        )
        
        # Build detailed metrics
        contribution_types = {
            'commits': len(commits),
            'issues': len(issues),
            'prs': len(prs),
            'merged_prs': len([pr for pr in prs if pr.get('merged_at')]),
        }
        
        interaction_types = {
            'comments': len(comments),
            'reviews': len(reviews),
            'collaborations': len(collaborators),
        }
        
        # Activity dates and frequency
        all_activities = commits + issues + prs + comments
        dates = [self._parse_date(item.get('created_at') or item.get('commit', {}).get('author', {}).get('date')) 
                for item in all_activities]
        dates = [d for d in dates if d]
        
        first_activity = min(dates) if dates else None
        last_activity = max(dates) if dates else None
        active_days = len(set(d.date() for d in dates)) if dates else 0
        
        # Calculate contribution frequency (activities per month)
        if first_activity and last_activity:
            months_active = max(1, (last_activity - first_activity).days / 30)
            contribution_frequency = len(all_activities) / months_active
        else:
            contribution_frequency = 0
        
        return EngagementScore(
            login=login,
            total_score=total_score,
            contribution_score=contribution_score,
            interaction_score=interaction_score,
            consistency_score=consistency_score,
            community_score=community_score,
            impact_score=impact_score,
            growth_score=growth_score,
            total_contributions=len(all_activities),
            total_interactions=len(comments) + len(reviews),
            contribution_types=contribution_types,
            interaction_types=interaction_types,
            first_activity_date=first_activity,
            last_activity_date=last_activity,
            active_days=active_days,
            contribution_frequency=contribution_frequency,
            commits_merged=len([pr for pr in prs if pr.get('merged_at')]),
            reviews_given=len(reviews),
            issues_responded=len([issue for issue in issues if issue.get('comments', 0) > 0]),
            collaborations=len(collaborators)
        )
    
    def _calculate_contribution_score(self, commits: List[Dict], issues: List[Dict], prs: List[Dict]) -> float:
        """Calculate contribution score based on direct contributions"""
        score = 0.0
        
        # Code contributions (weighted by merged PRs)
        merged_prs = [pr for pr in prs if pr.get('merged_at')]
        score += min(40, len(commits) * 0.5 + len(merged_prs) * 2)
        
        # Issue creation (quality indicator)
        score += min(20, len(issues) * 0.3)
        
        # PR submissions (attempted contributions)
        unmerged_prs = [pr for pr in prs if not pr.get('merged_at')]
        score += min(15, len(unmerged_prs) * 0.5)
        
        # Contribution diversity bonus
        contribution_types = 0
        if commits: contribution_types += 1
        if issues: contribution_types += 1
        if prs: contribution_types += 1
        
        score += contribution_types * 5
        
        return min(100, score)
    
    def _calculate_interaction_score(self, comments: List[Dict], reviews: List[Dict], collaborators: Set[str]) -> float:
        """Calculate interaction score based on community engagement"""
        score = 0.0
        
        # Code reviews (high-value interaction)
        score += min(40, len(reviews) * 3)
        
        # Issue comments and discussions
        score += min(30, len(comments) * 0.5)
        
        # Collaborations (working with others)
        collaboration_bonus = min(20, len(collaborators) * 2)
        score += collaboration_bonus
        
        # Diversity of interaction types
        interaction_types = 0
        if reviews: interaction_types += 1
        if comments: interaction_types += 1
        if collaborators: interaction_types += 1
        
        score += interaction_types * 5
        
        return min(100, score)
    
    def _calculate_consistency_score(self, commits: List[Dict], issues: List[Dict], prs: List[Dict], comments: List[Dict]) -> float:
        """Calculate consistency score based on regular activity patterns"""
        if not any([commits, issues, prs, comments]):
            return 0.0
        
        # Get all activity dates
        all_activities = commits + issues + prs + comments
        dates = [self._parse_date(item.get('created_at') or item.get('commit', {}).get('author', {}).get('date')) 
                for item in all_activities]
        dates = [d for d in dates if d]
        
        if len(dates) < 2:
            return 30.0  # New member
        
        # Sort dates and calculate gaps
        dates.sort()
        gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        
        # Calculate consistency metrics
        avg_gap = statistics.mean(gaps)
        gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        # Score based on regular intervals (lower std dev = more consistent)
        if avg_gap == 0:
            consistency_factor = 1.0
        else:
            consistency_factor = max(0, 1 - (gap_std / avg_gap))
        
        # Activity frequency bonus
        days_span = (max(dates) - min(dates)).days
        activity_frequency = len(dates) / max(1, days_span / 30)  # activities per month
        
        # Combine factors
        score = (consistency_factor * 60) + (min(40, activity_frequency * 5))
        
        return min(100, score)
    
    def _calculate_community_score(self, issues: List[Dict], comments: List[Dict], reviews: List[Dict], collaborators: Set[str]) -> float:
        """Calculate community building score"""
        score = 0.0
        
        # Mentoring through code reviews
        score += min(30, len(reviews) * 2)
        
        # Helping others through comments
        score += min(25, len(comments) * 0.3)
        
        # Opening constructive issues
        constructive_issues = len([issue for issue in issues if issue.get('comments', 0) > 0])
        score += min(20, constructive_issues * 1)
        
        # Collaboration network
        collaboration_score = min(15, len(collaborators) * 1.5)
        score += collaboration_score
        
        # Long-term community engagement
        recent_comments = [c for c in comments if self._is_recent(c.get('created_at'), 30)]
        if len(recent_comments) > 5:
            score += 10
        
        return min(100, score)
    
    def _calculate_impact_score(self, prs: List[Dict], issues: List[Dict]) -> float:
        """Calculate impact score based on merged contributions"""
        score = 0.0
        
        # Merged PRs (direct impact)
        merged_prs = [pr for pr in prs if pr.get('merged_at')]
        score += min(50, len(merged_prs) * 3)
        
        # Resolved issues
        resolved_issues = [issue for issue in issues if issue.get('state') == 'closed']
        score += min(30, len(resolved_issues) * 2)
        
        # Large PR bonus (indicates significant contributions)
        large_prs = [pr for pr in merged_prs if pr.get('additions', 0) + pr.get('deletions', 0) > 100]
        score += min(20, len(large_prs) * 2)
        
        return min(100, score)
    
    def _calculate_growth_score(self, login: str, commits: List[Dict], issues: List[Dict], prs: List[Dict]) -> float:
        """Calculate growth score based on improvement over time"""
        if login not in self.score_history or len(self.score_history[login]) < 2:
            return 50.0  # Neutral score for new members
        
        # Get recent score history
        recent_scores = [score.total_score for _, score in self.score_history[login][-6:]]  # Last 6 data points
        
        if len(recent_scores) < 2:
            return 50.0
        
        # Calculate growth trend
        if len(recent_scores) >= 3:
            # Simple linear trend
            recent_activity = len(commits) + len(issues) + len(prs)
            older_scores = recent_scores[:-3]
            recent_trend_scores = recent_scores[-3:]
            
            older_avg = statistics.mean(older_scores) if older_scores else recent_trend_scores[0]
            recent_avg = statistics.mean(recent_trend_scores)
            
            if older_avg > 0:
                growth_rate = ((recent_avg - older_avg) / older_avg) * 100
                score = 50 + min(50, max(-50, growth_rate))
            else:
                score = 75  # Starting from zero, current is positive
        else:
            # For only 2 data points, use simpler calculation
            score = 50 + min(30, max(-30, (recent_scores[-1] - recent_scores[0]) / 2))
        
        return min(100, max(0, score))
    
    def _calculate_community_score(self, individual_scores: List[EngagementScore]) -> CommunityEngagementScore:
        """Calculate aggregate community engagement metrics"""
        if not individual_scores:
            return CommunityEngagementScore(timestamp=datetime.now(), total_engagement_score=0.0)
        
        # Calculate aggregate scores
        total_score = statistics.mean([score.total_score for score in individual_scores])
        
        # Dimension-specific aggregates
        contribution_avg = statistics.mean([score.contribution_score for score in individual_scores])
        interaction_avg = statistics.mean([score.interaction_score for score in individual_scores])
        consistency_avg = statistics.mean([score.consistency_score for score in individual_scores])
        community_avg = statistics.mean([score.community_score for score in individual_scores])
        impact_avg = statistics.mean([score.impact_score for score in individual_scores])
        growth_avg = statistics.mean([score.growth_score for score in individual_scores])
        
        # Member distribution
        highly_engaged = len([s for s in individual_scores if s.total_score >= 80])
        moderately_engaged = len([s for s in individual_scores if 50 <= s.total_score < 80])
        low_engagement = len([s for s in individual_scores if s.total_score < 50])
        
        # Activity metrics
        avg_freq = statistics.mean([s.contribution_frequency for s in individual_scores if s.contribution_frequency > 0])
        avg_active_days = statistics.mean([s.active_days for s in individual_scores if s.active_days > 0])
        
        # Community health index (weighted composite)
        health_components = [
            total_score * 0.3,
            (highly_engaged / len(individual_scores)) * 100 * 0.2,
            (avg_freq / 10) * 100 * 0.2,  # Normalize to 10 contributions/month as excellent
            contribution_avg * 0.15,
            community_avg * 0.15
        ]
        health_index = min(100, sum(health_components))
        
        # Identify top contributors by dimension
        top_contributors = {
            'contribution': sorted(individual_scores, key=lambda x: x.contribution_score, reverse=True)[:5],
            'interaction': sorted(individual_scores, key=lambda x: x.interaction_score, reverse=True)[:5],
            'community': sorted(individual_scores, key=lambda x: x.community_score, reverse=True)[:5],
            'impact': sorted(individual_scores, key=lambda x: x.impact_score, reverse=True)[:5]
        }
        
        # Calculate trends (simplified - would need historical data for full implementation)
        engagement_trend_30d = 0.0
        engagement_trend_90d = 0.0
        
        # Activity patterns
        all_hours = []
        all_days = []
        for score in individual_scores:
            if score.first_activity_date and score.last_activity_date:
                # This would need more detailed timestamp analysis in a real implementation
                all_hours.extend([12, 14, 16])  # Placeholder
                all_days.extend([1, 2, 3])  # Placeholder (1=Monday)
        
        peak_activity_hours = sorted(Counter(all_hours).most_common(3), key=lambda x: x[1], reverse=True)
        peak_activity_days = sorted(Counter(all_days).most_common(3), key=lambda x: x[1], reverse=True)
        
        # Contribution distribution
        contribution_distribution = Counter()
        for score in individual_scores:
            contribution_distribution.update(score.contribution_types)
        
        return CommunityEngagementScore(
            timestamp=datetime.now(),
            total_engagement_score=total_score,
            contribution_engagement=contribution_avg,
            interaction_engagement=interaction_avg,
            consistency_engagement=consistency_avg,
            community_engagement=community_avg,
            impact_engagement=impact_avg,
            growth_engagement=growth_avg,
            highly_engaged_count=highly_engaged,
            moderately_engaged_count=moderately_engaged,
            low_engagement_count=low_engagement,
            avg_contribution_frequency=avg_freq,
            avg_active_days_per_month=avg_active_days,
            community_health_index=health_index,
            engagement_trend_30d=engagement_trend_30d,
            engagement_trend_90d=engagement_trend_90d,
            top_contributors={dim: [s.login for s in contributors] for dim, contributors in top_contributors.items()},
            peak_activity_hours=[h for h, _ in peak_activity_hours],
            peak_activity_days=[d for d, _ in peak_activity_days],
            contribution_distribution=dict(contribution_distribution)
        )
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            return None
    
    def _is_recent(self, date_string: Optional[str], days: int) -> bool:
        """Check if date is within the last N days"""
        if not date_string:
            return False
        date = self._parse_date(date_string)
        if not date:
            return False
        return (datetime.now() - date).days <= days
    
    def get_member_engagement_breakdown(self, login: str) -> Optional[EngagementScore]:
        """Get detailed engagement breakdown for a specific member"""
        if login in self.score_history and self.score_history[login]:
            return self.score_history[login][-1][1]  # Most recent score
        return None
    
    def compare_member_engagement(self, login1: str, login2: str) -> Dict[str, Any]:
        """Compare engagement between two members"""
        score1 = self.get_member_engagement_breakdown(login1)
        score2 = self.get_member_engagement_breakdown(login2)
        
        if not score1 or not score2:
            return {"error": "One or both members not found"}
        
        comparison = {
            "member1": {
                "login": score1.login,
                "total_score": score1.total_score,
                "strengths": self._get_score_strengths(score1),
                "improvement_areas": self._get_improvement_areas(score1)
            },
            "member2": {
                "login": score2.login,
                "total_score": score2.total_score,
                "strengths": self._get_score_strengths(score2),
                "improvement_areas": self._get_improvement_areas(score2)
            },
            "relative_performance": self._compare_relative_performance(score1, score2)
        }
        
        return comparison
    
    def _get_score_strengths(self, score: EngagementScore) -> List[str]:
        """Identify strengths based on score breakdown"""
        strengths = []
        scores = {
            'Contribution': score.contribution_score,
            'Interaction': score.interaction_score,
            'Consistency': score.consistency_score,
            'Community': score.community_score,
            'Impact': score.impact_score,
            'Growth': score.growth_score
        }
        
        for dimension, dimension_score in scores.items():
            if dimension_score >= 70:
                strengths.append(f"Strong {dimension.lower()} ({dimension_score:.1f})")
        
        return strengths
    
    def _get_improvement_areas(self, score: EngagementScore) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        scores = {
            'Contribution': score.contribution_score,
            'Interaction': score.interaction_score,
            'Consistency': score.consistency_score,
            'Community': score.community_score,
            'Impact': score.impact_score,
            'Growth': score.growth_score
        }
        
        for dimension, dimension_score in scores.items():
            if dimension_score < 50:
                improvements.append(f"Needs improvement in {dimension.lower()} ({dimension_score:.1f})")
        
        return improvements
    
    def _compare_relative_performance(self, score1: EngagementScore, score2: EngagementScore) -> Dict[str, Any]:
        """Compare relative performance between two members"""
        comparisons = {}
        
        dimensions = ['contribution_score', 'interaction_score', 'consistency_score', 
                     'community_score', 'impact_score', 'growth_score']
        
        for dimension in dimensions:
            val1 = getattr(score1, dimension)
            val2 = getattr(score2, dimension)
            
            if val1 > val2:
                comparisons[dimension] = f"{score1.login} leads by {val1 - val2:.1f}"
            elif val2 > val1:
                comparisons[dimension] = f"{score2.login} leads by {val2 - val1:.1f}"
            else:
                comparisons[dimension] = "Tied"
        
        overall_winner = score1.login if score1.total_score > score2.total_score else score2.login
        margin = abs(score1.total_score - score2.total_score)
        
        return {
            "overall_winner": overall_winner,
            "score_margin": margin,
            "dimension_breakdown": comparisons
        }