"""
Automation API routes for controlling analytics workflows
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from ...core.orchestrator import AnalyticsOrchestrator, WorkflowStatus

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


@router.get("/automation/workflows")
async def get_workflows(
    status: Optional[str] = Query(None, description="Filter by workflow status"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: int = Query(50, description="Maximum number of workflows to return"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get list of automation workflows"""
    try:
        workflows = []
        
        # Get workflows from orchestrator
        for workflow_id, workflow_info in orchestrator.workflows.items():
            workflow_data = {
                'id': workflow_id,
                'name': workflow_info.name,
                'status': workflow_info.status.value,
                'start_time': workflow_info.start_time.isoformat() if workflow_info.start_time else None,
                'end_time': workflow_info.end_time.isoformat() if workflow_info.end_time else None,
                'duration': workflow_info.duration,
                'retry_count': workflow_info.retry_count,
                'error_message': workflow_info.error_message,
                'results_summary': {
                    'total_keys': len(workflow_info.results),
                    'has_error': workflow_info.error_message is not None
                }
            }
            
            # Filter by status if specified
            if status and workflow_info.status.value != status:
                continue
            
            # Filter by component if specified (simple heuristic)
            if component:
                workflow_name_lower = workflow_info.name.lower()
                component_lower = component.lower()
                if component_lower not in workflow_name_lower:
                    continue
            
            workflows.append(workflow_data)
        
        # Sort by start time (newest first)
        workflows.sort(key=lambda x: x['start_time'] or '', reverse=True)
        
        # Apply limit
        workflows = workflows[:limit]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_workflows': len(workflows),
            'workflows': workflows,
            'summary': {
                'by_status': _get_workflow_status_summary(workflows),
                'running_workflows': len([w for w in workflows if w['status'] == 'running']),
                'completed_workflows': len([w for w in workflows if w['status'] == 'completed']),
                'failed_workflows': len([w for w in workflows if w['status'] == 'failed'])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")


@router.get("/automation/workflows/{workflow_id}")
async def get_workflow_details(
    workflow_id: str,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get detailed information about a specific workflow"""
    try:
        if workflow_id not in orchestrator.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow_info = orchestrator.workflows[workflow_id]
        
        # Get detailed workflow information
        workflow_details = {
            'id': workflow_id,
            'name': workflow_info.name,
            'status': workflow_info.status.value,
            'start_time': workflow_info.start_time.isoformat() if workflow_info.start_time else None,
            'end_time': workflow_info.end_time.isoformat() if workflow_info.end_time else None,
            'duration': workflow_info.duration,
            'retry_count': workflow_info.retry_count,
            'error_message': workflow_info.error_message,
            'results': workflow_info.results,
            'progress': _calculate_workflow_progress(workflow_info),
            'timeline': _get_workflow_timeline(workflow_info)
        }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'workflow': workflow_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow details: {str(e)}")


@router.post("/automation/workflows/{workflow_id}/start")
async def start_workflow(
    workflow_id: str,
    parameters: Optional[Dict[str, Any]] = Query(None, description="Workflow parameters"),
    background_tasks: BackgroundTasks = None,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Start a specific workflow"""
    try:
        # Define available workflows
        workflow_functions = {
            'health_monitoring': orchestrator._run_health_monitoring_workflow,
            'security_scanning': orchestrator._run_security_scanning_workflow,
            'automation_tracking': orchestrator._run_automation_tracking_workflow,
            'community_analysis': orchestrator._run_community_analysis_workflow
        }
        
        if workflow_id not in workflow_functions:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        # Check if workflow is already running
        if workflow_id in orchestrator.workflows:
            existing_workflow = orchestrator.workflows[workflow_id]
            if existing_workflow.status == WorkflowStatus.RUNNING:
                raise HTTPException(status_code=400, detail=f"Workflow {workflow_id} is already running")
        
        # Define workflow name
        workflow_name = _get_workflow_display_name(workflow_id)
        
        # Execute workflow
        async def execute_workflow():
            try:
                await orchestrator.execute_workflow(workflow_id, workflow_name, workflow_functions[workflow_id])
            except Exception as e:
                logger.error(f"Workflow execution failed: {str(e)}")
        
        if background_tasks:
            background_tasks.add_task(execute_workflow)
        else:
            # Execute synchronously
            await execute_workflow()
        
        return {
            'message': f'Workflow {workflow_id} started successfully',
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'initiated'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.post("/automation/workflows/{workflow_id}/stop")
async def stop_workflow(
    workflow_id: str,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Stop a specific workflow"""
    try:
        if workflow_id not in orchestrator.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow_info = orchestrator.workflows[workflow_id]
        
        if workflow_info.status != WorkflowStatus.RUNNING:
            raise HTTPException(status_code=400, detail=f"Workflow {workflow_id} is not running")
        
        # For now, we can't actually stop a running workflow asynchronously
        # This would require implementing proper workflow cancellation
        # For demonstration, we'll mark it as cancelled
        
        workflow_info.status = WorkflowStatus.CANCELLED
        workflow_info.end_time = datetime.utcnow()
        workflow_info.duration = (workflow_info.end_time - workflow_info.start_time).total_seconds() if workflow_info.start_time else None
        
        return {
            'message': f'Workflow {workflow_id} stop requested',
            'workflow_id': workflow_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'stop_requested'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop workflow: {str(e)}")


@router.get("/automation/status")
async def get_automation_status(
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get overall automation status"""
    try:
        # Get orchestrator status
        orchestrator_status = orchestrator.get_status()
        
        # Get component automation status
        component_status = {}
        for component_name, component_info in orchestrator.components.items():
            # Get component-specific automation data
            try:
                component_data = await orchestrator.integration_manager.collect_component_data(component_name)
                component_status[component_name] = {
                    'status': component_info.status,
                    'enabled': component_info.enabled,
                    'automation_data': _extract_automation_data(component_name, component_data)
                }
            except Exception as e:
                logger.warning(f"Failed to get automation data for {component_name}: {str(e)}")
                component_status[component_name] = {
                    'status': component_info.status,
                    'enabled': component_info.enabled,
                    'automation_data': {},
                    'error': str(e)
                }
        
        # Get workflow summary
        workflow_summary = _get_workflow_status_summary(orchestrator.workflows.values())
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'orchestrator': {
                'running': orchestrator_status.get('orchestrator', {}).get('running', False),
                'uptime_seconds': orchestrator_status.get('orchestrator', {}).get('uptime_seconds', 0)
            },
            'components': component_status,
            'workflows': {
                'summary': workflow_summary,
                'total_workflows': len(orchestrator.workflows),
                'running_workflows': sum(1 for w in orchestrator.workflows.values() if w.status == WorkflowStatus.RUNNING)
            },
            'automation_health': {
                'overall_status': _determine_automation_health(component_status, workflow_summary),
                'enabled_components': sum(1 for c in component_status.values() if c.get('enabled', False)),
                'healthy_components': sum(1 for c in component_status.values() if c.get('status') == 'healthy')
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get automation status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation status: {str(e)}")


@router.get("/automation/metrics")
async def get_automation_metrics(
    component: Optional[str] = Query(None, description="Filter by component"),
    hours: int = Query(24, description="Hours of metrics to retrieve"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get automation performance metrics"""
    try:
        automation_metrics = {}
        
        # Get component metrics
        for component_name, component_info in orchestrator.components.items():
            if component and component_name != component:
                continue
            
            try:
                # Get component data
                component_data = await orchestrator.integration_manager.collect_component_data(component_name)
                
                # Extract automation metrics based on component type
                if component_name == 'follow_automation':
                    automation_metrics[component_name] = _extract_follow_automation_metrics(component_data)
                elif component_name == 'security_scanner':
                    automation_metrics[component_name] = _extract_security_automation_metrics(component_data)
                elif component_name == 'health_monitor':
                    automation_metrics[component_name] = _extract_health_automation_metrics(component_data)
                elif component_name == 'daily_contributions':
                    automation_metrics[component_name] = _extract_contributions_automation_metrics(component_data)
                else:
                    automation_metrics[component_name] = _extract_generic_automation_metrics(component_data)
                
                automation_metrics[component_name]['component_status'] = component_info.status
                automation_metrics[component_name]['last_updated'] = datetime.utcnow().isoformat()
                
            except Exception as e:
                logger.warning(f"Failed to get automation metrics for {component_name}: {str(e)}")
                automation_metrics[component_name] = {
                    'error': str(e),
                    'component_status': component_info.status
                }
        
        # Calculate summary metrics
        summary = _calculate_automation_summary(automation_metrics)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'metrics': automation_metrics,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get automation metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation metrics: {str(e)}")


@router.post("/automation/actions")
async def execute_automation_action(
    component: str = Query(..., description="Component to execute action on"),
    action: str = Query(..., description="Action to execute"),
    parameters: Optional[Dict[str, Any]] = Query(None, description="Action parameters"),
    background_tasks: BackgroundTasks = None,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Execute a specific automation action on a component"""
    try:
        # Validate component exists
        if component not in orchestrator.components:
            raise HTTPException(status_code=404, detail=f"Component {component} not found")
        
        # Execute action through integration manager
        result = await orchestrator.integration_manager.run_component_action(component, action, **(parameters or {}))
        
        # Schedule background execution if needed
        if background_tasks and not result.get('success', False):
            # This would be for long-running actions
            pass
        
        return {
            'message': f'Action {action} executed on component {component}',
            'component': component,
            'action': action,
            'parameters': parameters or {},
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute automation action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute action: {str(e)}")


@router.get("/automation/schedules")
async def get_automation_schedules(
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get automation schedules and next run times"""
    try:
        # Get workflow schedules from orchestrator configuration
        workflow_config = orchestrator.config.get('workflows', {})
        schedules = workflow_config.get('schedules', {})
        
        schedule_info = []
        for workflow_name, cron_schedule in schedules.items():
            # Calculate next run time (simplified)
            next_run = _calculate_next_run_time(cron_schedule)
            
            schedule_info.append({
                'workflow': workflow_name,
                'cron_schedule': cron_schedule,
                'next_run': next_run.isoformat() if next_run else None,
                'description': _get_workflow_description(workflow_name),
                'status': 'active'  # Could be dynamic based on component status
            })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_schedules': len(schedule_info),
            'schedules': schedule_info,
            'summary': {
                'daily_schedules': len([s for s in schedule_info if '2' in s['cron_schedule'] or '3' in s['cron_schedule']]),
                'hourly_schedules': len([s for s in schedule_info if '*/4' in s['cron_schedule']]),
                'weekly_schedules': len([s for s in schedule_info if '0 0 * * 0' in s['cron_schedule']])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get automation schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation schedules: {str(e)}")


# Helper functions
def _get_workflow_status_summary(workflows: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get summary of workflow statuses"""
    summary = {
        'pending': 0,
        'running': 0,
        'completed': 0,
        'failed': 0,
        'cancelled': 0,
        'retrying': 0
    }
    
    for workflow in workflows:
        status = workflow.get('status', 'unknown')
        summary[status] = summary.get(status, 0) + 1
    
    return summary


def _calculate_workflow_progress(workflow_info) -> Dict[str, Any]:
    """Calculate workflow progress"""
    try:
        if workflow_info.status == WorkflowStatus.COMPLETED:
            return {'percent': 100, 'stage': 'completed'}
        elif workflow_info.status == WorkflowStatus.FAILED:
            return {'percent': 0, 'stage': 'failed'}
        elif workflow_info.status == WorkflowStatus.RUNNING and workflow_info.start_time:
            # Estimate progress based on duration
            elapsed = (datetime.utcnow() - workflow_info.start_time).total_seconds()
            # Assume workflows take around 5 minutes on average
            estimated_duration = 300
            percent = min(100, (elapsed / estimated_duration) * 100)
            return {'percent': percent, 'stage': 'running'}
        else:
            return {'percent': 0, 'stage': workflow_info.status.value}
    except Exception:
        return {'percent': 0, 'stage': 'unknown'}


def _get_workflow_timeline(workflow_info) -> List[Dict[str, str]]:
    """Get workflow timeline events"""
    timeline = []
    
    if workflow_info.start_time:
        timeline.append({
            'timestamp': workflow_info.start_time.isoformat(),
            'event': 'started',
            'description': 'Workflow execution started'
        })
    
    if workflow_info.end_time:
        timeline.append({
            'timestamp': workflow_info.end_time.isoformat(),
            'event': 'completed' if workflow_info.status == WorkflowStatus.COMPLETED else 'failed',
            'description': f'Workflow {"completed successfully" if workflow_info.status == WorkflowStatus.COMPLETED else "failed"}'
        })
    
    return timeline


def _get_workflow_display_name(workflow_id: str) -> str:
    """Get human-readable workflow name"""
    names = {
        'health_monitoring': 'Daily Health Monitoring',
        'security_scanning': 'Daily Security Scanning',
        'automation_tracking': 'Automation Performance Tracking',
        'community_analysis': 'Weekly Community Analysis'
    }
    return names.get(workflow_id, workflow_id.replace('_', ' ').title())


def _determine_automation_health(component_status: Dict[str, Dict], workflow_summary: Dict[str, int]) -> str:
    """Determine overall automation health"""
    try:
        # Check component health
        failed_components = sum(1 for c in component_status.values() if c.get('component_status') == 'failed')
        if failed_components > len(component_status) / 2:
            return 'critical'
        
        # Check workflow health
        failed_workflows = workflow_summary.get('failed', 0)
        total_workflows = sum(workflow_summary.values())
        
        if total_workflows > 0 and failed_workflows / total_workflows > 0.3:
            return 'degraded'
        
        # Overall assessment
        healthy_components = sum(1 for c in component_status.values() if c.get('component_status') == 'healthy')
        if healthy_components == len(component_status):
            return 'healthy'
        else:
            return 'degraded'
            
    except Exception:
        return 'unknown'


def _extract_automation_data(component_name: str, component_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract automation-specific data from component data"""
    try:
        if component_name == 'follow_automation':
            return {
                'enabled': component_data.get('automation_status', {}).get('enabled', False),
                'safety_mode': component_data.get('safety_status', {}).get('safe_mode', False),
                'success_rate': component_data.get('follow_metrics', {}).get('success_rate', 0)
            }
        elif component_name == 'security_scanner':
            return {
                'last_scan': component_data.get('scan_results', {}).get('last_scan'),
                'vulnerabilities_found': sum(component_data.get('vulnerability_counts', {}).values()),
                'compliance_score': component_data.get('compliance_status', {}).get('score', 0)
            }
        elif component_name == 'health_monitor':
            return {
                'repositories_monitored': len(component_data.get('health_scores', [])),
                'active_alerts': len([a for a in component_data.get('alerts', []) if a.get('status') == 'active']),
                'average_health_score': sum(s.get('score', 0) for s in component_data.get('health_scores', [])) / max(1, len(component_data.get('health_scores', [])))
            }
        elif component_name == 'daily_contributions':
            return {
                'total_contributions': component_data.get('contribution_metrics', {}).get('total_contributions', 0),
                'active_contributors': component_data.get('community_data', {}).get('active_contributors', 0),
                'growth_rate': component_data.get('growth_metrics', {}).get('growth_rate', 0)
            }
        else:
            return {
                'component_type': component_name,
                'data_points': len(component_data)
            }
    except Exception:
        return {'error': 'Failed to extract automation data'}


def _extract_follow_automation_metrics(component_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract follow automation specific metrics"""
    return {
        'total_actions': component_data.get('follow_metrics', {}).get('total_actions', 0),
        'successful_actions': component_data.get('follow_metrics', {}).get('successful_actions', 0),
        'success_rate': component_data.get('follow_metrics', {}).get('success_rate', 0),
        'rate_limit_hits': component_data.get('rate_limit', {}).get('hits', 0),
        'safety_compliance': component_data.get('safety_status', {}).get('compliance_score', 0)
    }


def _extract_security_automation_metrics(component_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract security automation specific metrics"""
    return {
        'last_scan': component_data.get('scan_results', {}).get('last_scan'),
        'vulnerabilities': component_data.get('vulnerability_counts', {}),
        'total_issues': sum(component_data.get('vulnerability_counts', {}).values()),
        'security_score': 100 - sum(component_data.get('vulnerability_counts', {}).values())
    }


def _extract_health_automation_metrics(component_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract health monitoring specific metrics"""
    return {
        'repositories': len(component_data.get('health_scores', [])),
        'average_health_score': sum(s.get('score', 0) for s in component_data.get('health_scores', [])) / max(1, len(component_data.get('health_scores', []))),
        'active_alerts': len([a for a in component_data.get('alerts', []) if a.get('status') == 'active'])
    }


def _extract_contributions_automation_metrics(component_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract daily contributions specific metrics"""
    return {
        'total_contributions': component_data.get('contribution_metrics', {}).get('total_contributions', 0),
        'new_contributors': component_data.get('growth_metrics', {}).get('new_contributors', 0),
        'retention_rate': component_data.get('growth_metrics', {}).get('retention_rate', 0)
    }


def _extract_generic_automation_metrics(component_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract generic automation metrics"""
    return {
        'data_points': len(component_data),
        'has_status': 'status' in component_data,
        'has_metrics': 'metrics' in component_data,
        'last_updated': component_data.get('collection_timestamp')
    }


def _calculate_automation_summary(automation_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate summary of automation metrics"""
    try:
        enabled_components = sum(1 for m in automation_metrics.values() if m.get('component_status') == 'healthy')
        total_components = len(automation_metrics)
        
        # Calculate overall success rate (example calculation)
        success_rates = []
        for component_name, metrics in automation_metrics.items():
            if 'success_rate' in metrics:
                success_rates.append(metrics['success_rate'])
        
        average_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        return {
            'total_components': total_components,
            'enabled_components': enabled_components,
            'success_rate': average_success_rate,
            'health_status': 'healthy' if enabled_components == total_components else 'degraded'
        }
    except Exception:
        return {'error': 'Failed to calculate summary'}


def _calculate_next_run_time(cron_schedule: str) -> Optional[datetime]:
    """Calculate next run time from cron schedule (simplified)"""
    try:
        # This is a simplified implementation
        # In production, you'd use a proper cron parser like croniter
        
        now = datetime.utcnow()
        
        if cron_schedule == '0 2 * * *':  # Daily at 2 AM
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        elif cron_schedule == '0 3 * * *':  # Daily at 3 AM
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        elif cron_schedule == '0 */4 * * *':  # Every 4 hours
            next_run = now.replace(minute=0, second=0, microsecond=0)
            current_hour_block = now.hour // 4
            next_run = next_run.replace(hour=(current_hour_block + 1) * 4)
            if next_run <= now or next_run.hour >= 24:
                next_run = next_run.replace(hour=0) + timedelta(days=1)
            return next_run
        elif cron_schedule == '0 0 * * 0':  # Weekly on Sunday
            days_ahead = 6 - now.weekday()  # Sunday is 6
            next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
            if next_run <= now:
                next_run += timedelta(days=7)
            return next_run
        else:
            return None
            
    except Exception:
        return None


def _get_workflow_description(workflow_name: str) -> str:
    """Get description for workflow"""
    descriptions = {
        'health_monitoring': 'Daily comprehensive health analysis of all repositories',
        'security_scanning': 'Daily security vulnerability assessment and compliance check',
        'automation_tracking': 'Performance monitoring of all automation components',
        'community_analysis': 'Weekly community growth and engagement analysis'
    }
    return descriptions.get(workflow_name, 'Automated workflow execution')