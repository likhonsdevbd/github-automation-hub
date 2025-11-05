"""
GitHub Client - Secure, authenticated GitHub API client.

Handles all GitHub API interactions with:
- Least privilege token management
- Proper error handling for rate limits and validation errors
- Conditional requests for efficient API usage
- Comprehensive logging for audit trails
"""

import time
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GitHubClient:
    """
    Secure GitHub API client with compliance-first design.
    
    Features:
    - Token-based authentication with minimal scopes
    - Rate limit awareness and proper backoff handling
    - Conditional requests using ETags
    - Comprehensive error handling
    - Audit logging for all operations
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize session with retry strategy
        self.session = requests.Session()
        self._setup_session()
        
        # Token management
        self.token = config.get('token')
        if not self.token:
            raise ValueError("GitHub token is required in configuration")
        
        # Rate limiting headers cache
        self._rate_limit_cache = {}
        
        # ETag cache for conditional requests
        self._etag_cache = {}
        
        self.logger.info("GitHub client initialized")
    
    def _setup_session(self):
        """Configure the requests session with retry strategy."""
        # Configure retry strategy for transient failures
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "PUT", "DELETE"]  # Only retry safe methods
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AutomationHub/1.0.0',
            'X-GitHub-Api-Version': '2022-11-28'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make authenticated API request with proper error handling.
        
        Args:
            method: HTTP method (GET, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            requests.Response: Response object
            
        Raises:
            requests.HTTPError: For HTTP error responses
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Add authentication
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"token {self.token}"
        kwargs['headers'] = headers
        
        # Add ETag for conditional requests (GET only)
        if method == 'GET':
            if endpoint in self._etag_cache:
                headers['If-None-Match'] = self._etag_cache[endpoint]
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            
            response = self.session.request(method, url, **kwargs)
            
            # Cache rate limit headers
            self._cache_rate_limit_headers(response.headers)
            
            # Cache ETag for conditional requests
            if method == 'GET' and response.status_code == 200:
                etag = response.headers.get('ETag')
                if etag:
                    self._etag_cache[endpoint] = etag
            
            # Log response
            self._log_api_call(method, endpoint, response)
            
            # Raise HTTP error for non-2xx responses
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {method} {url} - {str(e)}")
            raise
    
    def follow_user(self, username: str) -> requests.Response:
        """
        Follow a user.
        
        Args:
            username: Target username to follow
            
        Returns:
            requests.Response: Response object
        """
        self.logger.info(f"Attempting to follow {username}")
        
        try:
            response = self._make_request(
                'PUT',
                f"/user/following/{username}",
                data=""  # PUT requests require empty body
            )
            
            self.logger.info(f"Successfully followed {username}")
            return response
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Failed to follow {username}: HTTP {e.response.status_code}")
            return e.response
        except Exception as e:
            self.logger.error(f"Error following {username}: {str(e)}")
            raise
    
    def unfollow_user(self, username: str) -> requests.Response:
        """
        Unfollow a user.
        
        Args:
            username: Target username to unfollow
            
        Returns:
            requests.Response: Response object
        """
        self.logger.info(f"Attempting to unfollow {username}")
        
        try:
            response = self._make_request(
                'DELETE',
                f"/user/following/{username}"
            )
            
            self.logger.info(f"Successfully unfollowed {username}")
            return response
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Failed to unfollow {username}: HTTP {e.response.status_code}")
            return e.response
        except Exception as e:
            self.logger.error(f"Error unfollowing {username}: {str(e)}")
            raise
    
    def get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile data.
        
        Args:
            username: Target username
            
        Returns:
            Dict or None: User data if found
        """
        try:
            response = self._make_request('GET', f"/users/{username}")
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"User {username} not found or inaccessible")
                return None
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"User {username} not found")
                return None
            else:
                self.logger.error(f"Error getting user data for {username}: {e.response.status_code}")
                return None
    
    def check_follow_status(self, username: str) -> bool:
        """
        Check if currently following a user.
        
        Args:
            username: Target username
            
        Returns:
            bool: True if following, False otherwise
        """
        try:
            response = self._make_request('GET', f"/user/following/{username}")
            
            # 204 = following, 404 = not following
            return response.status_code == 204
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                self.logger.error(f"Error checking follow status for {username}: {e.response.status_code}")
                return False
    
    def get_followers_list(self, username: str = None, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of followers.
        
        Args:
            username: Target username (uses authenticated user if None)
            per_page: Number of results per page (max 100)
            
        Returns:
            List[Dict]: List of follower data
        """
        endpoint = "/user/followers" if username is None else f"/users/{username}/followers"
        
        try:
            response = self._make_request('GET', endpoint, params={'per_page': min(per_page, 100)})
            
            if response.status_code == 200:
                followers = response.json()
                self.logger.debug(f"Retrieved {len(followers)} followers")
                return followers
            else:
                self.logger.warning(f"Failed to get followers: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting followers: {str(e)}")
            return []
    
    def get_following_list(self, username: str = None, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of people the user is following.
        
        Args:
            username: Target username (uses authenticated user if None)
            per_page: Number of results per page (max 100)
            
        Returns:
            List[Dict]: List of following data
        """
        endpoint = "/user/following" if username is None else f"/users/{username}/following"
        
        try:
            response = self._make_request('GET', endpoint, params={'per_page': min(per_page, 100)})
            
            if response.status_code == 200:
                following = response.json()
                self.logger.debug(f"Retrieved {len(following)} following")
                return following
            else:
                self.logger.warning(f"Failed to get following: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting following: {str(e)}")
            return []
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dict: Rate limit information
        """
        try:
            response = self._make_request('GET', '/rate_limit')
            
            if response.status_code == 200:
                rate_limit_data = response.json()
                return rate_limit_data.get('resources', {})
            else:
                self.logger.warning(f"Failed to get rate limit status: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting rate limit status: {str(e)}")
            return {}
    
    def get_repository_stats(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get repository statistics (stars, forks, etc.).
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dict or None: Repository statistics
        """
        try:
            response = self._make_request('GET', f"/repos/{owner}/{repo}")
            
            if response.status_code == 200:
                repo_data = response.json()
                stats = {
                    'stars': repo_data.get('stargazers_count', 0),
                    'forks': repo_data.get('forks_count', 0),
                    'watchers': repo_data.get('watchers_count', 0),
                    'open_issues': repo_data.get('open_issues_count', 0),
                    'subscribers_count': repo_data.get('subscribers_count', 0)
                }
                return stats
            else:
                self.logger.warning(f"Repository {owner}/{repo} not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting repository stats for {owner}/{repo}: {str(e)}")
            return None
    
    def get_pull_request_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository pull request analytics.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dict: PR statistics
        """
        try:
            # Get recent PRs
            response = self._make_request(
                'GET', 
                f"/repos/{owner}/{repo}/pulls",
                params={'state': 'all', 'per_page': 100}
            )
            
            if response.status_code == 200:
                prs = response.json()
                
                # Calculate statistics
                total_prs = len(prs)
                merged_prs = len([pr for pr in prs if pr.get('merged_at')])
                open_prs = len([pr for pr in prs if pr.get('state') == 'open'])
                
                # Calculate time to merge
                merge_times = []
                for pr in prs:
                    if pr.get('merged_at') and pr.get('created_at'):
                        try:
                            created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                            merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                            merge_times.append((merged - created).total_seconds() / 86400)  # days
                        except:
                            pass
                
                avg_merge_time = sum(merge_times) / len(merge_times) if merge_times else 0
                
                return {
                    'total_prs': total_prs,
                    'merged_prs': merged_prs,
                    'open_prs': open_prs,
                    'merge_rate': merged_prs / total_prs if total_prs > 0 else 0,
                    'avg_merge_time_days': avg_merge_time
                }
            else:
                self.logger.warning(f"Failed to get PR stats for {owner}/{repo}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting PR stats for {owner}/{repo}: {str(e)}")
            return {}
    
    def _cache_rate_limit_headers(self, headers: Dict[str, str]):
        """Cache rate limit headers for monitoring."""
        self._rate_limit_cache = {
            'limit': headers.get('X-RateLimit-Limit'),
            'remaining': headers.get('X-RateLimit-Remaining'),
            'reset': headers.get('X-RateLimit-Reset'),
            'used': headers.get('X-RateLimit-Used'),
            'retry_after': headers.get('Retry-After')
        }
    
    def _log_api_call(self, method: str, endpoint: str, response: requests.Response):
        """Log API call for audit purposes."""
        status = response.status_code
        rate_limit = self._rate_limit_cache.get('remaining', 'unknown')
        
        self.logger.debug(f"API {method} {endpoint} - Status: {status}, Rate Limit Remaining: {rate_limit}")
        
        # Log warning for rate limit issues
        if status == 429:
            self.logger.warning(f"Rate limit exceeded on {method} {endpoint}")
        elif status == 422:
            self.logger.error(f"Validation error on {method} {endpoint} - potential spam flag")
        elif status == 403:
            self.logger.error(f"Access forbidden on {method} {endpoint}")
    
    def get_current_rate_limit(self) -> Dict[str, Any]:
        """Get current rate limit information."""
        return self._rate_limit_cache.copy()
    
    def validate_token(self) -> bool:
        """
        Validate the GitHub token by making a simple API call.
        
        Returns:
            bool: True if token is valid
        """
        try:
            response = self._make_request('GET', '/user')
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Token validation failed: {str(e)}")
            return False
