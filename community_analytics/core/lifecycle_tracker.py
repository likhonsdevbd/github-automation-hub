"""
Community Member Lifecycle Tracking System

Tracks individual members through their lifecycle stages from new contributor
to veteran community member, providing insights into progression patterns
and identifying potential contributors at risk of attrition.
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
import statistics
import numpy as np

from github_api_client import GitHubAPIClient


class LifecycleStage(Enum):
    """Community member lifecycle stages"""
    NEW = "new"
    ACTIVE = "active" 
    VETERAN = "veteran"
    LURKER = "lurker"
    AT_RISK = "at_risk"
    LOST = "lost"


@dataclass
class MemberProfile:
    """Enhanced member profile with lifecycle tracking"""
    login: str
    github_id: int
    first_contribution_date: datetime
    first_seen_date: datetime
    
    # Lifecycle tracking
    current_stage: LifecycleStage
    stage_transitions: List[Tuple[datetime, LifecycleStage, LifecycleStage]] = field(default_factory=list)
    stage_durations: Dict[LifecycleStage, int] = field(default_factory=dict)
    
    # Activity metrics
    total_contributions: int = 0
    contribution_types: Dict[str, int] = field(default_factory=dict)
    contribution_frequency: float = 0.0  # contributions per month
    last_activity_date: Optional[datetime] = None
    
    # Engagement metrics
    issues_opened: int = 0
    issues_commented: int = 0
    prs_opened: int = 0
    prs_merged: int = 0
    discussions_posts: int = 0
    discussions_comments: int = 0
    
    # Network metrics
    collaborators_worked_with: Set[str] = field(default_factory=set)
    review_count: int = 0
    
    # Retention factors
    consecutive_active_months: int = 0
    gap_months: int = 0
    predicted_retention_months: float = 0.0
    
    # Risk indicators
    risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize derived fields after dataclass creation"""
        if not self.stage_durations:
            self._calculate_stage_durations()
    
    def _calculate_stage_durations(self):
        """Calculate duration spent in each lifecycle stage"""
        now = datetime.now()
        for stage, start_date in self.get_stage_start_dates():
            end_date = now if stage == self.current_stage else self.get_stage_end_date(stage)
            duration_days = (end_date - start_date).days
            self.stage_durations[stage] = duration_days
    
    def get_stage_start_dates(self) -> List[Tuple[LifecycleStage, datetime]]:
        """Get start date for each stage transition"""
        stage_dates = []
        for transition_date, from_stage, to_stage in self.stage_transitions:
            stage_dates.append((to_stage, transition_date))
        return stage_dates
    
    def get_stage_end_date(self, stage: LifecycleStage) -> datetime:
        """Get end date for a specific stage"""
        stage_dates = self.get_stage_start_dates()
        stage_index = None
        for i, (s, date) in enumerate(stage_dates):
            if s == stage:
                stage_index = i
                break
        
        if stage_index is None:
            return self.first_contribution_date
        
        if stage_index + 1 < len(stage_dates):
            return stage_dates[stage_index + 1][1]
        else:
            return datetime.now()


@dataclass
class LifecycleMetrics:
    """Aggregate lifecycle metrics for the community"""
    timestamp: datetime
    total_members: int
    
    # Stage distribution
    new_members: int = 0
    active_members: int = 0
    veteran_members: int = 0
    lurker_members: int = 0
    at_risk_members: int = 0
    lost_members: int = 0
    
    # Progression metrics
    new_to_active_rate: float = 0.0  # % of new members who become active
    active_to_veteran_rate: float = 0.0  # % of active who become veteran
    retention_rate_3_months: float = 0.0
    retention_rate_6_months: float = 0.0
    retention_rate_12_months: float = 0.0
    
    # Churn metrics
    monthly_churn_rate: float = 0.0
    at_risk_count: int = 0
    predicted_lost_next_month: int = 0
    
    # Velocity metrics
    avg_time_to_active_days: float = 0.0
    avg_time_to_veteran_days: float = 0.0
    median_stage_durations: Dict[LifecycleStage, int] = field(default_factory=dict)


