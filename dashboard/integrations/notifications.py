import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    ALERT = "alert"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"

@dataclass
class NotificationMessage:
    type: NotificationType
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = None
    severity: Optional[str] = None

class NotificationIntegrations:
    """Handle notifications across multiple platforms"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.slack_webhook = config.get('slack_webhook_url')
        self.discord_webhook = config.get('discord_webhook_url')
        self.teams_webhook = config.get('teams_webhook_url')
        
    async def send_notification(self, notification: NotificationMessage) -> Dict[str, bool]:
        """Send notification to all configured platforms"""
        results = {}
        
        # Send to Slack
        if self.slack_webhook:
            results['slack'] = await self._send_slack_notification(notification)
        
        # Send to Discord
        if self.discord_webhook:
            results['discord'] = await self._send_discord_notification(notification)
        
        # Send to Teams
        if self.teams_webhook:
            results['teams'] = await self._send_teams_notification(notification)
            
        return results
    
    async def _send_slack_notification(self, notification: NotificationMessage) -> bool:
        """Send notification to Slack"""
        try:
            async with aiohttp.ClientSession() as session:
                # Determine color based on notification type
                color = {
                    NotificationType.ERROR: 'danger',
                    NotificationType.WARNING: 'warning',
                    NotificationType.SUCCESS: 'good',
                    NotificationType.ALERT: 'warning',
                    NotificationType.INFO: '#36a3d9'
                }.get(notification.type, '#36a3d9')
                
                payload = {
                    "channel": self.config.get('slack_channel', '#automation-alerts'),
                    "username": "Automation Hub",
                    "icon_emoji": ":robot_face:",
                    "attachments": [
                        {
                            "color": color,
                            "title": notification.title,
                            "text": notification.message,
                            "fields": [
                                {
                                    "title": "Type",
                                    "value": notification.type.value,
                                    "short": True
                                },
                                {
                                    "title": "Severity",
                                    "value": notification.severity or "N/A",
                                    "short": True
                                }
                            ],
                            "footer": notification.source or "Automation Hub",
                            "ts": int(notification.timestamp.timestamp()) if notification.timestamp else int(datetime.now().timestamp())
                        }
                    ]
                }
                
                # Add details if available
                if notification.details:
                    payload["attachments"][0]["fields"].append({
                        "title": "Details",
                        "value": f"```{json.dumps(notification.details, indent=2)}```",
                        "short": False
                    })
                
                async with session.post(self.slack_webhook, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent: {notification.title}")
                        return True
                    else:
                        logger.error(f"Slack notification failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    async def _send_discord_notification(self, notification: NotificationMessage) -> bool:
        """Send notification to Discord"""
        try:
            async with aiohttp.ClientSession() as session:
                # Determine color based on severity
                color = {
                    'critical': 0xff0000,  # Red
                    'warning': 0xffa500,   # Orange
                    'info': 0x00ff00,      # Green
                    'success': 0x00ff00,   # Green
                    'error': 0xff0000      # Red
                }.get(notification.severity or notification.type.value, 0x00ff00)
                
                payload = {
                    "embeds": [
                        {
                            "title": notification.title,
                            "description": notification.message,
                            "color": color,
                            "timestamp": (notification.timestamp or datetime.now()).isoformat(),
                            "footer": {
                                "text": notification.source or "Automation Hub"
                            },
                            "fields": []
                        }
                    ]
                }
                
                # Add type and severity fields
                payload["embeds"][0]["fields"].append({
                    "name": "Type",
                    "value": notification.type.value,
                    "inline": True
                })
                
                payload["embeds"][0]["fields"].append({
                    "name": "Severity",
                    "value": notification.severity or "N/A",
                    "inline": True
                })
                
                # Add details if available
                if notification.details:
                    payload["embeds"][0]["fields"].append({
                        "name": "Details",
                        "value": f"```json\n{json.dumps(notification.details, indent=2)}\n```",
                        "inline": False
                    })
                
                async with session.post(self.discord_webhook, json=payload) as response:
                    if response.status in [200, 204]:
                        logger.info(f"Discord notification sent: {notification.title}")
                        return True
                    else:
                        logger.error(f"Discord notification failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
    
    async def _send_teams_notification(self, notification: NotificationMessage) -> bool:
        """Send notification to Microsoft Teams"""
        try:
            async with aiohttp.ClientSession() as session:
                # Microsoft Teams card format
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "summary": notification.title,
                    "themeColor": {
                        'critical': 'FF0000',
                        'warning': 'FFA500',
                        'info': '00FF00',
                        'success': '00FF00',
                        'error': 'FF0000'
                    }.get(notification.severity or notification.type.value, '00FF00'),
                    "title": notification.title,
                    "text": notification.message,
                    "sections": [
                        {
                            "activityTitle": notification.source or "Automation Hub",
                            "activitySubtitle": notification.timestamp.strftime("%Y-%m-%d %H:%M:%S") if notification.timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "facts": [
                                {
                                    "name": "Type",
                                    "value": notification.type.value
                                },
                                {
                                    "name": "Severity",
                                    "value": notification.severity or "N/A"
                                }
                            ]
                        }
                    ]
                }
                
                # Add details if available
                if notification.details:
                    payload["sections"][0]["text"] += f"\n\n**Details:**\n```json\n{json.dumps(notification.details, indent=2)}\n```"
                
                async with session.post(self.teams_webhook, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Teams notification sent: {notification.title}")
                        return True
                    else:
                        logger.error(f"Teams notification failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return False
    
    async def test_notifications(self) -> Dict[str, bool]:
        """Test all notification channels"""
        test_notification = NotificationMessage(
            type=NotificationType.INFO,
            title="Test Notification",
            message="This is a test notification from Automation Hub Dashboard",
            source="Dashboard Test",
            severity="info"
        )
        
        return await self.send_notification(test_notification)

class NotificationManager:
    """Central notification manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.integrations = NotificationIntegrations(config)
        self.notification_history: List[NotificationMessage] = []
        self.rate_limits: Dict[str, List[datetime]] = {}
        
    async def send_alert(self, title: str, message: str, severity: str = "info", details: Optional[Dict] = None) -> Dict[str, bool]:
        """Send alert notification"""
        notification = NotificationMessage(
            type=NotificationType.ALERT,
            title=title,
            message=message,
            severity=severity,
            details=details,
            timestamp=datetime.now(),
            source="Alert System"
        )
        
        # Add to history
        self.notification_history.append(notification)
        
        # Check rate limiting
        if self._is_rate_limited(severity):
            logger.warning(f"Rate limit exceeded for {severity} notifications")
            return {}
        
        # Send notification
        results = await self.integrations.send_notification(notification)
        
        # Update rate limit
        self._update_rate_limit(severity)
        
        return results
    
    async def send_system_alert(self, alert_type: str, details: Dict[str, Any]) -> Dict[str, bool]:
        """Send system alert notification"""
        severity = "critical" if "critical" in alert_type.lower() else "warning"
        
        return await self.send_alert(
            title=f"System Alert: {alert_type}",
            message=f"System {alert_type} has been detected",
            severity=severity,
            details=details
        )
    
    async def send_automation_alert(self, automation_type: str, status: str, details: Optional[Dict] = None) -> Dict[str, bool]:
        """Send automation alert notification"""
        severity = "error" if status == "failed" else "info"
        
        return await self.send_alert(
            title=f"Automation {status.title()}",
            message=f"{automation_type} automation has {status}",
            severity=severity,
            details=details
        )
    
    def _is_rate_limited(self, severity: str) -> bool:
        """Check if notification type is rate limited"""
        current_time = datetime.now()
        rate_limit_window = 300  # 5 minutes
        
        # Clean old entries
        if severity in self.rate_limits:
            self.rate_limits[severity] = [
                timestamp for timestamp in self.rate_limits[severity]
                if (current_time - timestamp).total_seconds() < rate_limit_window
            ]
            
            # Check if limit exceeded (10 notifications per 5 minutes)
            if len(self.rate_limits[severity]) >= 10:
                return True
        
        return False
    
    def _update_rate_limit(self, severity: str):
        """Update rate limit tracking"""
        current_time = datetime.now()
        
        if severity not in self.rate_limits:
            self.rate_limits[severity] = []
            
        self.rate_limits[severity].append(current_time)
    
    async def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history"""
        recent_notifications = sorted(
            self.notification_history,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]
        
        return [
            {
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "timestamp": n.timestamp.isoformat(),
                "source": n.source,
                "severity": n.severity
            }
            for n in recent_notifications
        ]

# Example usage and configuration
async def main():
    # Example configuration
    config = {
        'slack_webhook_url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
        'discord_webhook_url': 'https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK',
        'teams_webhook_url': 'https://your-org.webhook.office.com/webhookb2/YOUR/TEAMS/WEBHOOK',
        'slack_channel': '#automation-alerts'
    }
    
    # Initialize notification manager
    manager = NotificationManager(config)
    
    # Test notifications
    await manager.test_notifications()
    
    # Send a system alert
    await manager.send_system_alert("high_cpu_usage", {
        "cpu_usage": 85,
        "threshold": 80,
        "host": "automation-hub-01"
    })

if __name__ == "__main__":
    asyncio.run(main())