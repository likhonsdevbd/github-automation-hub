"""
GitHub API Integration
=====================

GitHub API client for collecting repository metrics:
- Commits, stars, forks, issues, PRs, contributors
- Rate limiting and caching
- Error handling and retry logic
- Efficient pagination and batching
"""

import time
import logging
from typing import Dict, List, Optional, Any, Iterator, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import requests
from urllib.parse import urlencode

from ..core.rate_limiter import RateLimiter
from ..core.error_handler import ErrorHandler, with_error_handling
from ..core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class RepositoryInfo:
    """Repository information structure"""
    owner: str
    name: str
    full_name: str
    private: bool
    fork: bool
    created_at: datetime
    updated_at: datetime
    default_branch: str
    languages: Dict[str, int]
    topics: List[str]
    description: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    open_issues_count: int = 0
    watchers_count: int = 0
    stargazers_count: int = 0
    forks_count: int = 0


@dataclass
class CommitInfo:
    """Commit information structure"""
    sha: str
    author_login: str
    author_name: str
    author_email: str
    date: datetime
    message: str
    files_changed: int
    additions: int
    deletions: int
    repository: str
    branch: str = ""


@dataclass
class ContributorInfo:
    """Contributor information structure"""
    login: str
    id: int
    name: str
    email: str
    contributions: int
    location: Optional[str] = None
    company: Optional[str] = None
    followers: int = 0
    following: int = 0


@dataclass
class IssueInfo:
    """Issue information structure"""
    id: int
    number: int
    title: str
    state: str  # "open" or "closed"
    author_login: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    labels: List[str] = None
    assignees: List[str] = None
    milestone: Optional[str] = None


@dataclass
class PRInfo:
    """Pull Request information structure"""
    id: int
    number: int
    title: str
    state: str  # "open", "closed", "merged"
    author_login: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    base_branch: str = ""
    head_branch: str = ""
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits: int = 0
    reviewers: List[str] = None
    review_comments: int = 0