class MemberLifecycleTracker:
    """
    Track community members through their lifecycle stages.
    
    This class provides comprehensive tracking of individual member progression
    through community engagement stages, identifies at-risk members, and 
    calculates lifecycle metrics for the entire community.
    """
    
    def __init__(self, 
                 inactivity_threshold_days: int = 90,
                 new_member_window_days: int = 30,
                 active_member_min_contributions: int = 5,
                 veteran_member_min_contributions: int = 50):
        """
        Initialize the lifecycle tracker.
        
        Args:
            inactivity_threshold_days: Days without activity before considered at risk
            new_member_window_days: Days since first contribution to be considered new
            active_member_min_contributions: Min contributions to be considered active
            veteran_member_min_contributions: Min contributions to be considered veteran
        """
        self.inactivity_threshold_days = inactivity_threshold_days
        self.new_member_window_days = new_member_window_days
        self.active_member_min_contributions = active_member_min_contributions
        self.veteran_member_min_contributions = veteran_member_min_contributions
        
        self.logger = logging.getLogger(__name__)
        
        # Member tracking
        self.member_profiles: Dict[str, MemberProfile] = {}
        self.member_activity_timeline: Dict[str, deque] = defaultdict(lambda: deque(maxlen=365))
        
        # Community metrics over time
        self.lifecycle_metrics_history: List[LifecycleMetrics] = []
        
        # Stage transition patterns
        self.transition_patterns = defaultdict(list)
        
    async def analyze_member_lifecycle(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int = 180
    ) -> LifecycleMetrics:
        """
        Perform comprehensive lifecycle analysis for all community members.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            lookback_days: Days of historical data to analyze
            
        Returns:
            LifecycleMetrics with comprehensive lifecycle analysis
        """
        self.logger.info(f"Analyzing member lifecycle for {owner}/{repo}")
        
        # Collect comprehensive activity data
        activity_data = await self._collect_activity_data(client, owner, repo, lookback_days)
        
        # Build/update member profiles
        member_profiles = await self._build_member_profiles(activity_data)
        
        # Update lifecycle stages
        updated_profiles = []
        for profile in member_profiles.values():
            old_stage = profile.current_stage
            new_stage = self._determine_lifecycle_stage(profile)
            
            if old_stage != new_stage:
                profile.stage_transitions.append((datetime.now(), old_stage, new_stage))
                profile.current_stage = new_stage
                self.logger.info(f"{profile.login} transitioned from {old_stage.value} to {new_stage.value}")
            
            # Calculate risk factors
            self._assess_risk_factors(profile)
            
            updated_profiles.append(profile)
        
        # Calculate lifecycle metrics
        lifecycle_metrics = self._calculate_lifecycle_metrics(updated_profiles)
        
        # Store historical data
        self.member_profiles.update({p.login: p for p in updated_profiles})
        self.lifecycle_metrics_history.append(lifecycle_metrics)
        
        # Analyze transition patterns
        self._analyze_transition_patterns(updated_profiles)
        
        return lifecycle_metrics
    
    async def _collect_activity_data(
        self, 
        client: GitHubAPIClient, 
        owner: str, 
        repo: str, 
        lookback_days: int
    ) -> Dict[str, Any]:
        """Collect comprehensive activity data for all contributors"""
        
        since_date = datetime.now() - timedelta(days=lookback_days)
        
        try:
            # Collect data concurrently
            contributors, issues, prs, commits, comments = await asyncio.gather(
                client.get_contributors(owner, repo),
                client.get_issues(owner, repo, state="all", since=since_date),
                client.get_pull_requests(owner, repo, state="all"),
                client.get_commits(owner, repo, since=since_date),
                client.get_issue_comments(owner, repo, since=since_date),
                return_exceptions=True
            )
            
            # Handle potential exceptions
            data = {}
            for key, result in zip(['contributors', 'issues', 'prs', 'commits', 'comments'], 
                                 [contributors, issues, prs, commits, comments]):
                data[key] = result if not isinstance(result, Exception) else []
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to collect activity data: {e}")
            return {}
    
    async def _build_member_profiles(self, activity_data: Dict[str, Any]) -> Dict[str, MemberProfile]:
        """Build comprehensive member profiles from activity data"""
        profiles = {}
        
        # Initialize profiles from contributors
        for contributor in activity_data.get('contributors', []):
            login = contributor.get('login')
            if not login:
                continue
                
            profiles[login] = MemberProfile(
                login=login,
                github_id=contributor.get('id', 0),
                first_contribution_date=datetime.now() - timedelta(days=90),  # Default
                first_seen_date=datetime.now() - timedelta(days=90),  # Default
                current_stage=LifecycleStage.NEW,
                total_contributions=contributor.get('contributions', 0)
            )
        
        # Add activity from issues
        for issue in activity_data.get('issues', []):
            user = issue.get('user', {})
            login = user.get('login')
            if login and login in profiles:
                profile = profiles[login]
                profile.issues_opened += 1
                profile.last_activity_date = self._parse_date(issue.get('created_at'))
                profile.first_contribution_date = min(
                    profile.first_contribution_date,
                    profile.last_activity_date or datetime.now()
                )
                profile.member_activity_timeline[login].append({
                    'date': profile.last_activity_date,
                    'type': 'issue_opened',
                    'data': issue
                })
        
        # Add activity from PRs
        for pr in activity_data.get('prs', []):
            user = pr.get('user', {})
            login = user.get('login')
            if login and login in profiles:
                profile = profiles[login]
                profile.prs_opened += 1
                if pr.get('merged_at'):
                    profile.prs_merged += 1
                profile.last_activity_date = self._parse_date(pr.get('created_at'))
                profile.first_contribution_date = min(
                    profile.first_contribution_date,
                    profile.last_activity_date or datetime.now()
                )
                profile.member_activity_timeline[login].append({
                    'date': profile.last_activity_date,
                    'type': 'pr_opened',
                    'data': pr
                })
        
        # Add activity from commits
        for commit in activity_data.get('commits', []):
            author = commit.get('author', {})
            login = author.get('login')
            if login and login in profiles:
                profile = profiles[login]
                profile.total_contributions += 1
                commit_date = self._parse_date(commit.get('commit', {}).get('author', {}).get('date'))
                if commit_date:
                    profile.last_activity_date = commit_date
                    profile.first_contribution_date = min(
                        profile.first_contribution_date,
                        commit_date
                    )
                    profile.member_activity_timeline[login].append({
                        'date': commit_date,
                        'type': 'commit',
                        'data': commit
                    })
        
        # Calculate derived metrics
        for profile in profiles.values():
            self._calculate_profile_metrics(profile)
        
        return profiles
    
    def _calculate_profile_metrics(self, profile: MemberProfile):
        """Calculate derived metrics for a member profile"""
        # Contribution frequency
        if profile.first_contribution_date and profile.last_activity_date:
            activity_span_days = (profile.last_activity_date - profile.first_contribution_date).days
            activity_span_months = max(1, activity_span_days / 30)
            profile.contribution_frequency = profile.total_contributions / activity_span_months
        
        # Consecutive active months
        activity_dates = sorted([item['date'] for item in profile.member_activity_timeline[profile.login] 
                               if item['date']])
        if activity_dates:
            current_month = None
            consecutive_months = 0
            for date in activity_dates:
                month = date.replace(day=1)
                if month != current_month:
                    if current_month is None or (month - current_month).days <= 45:
                        consecutive_months += 1
                    else:
                        consecutive_months = 1
                    current_month = month
            profile.consecutive_active_months = consecutive_months
        
        # Gap months calculation
        if profile.last_activity_date:
            gap_days = (datetime.now() - profile.last_activity_date).days
            profile.gap_months = gap_days / 30
    
    def _determine_lifecycle_stage(self, profile: MemberProfile) -> LifecycleStage:
        """Determine current lifecycle stage for a member"""
        
        # Check for lost members (inactive for extended period)
        if profile.gap_months > 6:
            return LifecycleStage.LOST
        
        # Check for at-risk members
        if (profile.gap_months > 3 or 
            profile.consecutive_active_months == 0 or
            profile.contribution_frequency < 0.5):
            return LifecycleStage.AT_RISK
        
        # Determine active stage based on contributions and time
        total_contributions = profile.total_contributions
        months_active = max(1, profile.gap_months + profile.consecutive_active_months)
        
        if profile.gap_months <= 1:  # Recently active
            if total_contributions < self.new_member_window_days:
                return LifecycleStage.NEW
            elif total_contributions < self.active_member_min_contributions:
                return LifecycleStage.ACTIVE
            elif total_contributions < self.veteran_member_min_contributions:
                return LifecycleStage.ACTIVE
            else:
                return LifecycleStage.VETERAN
        else:
            # Inactive - could be lurker or at-risk
            return LifecycleStage.LURKER if profile.gap_months < 3 else LifecycleStage.AT_RISK
    
    def _assess_risk_factors(self, profile: MemberProfile):
        """Assess risk factors for member attrition"""
        risk_factors = []
        risk_score = 0.0
        
        # Long gaps in activity
        if profile.gap_months > 3:
            risk_factors.append(f"Inactive for {profile.gap_months:.1f} months")
            risk_score += 0.3
        
        # Declining contribution frequency
        if profile.contribution_frequency < 1.0:
            risk_factors.append(f"Low contribution frequency ({profile.contribution_frequency:.1f}/month)")
            risk_score += 0.2
        
        # No recent review activity
        if profile.review_count == 0 and profile.total_contributions > 10:
            risk_factors.append("No community participation (reviews)")
            risk_score += 0.1
        
        # Limited contribution types
        contribution_types_count = len([k for k, v in profile.contribution_types.items() if v > 0])
        if contribution_types_count == 1 and profile.total_contributions > 5:
            risk_factors.append("Limited contribution diversity")
            risk_score += 0.1
        
        # Very low engagement in discussions
        total_discussion_activity = profile.discussions_posts + profile.discussions_comments
        if total_discussion_activity == 0 and profile.total_contributions > 20:
            risk_factors.append("No community discussions")
            risk_score += 0.1
        
        profile.risk_factors = risk_factors
        profile.risk_score = min(1.0, risk_score)
    
    def _calculate_lifecycle_metrics(self, profiles: List[MemberProfile]) -> LifecycleMetrics:
        """Calculate aggregate lifecycle metrics"""
        
        total_members = len(profiles)
        stage_counts = defaultdict(int)
        
        for profile in profiles:
            stage_counts[profile.current_stage] += 1
        
        # Calculate progression rates
        new_members = [p for p in profiles if p.current_stage == LifecycleStage.NEW]
        active_members = [p for p in profiles if p.current_stage == LifecycleStage.ACTIVE]
        veteran_members = [p for p in profiles if p.current_stage == LifecycleStage.VETERAN]
        
        # Calculate retention rates
        retention_3m = self._calculate_retention_rate(profiles, 3)
        retention_6m = self._calculate_retention_rate(profiles, 6)
        retention_12m = self._calculate_retention_rate(profiles, 12)
        
        # Calculate churn rate
        monthly_churn = self._calculate_monthly_churn_rate(profiles)
        
        # Stage durations
        stage_durations = {}
        for stage in LifecycleStage:
            durations = [p.stage_durations.get(stage, 0) for p in profiles if p.stage_durations.get(stage, 0) > 0]
            if durations:
                stage_durations[stage] = int(statistics.median(durations))
        
        # Predict future losses
        at_risk_members = [p for p in profiles if p.current_stage == LifecycleStage.AT_RISK]
        predicted_lost = int(len(at_risk_members) * 0.3)  # 30% of at-risk members likely to be lost
        
        # Velocity metrics
        time_to_active = []
        time_to_veteran = []
        
        for profile in profiles:
            if profile.stage_durations.get(LifecycleStage.ACTIVE, 0) > 0:
                time_to_active.append(profile.stage_durations[LifecycleStage.ACTIVE])
            if profile.stage_durations.get(LifecycleStage.VETERAN, 0) > 0:
                time_to_veteran.append(profile.stage_durations[LifecycleStage.VETERAN])
        
        return LifecycleMetrics(
            timestamp=datetime.now(),
            total_members=total_members,
            new_members=stage_counts[LifecycleStage.NEW],
            active_members=stage_counts[LifecycleStage.ACTIVE],
            veteran_members=stage_counts[LifecycleStage.VETERAN],
            lurker_members=stage_counts[LifecycleStage.LURKER],
            at_risk_members=stage_counts[LifecycleStage.AT_RISK],
            lost_members=stage_counts[LifecycleStage.LOST],
            retention_rate_3_months=retention_3m,
            retention_rate_6_months=retention_6m,
            retention_rate_12_months=retention_12m,
            monthly_churn_rate=monthly_churn,
            at_risk_count=len(at_risk_members),
            predicted_lost_next_month=predicted_lost,
            avg_time_to_active_days=statistics.mean(time_to_active) if time_to_active else 0,
            avg_time_to_veteran_days=statistics.mean(time_to_veteran) if time_to_veteran else 0,
            median_stage_durations=stage_durations
        )
    
    def _calculate_retention_rate(self, profiles: List[MemberProfile], months: int) -> float:
        """Calculate retention rate for a specific time period"""
        if not profiles:
            return 0.0
        
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        retained_members = 0
        
        for profile in profiles:
            if profile.last_activity_date and profile.last_activity_date >= cutoff_date:
                retained_members += 1
        
        return (retained_members / len(profiles)) * 100
    
    def _calculate_monthly_churn_rate(self, profiles: List[MemberProfile]) -> float:
        """Calculate monthly churn rate"""
        if not profiles:
            return 0.0
        
        # Simple churn calculation: lost members / total members * 100
        lost_count = len([p for p in profiles if p.current_stage == LifecycleStage.LOST])
        return (lost_count / len(profiles)) * 100
    
    def _analyze_transition_patterns(self, profiles: List[MemberProfile]):
        """Analyze patterns in stage transitions"""
        for profile in profiles:
            for transition in profile.stage_transitions:
                transition_date, from_stage, to_stage = transition
                self.transition_patterns[f"{from_stage.value}_to_{to_stage.value}"].append({
                    'date': transition_date,
                    'member': profile.login,
                    'duration_days': self._calculate_transition_duration(profile, from_stage)
                })
    
    def _calculate_transition_duration(self, profile: MemberProfile, from_stage: LifecycleStage) -> int:
        """Calculate how long a member spent in a stage before transitioning"""
        stage_dates = profile.get_stage_start_dates()
        for i, (stage, start_date) in enumerate(stage_dates):
            if stage == from_stage:
                if i + 1 < len(stage_dates):
                    end_date = stage_dates[i + 1][1]
                    return (end_date - start_date).days
                else:
                    # Still in this stage
                    return (datetime.now() - start_date).days
        return 0
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            return None
    
    def get_member_progression_path(self, login: str) -> List[Tuple[str, int]]:
        """Get the progression path for a specific member"""
        if login not in self.member_profiles:
            return []
        
        profile = self.member_profiles[login]
        path = []
        
        for transition_date, from_stage, to_stage in profile.stage_transitions:
            path.append((f"{from_stage.value} → {to_stage.value}", 
                        (transition_date - profile.first_contribution_date).days))
        
        return path
    
    def identify_promising_new_members(self, limit: int = 10) -> List[MemberProfile]:
        """Identify new members with high potential for progression"""
        new_members = [p for p in self.member_profiles.values() 
                      if p.current_stage == LifecycleStage.NEW]
        
        # Score new members based on activity, diversity, and engagement
        def potential_score(profile: MemberProfile) -> float:
            score = 0.0
            
            # Recent activity (last 14 days)
            if profile.last_activity_date:
                days_since_activity = (datetime.now() - profile.last_activity_date).days
                if days_since_activity <= 14:
                    score += 0.4
                elif days_since_activity <= 30:
                    score += 0.2
            
            # Contribution frequency
            if profile.contribution_frequency > 2:
                score += 0.3
            elif profile.contribution_frequency > 1:
                score += 0.2
            
            # Contribution diversity
            diversity = len([k for k, v in profile.contribution_types.items() if v > 0])
            score += min(0.3, diversity * 0.1)
            
            return score
        
        # Sort by potential score and return top candidates
        return sorted(new_members, key=potential_score, reverse=True)[:limit]
    
    def get_lifecycle_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive lifecycle summary report"""
        if not self.lifecycle_metrics_history:
            return {"error": "No lifecycle data available"}
        
        latest_metrics = self.lifecycle_metrics_history[-1]
        
        # Calculate trends
        trends = {}
        if len(self.lifecycle_metrics_history) >= 2:
            previous = self.lifecycle_metrics_history[-2]
            trends = {
                "total_members_change": latest_metrics.total_members - previous.total_members,
                "retention_trend": latest_metrics.retention_rate_3_months - previous.retention_rate_3_months,
                "churn_trend": latest_metrics.monthly_churn_rate - previous.monthly_churn_rate,
                "at_risk_trend": latest_metrics.at_risk_count - previous.at_risk_count
            }
        
        # Identify top risk factors across community
        all_risk_factors = []
        for profile in self.member_profiles.values():
            all_risk_factors.extend(profile.risk_factors)
        
        risk_factor_counts = {}
        for factor in all_risk_factors:
            risk_factor_counts[factor] = risk_factor_counts.get(factor, 0) + 1
        
        return {
            "current_metrics": {
                "total_members": latest_metrics.total_members,
                "stage_distribution": {
                    "new": latest_metrics.new_members,
                    "active": latest_metrics.active_members,
                    "veteran": latest_metrics.veteran_members,
                    "lurker": latest_metrics.lurker_members,
                    "at_risk": latest_metrics.at_risk_members,
                    "lost": latest_metrics.lost_members
                },
                "retention_rates": {
                    "3_months": latest_metrics.retention_rate_3_months,
                    "6_months": latest_metrics.retention_rate_6_months,
                    "12_months": latest_metrics.retention_rate_12_months
                },
                "monthly_churn_rate": latest_metrics.monthly_churn_rate,
                "predicted_lost_next_month": latest_metrics.predicted_lost_next_month
            },
            "trends": trends,
            "top_risk_factors": sorted(risk_factor_counts.items(), 
                                     key=lambda x: x[1], reverse=True)[:5],
            "promising_new_members": len([p for p in self.member_profiles.values() 
                                        if p.current_stage == LifecycleStage.NEW and p.risk_score < 0.2])
        }