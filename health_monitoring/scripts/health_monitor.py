#!/usr/bin/env python3
"""
Repository Health Monitoring System - Main Script

This is the main entry point for the repository health monitoring system.
It orchestrates the collection, analysis, reporting, and alerting processes.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from github_api_client import GitHubAPIClient
from health_score_calculator import HealthScoreCalculator
from community_engagement_tracker import CommunityEngagementTracker
from report_generator import ReportGenerator, ReportConfig
from dashboard_data_generator import DashboardDataGenerator, DashboardConfig
from alert_system import AlertSystem, NotificationConfig, AlertSeverity


class HealthMonitoringOrchestrator:
    """
    Main orchestrator for the repository health monitoring system.
    
    Coordinates:
    - Data collection from GitHub API
    - Health score calculation
    - Community engagement analysis
    - Report generation
    - Dashboard data creation
    - Alert monitoring and notifications
    """
    
    def __init__(self, config_path: str, alert_rules_path: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to main configuration file
            alert_rules_path: Path to alert rules configuration
        """
        self.config_path = config_path
        self.alert_rules_path = alert_rules_path
        self.config = self._load_config()
        self.alert_config = self._load_alert_rules() if alert_rules_path else None
        
        # Set up logging
        self._setup_logging()
        
        # Initialize components
        self.github_client: Optional[GitHubAPIClient] = None
        self.health_calculator = HealthScoreCalculator()
        self.engagement_tracker = CommunityEngagementTracker()
        self.report_generator = ReportGenerator(ReportConfig(
            output_dir=self.config.get('reporting', {}).get('output', {}).get('reports', './reports')
        ))
        self.dashboard_generator = DashboardDataGenerator(DashboardConfig(
            output_dir=self.config.get('dashboard', {}).get('output', {}).get('dashboard_data', './dashboard_data'),
            kpi_update_frequency=self.config.get('dashboard', {}).get('kpi_update_frequency', 'daily')
        ))
        
        # Initialize alert system
        notification_config = self._create_notification_config()
        self.alert_system = AlertSystem(notification_config)
        
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alert rules configuration"""
        if not self.alert_rules_path:
            return {}
        
        try:
            with open(self.alert_rules_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading alert rules: {e}")
            return {}
    
    def _setup_logging(self):
        """Set up logging configuration"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO').upper())
        
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=level,
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_dir / 'health_monitor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _create_notification_config(self) -> NotificationConfig:
        """Create notification configuration from settings"""
        notifications = self.config.get('alerts', {}).get('notifications', {})
        
        return NotificationConfig(
            email_enabled=notifications.get('email', {}).get('enabled', False),
            slack_enabled=notifications.get('slack', {}).get('enabled', False),
            discord_enabled=notifications.get('discord', {}).get('enabled', False),
            webhook_enabled=notifications.get('webhook', {}).get('enabled', False),
            github_issues_enabled=notifications.get('github_issues', {}).get('enabled', False),
            
            # Email settings
            smtp_server=os.getenv('SMTP_SERVER', notifications.get('email', {}).get('smtp_server', '')),
            smtp_port=notifications.get('email', {}).get('smtp_port', 587),
            email_user=os.getenv('EMAIL_USERNAME', ''),
            email_password=os.getenv('EMAIL_PASSWORD', ''),
            email_recipients=notifications.get('email', {}).get('recipients', []),
            
            # Slack settings
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL', notifications.get('slack', {}).get('webhook_url', '')),
            slack_channel=notifications.get('slack', {}).get('channel', '#health-alerts'),
            
            # Discord settings
            discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL', notifications.get('discord', {}).get('webhook_url', '')),
            
            # Webhook settings
            webhook_urls=notifications.get('webhook', {}).get('urls', []),
            
            # GitHub settings
            github_token=os.getenv('GITHUB_TOKEN', ''),
            github_repo=notifications.get('github_issues', {}).get('repository', '')
        )
    
    async def run_health_monitoring(
        self,
        repositories: List[str],
        output_dir: str = "./data",
        reports_dir: str = "./reports",
        dashboard_dir: str = "./dashboard_data",
        skip_alerts: bool = False,
        include_realtime: bool = False
    ) -> Dict[str, Any]:
        """
        Run comprehensive health monitoring for repositories.
        
        Args:
            repositories: List of repositories to monitor (format: "owner/repo")
            output_dir: Directory to store raw data
            reports_dir: Directory to store reports
            dashboard_dir: Directory to store dashboard data
            skip_alerts: Whether to skip alert notifications
            include_realtime: Whether to include real-time data
            
        Returns:
            Summary of monitoring results
        """
        self.logger.info(f"Starting health monitoring for {len(repositories)} repositories")
        
        # Create output directories
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        Path(dashboard_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize GitHub client
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        async with GitHubAPIClient(github_token) as client:
            self.github_client = client
            
            # Process each repository
            results = {}
            all_alerts = []
            
            for repo in repositories:
                try:
                    self.logger.info(f"Processing repository: {repo}")
                    repo_result = await self._process_repository(
                        repo, output_dir, reports_dir, dashboard_dir, skip_alerts
                    )
                    results[repo] = repo_result
                    
                    # Collect alerts
                    if 'alerts' in repo_result:
                        all_alerts.extend(repo_result['alerts'])
                    
                except Exception as e:
                    self.logger.error(f"Error processing repository {repo}: {e}")
                    results[repo] = {"error": str(e)}
            
            # Generate portfolio summary if multiple repositories
            if len(repositories) > 1:
                await self._generate_portfolio_summary(repositories, reports_dir)
            
            # Generate real-time updates if requested
            if include_realtime:
                await self._generate_realtime_updates(repositories)
            
            # Log final statistics
            self._log_monitoring_summary(results, all_alerts)
            
            return {
                "repositories_processed": len(repositories),
                "successful_repos": len([r for r in results.values() if "error" not in r]),
                "failed_repos": len([r for r in results.values() if "error" in r]),
                "total_alerts": len(all_alerts),
                "results": results
            }
    
    async def _process_repository(
        self,
        repository: str,
        output_dir: str,
        reports_dir: str,
        dashboard_dir: str,
        skip_alerts: bool
    ) -> Dict[str, Any]:
        """Process a single repository"""
        
        # Parse repository name
        if '/' not in repository:
            raise ValueError(f"Invalid repository format: {repository}. Expected 'owner/repo'")
        
        owner, repo = repository.split('/', 1)
        
        # Load historical data if available
        historical_data = await self._load_historical_data(owner, repo, output_dir)
        
        # Collect metrics
        metrics = await self.github_client.collect_repository_metrics(owner, repo)
        
        # Calculate health score
        historical_metrics = [m for m in historical_data if isinstance(m, dict)]
        health_score = self.health_calculator.calculate_health_score(metrics, historical_metrics)
        
        # Analyze community engagement
        engagement_metrics = await self.engagement_tracker.analyze_community_engagement(
            self.github_client, owner, repo, historical_metrics
        )
        
        # Generate reports
        report_path = await self.report_generator._generate_weekly_report_content(
            metrics, health_score, engagement_metrics, historical_metrics
        )
        
        # Generate dashboard data
        dashboard_data = await self.dashboard_generator.generate_dashboard_data(
            self.github_client, owner, repo, historical_data
        )
        
        # Check for alerts (unless skipped)
        alerts = []
        if not skip_alerts:
            alerts = await self.alert_system.check_repository_health(
                self.github_client, owner, repo, historical_data
            )
        
        # Save raw data
        await self._save_repository_data(
            owner, repo, metrics, health_score, engagement_metrics, output_dir
        )
        
        return {
            "metrics": metrics,
            "health_score": health_score,
            "engagement": engagement_metrics,
            "report_path": report_path,
            "dashboard_data": dashboard_data,
            "alerts": [alert.__dict__ for alert in alerts],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _load_historical_data(self, owner: str, repo: str, data_dir: str) -> List[Dict[str, Any]]:
        """Load historical data for trend analysis"""
        data_path = Path(data_dir) / f"{owner}_{repo}_historical.json"
        
        if not data_path.exists():
            return []
        
        try:
            with open(data_path, 'r') as f:
                return yaml.safe_load(f) or []
        except Exception as e:
            self.logger.warning(f"Could not load historical data for {owner}/{repo}: {e}")
            return []
    
    async def _save_repository_data(
        self,
        owner: str,
        repo: str,
        metrics,
        health_score,
        engagement_metrics,
        output_dir: str
    ):
        """Save repository data for historical analysis"""
        data_path = Path(output_dir) / f"{owner}_{repo}_historical.json"
        
        # Load existing data
        existing_data = await self._load_historical_data(owner, repo, output_dir)
        
        # Add new data point
        new_data_point = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "stars": metrics.stars,
                "forks": metrics.forks,
                "watchers": metrics.watchers,
                "commits_this_month": metrics.commits_this_month,
                "open_issues": metrics.open_issues,
                "closed_issues": metrics.closed_issues,
                "merged_prs": metrics.merged_prs,
                "total_contributors": metrics.total_contributors,
                "issue_closure_rate": metrics.issue_closure_rate,
                "pr_merge_time_avg": metrics.pr_merge_time_avg
            },
            "health_score": health_score.overall_score,
            "engagement": {
                "active_contributors": engagement_metrics.active_contributors,
                "new_contributors_month": engagement_metrics.new_contributors_month,
                "retention_rate": engagement_metrics.contributor_retention_rate,
                "avg_response_time_hours": engagement_metrics.avg_response_time_hours
            }
        }
        
        existing_data.append(new_data_point)
        
        # Keep only last 90 days of data
        cutoff_date = datetime.now() - timedelta(days=90)
        existing_data = [
            d for d in existing_data 
            if datetime.fromisoformat(d['timestamp']) > cutoff_date
        ]
        
        # Save updated data
        with open(data_path, 'w') as f:
            yaml.dump(existing_data, f)
    
    async def _generate_portfolio_summary(self, repositories: List[str], reports_dir: str):
        """Generate portfolio-level summary report"""
        if len(repositories) <= 1:
            return
        
        repo_tuples = [(r.split('/')[0], r.split('/')[1]) for r in repositories if '/' in r]
        
        portfolio_data = await self.dashboard_generator.generate_portfolio_dashboard_data(
            repo_tuples, self.github_client
        )
        
        # Save portfolio dashboard data
        portfolio_path = Path(reports_dir) / "portfolio_dashboard_data.json"
        import json
        with open(portfolio_path, 'w') as f:
            json.dump(portfolio_data, f, indent=2, default=str)
    
    async def _generate_realtime_updates(self, repositories: List[str]):
        """Generate real-time updates for dashboards"""
        for repo in repositories:
            if '/' not in repo:
                continue
            
            owner, repo_name = repo.split('/', 1)
            
            try:
                metrics = await self.github_client.collect_repository_metrics(owner, repo_name)
                realtime_data = self.dashboard_generator.generate_realtime_updates(metrics)
                
                # Save real-time update
                update_path = Path("dashboard_data") / f"{owner}_{repo_name}_realtime.json"
                with open(update_path, 'w') as f:
                    import json
                    json.dump(realtime_data, f, indent=2, default=str)
                    
            except Exception as e:
                self.logger.warning(f"Could not generate real-time update for {repo}: {e}")
    
    def _log_monitoring_summary(self, results: Dict[str, Any], alerts: List[Any]):
        """Log summary of monitoring run"""
        successful_repos = len([r for r in results.values() if "error" not in r])
        failed_repos = len([r for r in results.values() if "error" in r])
        
        # Alert summary
        critical_alerts = len([a for a in alerts if hasattr(a, 'severity') and a.severity == AlertSeverity.CRITICAL])
        high_alerts = len([a for a in alerts if hasattr(a, 'severity') and a.severity == AlertSeverity.HIGH])
        
        self.logger.info(f"""
        HEALTH MONITORING SUMMARY
        =========================
        Repositories processed: {len(results)}
        Successful: {successful_repos}
        Failed: {failed_repos}
        
        ALERTS GENERATED
        ================
        Total alerts: {len(alerts)}
        Critical: {critical_alerts}
        High: {high_alerts}
        
        SYSTEM HEALTH
        =============
        GitHub API calls made: {self.github_client._requests_made if self.github_client else 0}
        Cache hit rate: {self.github_client._requests_cached / max(1, self.github_client._requests_made + self.github_client._requests_cached) if self.github_client else 0:.2%}
        """)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Repository Health Monitoring System")
    parser.add_argument("--repositories", required=True, help="Repository list (owner/repo, comma or newline separated)")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--alert-rules", help="Path to alert rules configuration")
    parser.add_argument("--output-dir", default="./data", help="Output directory for raw data")
    parser.add_argument("--reports-dir", default="./reports", help="Output directory for reports")
    parser.add_argument("--dashboard-dir", default="./dashboard_data", help="Output directory for dashboard data")
    parser.add_argument("--skip-alerts", action="store_true", help="Skip alert notifications")
    parser.add_argument("--realtime", action="store_true", help="Include real-time updates")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Parse repositories
    if args.repositories:
        # Handle both comma-separated and newline-separated input
        if '\n' in args.repositories:
            repositories = [r.strip() for r in args.repositories.split('\n') if r.strip()]
        else:
            repositories = [r.strip() for r in args.repositories.split(',') if r.strip()]
    else:
        repositories = []
    
    # Initialize orchestrator
    orchestrator = HealthMonitoringOrchestrator(args.config, args.alert_rules)
    
    # Run monitoring
    try:
        results = await orchestrator.run_health_monitoring(
            repositories=repositories,
            output_dir=args.output_dir,
            reports_dir=args.reports_dir,
            dashboard_dir=args.dashboard_dir,
            skip_alerts=args.skip_alerts,
            include_realtime=args.realtime
        )
        
        # Print summary
        print(f"\n{'='*50}")
        print("HEALTH MONITORING COMPLETED")
        print(f"{'='*50}")
        print(f"Repositories processed: {results['repositories_processed']}")
        print(f"Successful: {results['successful_repos']}")
        print(f"Failed: {results['failed_repos']}")
        print(f"Total alerts generated: {results['total_alerts']}")
        print(f"\nResults saved to:")
        print(f"  - Data: {args.output_dir}")
        print(f"  - Reports: {args.reports_dir}")
        print(f"  - Dashboard: {args.dashboard_dir}")
        
        # Exit with error code if there were failures
        if results['failed_repos'] > 0:
            print(f"\n⚠️  {results['failed_repos']} repositories failed to process")
            sys.exit(1)
        else:
            print(f"\n✅ All repositories processed successfully")
            
    except Exception as e:
        print(f"❌ Error running health monitoring: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Set up asyncio event loop policy for Windows compatibility
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())