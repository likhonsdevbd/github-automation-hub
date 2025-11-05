"""
Telemetry Logger - Comprehensive telemetry and analytics tracking.

Records automation activities, performance metrics, and compliance data
for monitoring, optimization, and audit purposes.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class TelemetryEvent:
    """Telemetry event data structure."""
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = None


class TelemetryLogger:
    """
    Comprehensive telemetry logger for the automation hub.
    
    Tracks:
    - Automation actions and outcomes
    - Performance metrics
    - Rate limit events
    - Compliance signals
    - System health indicators
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enabled = config.get('enabled', True)
        self.audit_log_retention_days = config.get('audit_log_retention_days', 30)
        self.privacy_mode = config.get('privacy_mode', True)
        
        # Data storage
        self.events: List[TelemetryEvent] = []
        self.metrics: List[PerformanceMetric] = []
        self.session_start = datetime.now()
        
        # Aggregated statistics
        self.stats = {
            'session_start': self.session_start,
            'total_events': 0,
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'rate_limit_events': 0,
            'compliance_events': 0,
            'average_action_latency': 0.0
        }
        
        # Action tracking for performance analysis
        self.action_timings = defaultdict(list)
        
        if self.enabled:
            self.logger.info("Telemetry logger initialized")
    
    def record_event(self, event_type: str, data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """
        Record a telemetry event.
        
        Args:
            event_type: Type of event (e.g., 'follow_action', 'rate_limit_hit', 'compliance_alert')
            data: Event data
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        # Apply privacy controls
        sanitized_data = self._sanitize_data(data) if self.privacy_mode else data.copy()
        
        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            data=sanitized_data,
            metadata=metadata
        )
        
        self.events.append(event)
        self.stats['total_events'] += 1
        
        # Log at appropriate level
        if event_type in ['compliance_alert', 'emergency_stop', 'enforcement_signal']:
            self.logger.warning(f"Telemetry: {event_type} - {sanitized_data}")
        else:
            self.logger.debug(f"Telemetry: {event_type} - {sanitized_data}")
    
    def record_action(self, action_type: str, username: str, status: str, 
                     response_code: Optional[int] = None, latency: float = 0.0,
                     rate_limit_remaining: Optional[int] = None):
        """
        Record an automation action.
        
        Args:
            action_type: Type of action ('follow', 'unfollow')
            username: Target username
            status: Action status ('success', 'failed', 'error')
            response_code: HTTP response code
            latency: Action latency in seconds
            rate_limit_remaining: Remaining API calls
        """
        action_data = {
            'action_type': action_type,
            'username': username,
            'status': status,
            'response_code': response_code,
            'latency_seconds': latency,
            'rate_limit_remaining': rate_limit_remaining
        }
        
        self.record_event('automation_action', action_data)
        
        # Update statistics
        self.stats['total_actions'] += 1
        if status == 'success':
            self.stats['successful_actions'] += 1
        else:
            self.stats['failed_actions'] += 1
        
        # Track performance
        self.action_timings[f'{action_type}_{status}'].append(latency)
        
        # Calculate running average latency
        all_latencies = []
        for timings in self.action_timings.values():
            all_latencies.extend(timings)
        
        if all_latencies:
            self.stats['average_action_latency'] = sum(all_latencies) / len(all_latencies)
    
    def record_rate_limit_event(self, event_type: str, details: Dict[str, Any]):
        """
        Record a rate limit related event.
        
        Args:
            event_type: Type of rate limit event ('429_hit', 'reset_window', 'backoff_applied')
            details: Event details
        """
        rate_limit_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        self.record_event('rate_limit', rate_limit_data)
        self.stats['rate_limit_events'] += 1
    
    def record_compliance_event(self, event_type: str, details: Dict[str, Any]):
        """
        Record a compliance-related event.
        
        Args:
            event_type: Type of compliance event ('422_error', 'policy_violation', 'emergency_stop')
            details: Event details
        """
        compliance_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'compliance_status': 'violation' if event_type in ['422_error', 'policy_violation'] else 'alert'
        }
        
        self.record_event('compliance', compliance_data)
        self.stats['compliance_events'] += 1
    
    def record_performance_metric(self, metric_name: str, value: float, unit: str, tags: Dict[str, str] = None):
        """
        Record a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            tags: Additional tags for filtering
        """
        if not self.enabled:
            return
        
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the current session."""
        runtime = datetime.now() - self.session_start
        runtime_hours = runtime.total_seconds() / 3600
        
        return {
            'session_duration': {
                'total_seconds': runtime.total_seconds(),
                'hours': runtime_hours,
                'start_time': self.session_start.isoformat(),
                'end_time': datetime.now().isoformat()
            },
            'action_statistics': {
                'total_actions': self.stats['total_actions'],
                'successful_actions': self.stats['successful_actions'],
                'failed_actions': self.stats['failed_actions'],
                'success_rate': (self.stats['successful_actions'] / max(self.stats['total_actions'], 1)) * 100,
                'actions_per_hour': self.stats['total_actions'] / max(runtime_hours, 0.1)
            },
            'performance_metrics': {
                'average_action_latency': self.stats['average_action_latency'],
                'total_events': self.stats['total_events'],
                'rate_limit_events': self.stats['rate_limit_events'],
                'compliance_events': self.stats['compliance_events']
            },
            'action_breakdown': self._get_action_breakdown(),
            'error_analysis': self._get_error_analysis()
        }
    
    def _get_action_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of actions by type and status."""
        breakdown = defaultdict(lambda: defaultdict(int))
        
        for event in self.events:
            if event.event_type == 'automation_action':
                action_type = event.data.get('action_type', 'unknown')
                status = event.data.get('status', 'unknown')
                breakdown[action_type][status] += 1
        
        return dict(breakdown)
    
    def _get_error_analysis(self) -> Dict[str, Any]:
        """Analyze error patterns and rates."""
        errors = []
        rate_limit_errors = []
        compliance_issues = []
        
        for event in self.events:
            if event.event_type == 'automation_action':
                if event.data.get('status') != 'success':
                    errors.append(event.data)
            elif event.event_type == 'rate_limit':
                if event.data.get('event_type') == '429_hit':
                    rate_limit_errors.append(event.data)
            elif event.event_type == 'compliance':
                if event.data.get('compliance_status') == 'violation':
                    compliance_issues.append(event.data)
        
        return {
            'total_errors': len(errors),
            'rate_limit_errors': len(rate_limit_errors),
            'compliance_violations': len(compliance_issues),
            'recent_errors': errors[-10:] if errors else [],  # Last 10 errors
            'error_rate_per_hour': len(errors) / max(self._get_runtime_hours(), 0.1)
        }
    
    def _get_runtime_hours(self) -> float:
        """Get session runtime in hours."""
        return (datetime.now() - self.session_start).total_seconds() / 3600
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for privacy protection."""
        sanitized = data.copy()
        
        # Remove or mask sensitive information
        sensitive_keys = ['token', 'password', 'api_key', 'secret']
        
        def sanitize_dict(d):
            if isinstance(d, dict):
                return {k: sanitize_dict(v) if k not in sensitive_keys else '***REDACTED***' 
                       for k, v in d.items()}
            elif isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            else:
                return d
        
        return sanitize_dict(sanitized)
    
    def export_metrics(self, format: str = 'json', output_file: str = None) -> str:
        """
        Export telemetry data to file.
        
        Args:
            format: Export format ('json' or 'csv')
            output_file: Output file path
            
        Returns:
            str: Path to exported file
        """
        if not self.enabled:
            self.logger.warning("Telemetry is disabled, cannot export metrics")
            return ""
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"telemetry_export_{timestamp}.{format}"
        
        if format.lower() == 'json':
            self._export_json(output_file)
        elif format.lower() == 'csv':
            self._export_csv(output_file)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        self.logger.info(f"Telemetry data exported to {output_file}")
        return output_file
    
    def _export_json(self, file_path: str):
        """Export telemetry data as JSON."""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'session_info': {
                'start_time': self.session_start.isoformat(),
                'duration_hours': self._get_runtime_hours()
            },
            'statistics': self.stats,
            'performance_summary': self.get_performance_summary(),
            'events': [asdict(event) for event in self.events],
            'metrics': [asdict(metric) for metric in self.metrics]
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def _export_csv(self, file_path: str):
        """Export events as CSV."""
        import csv
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'timestamp', 'event_type', 'action_type', 'username', 'status', 
                'response_code', 'latency_seconds', 'rate_limit_remaining'
            ])
            
            # Write event data
            for event in self.events:
                if event.event_type == 'automation_action':
                    writer.writerow([
                        event.timestamp.isoformat(),
                        event.event_type,
                        event.data.get('action_type', ''),
                        event.data.get('username', ''),
                        event.data.get('status', ''),
                        event.data.get('response_code', ''),
                        event.data.get('latency_seconds', ''),
                        event.data.get('rate_limit_remaining', '')
                    ])
    
    def cleanup_old_data(self):
        """Clean up old telemetry data based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.audit_log_retention_days)
        
        # Filter events
        old_count = len(self.events)
        self.events = [event for event in self.events if event.timestamp > cutoff_date]
        cleaned_count = old_count - len(self.events)
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old telemetry events")
        
        # Filter metrics
        old_metric_count = len(self.metrics)
        self.metrics = [metric for metric in self.metrics if metric.timestamp > cutoff_date]
        cleaned_metrics_count = old_metric_count - len(self.metrics)
        
        if cleaned_metrics_count > 0:
            self.logger.info(f"Cleaned up {cleaned_metrics_count} old metrics")
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report for audit purposes."""
        runtime_hours = self._get_runtime_hours()
        
        compliance_data = {
            'report_timestamp': datetime.now().isoformat(),
            'session_info': {
                'start_time': self.session_start.isoformat(),
                'duration_hours': runtime_hours
            },
            'compliance_score': self._calculate_compliance_score(),
            'risk_indicators': self._get_risk_indicators(),
            'recommendations': self._get_compliance_recommendations(),
            'audit_trail': self._get_audit_trail()
        }
        
        return compliance_data
    
    def _calculate_compliance_score(self) -> float:
        """Calculate overall compliance score (0-100)."""
        if self.stats['total_actions'] == 0:
            return 100.0  # No actions = full compliance
        
        score = 100.0
        
        # Deduct points for errors
        error_rate = self.stats['failed_actions'] / self.stats['total_actions']
        score -= error_rate * 50  # Max 50 points for error rate
        
        # Deduct points for compliance events
        compliance_violations = len([e for e in self.events if e.event_type == 'compliance' and 
                                   e.data.get('compliance_status') == 'violation'])
        score -= compliance_violations * 10  # 10 points per violation
        
        # Deduct points for rate limit issues
        rate_limit_issues = len([e for e in self.events if e.event_type == 'rate_limit' and 
                               e.data.get('event_type') == '429_hit'])
        score -= rate_limit_issues * 5  # 5 points per rate limit hit
        
        return max(0.0, min(100.0, score))
    
    def _get_risk_indicators(self) -> List[Dict[str, Any]]:
        """Get list of risk indicators."""
        risks = []
        
        # High error rate
        if self.stats['total_actions'] > 10:
            error_rate = self.stats['failed_actions'] / self.stats['total_actions']
            if error_rate > 0.2:
                risks.append({
                    'type': 'high_error_rate',
                    'severity': 'high' if error_rate > 0.5 else 'medium',
                    'value': error_rate,
                    'description': f'Error rate of {error_rate:.1%} exceeds threshold'
                })
        
        # Compliance violations
        violations = [e for e in self.events if e.event_type == 'compliance' and 
                     e.data.get('compliance_status') == 'violation']
        if violations:
            risks.append({
                'type': 'compliance_violations',
                'severity': 'high',
                'count': len(violations),
                'description': f'{len(violations)} compliance violations detected'
            })
        
        # Frequent rate limiting
        rate_limit_hits = len([e for e in self.events if e.event_type == 'rate_limit' and 
                             e.data.get('event_type') == '429_hit'])
        if rate_limit_hits > 5:
            risks.append({
                'type': 'frequent_rate_limiting',
                'severity': 'medium',
                'count': rate_limit_hits,
                'description': f'{rate_limit_hits} rate limit hits in session'
            })
        
        return risks
    
    def _get_compliance_recommendations(self) -> List[str]:
        """Get compliance recommendations based on telemetry data."""
        recommendations = []
        
        # Error rate recommendations
        if self.stats['total_actions'] > 0:
            error_rate = self.stats['failed_actions'] / self.stats['total_actions']
            if error_rate > 0.1:
                recommendations.append("Review and address high error rate - consider reducing action frequency")
        
        # Rate limit recommendations
        rate_limit_hits = len([e for e in self.events if e.event_type == 'rate_limit'])
        if rate_limit_hits > 0:
            recommendations.append("Increase delays between actions to reduce rate limit occurrences")
        
        # General safety recommendations
        if not self.config.get('privacy_mode', True):
            recommendations.append("Enable privacy mode to protect sensitive data in logs")
        
        return recommendations
    
    def _get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get audit trail for compliance reporting."""
        audit_events = []
        
        for event in self.events:
            if event.event_type in ['automation_action', 'compliance', 'rate_limit']:
                audit_events.append({
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type,
                    'summary': self._summarize_event(event),
                    'data': event.data
                })
        
        return audit_events[-100:]  # Last 100 events for audit trail
    
    def _summarize_event(self, event: TelemetryEvent) -> str:
        """Create a human-readable summary of an event."""
        if event.event_type == 'automation_action':
            action_type = event.data.get('action_type', 'unknown')
            status = event.data.get('status', 'unknown')
            username = event.data.get('username', 'unknown')
            return f"{action_type} {status} for {username}"
        elif event.event_type == 'compliance':
            return f"Compliance: {event.data.get('event_type', 'unknown')}"
        elif event.event_type == 'rate_limit':
            return f"Rate limit: {event.data.get('event_type', 'unknown')}"
        else:
            return f"{event.event_type}: {event.data.get('summary', 'No summary')}"
