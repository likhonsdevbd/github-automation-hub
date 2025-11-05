"""
Alert System for Repository Health Anomalies

This module provides intelligent alerting for repository health monitoring,
detecting anomalies, threshold breaches, and providing notification routing.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import statistics
import smtplib
import aiohttp
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from github_api_client import GitHubAPIClient, RepositoryMetrics
from health_score_calculator import HealthScoreCalculator, HealthScoreBreakdown
from community_engagement_tracker import CommunityEngagementTracker, EngagementMetrics


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(Enum):
    """Types of alerts"""
    HEALTH_SCORE_DROP = "health_score_drop"
    RESPONSE_TIME_HIGH = "response_time_high"
    ISSUE_CLOSURE_LOW = "issue_closure_low"
    CONTRIBUTOR_INACTIVITY = "contributor_inactivity"
    PR_MERGE_TIME_HIGH = "pr_merge_time_high"
    STAR_DECLINE = "star_decline"
    FORK_ACTIVITY_SPIKE = "fork_activity_spike"
    SECURITY_VULNERABILITY = "security_vulnerability"
    DEPENDENCY_OUTDATED = "dependency_outdated"
    COMMUNITY_SATISFACTION_LOW = "community_satisfaction_low"


@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    alert_type: AlertType
    severity: AlertSeverity
    condition: Callable
    threshold: Any
    time_window: timedelta
    cooldown_period: timedelta = field(default_factory=lambda: timedelta(hours=1))
    description: str = ""
    recommendation: str = ""


@dataclass
class Alert:
    """Alert instance"""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    repository: str
    timestamp: datetime
    resolved: bool = False
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    escalation_level: int = 0


@dataclass
class NotificationConfig:
    """Configuration for alert notifications"""
    email_enabled: bool = True
    slack_enabled: bool = False
    discord_enabled: bool = False
    webhook_enabled: bool = False
    github_issues_enabled: bool = True
    
    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_recipients: List[str] = field(default_factory=list)
    
    # Slack settings
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Discord settings
    discord_webhook_url: str = ""
    
    # Webhook settings
    webhook_urls: List[str] = field(default_factory=list)
    
    # GitHub settings
    github_token: str = ""
    github_repo: str = ""


class AlertSystem:
    """
    Intelligent alert system for repository health monitoring.
    
    Features:
    - Configurable alert rules and thresholds
    - Multiple notification channels
    - Alert suppression and deduplication
    - Escalation handling
    - Historical alert tracking
    """
    
    def __init__(self, config: NotificationConfig = None):
        """
        Initialize alert system.
        
        Args:
            config: Notification configuration
        """
        self.config = config or NotificationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: List[AlertRule] = []
        
        # Alert suppression
        self.suppressed_alerts: Dict[str, datetime] = {}
        
        # Alert statistics
        self.alert_stats = {
            "total_alerts": 0,
            "resolved_alerts": 0,
            "acknowledged_alerts": 0,
            "alerts_by_severity": {severity.value: 0 for severity in AlertSeverity},
            "alerts_by_type": {alert_type.value: 0 for alert_type in AlertType}
        }
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        
        # Health Score Alert Rules
        self.add_rule(AlertRule(
            name="Low Health Score",
            alert_type=AlertType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.HIGH,
            condition=lambda metrics, health_score, engagement: health_score.overall_score < 60,
            threshold=60,
            time_window=timedelta(days=1),
            description="Repository health score has dropped below acceptable threshold",
            recommendation="Review all health components and implement improvement plan"
        ))
        
        self.add_rule(AlertRule(
            name="Critical Health Score",
            alert_type=AlertType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.CRITICAL,
            condition=lambda metrics, health_score, engagement: health_score.overall_score < 40,
            threshold=40,
            time_window=timedelta(hours=12),
            description="Repository health score is critically low",
            recommendation="Immediate action required - review and address all issues"
        ))
        
        # Response Time Alert Rules
        self.add_rule(AlertRule(
            name="High Response Time",
            alert_type=AlertType.RESPONSE_TIME_HIGH,
            severity=AlertSeverity.MEDIUM,
            condition=lambda metrics, health_score, engagement: engagement.avg_response_time_hours > 48,
            threshold=48,
            time_window=timedelta(days=3),
            description="Average issue response time is too high",
            recommendation="Assign more maintainers or implement automated triaging"
        ))
        
        self.add_rule(AlertRule(
            name="Critical Response Time",
            alert_type=AlertType.RESPONSE_TIME_HIGH,
            severity=AlertSeverity.HIGH,
            condition=lambda metrics, health_score, engagement: engagement.avg_response_time_hours > 96,
            threshold=96,
            time_window=timedelta(days=1),
            description="Average issue response time is critically high",
            recommendation="Urgent: Assign dedicated triage team and review processes"
        ))
        
        # Issue Closure Rate Alert Rules
        self.add_rule(AlertRule(
            name="Low Issue Closure Rate",
            alert_type=AlertType.ISSUE_CLOSURE_LOW,
            severity=AlertSeverity.MEDIUM,
            condition=lambda metrics, health_score, engagement: metrics.issue_closure_rate < 60,
            threshold=60,
            time_window=timedelta(days=7),
            description="Issue closure rate is below acceptable threshold",
            recommendation="Implement systematic issue triage and closure processes"
        ))
        
        # Contributor Inactivity Alert Rules
        self.add_rule(AlertRule(
            name="No New Contributors",
            alert_type=AlertType.CONTRIBUTOR_INACTIVITY,
            severity=AlertSeverity.MEDIUM,
            condition=lambda metrics, health_score, engagement: engagement.new_contributors_month == 0,
            threshold=0,
            time_window=timedelta(days=30),
            description="No new contributors in the last month",
            recommendation="Launch contributor onboarding campaign and improve good first issues"
        ))
        
        # PR Merge Time Alert Rules
        self.add_rule(AlertRule(
            name="High PR Merge Time",
            alert_type=AlertType.PR_MERGE_TIME_HIGH,
            severity=AlertSeverity.MEDIUM,
            condition=lambda metrics, health_score, engagement: metrics.pr_merge_time_avg > 120,
            threshold=120,
            time_window=timedelta(days=7),
            description="Average PR merge time is too high",
            recommendation="Add more reviewers and streamline review process"
        ))
        
        # Star Decline Alert Rules
        self.add_rule(AlertRule(
            name="Star Decline",
            alert_type=AlertType.STAR_DECLINE,
            severity=AlertSeverity.LOW,
            condition=lambda metrics, health_score, engagement: False,  # Would need historical data
            threshold=0,
            time_window=timedelta(days=30),
            description="Repository stars are declining",
            recommendation="Review community engagement and project visibility"
        ))
        
        # Community Satisfaction Alert Rules
        self.add_rule(AlertRule(
            name="Low Community Satisfaction",
            alert_type=AlertType.COMMUNITY_SATISFACTION_LOW,
            severity=AlertSeverity.MEDIUM,
            condition=lambda metrics, health_score, engagement: engagement.community_satisfaction_score < 50,
            threshold=50,
            time_window=timedelta(days=14),
            description="Community satisfaction score is low",
            recommendation="Conduct community survey and address feedback"
        ))
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule to the system"""
        self.alert_rules.append(rule)
        self.logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule by name"""
        original_length = len(self.alert_rules)
        self.alert_rules = [rule for rule in self.alert_rules if rule.name != rule_name]
        removed = len(self.alert_rules) < original_length
        if removed:
            self.logger.info(f"Removed alert rule: {rule_name}")
        return removed
    
    async def check_repository_health(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Alert]:
        """
        Check repository health and generate alerts.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            historical_data: Historical metrics data
            
        Returns:
            List of generated alerts
        """
        self.logger.info(f"Checking repository health for {owner}/{repo}")
        
        # Collect current metrics
        current_metrics = await client.collect_repository_metrics(owner, repo)
        
        # Calculate health score
        health_calculator = HealthScoreCalculator()
        historical_metrics = self._parse_historical_data(historical_data) if historical_data else None
        health_score = health_calculator.calculate_health_score(current_metrics, historical_metrics)
        
        # Analyze community engagement
        engagement_tracker = CommunityEngagementTracker()
        engagement_metrics = await engagement_tracker.analyze_community_engagement(
            client, owner, repo, historical_metrics
        )
        
        # Check alert rules
        alerts = await self._check_alert_rules(
            current_metrics, health_score, engagement_metrics, f"{owner}/{repo}"
        )
        
        # Send notifications
        await self._send_notifications(alerts)
        
        # Update alert statistics
        self._update_alert_stats(alerts)
        
        return alerts
    
    async def _check_alert_rules(
        self,
        metrics: RepositoryMetrics,
        health_score: HealthScoreBreakdown,
        engagement_metrics: EngagementMetrics,
        repository: str
    ) -> List[Alert]:
        """Check all alert rules against current data"""
        
        alerts = []
        
        for rule in self.alert_rules:
            try:
                # Check if condition is met
                if rule.condition(metrics, health_score, engagement_metrics):
                    # Check cooldown period
                    alert_key = f"{rule.alert_type.value}_{repository}"
                    if self._is_alert_suppressed(alert_key, rule.cooldown_period):
                        continue
                    
                    # Generate alert
                    alert = await self._create_alert(rule, repository, metrics, health_score, engagement_metrics)
                    alerts.append(alert)
                    
                    # Suppress future alerts for cooldown period
                    self.suppressed_alerts[alert_key] = datetime.now()
                    
            except Exception as e:
                self.logger.error(f"Error checking rule {rule.name}: {e}")
        
        # Update active alerts
        for alert in alerts:
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)
        
        return alerts
    
    async def _create_alert(
        self,
        rule: AlertRule,
        repository: str,
        metrics: RepositoryMetrics,
        health_score: HealthScoreBreakdown,
        engagement_metrics: EngagementMetrics
    ) -> Alert:
        """Create alert instance from rule and data"""
        
        # Generate unique alert ID
        alert_id = f"{rule.alert_type.value}_{repository}_{int(datetime.now().timestamp())}"
        
        # Generate title and message
        title = f"{rule.alert_type.value.replace('_', ' ').title()}: {repository}"
        message = rule.description
        
        # Add specific details based on alert type
        metadata = {}
        if rule.alert_type == AlertType.HEALTH_SCORE_DROP:
            message += f" Current score: {health_score.overall_score:.1f}/100"
            metadata["current_score"] = health_score.overall_score
            metadata["threshold"] = rule.threshold
        elif rule.alert_type == AlertType.RESPONSE_TIME_HIGH:
            message += f" Current response time: {engagement_metrics.avg_response_time_hours:.1f} hours"
            metadata["current_response_time"] = engagement_metrics.avg_response_time_hours
            metadata["threshold"] = rule.threshold
        elif rule.alert_type == AlertType.ISSUE_CLOSURE_LOW:
            message += f" Current closure rate: {metrics.issue_closure_rate:.1f}%"
            metadata["current_closure_rate"] = metrics.issue_closure_rate
            metadata["threshold"] = rule.threshold
        elif rule.alert_type == AlertType.CONTRIBUTOR_INACTIVITY:
            message += f" New contributors this month: {engagement_metrics.new_contributors_month}"
            metadata["new_contributors"] = engagement_metrics.new_contributors_month
        elif rule.alert_type == AlertType.PR_MERGE_TIME_HIGH:
            message += f" Average merge time: {metrics.pr_merge_time_avg:.1f} hours"
            metadata["merge_time"] = metrics.pr_merge_time_avg
            metadata["threshold"] = rule.threshold
        elif rule.alert_type == AlertType.COMMUNITY_SATISFACTION_LOW:
            message += f" Satisfaction score: {engagement_metrics.community_satisfaction_score:.1f}/100"
            metadata["satisfaction_score"] = engagement_metrics.community_satisfaction_score
            metadata["threshold"] = rule.threshold
        
        return Alert(
            id=alert_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            title=title,
            message=message,
            repository=repository,
            timestamp=datetime.now(),
            metadata=metadata
        )
    
    def _is_alert_suppressed(self, alert_key: str, cooldown_period: timedelta) -> bool:
        """Check if alert should be suppressed due to cooldown"""
        if alert_key not in self.suppressed_alerts:
            return False
        
        last_alert_time = self.suppressed_alerts[alert_key]
        return (datetime.now() - last_alert_time) < cooldown_period
    
    async def _send_notifications(self, alerts: List[Alert]):
        """Send notifications for generated alerts"""
        
        for alert in alerts:
            try:
                # Send email notification
                if self.config.email_enabled and self._should_send_email(alert):
                    await self._send_email_notification(alert)
                
                # Send Slack notification
                if self.config.slack_enabled and self._should_send_slack(alert):
                    await self._send_slack_notification(alert)
                
                # Send Discord notification
                if self.config.discord_enabled and self._should_send_discord(alert):
                    await self._send_discord_notification(alert)
                
                # Send webhook notification
                if self.config.webhook_enabled and self._should_send_webhook(alert):
                    await self._send_webhook_notification(alert)
                
                # Create GitHub issue
                if self.config.github_issues_enabled and self._should_create_github_issue(alert):
                    await self._create_github_issue(alert)
                    
            except Exception as e:
                self.logger.error(f"Failed to send notification for alert {alert.id}: {e}")
    
    def _should_send_email(self, alert: Alert) -> bool:
        """Determine if email notification should be sent"""
        if not self.config.email_recipients:
            return False
        
        # Send emails for critical, high, and medium severity alerts
        return alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM]
    
    def _should_send_slack(self, alert: Alert) -> bool:
        """Determine if Slack notification should be sent"""
        # Send Slack notifications for all severity levels
        return bool(self.config.slack_webhook_url)
    
    def _should_send_discord(self, alert: Alert) -> bool:
        """Determine if Discord notification should be sent"""
        # Send Discord notifications for critical and high severity
        return alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH] and bool(self.config.discord_webhook_url)
    
    def _should_send_webhook(self, alert: Alert) -> bool:
        """Determine if webhook notification should be sent"""
        # Send webhook for all alerts
        return len(self.config.webhook_urls) > 0
    
    def _should_create_github_issue(self, alert: Alert) -> bool:
        """Determine if GitHub issue should be created"""
        # Create GitHub issues for critical and high severity alerts
        return alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH] and bool(self.config.github_repo)
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        if not self.config.email_recipients:
            return
        
        try:
            subject = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
Repository Health Alert

Repository: {alert.repository}
Severity: {alert.severity.value.upper()}
Alert Type: {alert.alert_type.value.replace('_', ' ').title()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message: {alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2)}

---
Generated by Repository Health Monitoring System
"""
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.config.email_user
            msg['To'] = ", ".join(self.config.email_recipients)
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_user, self.config.email_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email notification sent for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        if not self.config.slack_webhook_url:
            return
        
        try:
            color = self._get_severity_color(alert.severity)
            
            payload = {
                "channel": self.config.slack_channel,
                "username": "Health Monitor",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {"title": "Repository", "value": alert.repository, "short": True},
                            {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                            {"title": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M'), "short": True}
                        ],
                        "footer": "Health Monitoring System",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack notification sent for alert {alert.id}")
                    else:
                        self.logger.error(f"Failed to send Slack notification: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_discord_notification(self, alert: Alert):
        """Send Discord notification"""
        if not self.config.discord_webhook_url:
            return
        
        try:
            color = self._get_severity_color(alert.severity)
            
            embed = {
                "title": alert.title,
                "description": alert.message,
                "color": color,
                "fields": [
                    {"name": "Repository", "value": alert.repository, "inline": True},
                    {"name": "Severity", "value": alert.severity.value.upper(), "inline": True},
                    {"name": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M'), "inline": True}
                ],
                "footer": {"text": "Health Monitoring System"},
                "timestamp": alert.timestamp.isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.discord_webhook_url, json=payload) as response:
                    if response.status == 204:
                        self.logger.info(f"Discord notification sent for alert {alert.id}")
                    else:
                        self.logger.error(f"Failed to send Discord notification: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {e}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification"""
        if not self.config.webhook_urls:
            return
        
        payload = {
            "alert_id": alert.id,
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "repository": alert.repository,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata
        }
        
        for webhook_url in self.config.webhook_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, json=payload) as response:
                        if response.status in [200, 201, 204]:
                            self.logger.info(f"Webhook notification sent for alert {alert.id}")
                        else:
                            self.logger.error(f"Failed to send webhook notification: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Failed to send webhook notification: {e}")
    
    async def _create_github_issue(self, alert: Alert):
        """Create GitHub issue for alert"""
        if not self.config.github_repo or not self.config.github_token:
            return
        
        try:
            owner, repo = self.config.github_repo.split('/')
            
            # Format issue body
            body = f"""## {alert.title}

**Repository:** {alert.repository}  
**Severity:** {alert.severity.value.upper()}  
**Alert Type:** {alert.alert_type.value.replace('_', ' ').title()}  
**Time:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

### Message
{alert.message}

### Metadata
```
{json.dumps(alert.metadata, indent=2)}
```

### Recommendation
This alert indicates a potential issue with repository health. Please review the relevant metrics and take appropriate action.

---
*Automatically generated by Repository Health Monitoring System*
"""
            
            # Create issue via GitHub API
            headers = {
                "Authorization": f"token {self.config.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            issue_data = {
                "title": f"[{alert.severity.value.upper()}] {alert.title}",
                "body": body,
                "labels": ["health-alert", alert.severity.value]
            }
            
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, json=issue_data) as response:
                    if response.status == 201:
                        self.logger.info(f"GitHub issue created for alert {alert.id}")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to create GitHub issue: {response.status} - {error_text}")
                        
        except Exception as e:
            self.logger.error(f"Failed to create GitHub issue: {e}")
    
    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get color code for alert severity"""
        color_map = {
            AlertSeverity.CRITICAL: 0xFF0000,  # Red
            AlertSeverity.HIGH: 0xFF8800,      # Orange
            AlertSeverity.MEDIUM: 0xFFFF00,    # Yellow
            AlertSeverity.LOW: 0x00FF00,       # Green
            AlertSeverity.INFO: 0x0088FF       # Blue
        }
        return color_map.get(severity, 0x666666)
    
    def _update_alert_stats(self, alerts: List[Alert]):
        """Update alert statistics"""
        for alert in alerts:
            self.alert_stats["total_alerts"] += 1
            self.alert_stats["alerts_by_severity"][alert.severity.value] += 1
            self.alert_stats["alerts_by_type"][alert.alert_type.value] += 1
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.alert_stats["acknowledged_alerts"] += 1
            self.logger.info(f"Alert {alert_id} acknowledged")
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            self.alert_stats["resolved_alerts"] += 1
            del self.active_alerts[alert_id]
            self.logger.info(f"Alert {alert_id} resolved")
            return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert statistics"""
        return {
            **self.alert_stats,
            "active_alerts_count": len(self.active_alerts),
            "suppressed_alerts_count": len(self.suppressed_alerts),
            "configured_rules_count": len(self.alert_rules)
        }
    
    def _parse_historical_data(self, historical_data: List[Dict[str, Any]]) -> List[RepositoryMetrics]:
        """Parse historical data from file format to RepositoryMetrics objects"""
        # Placeholder implementation
        return []
    
    def export_alerts(self, filepath: str):
        """Export alert history to file"""
        alerts_data = {
            "export_timestamp": datetime.now().isoformat(),
            "alert_history": [alert.__dict__ for alert in self.alert_history],
            "active_alerts": [alert.__dict__ for alert in self.active_alerts.values()],
            "statistics": self.alert_stats
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, indent=2, default=str)
        
        self.logger.info(f"Alert history exported to {filepath}")