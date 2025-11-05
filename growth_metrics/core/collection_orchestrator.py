"""
Daily Metrics Collection Orchestrator
====================================

Orchestrates the daily collection process:
- Coordinates data collection from multiple repositories
- Manages workflow scheduling and execution
- Handles collection errors and retries
- Generates collection reports
- Triggers analytics processing
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.config_manager import ConfigManager
from core.rate_limiter import RateLimiter
from core.error_handler import ErrorHandler
from api.github_client import GitHubAPIClient
from storage.metrics_storage import MetricsStorage
from analytics.growth_analytics import GrowthAnalyticsEngine

logger = logging.getLogger(__name__)


class RepositoryMetrics:
    """Container for repository metrics data"""
    
    def __init__(self, owner: str, name: str):
        self.owner = owner
        self.name = name
        self.full_name = f"{owner}/{name}"
        self.repository_info = None
        self.metrics_data = {}
        self.collection_errors = []
        self.collection_timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'repository': self.full_name,
            'timestamp': self.collection_timestamp.isoformat(),
            'repository_info': self.repository_info.__dict__ if self.repository_info else None,
            'metrics_data': self.metrics_data,
            'collection_errors': self.collection_errors,
            'collection_timestamp': self.collection_timestamp.isoformat()
        }


class DailyMetricsCollector:
    """
    Orchestrates daily metrics collection for multiple repositories
    
    Features:
    - Concurrent collection for multiple repositories
    - Rate limit aware processing
    - Error handling and retry logic
    - Progress tracking and reporting
    - Automatic analytics processing
    """
    
    def __init__(self, config_path: str = None):
        # Initialize configuration
        self.config = ConfigManager(config_path)
        self.config.load_from_file('config/growth_metrics.yaml') if config_path else None
        self.config.load_from_environment()
        
        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            logger.error(f"Configuration errors: {config_errors}")
            raise ValueError(f"Configuration validation failed: {config_errors}")
            
        # Initialize components
        self.github_client = GitHubAPIClient(self.config)
        self.metrics_storage = MetricsStorage(self.config.get_effective_config()['storage'])
        self.analytics_engine = GrowthAnalyticsEngine(self.config.get_effective_config()['analytics'])
        
        # Collection state
        self.repos_to_collect = []
        self.collection_results = {}
        self.collection_errors = []
        
    def setup_collection_targets(self) -> None:
        """Setup repositories to collect metrics for"""
        
        self.repos_to_collect = []
        
        # Add repositories from configuration
        for repo_full_name in self.config.github.repositories:
            if '/' in repo_full_name:
                owner, name = repo_full_name.split('/', 1)
                self.repos_to_collect.append((owner, name))
                
        # Add repositories from organizations
        for org in self.config.github.organizations:
            logger.info(f"Discovering repositories for organization: {org}")
            try:
                org_repos = self.github_client.get_organization_repos(org, 'public')
                
                # Filter repositories based on criteria (e.g., minimum stars, recent activity)
                min_stars = self.config.collection.historical_days  # Use as filter criteria
                filtered_repos = []
                
                for repo in org_repos:
                    if repo['stargazers_count'] >= min_stars and not repo['fork']:
                        filtered_repos.append((repo['owner']['login'], repo['name']))
                        
                logger.info(f"Found {len(filtered_repos)} qualifying repositories for {org}")
                self.repos_to_collect.extend(filtered_repos)
                
            except Exception as e:
                logger.error(f"Failed to get repositories for organization {org}: {e}")
                self.collection_errors.append(f"Organization {org}: {e}")
                
        # Remove duplicates
        self.repos_to_collect = list(set(self.repos_to_collect))
        
        logger.info(f"Setup complete. Will collect metrics for {len(self.repos_to_collect)} repositories")
        
    def collect_repository_metrics(self, owner: str, name: str, 
                                 start_date: datetime = None, end_date: datetime = None) -> RepositoryMetrics:
        """Collect all metrics for a single repository"""
        
        repo_metrics = RepositoryMetrics(owner, name)
        
        try:
            # Set default date range if not provided
            if start_date is None:
                start_date = datetime.now() - timedelta(days=self.config.collection.snapshot_interval)
            if end_date is None:
                end_date = datetime.now()
                
            logger.info(f"Collecting metrics for {repo_metrics.full_name}")
            
            # 1. Repository information
            try:
                repo_info = self.github_client.get_repository(owner, name)
                repo_metrics.repository_info = repo_info
                logger.debug(f"Retrieved repository info for {repo_metrics.full_name}")
            except Exception as e:
                error_msg = f"Failed to get repository info: {e}"
                logger.error(error_msg)
                repo_metrics.collection_errors.append(error_msg)
                
            # 2. Commits (if date range specified)
            if start_date and end_date:
                try:
                    commits = self.github_client.get_commits(owner, name, start_date, end_date)
                    repo_metrics.metrics_data['commits'] = commits
                    logger.debug(f"Collected {len(commits)} commits for {repo_metrics.full_name}")
                except Exception as e:
                    error_msg = f"Failed to get commits: {e}"
                    logger.error(error_msg)
                    repo_metrics.collection_errors.append(error_msg)
                    
            # 3. Contributors
            try:
                contributors = self.github_client.get_contributors(owner, name)
                repo_metrics.metrics_data['contributors'] = contributors
                logger.debug(f"Collected {len(contributors)} contributors for {repo_metrics.full_name}")
            except Exception as e:
                error_msg = f"Failed to get contributors: {e}"
                logger.error(error_msg)
                repo_metrics.collection_errors.append(error_msg)
                
            # 4. Issues
            try:
                issues = self.github_client.get_issues(owner, repo, since=start_date if start_date else None)
                repo_metrics.metrics_data['issues'] = issues
                logger.debug(f"Collected {len(issues)} issues for {repo_metrics.full_name}")
            except Exception as e:
                error_msg = f"Failed to get issues: {e}"
                logger.error(error_msg)
                repo_metrics.collection_errors.append(error_msg)
                
            # 5. Pull Requests
            try:
                prs = self.github_client.get_pull_requests(owner, repo)
                repo_metrics.metrics_data['pull_requests'] = prs
                logger.debug(f"Collected {len(prs)} pull requests for {repo_metrics.full_name}")
            except Exception as e:
                error_msg = f"Failed to get pull requests: {e}"
                logger.error(error_msg)
                repo_metrics.collection_errors.append(error_msg)
                
            # 6. Current counts
            try:
                stars_count = self.github_client.get_stargazers_count(owner, name)
                forks_count = self.github_client.get_forks_count(owner, name)
                repo_metrics.metrics_data['current_stats'] = {
                    'stargazers_count': stars_count,
                    'forks_count': forks_count
                }
            except Exception as e:
                error_msg = f"Failed to get current counts: {e}"
                logger.error(error_msg)
                repo_metrics.collection_errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"Failed to collect metrics for {repo_metrics.full_name}: {e}"
            logger.error(error_msg)
            repo_metrics.collection_errors.append(error_msg)
            
        return repo_metrics
        
    def collect_metrics_batch(self, max_concurrent: int = None) -> Dict[str, RepositoryMetrics]:
        """Collect metrics for all repositories concurrently"""
        
        if not self.repos_to_collect:
            logger.warning("No repositories configured for collection")
            return {}
            
        if max_concurrent is None:
            max_concurrent = self.config.collection.max_concurrent_requests
            
        # Rate limit aware scheduling
        rate_limiter = self.github_client.rate_limiter
        
        results = {}
        collection_errors = []
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit collection tasks
            future_to_repo = {}
            
            for owner, name in self.repos_to_collect:
                # Check rate limits before submitting
                if not rate_limiter.stats.can_make_request():
                    logger.warning(f"Rate limit exceeded, pausing collections")
                    time.sleep(60)  # Wait 1 minute
                    
                future = executor.submit(self.collect_repository_metrics, owner, name)
                future_to_repo[future] = (owner, name)
                
            # Process completed collections
            for future in as_completed(future_to_repo):
                owner, name = future_to_repo[future]
                repo_name = f"{owner}/{name}"
                
                try:
                    repo_metrics = future.result()
                    results[repo_name] = repo_metrics
                    
                    # Log progress
                    if repo_metrics.collection_errors:
                        logger.warning(f"Completed collection for {repo_name} with errors: {len(repo_metrics.collection_errors)}")
                    else:
                        logger.info(f"Successfully collected metrics for {repo_name}")
                        
                except Exception as e:
                    error_msg = f"Failed to collect metrics for {repo_name}: {e}"
                    logger.error(error_msg)
                    collection_errors.append(error_msg)
                    
        self.collection_results = results
        self.collection_errors.extend(collection_errors)
        
        return results
        
    def process_and_store_metrics(self) -> None:
        """Process collected metrics and store them"""
        
        if not self.collection_results:
            logger.warning("No collection results to process")
            return
            
        logger.info(f"Processing and storing metrics for {len(self.collection_results)} repositories")
        
        # Process each repository's metrics
        for repo_name, repo_metrics in self.collection_results.items():
            try:
                # Convert metrics to storage format
                metrics_dict = repo_metrics.to_dict()
                
                # Add calculated metrics
                if repo_metrics.metrics_data:
                    metrics_dict['calculated_metrics'] = self._calculate_basic_metrics(repo_metrics.metrics_data)
                    
                # Store in database and file storage
                self.metrics_storage.save_repository_data(metrics_dict)
                
                logger.debug(f"Successfully stored metrics for {repo_name}")
                
            except Exception as e:
                error_msg = f"Failed to store metrics for {repo_name}: {e}"
                logger.error(error_msg)
                self.collection_errors.append(error_msg)
                
    def _calculate_basic_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic derived metrics from raw data"""
        
        calculated = {}
        
        # Count active contributors (with commits in the period)
        commits = metrics_data.get('commits', [])
        if commits:
            unique_committers = set()
            total_additions = 0
            total_deletions = 0
            
            for commit in commits:
                if commit.get('author_login'):
                    unique_committers.add(commit['author_login'])
                total_additions += commit.get('additions', 0)
                total_deletions += commit.get('deletions', 0)
                
            calculated['active_contributors'] = len(unique_committers)
            calculated['total_additions'] = total_additions
            calculated['total_deletions'] = total_deletions
            
        # Issue metrics
        issues = metrics_data.get('issues', [])
        if issues:
            open_issues = len([i for i in issues if i.get('state') == 'open'])
            closed_issues = len([i for i in issues if i.get('state') == 'closed'])
            
            calculated['open_issues'] = open_issues
            calculated['closed_issues'] = closed_issues
            calculated['issue_closure_rate'] = closed_issues / len(issues) if issues else 0
            
        # Pull request metrics
        prs = metrics_data.get('pull_requests', [])
        if prs:
            open_prs = len([pr for pr in prs if pr.get('state') == 'open'])
            merged_prs = len([pr for pr in prs if pr.get('state') == 'merged'])
            closed_prs = len([pr for pr in prs if pr.get('state') == 'closed'])
            
            calculated['open_prs'] = open_prs
            calculated['merged_prs'] = merged_prs
            calculated['closed_prs'] = closed_prs
            calculated['pr_merge_rate'] = merged_prs / len(prs) if prs else 0
            
        # Current stats
        current_stats = metrics_data.get('current_stats', {})
        calculated.update(current_stats)
        
        return calculated
        
    def run_daily_collection(self) -> Dict[str, Any]:
        """Run the complete daily collection process"""
        
        collection_start = datetime.now()
        logger.info("Starting daily metrics collection")
        
        try:
            # Step 1: Setup collection targets
            self.setup_collection_targets()
            
            if not self.repos_to_collect:
                return {
                    'status': 'no_repositories',
                    'timestamp': collection_start.isoformat(),
                    'message': 'No repositories configured for collection'
                }
                
            # Step 2: Collect metrics
            collection_results = self.collect_metrics_batch()
            
            # Step 3: Process and store
            self.process_and_store_metrics()
            
            # Step 4: Generate collection summary
            collection_summary = self._generate_collection_summary(collection_results, collection_start)
            
            logger.info("Daily metrics collection completed successfully")
            return collection_summary
            
        except Exception as e:
            error_msg = f"Daily collection failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            return {
                'status': 'failed',
                'timestamp': collection_start.isoformat(),
                'error': error_msg,
                'repositories_processed': len(self.collection_results),
                'errors': self.collection_errors
            }
            
    def _generate_collection_summary(self, results: Dict[str, RepositoryMetrics], 
                                   start_time: datetime) -> Dict[str, Any]:
        """Generate collection summary report"""
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        total_repos = len(results)
        successful_collections = len([r for r in results.values() if not r.collection_errors])
        failed_collections = total_repos - successful_collections
        total_errors = sum(len(r.collection_errors) for r in results.values())
        
        # Repository statistics
        repo_stats = {
            'total_repositories': total_repos,
            'successful': successful_collections,
            'failed': failed_collections,
            'success_rate': successful_collections / total_repos if total_repos > 0 else 0
        }
        
        # Performance statistics
        perf_stats = {
            'duration_seconds': duration,
            'duration_formatted': str(timedelta(seconds=int(duration))),
            'repos_per_minute': (successful_collections / (duration / 60)) if duration > 0 else 0,
            'avg_time_per_repo': duration / total_repos if total_repos > 0 else 0
        }
        
        # Rate limit status
        rate_limit_info = self.github_client.get_rate_limit_info()
        
        # Generate summary
        summary = {
            'status': 'completed',
            'timestamp': start_time.isoformat(),
            'duration': end_time.isoformat(),
            'repository_statistics': repo_stats,
            'performance_statistics': perf_stats,
            'rate_limit_status': rate_limit_info,
            'collection_errors': self.collection_errors
        }
        
        # Add top performing and problematic repositories
        if results:
            repos_with_errors = [(name, repo) for name, repo in results.items() if repo.collection_errors]
            repos_without_errors = [(name, repo) for name, repo in results.items() if not repo.collection_errors]
            
            summary['top_successful_repos'] = [name for name, _ in repos_without_errors[:5]]
            summary['repos_with_errors'] = [name for name, _ in repos_with_errors[:10]]
            
        return summary
        
    def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old data based on retention policy"""
        
        logger.info("Starting cleanup of old data")
        
        cleanup_stats = self.metrics_storage.cleanup_old_data()
        
        logger.info(f"Cleanup completed: {cleanup_stats}")
        
        return cleanup_stats
        
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status and statistics"""
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'configured_repositories': len(self.repos_to_collect),
            'last_collection_results': len(self.collection_results),
            'total_errors': len(self.collection_errors),
            'rate_limiter_stats': self.github_client.get_stats(),
            'storage_backend': self.config.storage.backend
        }
        
        if self.collection_results:
            # Get storage statistics
            if hasattr(self.metrics_storage.db, 'get_repository_history'):
                status['storage_stats'] = {
                    'recent_snapshots': len([r for r in self.collection_results.values() 
                                           if r.collection_timestamp > datetime.now() - timedelta(days=7)])
                }
                
        return status


def main():
    """Main entry point for daily collection"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/growth_metrics_collection.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Initialize collector
        collector = DailyMetricsCollector()
        
        # Run collection
        summary = collector.run_daily_collection()
        
        # Print summary
        print("\n=== Daily Metrics Collection Summary ===")
        print(f"Status: {summary['status']}")
        print(f"Duration: {summary.get('performance_statistics', {}).get('duration_formatted', 'N/A')}")
        print(f"Repositories: {summary.get('repository_statistics', {}).get('total_repositories', 0)}")
        print(f"Success Rate: {summary.get('repository_statistics', {}).get('success_rate', 0):.1%}")
        
        if summary.get('collection_errors'):
            print(f"\nErrors ({len(summary['collection_errors'])}):")
            for error in summary['collection_errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
                
        # Save summary to file
        summary_file = f"logs/collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        print(f"\nDetailed summary saved to: {summary_file}")
        
        # Return appropriate exit code
        if summary['status'] == 'failed':
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error in daily collection: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()