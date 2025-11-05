"""
Data Source Manager

Handles data collection from various sources including GitHub, Google Analytics,
custom APIs, and databases.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import pandas as pd


@dataclass
class DataSource:
    """Configuration for a data source"""
    name: str
    type: str  # github, analytics, api, database
    enabled: bool
    config: Dict[str, Any]
    rate_limit: Optional[int] = None
    last_accessed: Optional[datetime] = None


class DataSourceManager:
    """Manages data collection from multiple sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._sources: Dict[str, DataSource] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Initialize configured sources
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize configured data sources"""
        sources_config = self.config.get('sources', {})
        
        for source_name, source_config in sources_config.items():
            if source_config.get('enabled', False):
                self._sources[source_name] = DataSource(
                    name=source_name,
                    type=source_config.get('type', 'api'),
                    enabled=source_config.get('enabled', True),
                    config=source_config,
                    rate_limit=source_config.get('rate_limit')
                )
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    async def collect_data(self, sources: List[str], period: str, 
                          custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect data from specified sources
        
        Args:
            sources: List of source names to collect from
            period: Time period for data collection
            custom_params: Additional parameters for data collection
            
        Returns:
            Dictionary containing collected data from all sources
        """
        if not self._session:
            async with self:
                return await self._collect_data_sync(sources, period, custom_params)
        else:
            return await self._collect_data_sync(sources, period, custom_params)
    
    async def _collect_data_sync(self, sources: List[str], period: str, 
                                custom_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous implementation of data collection"""
        collected_data = {}
        date_range = self._calculate_date_range(period)
        
        # Create tasks for concurrent data collection
        tasks = []
        for source_name in sources:
            if source_name in self._sources:
                source = self._sources[source_name]
                task = asyncio.create_task(
                    self._collect_from_source(source, date_range, custom_params)
                )
                tasks.append((source_name, task))
        
        # Wait for all tasks to complete
        for source_name, task in tasks:
            try:
                data = await task
                collected_data[source_name] = data
                self.logger.info(f"Successfully collected data from {source_name}")
            except Exception as e:
                self.logger.error(f"Failed to collect data from {source_name}: {e}")
                collected_data[source_name] = {"error": str(e), "records": []}
        
        return collected_data
    
    async def _collect_from_source(self, source: DataSource, date_range: Dict[str, datetime],
                                  custom_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect data from a specific source"""
        source.last_accessed = datetime.utcnow()
        
        if source.type == 'github':
            return await self._collect_github_data(source, date_range, custom_params)
        elif source.type == 'api':
            return await self._collect_api_data(source, date_range, custom_params)
        elif source.type == 'analytics':
            return await self._collect_analytics_data(source, date_range, custom_params)
        elif source.type == 'database':
            return await self._collect_database_data(source, date_range, custom_params)
        else:
            raise ValueError(f"Unknown source type: {source.type}")
    
    async def _collect_github_data(self, source: DataSource, date_range: Dict[str, datetime],
                                  custom_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect data from GitHub"""
        token = source.config.get('token')
        org = source.config.get('organization')
        
        if not token or not org:
            raise ValueError("GitHub token and organization are required")
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Collect repository data
        repos_data = await self._github_request(
            f"https://api.github.com/orgs/{org}/repos", 
            headers
        )
        
        # Collect contribution data
        contributions_data = await self._collect_github_contributions(
            org, headers, date_range
        )
        
        return {
            "source": "github",
            "organization": org,
            "date_range": {
                "start": date_range["start"].isoformat(),
                "end": date_range["end"].isoformat()
            },
            "repositories": repos_data,
            "contributions": contributions_data,
            "records": self._process_github_records(repos_data, contributions_data)
        }
    
    async def _collect_github_contributions(self, org: str, headers: Dict[str, str],
                                          date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Collect GitHub contribution statistics"""
        # This is a simplified example - implement actual GitHub API calls
        end_date = date_range["end"]
        start_date = date_range["start"]
        
        # Get commits in the time period
        commits_url = f"https://api.github.com/search/commits"
        params = {
            'q': f'repo:{org} committer-date:{start_date.strftime("%Y-%m-%d")}..{end_date.strftime("%Y-%m-%d")}'
        }
        
        try:
            commits_data = await self._github_request(commits_url, headers, params)
            return {
                "total_commits": commits_data.get("total_count", 0),
                "committers": self._process_committers(commits_data.get("items", [])),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        except Exception as e:
            self.logger.warning(f"Could not collect commit data: {e}")
            return {"total_commits": 0, "committers": []}
    
    async def _github_request(self, url: str, headers: Dict[str, str], 
                             params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a request to GitHub API"""
        if not self._session:
            raise RuntimeError("HTTP session not initialized")
        
        async with self._session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise aiohttp.ClientError(f"GitHub API error: {response.status}")
    
    def _process_committers(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process commit data to extract committer statistics"""
        committers = {}
        for commit in commits:
            author = commit.get("committer", {})
            login = author.get("login", "unknown")
            if login not in committers:
                committers[login] = {
                    "login": login,
                    "commits": 0,
                    "email": author.get("email"),
                    "name": author.get("name")
                }
            committers[login]["commits"] += 1
        
        return list(committers.values())
    
    def _process_github_records(self, repos_data: List[Dict], contributions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process GitHub data into standardized records"""
        records = []
        
        # Add repository records
        for repo in repos_data:
            records.append({
                "type": "repository",
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "open_issues": repo.get("open_issues_count", 0)
            })
        
        # Add contribution records
        for committer in contributions.get("committers", []):
            records.append({
                "type": "contributor",
                "login": committer.get("login"),
                "commits": committer.get("commits", 0),
                "email": committer.get("email"),
                "name": committer.get("name")
            })
        
        return records
    
    async def _collect_api_data(self, source: DataSource, date_range: Dict[str, datetime],
                               custom_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect data from custom API"""
        endpoint = source.config.get('endpoint')
        api_key = source.config.get('api_key')
        
        if not endpoint:
            raise ValueError("API endpoint is required")
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        params = {
            'start_date': date_range["start"].isoformat(),
            'end_date': date_range["end"].isoformat()
        }
        
        if custom_params:
            params.update(custom_params)
        
        async with self._session.get(endpoint, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "source": "api",
                    "endpoint": endpoint,
                    "date_range": {
                        "start": date_range["start"].isoformat(),
                        "end": date_range["end"].isoformat()
                    },
                    "data": data,
                    "records": self._process_api_records(data)
                }
            else:
                raise aiohttp.ClientError(f"API request failed: {response.status}")
    
    def _process_api_records(self, data: Any) -> List[Dict[str, Any]]:
        """Process API data into standardized records"""
        if isinstance(data, list):
            return [{"raw": item, "type": "api_record"} for item in data]
        elif isinstance(data, dict):
            return [{"raw": data, "type": "api_record"}]
        else:
            return [{"raw": str(data), "type": "api_record"}]
    
    async def _collect_analytics_data(self, source: DataSource, date_range: Dict[str, datetime],
                                     custom_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect analytics data (placeholder for Google Analytics, etc.)"""
        # This would integrate with actual analytics APIs
        # For now, return mock data
        
        return {
            "source": "analytics",
            "provider": source.config.get('provider', 'unknown'),
            "date_range": {
                "start": date_range["start"].isoformat(),
                "end": date_range["end"].isoformat()
            },
            "metrics": {
                "pageviews": 10000,
                "sessions": 2500,
                "users": 1800,
                "bounce_rate": 0.35
            },
            "records": [
                {
                    "type": "analytics_summary",
                    "pageviews": 10000,
                    "sessions": 2500,
                    "users": 1800,
                    "bounce_rate": 0.35
                }
            ]
        }
    
    async def _collect_database_data(self, source: DataSource, date_range: Dict[str, datetime],
                                    custom_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect data from database"""
        # This would integrate with SQL databases
        # For now, return mock data
        
        return {
            "source": "database",
            "connection": source.config.get('connection_string'),
            "date_range": {
                "start": date_range["start"].isoformat(),
                "end": date_range["end"].isoformat()
            },
            "query": custom_params.get('query') if custom_params else "SELECT * FROM metrics",
            "records": [
                {"type": "database_record", "id": 1, "value": 100},
                {"type": "database_record", "id": 2, "value": 200}
            ]
        }
    
    def _calculate_date_range(self, period: str) -> Dict[str, datetime]:
        """Calculate date range based on period"""
        end_date = datetime.utcnow()
        
        if period == "daily":
            start_date = end_date - timedelta(days=1)
        elif period == "weekly":
            start_date = end_date - timedelta(weeks=1)
        elif period == "monthly":
            start_date = end_date - timedelta(days=30)
        elif period == "yearly":
            start_date = end_date - timedelta(days=365)
        else:
            # Custom period
            start_date = end_date - timedelta(days=1)
        
        return {"start": start_date, "end": end_date}
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured sources"""
        status = {}
        for name, source in self._sources.items():
            status[name] = {
                "enabled": source.enabled,
                "type": source.type,
                "last_accessed": source.last_accessed.isoformat() if source.last_accessed else None,
                "rate_limit": source.rate_limit,
                "config_keys": list(source.config.keys())
            }
        return status