import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import yaml
import psutil

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class EscalationLevel(Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    MANAGER = "manager"
    EXECUTIVE = "executive"

@dataclass
class AlertRule:
    name: str
    description: str
    query: str
    severity: AlertSeverity
    threshold: float
    duration: int  # seconds
    enabled: bool = True
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}

@dataclass
class Alert:
    id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    current_value: float
    threshold: float
    first_triggered: datetime
    last_triggered: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_1
    notification_channels: List[str] = None
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = []
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}
        if self.details is None:
            self.details = {}

class AlertManager:
    """Central alert management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.escalation_policies: Dict[AlertSeverity, Dict[int, List[str]]] = {}
        self.notification_callbacks: Dict[str, Callable] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Load default escalation policies
        self._setup_default_escalation_policies()
        
    def _setup_default_escalation_policies(self):
        """Set up default escalation policies"""
        # Critical alerts
        self.escalation_policies[AlertSeverity.CRITICAL] = {
            0: ["slack", "email"],  # Immediate
            300: ["slack", "discord", "sms"],  # 5 minutes
            900: ["slack", "discord", "sms", "phone"],  # 15 minutes
            1800: ["slack", "discord", "sms", "phone", "pagerduty"]  # 30 minutes
        }
        
        # Warning alerts
        self.escalation_policies[AlertSeverity.WARNING] = {
            0: ["slack"],  # Immediate
            600: ["slack", "email"],  # 10 minutes
            1800: ["slack", "email", "discord"]  # 30 minutes
        }
        
        # Info alerts
        self.escalation_policies[AlertSeverity.INFO] = {
            0: ["slack"],  # Immediate
            3600: ["email"]  # 1 hour
        }
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def add_escalation_policy(self, severity: AlertSeverity, level: int, channels: List[str]):
        """Add escalation policy for specific severity and level"""
        if severity not in self.escalation_policies:
            self.escalation_policies[severity] = {}
        self.escalation_policies[severity][level] = channels
        logger.info(f"Added escalation policy: {severity.value} level {level} -> {channels}")
    
    def register_notification_callback(self, channel: str, callback: Callable):
        """Register notification callback for a channel"""
        self.notification_callbacks[channel] = callback
        logger.info(f"Registered notification callback for: {channel}")
    
    def load_rules_from_file(self, file_path: str):
        """Load alert rules from YAML file"""
        try:
            with open(file_path, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            for rule_data in rules_data.get('rules', []):
                rule = AlertRule(
                    name=rule_data['name'],
                    description=rule_data['description'],
                    query=rule_data['query'],
                    severity=AlertSeverity(rule_data['severity']),
                    threshold=rule_data['threshold'],
                    duration=rule_data['duration'],
                    labels=rule_data.get('labels', {}),
                    annotations=rule_data.get('annotations', {})
                )
                self.add_alert_rule(rule)
                
            logger.info(f"Loaded {len(self.rules)} alert rules from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load alert rules from {file_path}: {e}")
    
    async def evaluate_rules(self, metrics_data: Dict[str, Any]) -> List[str]:
        """Evaluate all alert rules against current metrics"""
        triggered_alerts = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                # Execute rule query (simplified - in real implementation, use proper query engine)
                current_value = self._evaluate_rule_query(rule.query, metrics_data)
                
                if current_value is None:
                    continue
                
                # Check if threshold is exceeded
                if self._check_threshold(current_value, rule.threshold):
                    alert_key = f"{rule.name}"
                    
                    if alert_key not in self.active_alerts:
                        # Create new alert
                        alert = Alert(
                            id=f"{rule.name}_{int(datetime.now().timestamp())}",
                            name=rule.name,
                            description=rule.description,
                            severity=rule.severity,
                            status=AlertStatus.ACTIVE,
                            current_value=current_value,
                            threshold=rule.threshold,
                            first_triggered=datetime.now(),
                            last_triggered=datetime.now(),
                            labels=rule.labels,
                            annotations=rule.annotations,
                            details={
                                'query': rule.query,
                                'duration': rule.duration
                            }
                        )
                        
                        self.active_alerts[alert_key] = alert
                        triggered_alerts.append(alert_key)
                        
                        logger.warning(f"New alert triggered: {rule.name} - {current_value} >= {rule.threshold}")
                        
                        # Send notifications
                        await self._send_notifications(alert, "triggered")
                        
                    else:
                        # Update existing alert
                        alert = self.active_alerts[alert_key]
                        alert.current_value = current_value
                        alert.last_triggered = datetime.now()
                        
                        # Check for escalation
                        await self._check_escalation(alert)
                else:
                    # Check if alert should be resolved
                    alert_key = f"{rule.name}"
                    if alert_key in self.active_alerts:
                        await self._resolve_alert(alert_key)
                        
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
        
        return triggered_alerts
    
    def _evaluate_rule_query(self, query: str, metrics_data: Dict[str, Any]) -> Optional[float]:
        """Simplified rule query evaluation"""
        try:
            # This is a simplified implementation
            # In a real system, you'd use a proper query language or evaluator
            
            # Parse simple comparisons: metric > threshold, metric < threshold, etc.
            if '>' in query:
                parts = query.split('>')
                metric_name = parts[0].strip()
                if metric_name in metrics_data:
                    return float(metrics_data[metric_name])
            
            elif '<' in query:
                parts = query.split('<')
                metric_name = parts[0].strip()
                if metric_name in metrics_data:
                    return float(metrics_data[metric_name])
            
            elif '==' in query:
                parts = query.split('==')
                metric_name = parts[0].strip()
                if metric_name in metrics_data:
                    return float(metrics_data[metric_name])
            
            # Handle direct metric lookups
            if query in metrics_data:
                return float(metrics_data[query])
                
        except (ValueError, KeyError) as e:
            logger.error(f"Error evaluating query '{query}': {e}")
            
        return None
    
    def _check_threshold(self, value: float, threshold: float) -> bool:
        """Check if value exceeds threshold"""
        return value >= threshold
    
    async def _send_notifications(self, alert: Alert, event_type: str):
        """Send notifications for alert"""
        try:
            # Determine which channels to use based on severity and escalation
            channels = self._get_notification_channels(alert)
            
            notification_data = {
                'alert': alert,
                'event_type': event_type,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to each configured channel
            for channel in channels:
                if channel in self.notification_callbacks:
                    try:
                        await self.notification_callbacks[channel](notification_data)
                    except Exception as e:
                        logger.error(f"Failed to send notification to {channel}: {e}")
                        
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def _get_notification_channels(self, alert: Alert) -> List[str]:
        """Get notification channels for an alert"""
        # Get base channels for severity
        severity_policies = self.escalation_policies.get(alert.severity, {})
        
        # Find channels for current escalation level
        elapsed_time = (datetime.now() - alert.first_triggered).total_seconds()
        
        for time_threshold, channels in sorted(severity_policies.items()):
            if elapsed_time >= time_threshold:
                return channels
        
        return []
    
    async def _check_escalation(self, alert: Alert):
        """Check if alert should be escalated"""
        elapsed_time = (datetime.now() - alert.first_triggered).total_seconds()
        
        # Check for escalation timeouts
        escalation_policies = self.escalation_policies.get(alert.severity, {})
        
        for time_threshold, channels in escalation_policies.items():
            if elapsed_time >= time_threshold:
                current_channels = self._get_notification_channels(alert)
                if len(channels) > len(current_channels):
                    # Escalate to next level
                    await self._escalate_alert(alert, channels[len(current_channels):])
    
    async def _escalate_alert(self, alert: Alert, new_channels: List[str]):
        """Escalate alert to higher level"""
        alert.escalation_level = EscalationLevel(alert.escalation_level.value + 1)
        alert.status = AlertStatus.ESCALATED
        
        logger.warning(f"Alert escalated: {alert.name} -> {alert.escalation_level.name}")
        
        # Send escalation notifications
        await self._send_notifications(alert, "escalated")
    
    async def acknowledge_alert(self, alert_id: str, user: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user
            alert.acknowledged_at = datetime.now()
            
            logger.info(f"Alert acknowledged: {alert_id} by {user}")
            
            # Send acknowledgment notifications
            await self._send_notifications(alert, "acknowledged")
    
    async def _resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # Move to history
            self.alert_history.append(alert)
            
            logger.info(f"Alert resolved: {alert_id}")
            
            # Send resolution notifications
            await self._send_notifications(alert, "resolved")
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.active_alerts) + len(self.alert_history)
        resolved_alerts = len([a for a in self.alert_history if a.status == AlertStatus.RESOLVED])
        critical_alerts = len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL])
        warning_alerts = len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.WARNING])
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': len(self.active_alerts),
            'resolved_alerts': resolved_alerts,
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'acknowledged_alerts': len([a for a in self.active_alerts.values() if a.status == AlertStatus.ACKNOWLEDGED])
        }

class SystemMonitor:
    """System monitoring for alert rules"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.running = False
        
    async def start_monitoring(self, interval: int = 30):
        """Start system monitoring"""
        self.running = True
        logger.info(f"Started system monitoring with {interval}s interval")
        
        while self.running:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                
                # Evaluate alert rules
                triggered_alerts = await self.alert_manager.evaluate_rules(metrics)
                
                if triggered_alerts:
                    logger.info(f"Triggered alerts: {triggered_alerts}")
                
                # Wait for next cycle
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(interval)
    
    async def stop_monitoring(self):
        """Stop system monitoring"""
        self.running = False
        logger.info("Stopped system monitoring")
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        metrics = {}
        
        try:
            # CPU usage
            metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            mem = psutil.virtual_memory()
            metrics['memory_usage'] = mem.percent
            metrics['memory_available'] = mem.available
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics['disk_usage'] = disk.percent
            metrics['disk_free'] = disk.free
            
            # Process count
            metrics['process_count'] = len(psutil.pids())
            
            # Load average (Unix systems)
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                metrics['load_avg_1m'] = load_avg[0]
                metrics['load_avg_5m'] = load_avg[1]
                metrics['load_avg_15m'] = load_avg[2]
            
            # Network I/O
            net_io = psutil.net_io_counters()
            metrics['network_bytes_sent'] = net_io.bytes_sent
            metrics['network_bytes_recv'] = net_io.bytes_recv
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics

