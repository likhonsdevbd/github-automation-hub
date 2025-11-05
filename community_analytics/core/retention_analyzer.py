"""
Contributor Retention Analysis System

Analyzes contributor retention patterns, identifies retention risks, and provides
predictive insights for maintaining a healthy contributor base over time.
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
class ContributorRetention:
    """Individual contributor retention analysis"""
    login: str
    github_id: int
    
    # Retention metrics
    first_contribution_date: datetime
    last_activity_date: Optional[datetime]
    retention_period_days: int
    active_period_days: int
    
    # Retention status
    is_retained: bool  # Active within retention window
    retention_score: float  # 0-100 retention probability
    churn_risk_score: float  # 0-100 churn risk (higher = more risk)
    
    # Activity patterns
    total_contributions: int
    contribution_frequency: float  # Contributions per month
    activity_consistency_score: float  # Consistency of activity
    
    # Retention factors
    contribution_diversity: int  # Number of different contribution types
    collaboration_count: int  # Number of collaborators
    review_participation: int  # Reviews given/received
    community_engagement: float  # Score from community interactions
    
    # Timeline analysis
    active_months: List[int]  # Months with activity
    inactive_gaps: List[int]  # Lengths of inactivity periods (days)
    peak_activity_periods: List[Tuple[datetime, int]]  # (date, contribution_count)
    
    # Predictive indicators
    likely_to_return: bool
    predicted_churn_months: int
    retention_factors: List[str]  # Factors supporting retention
    churn_factors: List[str]  # Risk factors for churn
    
    def __post_init__(self):
        """Calculate derived retention metrics"""
        if not self.last_activity_date:
            self.last_activity_date = datetime.now()
        
        self.active_period_days = (self.last_activity_date - self.first_contribution_date).days
        self.retention_period_days = (datetime.now() - self.first_contribution_date).days


@dataclass
class CohortAnalysis:
    """Cohort-based retention analysis"""
    cohort_month: datetime  # First contribution month
    cohort_size: int
    
    # Retention rates at different time points
    retention_day_7: float = 0.0  # % retained after 7 days
    retention_day_30: float = 0.0  # % retained after 30 days
    retention_day_90: float = 0.0  # % retained after 90 days
    retention_day_180: float = 0.0  # % retained after 180 days
    retention_day_365: float = 0.0  # % retained after 365 days
    
    # Cohort characteristics
    avg_contributions_per_member: float = 0.0
    contribution_diversity_score: float = 0.0
    collaboration_score: float = 0.0
    community_engagement_score: float = 0.0
    
    # Predictive metrics
    predicted_long_term_retention: float = 0.0  # % likely to be long-term contributors
    churn_risk_score: float = 0.0  # Average churn risk for cohort
    
    # Timeline data
    monthly_activity: Dict[int, int] = field(default_factory=dict)  # month_offset -> active_members


@dataclass
class RetentionMetrics:
    """Aggregate retention metrics for the community"""
    timestamp: datetime
    total_contributors_analyzed: int
    
    # Overall retention rates
    retention_rate_day_7: float = 0.0
    retention_rate_day_30: float = 0.0
    retention_rate_day_90: float = 0.0
    retention_rate_day_365: float = 0.0
    
    # Churn metrics
    monthly_churn_rate: float = 0.0
    predicted_churn_next_30_days: int = 0
    high_risk_contributors: int = 0
    
    # Retention quality
    avg_retention_period_days: float = 0.0
    avg_contribution_frequency: float = 0.0
    activity_consistency_score: float = 0.0
    
    # Cohort analysis
    recent_cohorts: List[CohortAnalysis] = field(default_factory=list)
    best_performing_cohort: Optional[CohortAnalysis] = None
    worst_performing_cohort: Optional[CohortAnalysis] = None
    
    # Retention insights
    top_retention_factors: List[Tuple[str, float]] = field(default_factory=list)  # (factor, correlation)
    retention_recommendations: List[str] = field(default_factory=list)
    at_risk_contributors: List[str] = field(default_factory=list)


class RetentionAnalyzer:
    """
    Analyze contributor retention patterns and predict future retention.
    
    This class provides comprehensive retention analysis including cohort analysis,
    churn prediction, and identification of retention risk factors.
    """
    
    def __init__(self):
        """Initialize the retention analyzer"""
        self.logger = logging.getLogger(__name__)
        
        # Retention analysis parameters
        self.retention_windows = [7, 30, 90, 180, 365]  # Days to analyze retention
        self.cohort_analysis_months = 12  # Number of months for cohort analysis
        
        # Historical data for trend analysis
        self.retention_history: List[RetentionMetrics] = []
        self.cohort_data: List[CohortAnalysis] = []
        self.contributor_data: Dict[str, ContributorRetention] = {}
        
        # Retention factor weights (can be tuned based on community)
        self.retention_factor_weights = {
            'contribution_frequency': 0.25,
            'contribution_diversity': 0.20,
            'collaboration': 0.20,
            'community_engagement': 0.15,
            'activity_consistency': 0.20
        }
    
    async def analyze_contributor_retention(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int = 365
    ) -> RetentionMetrics:
        """
        Perform comprehensive retention analysis for all contributors.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            lookback_days: Days of historical data to analyze
            
        Returns:
            RetentionMetrics with comprehensive retention analysis
        """
        self.logger.info(f"Analyzing contributor retention for {owner}/{repo}")
        
        # Collect comprehensive activity data
        activity_data = await self._collect_retention_data(client, owner, repo, lookback_days)
        
        # Build contributor retention profiles
        retention_profiles = await self._build_retention_profiles(activity_data)
        
        # Perform cohort analysis
        cohort_analysis = self._perform_cohort_analysis(retention_profiles)
        
        # Calculate retention metrics
        retention_metrics = self._calculate_retention_metrics(retention_profiles, cohort_analysis)
        
        # Store for historical analysis
        self.contributor_data.update({p.login: p for p in retention_profiles})
        self.cohort_data.extend(cohort_analysis)
        self.retention_history.append(retention_metrics)
        
        return retention_metrics
    
    async def _collect_retention_data(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Collect comprehensive data for retention analysis"""
        
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
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to collect retention data: {e}")
            return {}
    
    async def _build_retention_profiles(self, activity_data: Dict[str, Any]) -> List[ContributorRetention]:
        """Build comprehensive retention profiles for all contributors"""
        
        # Group activity by contributor
        contributor_activities = defaultdict(lambda: {
            'commits': [],
            'issues': [],
            'prs': [],
            'comments': [],
            'reviews': [],
            'collaborators': set(),
            'activity_dates': []
        })
        
        # Process commits
        for commit in activity_data.get('commits', []):
            author = commit.get('author', {})
            login = author.get('login')
            if login:
                contributor_activities[login]['commits'].append(commit)
                date_str = commit.get('commit', {}).get('author', {}).get('date')
                if date_str:
                    date = self._parse_date(date_str)
                    if date:
                        contributor_activities[login]['activity_dates'].append(date)
        
        # Process issues
        for issue in activity_data.get('issues', []):
            user = issue.get('user', {})
            login = user.get('login')
            if login:
                contributor_activities[login]['issues'].append(issue)
                date = self._parse_date(issue.get('created_at'))
                if date:
                    contributor_activities[login]['activity_dates'].append(date)
        
        # Process PRs
        for pr in activity_data.get('prs', []):
            user = pr.get('user', {})
            login = user.get('login')
            if login:
                contributor_activities[login]['prs'].append(pr)
                date = self._parse_date(pr.get('created_at'))
                if date:
                    contributor_activities[login]['activity_dates'].append(date)
        
        # Process comments
        for comment in activity_data.get('comments', []):
            user = comment.get('user', {})
            login = user.get('login')
            if login:
                contributor_activities[login]['comments'].append(comment)
                date = self._parse_date(comment.get('created_at'))
                if date:
                    contributor_activities[login]['activity_dates'].append(date)
        
        # Process reviews
        for review in activity_data.get('reviews', []):
            user = review.get('user', {})
            login = user.get('login')
            if login:
                contributor_activities[login]['reviews'].append(review)
                date = self._parse_date(review.get('created_at'))
                if date:
                    contributor_activities[login]['activity_dates'].append(date)
        
        # Build retention profiles
        retention_profiles = []
        for login, activities in contributor_activities.items():
            profile = self._build_individual_retention_profile(login, activities)
            retention_profiles.append(profile)
        
        return retention_profiles
    
    def _build_individual_retention_profile(self, login: str, activities: Dict[str, Any]) -> ContributorRetention:
        """Build retention profile for a single contributor"""
        
        commits = activities.get('commits', [])
        issues = activities.get('issues', [])
        prs = activities.get('prs', [])
        comments = activities.get('comments', [])
        reviews = activities.get('reviews', [])
        activity_dates = sorted(activities.get('activity_dates', []))
        
        if not activity_dates:
            # No activity data
            return ContributorRetention(
                login=login,
                github_id=0,
                first_contribution_date=datetime.now(),
                last_activity_date=None,
                retention_period_days=0,
                active_period_days=0,
                is_retained=False,
                retention_score=0.0,
                churn_risk_score=100.0,
                total_contributions=0,
                contribution_frequency=0.0,
                activity_consistency_score=0.0,
                contribution_diversity=0,
                collaboration_count=0,
                review_participation=0,
                community_engagement=0.0,
                active_months=[],
                inactive_gaps=[],
                peak_activity_periods=[],
                likely_to_return=False,
                predicted_churn_months=0,
                retention_factors=[],
                churn_factors=["No activity recorded"]
            )
        
        # Calculate basic metrics
        first_activity = min(activity_dates)
        last_activity = max(activity_dates)
        retention_period_days = (datetime.now() - first_activity).days
        active_period_days = (last_activity - first_activity).days
        
        # Total contributions
        total_contributions = len(commits) + len(issues) + len(prs) + len(comments)
        
        # Contribution frequency
        months_active = max(1, active_period_days / 30)
        contribution_frequency = total_contributions / months_active
        
        # Activity consistency
        activity_consistency_score = self._calculate_activity_consistency(activity_dates)
        
        # Contribution diversity
        contribution_types = 0
        if commits: contribution_types += 1
        if issues: contribution_types += 1
        if prs: contribution_types += 1
        if comments: contribution_types += 1
        
        # Community engagement score
        community_engagement = self._calculate_community_engagement(comments, reviews, activities.get('collaborators', set()))
        
        # Active months
        active_months = sorted(list(set(date.month for date in activity_dates)))
        
        # Inactive gaps
        inactive_gaps = self._calculate_inactive_gaps(activity_dates)
        
        # Peak activity periods
        peak_periods = self._identify_peak_activity_periods(activity_dates)
        
        # Calculate retention and churn scores
        retention_score = self._calculate_retention_score(
            contribution_frequency, contribution_types, community_engagement, 
            activity_consistency_score, len(activities.get('collaborators', set()))
        )
        
        churn_risk_score = 100 - retention_score
        
        # Determine retention status
        days_since_last_activity = (datetime.now() - last_activity).days
        is_retained = days_since_last_activity <= 30  # Active within last 30 days
        
        # Predict return likelihood
        likely_to_return = self._predict_return_likelihood(
            retention_score, days_since_last_activity, contribution_frequency
        )
        
        # Identify retention and churn factors
        retention_factors, churn_factors = self._identify_retention_factors(
            contribution_frequency, contribution_types, community_engagement,
            activity_consistency_score, days_since_last_activity, total_contributions
        )
        
        # Predict churn timing
        predicted_churn_months = self._predict_churn_timing(churn_risk_score, days_since_last_activity)
        
        return ContributorRetention(
            login=login,
            github_id=0,  # Would need to be fetched from API
            first_contribution_date=first_activity,
            last_activity_date=last_activity,
            retention_period_days=retention_period_days,
            active_period_days=active_period_days,
            is_retained=is_retained,
            retention_score=retention_score,
            churn_risk_score=churn_risk_score,
            total_contributions=total_contributions,
            contribution_frequency=contribution_frequency,
            activity_consistency_score=activity_consistency_score,
            contribution_diversity=contribution_types,
            collaboration_count=len(activities.get('collaborators', set())),
            review_participation=len(reviews),
            community_engagement=community_engagement,
            active_months=active_months,
            inactive_gaps=inactive_gaps,
            peak_activity_periods=peak_periods,
            likely_to_return=likely_to_return,
            predicted_churn_months=predicted_churn_months,
            retention_factors=retention_factors,
            churn_factors=churn_factors
        )
    
    def _calculate_activity_consistency(self, activity_dates: List[datetime]) -> float:
        """Calculate activity consistency score based on gaps between activities"""
        if len(activity_dates) < 2:
            return 50.0  # Neutral score for minimal activity
        
        # Calculate gaps between activities
        gaps = [(activity_dates[i+1] - activity_dates[i]).days for i in range(len(activity_dates)-1)]
        
        # Calculate consistency metrics
        avg_gap = statistics.mean(gaps)
        gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        # Consistency score (lower standard deviation = higher consistency)
        if avg_gap == 0:
            return 100.0
        
        consistency_factor = max(0, 1 - (gap_std / avg_gap))
        return consistency_factor * 100
    
    def _calculate_community_engagement(self, comments: List[Dict], reviews: List[Dict], collaborators: Set[str]) -> float:
        """Calculate community engagement score"""
        score = 0.0
        
        # Comments (community discussion)
        score += min(40, len(comments) * 0.5)
        
        # Code reviews (high-value community contribution)
        score += min(35, len(reviews) * 2)
        
        # Collaborations
        score += min(25, len(collaborators) * 2)
        
        return min(100, score)
    
    def _calculate_inactive_gaps(self, activity_dates: List[datetime]) -> List[int]:
        """Calculate lengths of inactivity periods"""
        if len(activity_dates) < 2:
            return []
        
        gaps = []
        sorted_dates = sorted(activity_dates)
        
        for i in range(len(sorted_dates) - 1):
            gap_days = (sorted_dates[i+1] - sorted_dates[i]).days
            if gap_days > 1:  # Only count gaps > 1 day
                gaps.append(gap_days)
        
        return gaps
    
    def _identify_peak_activity_periods(self, activity_dates: List[datetime]) -> List[Tuple[datetime, int]]:
        """Identify periods of peak activity"""
        if not activity_dates:
            return []
        
        # Group activities by week
        weekly_activity = defaultdict(int)
        for date in activity_dates:
            week_start = date - timedelta(days=date.weekday())
            weekly_activity[week_start] += 1
        
        # Find peaks (weeks with >2x average activity)
        if not weekly_activity:
            return []
        
        avg_activity = statistics.mean(weekly_activity.values())
        threshold = avg_activity * 2
        
        peaks = [(week, count) for week, count in weekly_activity.items() if count >= threshold]
        return sorted(peaks, key=lambda x: x[1], reverse=True)[:3]  # Top 3 peaks
    
    def _calculate_retention_score(
        self,
        contribution_frequency: float,
        contribution_diversity: int,
        community_engagement: float,
        activity_consistency: float,
        collaboration_count: int
    ) -> float:
        """Calculate retention score based on multiple factors"""
        
        # Normalize factors to 0-100 scale
        freq_score = min(100, contribution_frequency * 10)  # 10 contributions/month = 100
        diversity_score = min(100, contribution_diversity * 25)  # 4 types = 100
        collab_score = min(100, collaboration_count * 10)  # 10 collaborators = 100
        
        # Weighted combination
        retention_score = (
            freq_score * self.retention_factor_weights['contribution_frequency'] +
            diversity_score * self.retention_factor_weights['contribution_diversity'] +
            community_engagement * self.retention_factor_weights['community_engagement'] +
            activity_consistency * self.retention_factor_weights['activity_consistency'] +
            collab_score * self.retention_factor_weights['collaboration']
        )
        
        return min(100, max(0, retention_score))
    
    def _predict_return_likelihood(
        self,
        retention_score: float,
        days_since_last_activity: int,
        contribution_frequency: float
    ) -> bool:
        """Predict likelihood of contributor returning"""
        
        # High retention score and recent activity = likely to return
        if retention_score >= 70 and days_since_last_activity <= 30:
            return True
        
        # Very high retention score can overcome longer inactivity
        if retention_score >= 85 and days_since_last_activity <= 90:
            return True
        
        # Low frequency contributors are less likely to return
        if contribution_frequency < 0.5 and days_since_last_activity > 60:
            return False
        
        return False
    
    def _identify_retention_factors(
        self,
        contribution_frequency: float,
        contribution_diversity: int,
        community_engagement: float,
        activity_consistency: float,
        days_since_last_activity: int,
        total_contributions: int
    ) -> Tuple[List[str], List[str]]:
        """Identify factors that support retention and cause churn"""
        
        retention_factors = []
        churn_factors = []
        
        # Retention factors
        if contribution_frequency >= 2.0:
            retention_factors.append("High contribution frequency")
        if contribution_diversity >= 3:
            retention_factors.append("Diverse contribution types")
        if community_engagement >= 60:
            retention_factors.append("Strong community engagement")
        if activity_consistency >= 70:
            retention_factors.append("Consistent activity pattern")
        if total_contributions >= 20:
            retention_factors.append("Substantial contribution history")
        
        # Churn factors
        if days_since_last_activity > 60:
            churn_factors.append("Long period of inactivity")
        if contribution_frequency < 0.5:
            churn_factors.append("Low contribution frequency")
        if contribution_diversity <= 1:
            churn_factors.append("Limited contribution types")
        if community_engagement < 30:
            churn_factors.append("Low community engagement")
        if activity_consistency < 40:
            churn_factors.append("Inconsistent activity")
        
        return retention_factors, churn_factors
    
    def _predict_churn_timing(self, churn_risk_score: float, days_since_last_activity: int) -> int:
        """Predict when churn is likely to occur"""
        
        if churn_risk_score >= 80:
            return 1  # Likely within 1 month
        elif churn_risk_score >= 60:
            return 3  # Likely within 3 months
        elif churn_risk_score >= 40:
            return 6  # Likely within 6 months
        else:
            return 12  # Low risk, possibly within 12 months
    
    def _perform_cohort_analysis(self, retention_profiles: List[ContributorRetention]) -> List[CohortAnalysis]:
        """Perform cohort analysis based on first contribution month"""
        
        # Group contributors by cohort month
        cohorts = defaultdict(list)
        for profile in retention_profiles:
            cohort_month = profile.first_contribution_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            cohorts[cohort_month].append(profile)
        
        # Analyze each cohort
        cohort_analyses = []
        for cohort_month, members in cohorts.items():
            if len(members) < 3:  # Skip very small cohorts
                continue
            
            analysis = self._analyze_cohort(cohort_month, members)
            cohort_analyses.append(analysis)
        
        # Sort by cohort month (most recent first)
        cohort_analyses.sort(key=lambda x: x.cohort_month, reverse=True)
        
        # Keep only recent cohorts
        return cohort_analyses[:self.cohort_analysis_months]
    
    def _analyze_cohort(self, cohort_month: datetime, members: List[ContributorRetention]) -> CohortAnalysis:
        """Analyze a specific cohort"""
        
        cohort_size = len(members)
        
        # Calculate retention rates at different time points
        retention_rates = {}
        for window_days in self.retention_windows:
            retained_count = self._count_retained_members(members, window_days)
            retention_rates[f'retention_day_{window_days}'] = (retained_count / cohort_size) * 100
        
        # Calculate cohort characteristics
        avg_contributions = statistics.mean([m.total_contributions for m in members])
        avg_diversity = statistics.mean([m.contribution_diversity for m in members])
        avg_collaboration = statistics.mean([m.collaboration_count for m in members])
        avg_engagement = statistics.mean([m.community_engagement for m in members])
        
        # Calculate diversity and collaboration scores
        diversity_score = min(100, avg_diversity * 25)
        collaboration_score = min(100, avg_collaboration * 10)
        
        # Predict long-term retention
        long_term_retention = self._predict_cohort_retention(members)
        
        # Calculate average churn risk
        avg_churn_risk = statistics.mean([m.churn_risk_score for m in members])
        
        # Monthly activity analysis
        monthly_activity = self._analyze_monthly_cohort_activity(members, cohort_month)
        
        return CohortAnalysis(
            cohort_month=cohort_month,
            cohort_size=cohort_size,
            retention_day_7=retention_rates.get('retention_day_7', 0.0),
            retention_day_30=retention_rates.get('retention_day_30', 0.0),
            retention_day_90=retention_rates.get('retention_day_90', 0.0),
            retention_day_180=retention_rates.get('retention_day_180', 0.0),
            retention_day_365=retention_rates.get('retention_day_365', 0.0),
            avg_contributions_per_member=avg_contributions,
            contribution_diversity_score=diversity_score,
            collaboration_score=collaboration_score,
            community_engagement_score=avg_engagement,
            predicted_long_term_retention=long_term_retention,
            churn_risk_score=avg_churn_risk,
            monthly_activity=monthly_activity
        )
    
    def _count_retained_members(self, members: List[ContributorRetention], days: int) -> int:
        """Count members retained for specified number of days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        retained = 0
        
        for member in members:
            if member.last_activity_date and member.last_activity_date >= cutoff_date:
                retained += 1
        
        return retained
    
    def _predict_cohort_retention(self, members: List[ContributorRetention]) -> float:
        """Predict long-term retention for a cohort"""
        
        # Factors that predict long-term retention
        high_freq_contributors = len([m for m in members if m.contribution_frequency >= 1.0])
        diverse_contributors = len([m for m in members if m.contribution_diversity >= 2])
        engaged_contributors = len([m for m in members if m.community_engagement >= 50])
        
        # Calculate prediction based on cohort characteristics
        cohort_strength = (
            (high_freq_contributors / len(members)) * 0.4 +
            (diverse_contributors / len(members)) * 0.3 +
            (engaged_contributors / len(members)) * 0.3
        )
        
        return cohort_strength * 100
    
    def _analyze_monthly_cohort_activity(
        self, 
        members: List[ContributorRetention], 
        cohort_month: datetime
    ) -> Dict[int, int]:
        """Analyze monthly activity for cohort"""
        
        monthly_activity = {}
        current_date = datetime.now()
        
        # Calculate months since cohort start
        months_since_cohort = ((current_date.year - cohort_month.year) * 12 + 
                             (current_date.month - cohort_month.month))
        
        for month_offset in range(min(months_since_cohort + 1, 12)):  # Analyze up to 12 months
            month_start = cohort_month + timedelta(days=month_offset * 30)
            month_end = month_start + timedelta(days=30)
            
            active_members = 0
            for member in members:
                if (member.first_contribution_date <= month_end and 
                    member.last_activity_date and 
                    member.last_activity_date >= month_start):
                    active_members += 1
            
            monthly_activity[month_offset] = active_members
        
        return monthly_activity
    
    def _calculate_retention_metrics(
        self, 
        retention_profiles: List[ContributorRetention], 
        cohort_analyses: List[CohortAnalysis]
    ) -> RetentionMetrics:
        """Calculate aggregate retention metrics"""
        
        total_contributors = len(retention_profiles)
        if total_contributors == 0:
            return RetentionMetrics(timestamp=datetime.now(), total_contributors_analyzed=0)
        
        # Overall retention rates
        retention_rates = {}
        for window_days in self.retention_windows:
            retained_count = self._count_retained_members(retention_profiles, window_days)
            retention_rates[f'retention_day_{window_days}'] = (retained_count / total_contributors) * 100
        
        # Churn metrics
        at_risk_count = len([p for p in retention_profiles if p.churn_risk_score >= 60])
        predicted_churn_30d = len([p for p in retention_profiles if p.predicted_churn_months <= 1])
        
        # Quality metrics
        avg_retention_period = statistics.mean([p.retention_period_days for p in retention_profiles])
        avg_contribution_freq = statistics.mean([p.contribution_frequency for p in retention_profiles])
        avg_consistency = statistics.mean([p.activity_consistency_score for p in retention_profiles])
        
        # Identify best and worst performing cohorts
        best_cohort = None
        worst_cohort = None
        
        if cohort_analyses:
            best_cohort = max(cohort_analyses, key=lambda x: x.retention_day_90)
            worst_cohort = min(cohort_analyses, key=lambda x: x.retention_day_90)
        
        # Top retention factors (correlation analysis)
        retention_factors = []
        for profile in retention_profiles:
            retention_factors.extend(profile.retention_factors)
        
        factor_counts = Counter(retention_factors)
        top_factors = factor_counts.most_common(5)
        
        # Generate recommendations
        recommendations = self._generate_retention_recommendations(retention_profiles, cohort_analyses)
        
        # At-risk contributors
        at_risk_contributors = [p.login for p in retention_profiles if p.churn_risk_score >= 70]
        
        return RetentionMetrics(
            timestamp=datetime.now(),
            total_contributors_analyzed=total_contributors,
            retention_rate_day_7=retention_rates.get('retention_day_7', 0.0),
            retention_rate_day_30=retention_rates.get('retention_day_30', 0.0),
            retention_rate_day_90=retention_rates.get('retention_day_90', 0.0),
            retention_rate_day_365=retention_rates.get('retention_day_365', 0.0),
            monthly_churn_rate=(at_risk_count / total_contributors) * 100,
            predicted_churn_next_30_days=predicted_churn_30d,
            high_risk_contributors=at_risk_count,
            avg_retention_period_days=avg_retention_period,
            avg_contribution_frequency=avg_contribution_freq,
            activity_consistency_score=avg_consistency,
            recent_cohorts=cohort_analyses[:6],  # Recent 6 months
            best_performing_cohort=best_cohort,
            worst_performing_cohort=worst_cohort,
            top_retention_factors=top_factors,
            retention_recommendations=recommendations,
            at_risk_contributors=at_risk_contributors
        )
    
    def _generate_retention_recommendations(
        self, 
        retention_profiles: List[ContributorRetention], 
        cohort_analyses: List[CohortAnalysis]
    ) -> List[str]:
        """Generate actionable retention recommendations"""
        
        recommendations = []
        
        # Analyze overall retention patterns
        if retention_profiles:
            low_freq_count = len([p for p in retention_profiles if p.contribution_frequency < 0.5])
            if low_freq_count > len(retention_profiles) * 0.3:
                recommendations.append("Implement programs to increase contribution frequency")
            
            low_diversity_count = len([p for p in retention_profiles if p.contribution_diversity <= 1])
            if low_diversity_count > len(retention_profiles) * 0.4:
                recommendations.append("Encourage contribution diversity through mentorship programs")
            
            low_engagement_count = len([p for p in retention_profiles if p.community_engagement < 30])
            if low_engagement_count > len(retention_profiles) * 0.5:
                recommendations.append("Focus on community engagement and collaboration opportunities")
        
        # Analyze cohort performance
        if cohort_analyses:
            recent_cohorts = [c for c in cohort_analyses if c.cohort_month >= datetime.now() - timedelta(days=180)]
            if recent_cohorts:
                avg_recent_retention = statistics.mean([c.retention_day_30 for c in recent_cohorts])
                if avg_recent_retention < 50:
                    recommendations.append("Improve new contributor onboarding and early engagement")
        
        # Specific risk-based recommendations
        at_risk_high = [p for p in retention_profiles if p.churn_risk_score >= 80]
        if len(at_risk_high) > 0:
            recommendations.append(f"Implement immediate outreach for {len(at_risk_high)} high-risk contributors")
        
        # Positive reinforcement recommendations
        high_performers = [p for p in retention_profiles if p.retention_score >= 80]
        if len(high_performers) > 0:
            recommendations.append("Recognize and retain high-performing contributors")
        
        return recommendations
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            return None
    
    def get_contributor_retention_profile(self, login: str) -> Optional[ContributorRetention]:
        """Get detailed retention profile for a specific contributor"""
        return self.contributor_data.get(login)
    
    def identify_retention_opportunities(self, limit: int = 10) -> List[ContributorRetention]:
        """Identify contributors with high retention potential who need engagement"""
        
        opportunities = []
        for profile in self.contributor_data.values():
            # Look for contributors who:
            # 1. Have good potential (diverse contributions, some engagement)
            # 2. Are at risk (low recent activity, medium retention score)
            # 3. Could be saved with intervention
            
            if (profile.retention_score >= 40 and profile.retention_score <= 70 and 
                profile.contribution_diversity >= 2 and 
                not profile.is_retained):
                opportunities.append(profile)
        
        # Sort by retention potential (higher score = more potential)
        return sorted(opportunities, key=lambda x: x.retention_score, reverse=True)[:limit]
    
    def get_retention_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive retention summary report"""
        
        if not self.retention_history:
            return {"error": "No retention data available"}
        
        latest_metrics = self.retention_history[-1]
        
        # Trend analysis
        trends = {}
        if len(self.retention_history) >= 2:
            previous = self.retention_history[-2]
            trends = {
                "retention_30d_change": latest_metrics.retention_rate_day_30 - previous.retention_rate_day_30,
                "churn_rate_change": latest_metrics.monthly_churn_rate - previous.monthly_churn_rate,
                "at_risk_change": latest_metrics.high_risk_contributors - previous.high_risk_contributors
            }
        
        # Cohort insights
        cohort_insights = {}
        if latest_metrics.recent_cohorts:
            best_cohort = latest_metrics.recent_cohorts[0]  # Most recent
            cohort_insights = {
                "best_cohort_month": best_cohort.cohort_month.strftime("%Y-%m"),
                "best_cohort_retention_30d": best_cohort.retention_day_30,
                "recent_cohort_count": len(latest_metrics.recent_cohorts)
            }
        
        # Top retention factors
        top_factors = latest_metrics.top_retention_factors[:5]
        
        return {
            "overall_retention": {
                "day_7": latest_metrics.retention_rate_day_7,
                "day_30": latest_metrics.retention_rate_day_30,
                "day_90": latest_metrics.retention_rate_day_90,
                "day_365": latest_metrics.retention_rate_day_365
            },
            "churn_metrics": {
                "monthly_churn_rate": latest_metrics.monthly_churn_rate,
                "predicted_churn_30d": latest_metrics.predicted_churn_next_30_days,
                "high_risk_contributors": latest_metrics.high_risk_contributors
            },
            "retention_quality": {
                "avg_retention_period_days": latest_metrics.avg_retention_period_days,
                "avg_contribution_frequency": latest_metrics.avg_contribution_frequency,
                "activity_consistency": latest_metrics.activity_consistency_score
            },
            "trends": trends,
            "cohort_insights": cohort_insights,
            "top_retention_factors": [factor for factor, _ in top_factors],
            "priority_actions": latest_metrics.retention_recommendations[:5],
            "at_risk_contributors_count": len(latest_metrics.at_risk_contributors)
        }