class GitHubAPIClient:
    """
    GitHub API client with comprehensive rate limiting and error handling
    
    Implements the API integration patterns from the growth analytics system:
    - Rate limit awareness and backoff
    - Request caching and deduplication
    - Pagination handling
    - Efficient batching for nested queries
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config = config_manager or ConfigManager()
        self.rate_limiter = RateLimiter({
            'max_retries': self.config.github.max_retries,
            'cache_ttl': self.config.collection.cache_ttl
        })
        self.error_handler = ErrorHandler()
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GrowthMetrics-Collection/1.0',
            'Authorization': f'token {self.config.github.token}'
        })
        
        self.base_url = self.config.github.base_url.rstrip('/')
        self.timeout = self.config.github.timeout
        
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     data: Dict[str, Any] = None) -> requests.Response:
        """Make HTTP request with rate limiting and error handling"""
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            url += f"?{urlencode(params)}"
            
        # Use error handler with retry logic
        def request_func():
            return self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                timeout=self.timeout
            )
            
        response = self.error_handler.handle_request_with_retry(
            request_func, endpoint=endpoint
        )
        
        # Update rate limit stats
        self.rate_limiter.check_rate_limits(dict(response.headers))
        
        return response
        
    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """Get repository information"""
        
        def _get_repo():
            response = self._make_request('GET', f'/repos/{owner}/{repo}')
            data = response.json()
            
            return RepositoryInfo(
                owner=owner,
                name=repo,
                full_name=data['full_name'],
                private=data['private'],
                fork=data['fork'],
                created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
                default_branch=data['default_branch'],
                languages=data.get('languages', {}),
                topics=data.get('topics', []),
                description=data.get('description'),
                homepage=data.get('homepage'),
                license=data.get('license', {}).get('spdx_id') if data.get('license') else None,
                open_issues_count=data['open_issues_count'],
                watchers_count=data['watchers_count'],
                stargazers_count=data['stargazers_count'],
                forks_count=data['forks_count']
            )
            
        return _get_repo()
        
    def get_commits(self, owner: str, repo: str, since: datetime = None, 
                   until: datetime = None, branch: str = None) -> List[CommitInfo]:
        """Get commits for repository"""
        
        def _get_commits():
            commits = []
            page = 1
            per_page = self.config.github.per_page
            
            params = {
                'per_page': per_page,
                'page': page
            }
            
            if since:
                params['since'] = since.isoformat() + 'Z'
            if until:
                params['until'] = until.isoformat() + 'Z'
            if branch:
                params['sha'] = branch
                
            while True:
                params['page'] = page
                
                response = self._make_request('GET', f'/repos/{owner}/{repo}/commits', params)
                commit_data = response.json()
                
                if not commit_data:
                    break
                    
                for commit in commit_data:
                    commits.append(CommitInfo(
                        sha=commit['sha'],
                        author_login=commit['author']['login'] if commit['author'] else '',
                        author_name=commit['commit']['author']['name'],
                        author_email=commit['commit']['author']['email'],
                        date=datetime.fromisoformat(commit['commit']['author']['date'].replace('Z', '+00:00')),
                        message=commit['commit']['message'],
                        files_changed=0,  # Would need additional API call
                        additions=commit['stats']['additions'] if commit['stats'] else 0,
                        deletions=commit['stats']['deletions'] if commit['stats'] else 0,
                        repository=f"{owner}/{repo}",
                        branch=branch or 'main'
                    ))
                    
                # Check if this is the last page
                if len(commit_data) < per_page:
                    break
                    
                page += 1
                
            return commits
            
        return _get_commits()
        
    def get_contributors(self, owner: str, repo: str, 
                        include_anonymous: bool = False) -> List[ContributorInfo]:
        """Get contributors for repository"""
        
        def _get_contributors():
            contributors = []
            page = 1
            per_page = self.config.github.per_page
            
            while True:
                params = {
                    'per_page': per_page,
                    'page': page,
                    'anon': 'true' if include_anonymous else 'false'
                }
                
                response = self._make_request('GET', f'/repos/{owner}/{repo}/contributors', params)
                contrib_data = response.json()
                
                if not contrib_data:
                    break
                    
                for contrib in contrib_data:
                    contributors.append(ContributorInfo(
                        login=contrib['login'] if contrib['login'] else '',
                        id=contrib['id'],
                        name=contrib.get('name', ''),
                        email=contrib.get('email', ''),
                        contributions=contrib['contributions']
                    ))
                    
                if len(contrib_data) < per_page:
                    break
                    
                page += 1
                
            return contributors
            
        return _get_contributors()
        
    def get_stargazers_count(self, owner: str, repo: str) -> int:
        """Get current stargazers count"""
        
        def _get_stars():
            response = self._make_request('GET', f'/repos/{owner}/{repo}')
            data = response.json()
            return data['stargazers_count']
            
        return _get_stars()
        
    def get_forks_count(self, owner: str, repo: str) -> int:
        """Get current forks count"""
        
        def _get_forks():
            response = self._make_request('GET', f'/repos/{owner}/{repo}')
            data = response.json()
            return data['forks_count']
            
        return _get_forks()
        
    def get_issues(self, owner: str, repo: str, state: str = 'all', 
                  since: datetime = None, labels: List[str] = None) -> List[IssueInfo]:
        """Get issues for repository"""
        
        def _get_issues():
            issues = []
            page = 1
            per_page = self.config.github.per_page
            
            params = {
                'per_page': per_page,
                'page': page,
                'state': state
            }
            
            if since:
                params['since'] = since.isoformat() + 'Z'
            if labels:
                params['labels'] = ','.join(labels)
                
            while True:
                params['page'] = page
                
                response = self._make_request('GET', f'/repos/{owner}/{repo}/issues', params)
                issues_data = response.json()
                
                if not issues_data:
                    break
                    
                for issue in issues_data:
                    # Skip pull requests (they appear in issues API)
                    if 'pull_request' in issue:
                        continue
                        
                    issues.append(IssueInfo(
                        id=issue['id'],
                        number=issue['number'],
                        title=issue['title'],
                        state=issue['state'],
                        author_login=issue['user']['login'],
                        created_at=datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(issue['updated_at'].replace('Z', '+00:00')),
                        closed_at=datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00')) 
                                if issue.get('closed_at') else None,
                        labels=[label['name'] for label in issue.get('labels', [])],
                        assignees=[assignee['login'] for assignee in issue.get('assignees', [])],
                        milestone=issue.get('milestone', {}).get('title') if issue.get('milestone') else None
                    ))
                    
                if len(issues_data) < per_page:
                    break
                    
                page += 1
                
            return issues
            
        return _get_issues()
        
    def get_pull_requests(self, owner: str, repo: str, state: str = 'all') -> List[PRInfo]:
        """Get pull requests for repository"""
        
        def _get_prs():
            prs = []
            page = 1
            per_page = self.config.github.per_page
            
            while True:
                params = {
                    'per_page': per_page,
                    'page': page,
                    'state': state
                }
                
                response = self._make_request('GET', f'/repos/{owner}/{repo}/pulls', params)
                prs_data = response.json()
                
                if not prs_data:
                    break
                    
                for pr in prs_data:
                    # Get additional PR details
                    files_response = self._make_request('GET', f'/repos/{owner}/{repo}/pulls/{pr["number"]}/files')
                    commits_response = self._make_request('GET', f'/repos/{owner}/{repo}/pulls/{pr["number"]}/commits')
                    
                    files_data = files_response.json() if files_response.status_code == 200 else []
                    commits_data = commits_response.json() if commits_response.status_code == 200 else []
                    
                    prs.append(PRInfo(
                        id=pr['id'],
                        number=pr['number'],
                        title=pr['title'],
                        state=pr['state'],
                        author_login=pr['user']['login'],
                        created_at=datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00')),
                        closed_at=datetime.fromisoformat(pr['closed_at'].replace('Z', '+00:00')) 
                                if pr.get('closed_at') else None,
                        merged_at=datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00')) 
                                if pr.get('merged_at') else None,
                        base_branch=pr['base']['ref'],
                        head_branch=pr['head']['ref'],
                        additions=pr['additions'],
                        deletions=pr['deletions'],
                        changed_files=len(files_data),
                        commits=len(commits_data),
                        reviewers=[review['user']['login'] for review in pr.get('requested_reviewers', [])]
                    ))
                    
                if len(prs_data) < per_page:
                    break
                    
                page += 1
                
            return prs
            
        return _get_prs()
        
    def get_organization_repos(self, org: str, repo_type: str = 'all') -> List[Dict[str, Any]]:
        """Get repositories for organization"""
        
        def _get_org_repos():
            repos = []
            page = 1
            per_page = self.config.github.per_page
            
            while True:
                params = {
                    'type': repo_type,
                    'per_page': per_page,
                    'page': page,
                    'sort': 'updated',
                    'direction': 'desc'
                }
                
                response = self._make_request('GET', f'/orgs/{org}/repos', params)
                repos_data = response.json()
                
                if not repos_data:
                    break
                    
                repos.extend(repos_data)
                
                if len(repos_data) < per_page:
                    break
                    
                page += 1
                
            return repos
            
        return _get_org_repos()
        
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        
        def _get_rate_limit():
            response = self._make_request('GET', '/rate_limit')
            return response.json()
            
        return _get_rate_limit()
        
    def batch_collect_metrics(self, repositories: List[Tuple[str, str]], 
                            start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Batch collect metrics for multiple repositories"""
        
        results = {}
        
        for owner, repo in repositories:
            logger.info(f"Collecting metrics for {owner}/{repo}")
            
            try:
                repo_metrics = {
                    'repository': f"{owner}/{repo}",
                    'timestamp': datetime.now().isoformat(),
                    'repository_info': None,
                    'commits': [],
                    'contributors': [],
                    'issues': [],
                    'pull_requests': [],
                    'stars_count': 0,
                    'forks_count': 0,
                    'collection_errors': []
                }
                
                # Collect repository info
                try:
                    repo_info = self.get_repository(owner, repo)
                    repo_metrics['repository_info'] = repo_info
                except Exception as e:
                    error_msg = f"Failed to get repository info: {e}"
                    logger.error(error_msg)
                    repo_metrics['collection_errors'].append(error_msg)
                    
                # Collect commits if date range provided
                if start_date and end_date:
                    try:
                        commits = self.get_commits(owner, repo, start_date, end_date)
                        repo_metrics['commits'] = [
                            {
                                'sha': c.sha,
                                'author': c.author_login,
                                'date': c.date.isoformat(),
                                'message': c.message[:100] + '...' if len(c.message) > 100 else c.message
                            } for c in commits
                        ]
                    except Exception as e:
                        error_msg = f"Failed to get commits: {e}"
                        logger.error(error_msg)
                        repo_metrics['collection_errors'].append(error_msg)
                        
                # Collect contributors
                try:
                    contributors = self.get_contributors(owner, repo)
                    repo_metrics['contributors'] = [
                        {
                            'login': c.login,
                            'contributions': c.contributions
                        } for c in contributors
                    ]
                except Exception as e:
                    error_msg = f"Failed to get contributors: {e}"
                    logger.error(error_msg)
                    repo_metrics['collection_errors'].append(error_msg)
                    
                # Collect issues
                try:
                    issues = self.get_issues(owner, repo, since=start_date if start_date else None)
                    repo_metrics['issues'] = [
                        {
                            'number': i.number,
                            'title': i.title,
                            'state': i.state,
                            'created_at': i.created_at.isoformat(),
                            'closed_at': i.closed_at.isoformat() if i.closed_at else None
                        } for i in issues
                    ]
                except Exception as e:
                    error_msg = f"Failed to get issues: {e}"
                    logger.error(error_msg)
                    repo_metrics['collection_errors'].append(error_msg)
                    
                # Collect pull requests
                try:
                    prs = self.get_pull_requests(owner, repo)
                    repo_metrics['pull_requests'] = [
                        {
                            'number': pr.number,
                            'title': pr.title,
                            'state': pr.state,
                            'created_at': pr.created_at.isoformat(),
                            'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                            'additions': pr.additions,
                            'deletions': pr.deletions
                        } for pr in prs
                    ]
                except Exception as e:
                    error_msg = f"Failed to get pull requests: {e}"
                    logger.error(error_msg)
                    repo_metrics['collection_errors'].append(error_msg)
                    
                # Get current counts
                try:
                    repo_metrics['stars_count'] = self.get_stargazers_count(owner, repo)
                    repo_metrics['forks_count'] = self.get_forks_count(owner, repo)
                except Exception as e:
                    error_msg = f"Failed to get counts: {e}"
                    logger.error(error_msg)
                    repo_metrics['collection_errors'].append(error_msg)
                    
                results[f"{owner}/{repo}"] = repo_metrics
                
            except Exception as e:
                error_msg = f"Failed to collect metrics for {owner}/{repo}: {e}"
                logger.error(error_msg)
                results[f"{owner}/{repo}"] = {
                    'repository': f"{owner}/{repo}",
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                
        return results
        
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            'rate_limiter': self.rate_limiter.get_stats(),
            'config': {
                'timeout': self.timeout,
                'per_page': self.config.github.per_page,
                'rate_limit_budget': self.config.github.rate_limit_budget
            }
        }