# Example configuration and usage
async def main():
    # Configuration
    config = {
        'prometheus_url': 'http://localhost:9090',
        'slack_webhook': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
        'email_config': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password'
        }
    }
    
    # Initialize alert manager
    alert_manager = AlertManager(config)
    
    # Load default alert rules
    default_rules = [
        AlertRule(
            name="High CPU Usage",
            description="CPU usage above 80%",
            query="cpu_usage",
            severity=AlertSeverity.CRITICAL,
            threshold=80.0,
            duration=60,
            labels={'monitor': 'system'},
            annotations={'summary': 'High CPU usage detected'}
        ),
        AlertRule(
            name="High Memory Usage",
            description="Memory usage above 85%",
            query="memory_usage",
            severity=AlertSeverity.WARNING,
            threshold=85.0,
            duration=300,
            labels={'monitor': 'system'},
            annotations={'summary': 'High memory usage detected'}
        ),
        AlertRule(
            name="Disk Space Low",
            description="Disk usage above 90%",
            query="disk_usage",
            severity=AlertSeverity.CRITICAL,
            threshold=90.0,
            duration=30,
            labels={'monitor': 'system'},
            annotations={'summary': 'Disk space critically low'}
        )
    ]
    
    for rule in default_rules:
        alert_manager.add_alert_rule(rule)
    
    # Register notification callbacks
    async def slack_notification(data):
        print(f"Slack notification: {data['alert'].name}")
    
    async def email_notification(data):
        print(f"Email notification: {data['alert'].name}")
    
    alert_manager.register_notification_callback('slack', slack_notification)
    alert_manager.register_notification_callback('email', email_notification)
    
    # Start monitoring
    system_monitor = SystemMonitor(alert_manager)
    monitoring_task = asyncio.create_task(system_monitor.start_monitoring(30))
    
    # Run for a while
    await asyncio.sleep(120)
    
    # Stop monitoring
    await system_monitor.stop_monitoring()
    monitoring_task.cancel()
    
    # Show statistics
    stats = alert_manager.get_alert_statistics()
    print(f"Alert statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(main())