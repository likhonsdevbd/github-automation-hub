"""
Webhooks API routes for external integrations and event handling
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
import hmac
import hashlib
import json

from ...core.orchestrator import AnalyticsOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator: Optional[AnalyticsOrchestrator] = None


def get_orchestrator() -> AnalyticsOrchestrator:
    """Get the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        from ...core.orchestrator import AnalyticsOrchestrator
        _orchestrator = AnalyticsOrchestrator()
    return _orchestrator


@router.post("/webhooks/github")
async def handle_github_webhook(
    request: Request,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Handle GitHub webhooks for repository events"""
    try:
        # Get request body
        body = await request.body()
        
        # Verify webhook signature if secret is configured
        if not await _verify_github_signature(request, body):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse webhook payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Extract webhook information
        event_type = request.headers.get('X-GitHub-Event', 'unknown')
        action = payload.get('action', 'unknown')
        
        # Process webhook based on event type
        if event_type == 'push':
            await _handle_push_event(payload, orchestrator)
        elif event_type == 'pull_request':
            await _handle_pull_request_event(payload, action, orchestrator)
        elif event_type == 'issues':
            await _handle_issues_event(payload, action, orchestrator)
        elif event_type == 'repository':
            await _handle_repository_event(payload, action, orchestrator)
        elif event_type == 'workflow_run':
            await _handle_workflow_run_event(payload, orchestrator)
        else:
            logger.info(f"Received unhandled GitHub webhook event: {event_type}")
        
        return {
            'status': 'success',
            'message': f'Webhook {event_type} processed successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process GitHub webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


@router.post("/webhooks/health-monitor")
async def handle_health_monitor_webhook(
    request: Request,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Handle webhooks from health monitoring system"""
    try:
        body = await request.body()
        payload = json.loads(body.decode('utf-8'))
        
        event_type = payload.get('event_type', 'unknown')
        
        if event_type == 'health_score_updated':
            await _handle_health_score_update(payload, orchestrator)
        elif event_type == 'alert_triggered':
            await _handle_health_alert(payload, orchestrator)
        elif event_type == 'repository_added':
            await _handle_repository_added(payload, orchestrator)
        else:
            logger.info(f"Received unhandled health monitor webhook: {event_type}")
        
        return {
            'status': 'success',
            'message': f'Health monitor webhook {event_type} processed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process health monitor webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


@router.post("/webhooks/automation")
async def handle_automation_webhook(
    request: Request,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Handle webhooks from automation systems"""
    try:
        body = await request.body()
        payload = json.loads(body.decode('utf-8'))
        
        event_type = payload.get('event_type', 'unknown')
        component = payload.get('component', 'unknown')
        
        if event_type == 'action_completed':
            await _handle_automation_action_completed(payload, orchestrator)
        elif event_type == 'safety_triggered':
            await _handle_automation_safety_triggered(payload, orchestrator)
        elif event_type == 'rate_limit_hit':
            await _handle_automation_rate_limit(payload, orchestrator)
        else:
            logger.info(f"Received unhandled automation webhook: {event_type}")
        
        return {
            'status': 'success',
            'message': f'Automation webhook {event_type} processed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process automation webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


@router.post("/webhooks/custom")
async def handle_custom_webhook(
    request: Request,
    source: str = Query(..., description="Webhook source identifier"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Handle custom webhooks from external systems"""
    try:
        body = await request.body()
        payload = json.loads(body.decode('utf-8'))
        
        # Add source information to payload
        payload['_webhook_source'] = source
        payload['_received_at'] = datetime.utcnow().isoformat()
        
        # Store webhook data for processing
        await _store_custom_webhook(source, payload, orchestrator)
        
        # Trigger appropriate processing based on source
        await _process_custom_webhook(source, payload, orchestrator)
        
        return {
            'status': 'success',
            'message': f'Custom webhook from {source} processed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process custom webhook from {source}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


@router.get("/webhooks/logs")
async def get_webhook_logs(
    source: Optional[str] = Query(None, description="Filter by webhook source"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    hours: int = Query(24, description="Hours of logs to retrieve"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get webhook processing logs"""
    try:
        # This would typically query a webhook logs store
        # For now, return mock data
        
        logs = []
        
        # Generate sample logs based on filters
        webhook_sources = ['github', 'health-monitor', 'automation', 'custom'] if not source else [source]
        event_types = ['push', 'pull_request', 'health_score_updated', 'action_completed'] if not event_type else [event_type]
        
        for i in range(min(limit, 20)):  # Generate sample logs
            timestamp = datetime.utcnow() - timedelta(minutes=i * 30)
            log_entry = {
                'id': f"webhook_log_{i}",
                'source': webhook_sources[i % len(webhook_sources)],
                'event_type': event_types[i % len(event_types)],
                'timestamp': timestamp.isoformat(),
                'status': 'success' if i % 10 != 0 else 'failed',
                'processing_time_ms': (i % 5) * 100 + 50,
                'payload_size_bytes': 1024 + (i * 100),
                'message': f'Webhook {event_types[i % len(event_types)]} processed successfully'
            }
            
            # Apply filters
            if source and log_entry['source'] != source:
                continue
            if event_type and log_entry['event_type'] != event_type:
                continue
            
            logs.append(log_entry)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'total_logs': len(logs),
            'logs': logs,
            'summary': {
                'by_source': {src: len([l for l in logs if l['source'] == src]) for src in webhook_sources},
                'by_status': {'success': len([l for l in logs if l['status'] == 'success']), 'failed': len([l for l in logs if l['status'] == 'failed'])},
                'average_processing_time_ms': sum(l['processing_time_ms'] for l in logs) / len(logs) if logs else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook logs: {str(e)}")


@router.get("/webhooks/subscriptions")
async def get_webhook_subscriptions(
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get configured webhook subscriptions"""
    try:
        # This would typically query a subscriptions store
        # For now, return configured subscriptions
        
        subscriptions = [
            {
                'id': 'github_main',
                'source': 'github',
                'url': '/api/v1/webhooks/github',
                'events': ['push', 'pull_request', 'issues', 'repository', 'workflow_run'],
                'secret_configured': True,
                'active': True,
                'created_at': '2024-01-01T00:00:00Z',
                'description': 'GitHub repository events webhook'
            },
            {
                'id': 'health_monitor_main',
                'source': 'health-monitor',
                'url': '/api/v1/webhooks/health-monitor',
                'events': ['health_score_updated', 'alert_triggered', 'repository_added'],
                'secret_configured': False,
                'active': True,
                'created_at': '2024-01-01T00:00:00Z',
                'description': 'Health monitoring system events'
            },
            {
                'id': 'automation_main',
                'source': 'automation',
                'url': '/api/v1/webhooks/automation',
                'events': ['action_completed', 'safety_triggered', 'rate_limit_hit'],
                'secret_configured': False,
                'active': True,
                'created_at': '2024-01-01T00:00:00Z',
                'description': 'Automation system events'
            }
        ]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_subscriptions': len(subscriptions),
            'active_subscriptions': len([s for s in subscriptions if s['active']]),
            'subscriptions': subscriptions
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook subscriptions: {str(e)}")


@router.post("/webhooks/test")
async def test_webhook(
    source: str = Query(..., description="Test webhook source"),
    event_type: str = Query(..., description="Test event type"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Send a test webhook to verify connectivity"""
    try:
        # Generate test payload
        test_payload = {
            'event_type': event_type,
            'source': source,
            'test': True,
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Test webhook from {source} with event type {event_type}',
            'payload': {
                'test_data': 'This is a test webhook payload',
                'webhook_id': f'test_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}'
            }
        }
        
        # Process test webhook
        await _process_custom_webhook(source, test_payload, orchestrator)
        
        return {
            'status': 'success',
            'message': 'Test webhook sent successfully',
            'test_payload': test_payload,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send test webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test webhook: {str(e)}")


# Event handler functions
async def _handle_push_event(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle GitHub push events"""
    try:
        repository = payload.get('repository', {})
        commits = payload.get('commits', [])
        
        # Update repository health data
        repo_name = repository.get('full_name', 'unknown')
        
        # Trigger health monitoring update
        if 'health_monitor' in orchestrator.components:
            try:
                await orchestrator.integration_manager.run_component_action(
                    'health_monitor', 'update_repository_health',
                    repository=repo_name,
                    commits_count=len(commits)
                )
            except Exception as e:
                logger.warning(f"Failed to update repository health for {repo_name}: {str(e)}")
        
        # Update metrics
        await orchestrator.data_pipeline.store_component_metrics('github_push', {
            'repository': repo_name,
            'commits_count': len(commits),
            'pusher': payload.get('pusher', {}).get('name', 'unknown'),
            'ref': payload.get('ref', 'unknown')
        })
        
        logger.info(f"Processed push event for {repo_name} with {len(commits)} commits")
        
    except Exception as e:
        logger.error(f"Failed to handle push event: {str(e)}")


async def _handle_pull_request_event(payload: Dict[str, Any], action: str, orchestrator: AnalyticsOrchestrator):
    """Handle GitHub pull request events"""
    try:
        repository = payload.get('repository', {})
        pull_request = payload.get('pull_request', {})
        
        repo_name = repository.get('full_name', 'unknown')
        pr_number = pull_request.get('number', 0)
        
        # Update metrics based on action
        if action in ['opened', 'closed', 'merged']:
            await orchestrator.data_pipeline.store_component_metrics('github_pull_request', {
                'repository': repo_name,
                'action': action,
                'pr_number': pr_number,
                'author': pull_request.get('user', {}).get('login', 'unknown'),
                'title': pull_request.get('title', 'unknown')[:100]  # Truncate long titles
            })
        
        logger.info(f"Processed pull request {action} event for {repo_name} PR #{pr_number}")
        
    except Exception as e:
        logger.error(f"Failed to handle pull request event: {str(e)}")


async def _handle_issues_event(payload: Dict[str, Any], action: str, orchestrator: AnalyticsOrchestrator):
    """Handle GitHub issues events"""
    try:
        repository = payload.get('repository', {})
        issue = payload.get('issue', {})
        
        repo_name = repository.get('full_name', 'unknown')
        issue_number = issue.get('number', 0)
        
        # Update community engagement metrics
        await orchestrator.data_pipeline.store_component_metrics('github_issues', {
            'repository': repo_name,
            'action': action,
            'issue_number': issue_number,
            'author': issue.get('user', {}).get('login', 'unknown'),
            'state': issue.get('state', 'unknown'),
            'labels_count': len(issue.get('labels', []))
        })
        
        logger.info(f"Processed issue {action} event for {repo_name} issue #{issue_number}")
        
    except Exception as e:
        logger.error(f"Failed to handle issues event: {str(e)}")


async def _handle_repository_event(payload: Dict[str, Any], action: str, orchestrator: AnalyticsOrchestrator):
    """Handle GitHub repository events"""
    try:
        repository = payload.get('repository', {})
        repo_name = repository.get('full_name', 'unknown')
        
        if action == 'created':
            # Add new repository to monitoring
            await _add_repository_to_monitoring(repo_name, orchestrator)
        elif action == 'deleted':
            # Remove repository from monitoring
            await _remove_repository_from_monitoring(repo_name, orchestrator)
        
        await orchestrator.data_pipeline.store_component_metrics('github_repository', {
            'repository': repo_name,
            'action': action,
            'private': repository.get('private', False),
            'fork': repository.get('fork', False)
        })
        
        logger.info(f"Processed repository {action} event for {repo_name}")
        
    except Exception as e:
        logger.error(f"Failed to handle repository event: {str(e)}")


async def _handle_workflow_run_event(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle GitHub workflow run events"""
    try:
        repository = payload.get('repository', {})
        workflow_run = payload.get('workflow_run', {})
        
        repo_name = repository.get('full_name', 'unknown')
        conclusion = workflow_run.get('conclusion', 'unknown')
        
        # Update CI/CD metrics
        await orchestrator.data_pipeline.store_component_metrics('github_workflows', {
            'repository': repo_name,
            'workflow_name': workflow_run.get('name', 'unknown'),
            'conclusion': conclusion,
            'duration_seconds': workflow_run.get('run_started_at') and workflow_run.get('updated_at'),
            'actor': workflow_run.get('actor', {}).get('login', 'unknown')
        })
        
        logger.info(f"Processed workflow run event for {repo_name}: {conclusion}")
        
    except Exception as e:
        logger.error(f"Failed to handle workflow run event: {str(e)}")


async def _handle_health_score_update(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle health score update events"""
    try:
        repository = payload.get('repository', 'unknown')
        score = payload.get('score', 0)
        grade = payload.get('grade', 'N/A')
        
        # Store health score
        await orchestrator.data_pipeline.store_component_metrics('health_score_update', {
            'repository': repository,
            'score': score,
            'grade': grade,
            'update_reason': payload.get('reason', 'scheduled_update')
        })
        
        logger.info(f"Processed health score update for {repository}: {score} ({grade})")
        
    except Exception as e:
        logger.error(f"Failed to handle health score update: {str(e)}")


async def _handle_health_alert(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle health alert events"""
    try:
        repository = payload.get('repository', 'unknown')
        severity = payload.get('severity', 'medium')
        alert_message = payload.get('message', 'Health alert')
        
        # Store alert
        await orchestrator.data_pipeline.store_component_metrics('health_alert', {
            'repository': repository,
            'severity': severity,
            'message': alert_message,
            'alert_type': payload.get('type', 'general')
        })
        
        logger.info(f"Processed health alert for {repository}: {severity} - {alert_message}")
        
    except Exception as e:
        logger.error(f"Failed to handle health alert: {str(e)}")


async def _handle_repository_added(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle repository added events"""
    try:
        repository = payload.get('repository', 'unknown')
        
        # Update monitoring list
        await orchestrator.data_pipeline.store_component_metrics('repository_added', {
            'repository': repository,
            'added_by': payload.get('added_by', 'system'),
            'configuration': payload.get('config', {})
        })
        
        logger.info(f"Processed repository added event: {repository}")
        
    except Exception as e:
        logger.error(f"Failed to handle repository added: {str(e)}")


async def _handle_automation_action_completed(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle automation action completed events"""
    try:
        component = payload.get('component', 'unknown')
        action = payload.get('action', 'unknown')
        success = payload.get('success', False)
        
        # Store automation metrics
        await orchestrator.data_pipeline.store_component_metrics('automation_action', {
            'component': component,
            'action': action,
            'success': success,
            'duration_seconds': payload.get('duration_seconds', 0),
            'target': payload.get('target', 'unknown')
        })
        
        logger.info(f"Processed automation action completed: {component}.{action} = {success}")
        
    except Exception as e:
        logger.error(f"Failed to handle automation action: {str(e)}")


async def _handle_automation_safety_triggered(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle automation safety triggered events"""
    try:
        component = payload.get('component', 'unknown')
        safety_type = payload.get('safety_type', 'unknown')
        
        # Store safety event
        await orchestrator.data_pipeline.store_component_metrics('automation_safety', {
            'component': component,
            'safety_type': safety_type,
            'reason': payload.get('reason', 'unknown'),
            'automatically_triggered': payload.get('auto_triggered', False)
        })
        
        logger.warning(f"Automation safety triggered for {component}: {safety_type}")
        
    except Exception as e:
        logger.error(f"Failed to handle automation safety: {str(e)}")


async def _handle_automation_rate_limit(payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Handle automation rate limit events"""
    try:
        component = payload.get('component', 'unknown')
        limit_type = payload.get('limit_type', 'api_rate_limit')
        
        # Store rate limit event
        await orchestrator.data_pipeline.store_component_metrics('automation_rate_limit', {
            'component': component,
            'limit_type': limit_type,
            'reset_time': payload.get('reset_time'),
            'current_usage': payload.get('current_usage', 0),
            'limit': payload.get('limit', 0)
        })
        
        logger.info(f"Automation rate limit hit for {component}: {limit_type}")
        
    except Exception as e:
        logger.error(f"Failed to handle automation rate limit: {str(e)}")


async def _store_custom_webhook(source: str, payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Store custom webhook for processing"""
    try:
        await orchestrator.data_pipeline.store_component_metrics('custom_webhook', {
            'source': source,
            'event_type': payload.get('event_type', 'custom'),
            'payload_size': len(json.dumps(payload)),
            'received_at': payload.get('_received_at')
        })
        
    except Exception as e:
        logger.error(f"Failed to store custom webhook: {str(e)}")


async def _process_custom_webhook(source: str, payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Process custom webhook based on source"""
    try:
        event_type = payload.get('event_type', 'custom')
        
        # Route to appropriate processor based on source
        if source == 'monitoring':
            await _process_monitoring_webhook(event_type, payload, orchestrator)
        elif source == 'alerts':
            await _process_alerts_webhook(event_type, payload, orchestrator)
        elif source == 'external_api':
            await _process_external_api_webhook(event_type, payload, orchestrator)
        else:
            logger.info(f"Processing custom webhook from {source}: {event_type}")
        
    except Exception as e:
        logger.error(f"Failed to process custom webhook from {source}: {str(e)}")


async def _process_monitoring_webhook(event_type: str, payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Process monitoring system webhooks"""
    # Implementation for monitoring system webhooks
    pass


async def _process_alerts_webhook(event_type: str, payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Process alerts system webhooks"""
    # Implementation for alerts system webhooks
    pass


async def _process_external_api_webhook(event_type: str, payload: Dict[str, Any], orchestrator: AnalyticsOrchestrator):
    """Process external API webhooks"""
    # Implementation for external API webhooks
    pass


async def _add_repository_to_monitoring(repository: str, orchestrator: AnalyticsOrchestrator):
    """Add repository to health monitoring"""
    try:
        if 'health_monitor' in orchestrator.components:
            await orchestrator.integration_manager.run_component_action(
                'health_monitor', 'add_repository',
                repository=repository
            )
    except Exception as e:
        logger.warning(f"Failed to add repository {repository} to monitoring: {str(e)}")


async def _remove_repository_from_monitoring(repository: str, orchestrator: AnalyticsOrchestrator):
    """Remove repository from health monitoring"""
    try:
        if 'health_monitor' in orchestrator.components:
            await orchestrator.integration_manager.run_component_action(
                'health_monitor', 'remove_repository',
                repository=repository
            )
    except Exception as e:
        logger.warning(f"Failed to remove repository {repository} from monitoring: {str(e)}")


async def _verify_github_signature(request: Request, body: bytes) -> bool:
    """Verify GitHub webhook signature"""
    try:
        # Get signature from header
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not signature:
            return False
        
        # Get secret from environment or config (this would be configured)
        secret = 'your-webhook-secret'  # This should be from environment variable
        
        # Calculate expected signature
        expected_signature = 'sha256=' + hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant time)
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception:
        return False


@router.get("/webhooks/events")
async def get_supported_events():
    """Get list of supported webhook events"""
    try:
        events = {
            'github': [
                'push', 'pull_request', 'issues', 'repository', 
                'workflow_run', 'release', 'deployment'
            ],
            'health_monitor': [
                'health_score_updated', 'alert_triggered', 'repository_added',
                'repository_removed', 'bulk_update_completed'
            ],
            'automation': [
                'action_completed', 'safety_triggered', 'rate_limit_hit',
                'workflow_started', 'workflow_completed'
            ],
            'custom': [
                'data_received', 'alert_received', 'status_update',
                'metric_threshold_breached'
            ]
        }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'supported_events': events,
            'total_events': sum(len(event_list) for event_list in events.values())
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported events: {str(e)}")