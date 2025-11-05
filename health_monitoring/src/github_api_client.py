"""
GitHub API Client for Repository Health Monitoring

This module provides rate-limit aware GitHub API integration for collecting
repository metrics including commits, stars, forks, issues, and pull requests.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError


@dataclass
class RateLimitInfo:
    """Rate limit information from GitHub API"""
    remaining: int
    limit: int
    reset_time: int
    used: int
    
    @property
    def reset_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.reset_time)
    
    @property
    def time_until_reset(self) -> float:
        return max(0, (self.reset_datetime - datetime.now()).total_seconds())


@dataclass
class RepositoryMetrics:
    """Repository metrics data structure"""
    repo_owner: str
    repo_name: str
    timestamp: datetime
    
    # Basic stats
    stars: int
    forks: int
    watchers: int
    size: int
    
    # Activity metrics
    commits_today: int
    commits_this_week: int
    commits_this_month: int
    
    # Issues and PRs
    open_issues: int
    closed_issues: int
    open_prs: int
    closed_prs: int
    merged_prs: int
    
    # Contributors
    total_contributors: int
    new_contributors_today: int
    new_contributors_week: int
    new_contributors_month: int
    
    # Health indicators
    issue_response_time_avg: float  # hours
    pr_merge_time_avg: float  # hours
    issue_closure_rate: float  # percentage
    
    # Community metrics
    discussions_count: int
    releases_count: int
    languages: Dict[str, int]  # language distribution
    
    # Forks analysis
    forks_active: int  # forks with recent activity
    forks_trending: List[str]  # forks with significant activity


class GitHubAPIClient:
    """
    Rate-limit aware GitHub API client for repository health monitoring.
    
    Features:
    - Automatic rate limit handling with backoff
    - Caching to reduce API calls
    - Batch operations for efficiency
    - Comprehensive error handling
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, rate_limit_buffer: int = 100):
        """
        Initialize the GitHub API client.
        
        Args:
            token: GitHub personal access token
            rate_limit_buffer: Minimum requests to keep in reserve
        """
        self.token = token
        self.rate_limit_buffer = rate_limit_buffer
        self.session: Optional[ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self._rate_limit_info: Optional[RateLimitInfo] = None
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Caching
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = 300  # 5 minutes default cache TTL
        
        # Metrics collection
        self._requests_made = 0
        self._requests_cached = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
        
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=30)
            self.session = ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Health-Monitor-Bot/1.0"
                }
            )
            
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache:
            return False
        _, timestamp = self._cache[key]
        return (datetime.now() - timestamp).total_seconds() < self._cache_ttl
    
    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for request"""
        params_str = json.dumps(params, sort_keys=True) if params else ""
        return f"{endpoint}:{params_str}"
    
    async def _handle_rate_limit(self, response_headers: Dict = None):
        """Handle rate limiting based on response headers"""
        if response_headers:
            remaining = int(response_headers.get('X-RateLimit-Remaining', 5000))
            limit = int(response_headers.get('X-RateLimit-Limit', 5000))
            reset = int(response_headers.get('X-RateLimit-Reset', 0))
            used = int(response_headers.get('X-RateLimit-Used', 0))
            
            self._rate_limit_info = RateLimitInfo(
                remaining=remaining,
                limit=limit,
                reset_time=reset,
                used=used
            )
            
            # If we're close to the limit, wait
            if remaining <= self.rate_limit_buffer:
                wait_time = self._rate_limit_info.time_until_reset + 1
                self.logger.warning(f"Rate limit low ({remaining}), waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        else:
            # Respect minimum interval between requests
            time_since_last = time.time() - self._last_request_time
            if time_since_last < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - time_since_last)
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict = None,
        method: str = "GET",
        cache_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a rate-limited API request with caching"""
        await self._ensure_session()
        
        # Check cache first
        if cache_key and self._is_cache_valid(cache_key):
            self._requests_cached += 1
            self.logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key][0]
        
        # Rate limit handling
        await self._handle_rate_limit()
        
        # Make request
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            self.logger.debug(f"Making request to {url}")
            async with self.session.request(method, url, params=params) as response:
                # Update rate limit info from headers
                await self._handle_rate_limit(response.headers)
                
                if response.status == 429:
                    # Rate limited, wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params, method, cache_key)
                
                if response.status == 403:
                    # Forbidden - might be rate limit or permissions
                    error_data = await response.json()
                    if "rate limit" in error_data.get("message", "").lower():
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        wait_time = max(60, (datetime.fromtimestamp(reset_time) - datetime.now()).total_seconds())
                        self.logger.warning(f"Rate limit exceeded, waiting {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(endpoint, params, method, cache_key)
                    else:
                        raise ClientError(f"Access forbidden: {error_data}")
                
                if not response.ok:
                    response.raise_for_status()
                
                data = await response.json()
                
                # Cache the response
                if cache_key:
                    self._cache[cache_key] = (data, datetime.now())
                
                self._requests_made += 1
                return data
                
        except ClientError as e:
            self.logger.error(f"Request failed: {e}")
            raise
    
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get basic repository information"""
        cache_key = self._get_cache_key(f"/repos/{owner}/{repo}")
        return await self._make_request(
            f"/repos/{owner}/{repo}",
            cache_key=cache_key
        )
    
    async def get_repository_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository statistics"""
        cache_key = self._get_cache_key(f"/repos/{owner}/{repo}/stats")
        return await self._make_request(
            f"/repos/{owner}/{repo}/stats",
            cache_key=cache_key
        )
    
    async def get_contributors(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository contributors"""
        cache_key = self._get_cache_key(f"/repos/{owner}/{repo}/contributors")
        return await self._make_request(
            f"/repos/{owner}/{repo}/contributors",
            cache_key=cache_key
        )
    
    async def get_commits(
        self,
        owner: str,
        repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get repository commits"""
        params = {"per_page": per_page}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
            
        return await self._make_request(
            f"/repos/{owner}/{repo}/commits",
            params=params
        )
    
    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        since: Optional[datetime] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get repository issues"""
        params = {
            "state": state,
            "per_page": per_page
        }
        if since:
            params["since"] = since.isoformat()
            
        return await self._make_request(
            f"/repos/{owner}/{repo}/issues",
            params=params
        )
    
    async def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get repository pull requests"""
        params = {
            "state": state,
            "per_page": per_page
        }
            
        return await self._make_request(
            f"/repos/{owner}/{repo}/pulls",
            params=params
        )
    
    async def get_forks(self, owner: str, repo: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get repository forks"""
        return await self._make_request(
            f"/repos/{owner}/{repo}/forks",
            params={"per_page": per_page}
        )
    
    async def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository language breakdown"""
        cache_key = self._get_cache_key(f"/repos/{owner}/{repo}/languages")
        return await self._make_request(
            f"/repos/{owner}/{repo}/languages",
            cache_key=cache_key
        )
    
    async def get_releases(self, owner: str, repo: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get repository releases"""
        return await self._make_request(
            f"/repos/{owner}/{repo}/releases",
            params={"per_page": per_page}
        )
    
    async def collect_repository_metrics(self, owner: str, repo: str) -> RepositoryMetrics:
        """
        Collect comprehensive repository metrics for health monitoring.
        
        This method aggregates data from multiple API endpoints to build
        a complete picture of repository health.
        """
        self.logger.info(f"Collecting metrics for {owner}/{repo}")
        
        # Parallel data collection for efficiency
        repo_info, contributors, commits, issues, prs, forks, languages = await asyncio.gather(
            self.get_repository_info(owner, repo),
            self.get_contributors(owner, repo),
            self.get_commits(owner, repo, since=datetime.now() - timedelta(days=30)),
            self.get_issues(owner, repo, state="all", since=datetime.now() - timedelta(days=30)),
            self.get_pull_requests(owner, repo, state="all"),
            self.get_forks(owner, repo),
            self.get_languages(owner, repo),
            return_exceptions=True
        )
        
        # Handle potential exceptions
        repo_info = repo_info if not isinstance(repo_info, Exception) else {}
        contributors = contributors if not isinstance(contributors, Exception) else []
        commits = commits if not isinstance(commits, Exception) else []
        issues = issues if not isinstance(issues, Exception) else []
        prs = prs if not isinstance(prs, Exception) else []
        forks = forks if not isinstance(forks, Exception) else []
        languages = languages if not isinstance(languages, Exception) else {}
        
        # Calculate time-based metrics
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        
        # Filter commits by time periods
        commits_today = [c for c in commits if datetime.fromisoformat(c['commit']['committer']['date'].replace('Z', '+00:00')) >= today_start]
        commits_this_week = [c for c in commits if datetime.fromisoformat(c['commit']['committer']['date'].replace('Z', '+00:00')) >= week_start]
        commits_this_month = [c for c in commits if datetime.fromisoformat(c['commit']['committer']['date'].replace('Z', '+00:00')) >= month_start]
        
        # Count issues by state
        open_issues = len([i for i in issues if i.get('state') == 'open' and not i.get('pull_request')])
        closed_issues = len([i for i in issues if i.get('state') == 'closed' and not i.get('pull_request')])
        
        # Count PRs by state
        open_prs = len([pr for pr in prs if pr.get('state') == 'open'])
        closed_prs = len([pr for pr in prs if pr.get('state') == 'closed' and not pr.get('merged_at')])
        merged_prs = len([pr for pr in prs if pr.get('merged_at')])
        
        # Calculate health indicators
        issue_response_time = await self._calculate_issue_response_time(issues)
        pr_merge_time = await self._calculate_pr_merge_time(prs)
        issue_closure_rate = (closed_issues / max(1, open_issues + closed_issues)) * 100
        
        # Count new contributors
        new_contributors_today = len([c for c in commits_today if c['commit']['author']['email'] not in [prev['commit']['author']['email'] for prev in commits if prev != c]])
        new_contributors_week = len([c for c in commits_this_week if c['commit']['author']['email'] not in [prev['commit']['author']['email'] for prev in commits if prev != c]])
        new_contributors_month = len([c for c in commits_this_month if c['commit']['author']['email'] not in [prev['commit']['author']['email'] for prev in commits if prev != c]])
        
        return RepositoryMetrics(
            repo_owner=owner,
            repo_name=repo,
            timestamp=now,
            stars=repo_info.get('stargazers_count', 0),
            forks=repo_info.get('forks_count', 0),
            watchers=repo_info.get('watchers_count', 0),
            size=repo_info.get('size', 0),
            commits_today=len(commits_today),
            commits_this_week=len(commits_this_week),
            commits_this_month=len(commits_this_month),
            open_issues=open_issues,
            closed_issues=closed_issues,
            open_prs=open_prs,
            closed_prs=closed_prs,
            merged_prs=merged_prs,
            total_contributors=len(contributors),
            new_contributors_today=new_contributors_today,
            new_contributors_week=new_contributors_week,
            new_contributors_month=new_contributors_month,
            issue_response_time_avg=issue_response_time,
            pr_merge_time_avg=pr_merge_time,
            issue_closure_rate=issue_closure_rate,
            discussions_count=0,  # Would need separate API call
            releases_count=len(await self.get_releases(owner, repo)) if 'Exception' not in str(type(await self.get_releases(owner, repo))) else 0,
            languages=languages,
            forks_active=len([f for f in forks if f.get('pushed_at') and datetime.fromisoformat(f['pushed_at'].replace('Z', '+00:00')) > (now - timedelta(days=30))]),
            forks_trending=[]
        )
    
    async def _calculate_issue_response_time(self, issues: List[Dict]) -> float:
        """Calculate average time to first response on issues"""
        response_times = []
        for issue in issues:
            if issue.get('comments', 0) > 0:
                # Would need to fetch issue comments to get response time
                # For now, return placeholder value
                response_times.append(24.0)  # 24 hours average
        return sum(response_times) / max(1, len(response_times))
    
    async def _calculate_pr_merge_time(self, prs: List[Dict]) -> float:
        """Calculate average time to merge for PRs"""
        merge_times = []
        for pr in prs:
            if pr.get('merged_at'):
                created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                merge_time = (merged - created).total_seconds() / 3600  # hours
                merge_times.append(merge_time)
        return sum(merge_times) / max(1, len(merge_times))
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of API client metrics"""
        return {
            "requests_made": self._requests_made,
            "requests_cached": self._requests_cached,
            "cache_hit_rate": self._requests_cached / max(1, self._requests_made + self._requests_cached),
            "rate_limit_info": self._rate_limit_info.__dict__ if self._rate_limit_info else None
        }