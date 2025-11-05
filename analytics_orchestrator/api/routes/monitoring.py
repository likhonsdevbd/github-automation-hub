"""
Monitoring API routes for the analytics orchestrator
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

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


@router.get("/monitoring/status")
async def get_monitoring_status(
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get comprehensive monitoring status"""
    try:
        # Get orchestrator status
        orchestrator_status = orchestrator.get_status()
        
        # Get component health status
        component_health = {}
        for component_name, component_info in orchestrator_status.get('components', {}).items():
            component_health[component_name] = {
                'status': component_info.get('status'),
                'health_score': component_info.get('health_score', 0),
                'last_check': component_info.get('last_check'),
                'error': component_info.get('error_message')
            }
        
        # Get data pipeline health
        pipeline_health = await orchestrator.data_pipeline.get_health_status()
        
        # Get system metrics
        system_metrics = await _get_system_metrics()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': _determine_overall_status(component_health, pipeline_health),
            'orchestrator': {
                'running': orchestrator_status.get('orchestrator', {}).get('running', False),
                'uptime_seconds': orchestrator_status.get('orchestrator', {}).get('uptime_seconds', 0),
                'start_time': orchestrator_status.get('orchestrator', {}).get('start_time')
            },
            'components': component_health,
            'data_pipeline': pipeline_health,
            'system_metrics': system_metrics,
            'health_summary': {
                'total_components': len(component_health),
                'healthy_components': sum(1 for c in component_health.values() if c.get('status') == 'healthy'),
                'degraded_components': sum(1 for c in component_health.values() if c.get('status') == 'degraded'),
                'failed_components': sum(1 for c in component_health.values() if c.get('status') == 'failed'),
                'average_health_score': _calculate_average_health_score(component_health)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")


@router.get("/monitoring/health/scores")
async def get_health_scores(
    component: Optional[str] = Query(None, description="Filter by component"),
    hours: int = Query(24, description="Hours of health score history"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get health scores for components"""
    try:
        health_scores = []
        
        # Get health scores from health monitoring component if available
        if 'health_monitor' in orchestrator.components:
            try:
                health_data = await orchestrator.integration_manager.collect_component_data('health_monitor')
                repository_scores = health_data.get('health_scores', [])
                
                for score_data in repository_scores:
                    health_scores.append({
                        'component': 'health_monitor',
                        'source': score_data.get('repository', 'unknown'),
                        'score': score_data.get('score', 0),
                        'grade': score_data.get('grade', 'N/A'),
                        'timestamp': score_data.get('timestamp', datetime.utcnow().isoformat()),
                        'metrics': score_data.get('metrics', {})
                    })
            except Exception as e:
                logger.warning(f"Failed to get health monitor scores: {str(e)}")
        
        # Get health scores from orchestrator components
        for component_name, component_info in orchestrator.components.items():
            if component is None or component == component_name:
                health_score = component_info.health_score if hasattr(component_info, 'health_score') else 0
                
                health_scores.append({
                    'component': component_name,
                    'source': component_name,
                    'score': health_score,
                    'grade': _score_to_grade(health_score),
                    'status': component_info.status,
                    'last_check': component_info.last_check.isoformat() if component_info.last_check else None
                })
        
        # Filter by component if specified
        if component:
            health_scores = [score for score in health_scores if score['component'] == component]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'total_scores': len(health_scores),
            'health_scores': health_scores,
            'summary': {
                'average_score': sum(s.get('score', 0) for s in health_scores) / len(health_scores) if health_scores else 0,
                'score_distribution': _calculate_score_distribution(health_scores),
                'top_performers': sorted(health_scores, key=lambda x: x.get('score', 0), reverse=True)[:5]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get health scores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health scores: {str(e)}")


@router.get("/monitoring/alerts")
async def get_monitoring_alerts(
    component: Optional[str] = Query(None, description="Filter by component"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low)"),
    hours: int = Query(24, description="Hours of alert history"),
    limit: int = Query(50, description="Maximum number of alerts to return"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get monitoring alerts"""
    try:
        alerts = []
        
        # Get alerts from health monitoring component
        if 'health_monitor' in orchestrator.components:
            try:
                health_data = await orchestrator.integration_manager.collect_component_data('health_monitor')
                component_alerts = health_data.get('alerts', [])
                
                for alert in component_alerts:
                    alerts.append({
                        'id': alert.get('id', f"alert_{len(alerts)}"),
                        'component': 'health_monitor',
                        'severity': alert.get('severity', 'medium'),
                        'title': alert.get('title', 'Health Alert'),
                        'message': alert.get('message', ''),
                        'source': alert.get('repository', 'unknown'),
                        'timestamp': alert.get('timestamp', datetime.utcnow().isoformat()),
                        'status': alert.get('status', 'active'),
                        'metadata': alert.get('metadata', {})
                    })
            except Exception as e:
                logger.warning(f"Failed to get health monitor alerts: {str(e)}")
        
        # Get alerts from component health checks
        for component_name, component_info in orchestrator.components.items():
            if component_info.error_message:
                alerts.append({
                    'id': f"{component_name}_error",
                    'component': component_name,
                    'severity': 'high',
                    'title': f'{component_name.title()} Component Error',
                    'message': component_info.error_message,
                    'source': component_name,
                    'timestamp': component_info.last_check.isoformat() if component_info.last_check else datetime.utcnow().isoformat(),
                    'status': 'active'
                })
        
        # Filter by component if specified
        if component:
            alerts = [alert for alert in alerts if alert['component'] == component]
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert['severity'] == severity]
        
        # Filter by time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        alerts = [
            alert for alert in alerts
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        
        # Sort by timestamp (newest first) and limit
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        alerts = alerts[:limit]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'total_alerts': len(alerts),
            'alerts': alerts,
            'summary': {
                'by_severity': {severity: len([a for a in alerts if a['severity'] == severity]) for severity in ['critical', 'high', 'medium', 'low']},
                'by_component': {comp: len([a for a in alerts if a['component'] == comp]) for comp in set(a['component'] for a in alerts)},
                'active_alerts': len([a for a in alerts if a['status'] == 'active']),
                'resolved_alerts': len([a for a in alerts if a['status'] == 'resolved'])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring alerts: {str(e)}")


@router.get("/monitoring/metrics/system")
async def get_system_metrics(
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get system-level metrics"""
    try:
        metrics = await _get_system_metrics()
        
        # Add orchestrator-specific metrics
        orchestrator_status = orchestrator.get_status()
        orchestrator_metrics = {
            'orchestrator_uptime_seconds': orchestrator_status.get('orchestrator', {}).get('uptime_seconds', 0),
            'total_workflows_executed': orchestrator_status.get('orchestrator', {}).get('total_workflows_executed', 0),
            'total_data_points_processed': orchestrator_status.get('orchestrator', {}).get('total_data_points_processed', 0),
            'active_components': sum(1 for c in orchestrator_status.get('components', {}).values() if c.get('status') == 'healthy'),
            'total_components': len(orchestrator_status.get('components', {})),
            'data_pipeline_queue_size': orchestrator_status.get('data_pipeline', {}).get('queue_size', 0)
        }
        
        metrics.update(orchestrator_metrics)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system_metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/monitoring/metrics/component/{component_name}")
async def get_component_metrics(
    component_name: str,
    hours: int = Query(24, description="Hours of metrics history"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get metrics for a specific component"""
    try:
        # Validate component exists
        if component_name not in orchestrator.components:
            raise HTTPException(status_code=404, detail=f"Component {component_name} not found")
        
        # Get component data from integration manager
        component_data = await orchestrator.integration_manager.collect_component_data(component_name)
        
        # Get component status
        component_status = await orchestrator.integration_manager.get_component_status(component_name)
        
        # Get recent metrics from data pipeline
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query_params = {
            'source': component_name,
            'start_time': start_time,
            'end_time': end_time
        }
        
        recent_metrics = await orchestrator.data_pipeline.query_data(query_params)
        
        # Format recent metrics
        formatted_metrics = []
        for metric in recent_metrics:
            formatted_metrics.append({
                'timestamp': metric.timestamp.isoformat(),
                'metric_name': metric.metric_name,
                'value': metric.value,
                'tags': metric.tags
            })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'component': component_name,
            'period_hours': hours,
            'component_data': component_data,
            'component_status': component_status,
            'recent_metrics': formatted_metrics,
            'metrics_count': len(formatted_metrics)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get component metrics for {component_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get component metrics: {str(e)}")


@router.post("/monitoring/health-check")
async def trigger_health_check(
    component: Optional[str] = Query(None, description="Component to check (all if not specified)"),
    background_tasks: BackgroundTasks = None,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Trigger health check for components"""
    try:
        components_to_check = [component] if component else list(orchestrator.components.keys())
        
        health_results = []
        
        for comp_name in components_to_check:
            if comp_name not in orchestrator.components:
                continue
            
            # Perform health check
            health_result = await orchestrator.integration_manager.check_component_health(comp_name)
            health_results.append({
                'component': comp_name,
                'status': health_result.get('status'),
                'healthy': health_result.get('healthy', False),
                'health_score': health_result.get('health_score', 0),
                'error': health_result.get('error'),
                'last_check': health_result.get('last_check')
            })
        
        return {
            'message': 'Health check completed',
            'components_checked': len(health_results),
            'timestamp': datetime.utcnow().isoformat(),
            'results': health_results
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger health check: {str(e)}")


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(
    hours: int = Query(24, description="Hours of dashboard data"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get dashboard data for monitoring UI"""
    try:
        # Get overall status
        status_response = await get_monitoring_status(orchestrator)
        
        # Get health scores
        health_scores_response = await get_health_scores(None, hours, orchestrator)
        
        # Get recent alerts
        alerts_response = await get_monitoring_alerts(None, None, min(hours, 6), 20, orchestrator)
        
        # Get system metrics
        system_metrics_response = await get_system_metrics(orchestrator)
        
        # Compile dashboard data
        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'overview': {
                'overall_status': status_response.get('overall_status'),
                'healthy_components': status_response.get('health_summary', {}).get('healthy_components', 0),
                'total_components': status_response.get('health_summary', {}).get('total_components', 0),
                'active_alerts': alerts_response.get('summary', {}).get('active_alerts', 0),
                'average_health_score': status_response.get('health_summary', {}).get('average_health_score', 0)
            },
            'health_scores': health_scores_response.get('health_scores', []),
            'recent_alerts': alerts_response.get('alerts', []),
            'system_metrics': system_metrics_response.get('system_metrics', {}),
            'component_details': status_response.get('components', {}),
            'data_pipeline': status_response.get('data_pipeline', {})
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring dashboard: {str(e)}")


@router.get("/monitoring/comparison")
async def get_component_comparison(
    components: str = Query(..., description="Comma-separated list of components to compare"),
    metric: Optional[str] = Query(None, description="Specific metric to compare"),
    hours: int = Query(24, description="Hours of comparison data"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Compare metrics across multiple components"""
    try:
        component_list = [comp.strip() for comp in components.split(',')]
        
        # Validate components exist
        valid_components = []
        for comp in component_list:
            if comp in orchestrator.components:
                valid_components.append(comp)
            else:
                logger.warning(f"Component {comp} not found, skipping")
        
        if not valid_components:
            raise HTTPException(status_code=400, detail="No valid components found")
        
        # Get comparison data
        comparison_data = []
        
        for component_name in valid_components:
            # Get component status
            status = await orchestrator.integration_manager.get_component_status(component_name)
            
            # Get component metrics
            metrics_response = await get_component_metrics(component_name, hours, orchestrator)
            
            comparison_data.append({
                'component': component_name,
                'status': status,
                'metrics': metrics_response.get('component_data', {}),
                'health_score': status.get('health', {}).get('health_score', 0)
            })
        
        # Calculate comparison metrics
        comparison_summary = {
            'components_compared': len(valid_components),
            'average_health_score': sum(c.get('health_score', 0) for c in comparison_data) / len(comparison_data),
            'best_performer': max(comparison_data, key=lambda x: x.get('health_score', 0))['component'] if comparison_data else None,
            'worst_performer': min(comparison_data, key=lambda x: x.get('health_score', 0))['component'] if comparison_data else None,
            'health_score_distribution': _calculate_score_distribution([{'score': c.get('health_score', 0)} for c in comparison_data])
        }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'components': valid_components,
            'comparison_data': comparison_data,
            'summary': comparison_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get component comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get component comparison: {str(e)}")


# Helper functions
async def _get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    try:
        import psutil
        
        # Basic system metrics
        metrics = {
            'cpu_usage_percent': psutil.cpu_percent(interval=1),
            'memory_usage_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'network_io': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv
            }
        }
        
        # Process-specific metrics
        process = psutil.Process()
        metrics['process'] = {
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'threads': process.num_threads()
        }
        
        return metrics
        
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {str(e)}")
        return {
            'cpu_usage_percent': 0,
            'memory_usage_percent': 0,
            'disk_usage_percent': 0,
            'load_average': 0,
            'error': str(e)
        }


def _determine_overall_status(component_health: Dict[str, Dict], pipeline_health: Dict[str, Any]) -> str:
    """Determine overall system status"""
    try:
        # Check for critical failures
        failed_components = sum(1 for c in component_health.values() if c.get('status') == 'failed')
        if failed_components > 0:
            return 'critical'
        
        # Check degraded components
        degraded_components = sum(1 for c in component_health.values() if c.get('status') == 'degraded')
        
        # Check data pipeline health
        pipeline_healthy = pipeline_health.get('healthy', False)
        
        # Determine status
        if pipeline_healthy and degraded_components == 0:
            healthy_components = sum(1 for c in component_health.values() if c.get('status') == 'healthy')
            if healthy_components == len(component_health):
                return 'healthy'
            else:
                return 'degraded'
        elif pipeline_healthy and degraded_components < len(component_health) / 2:
            return 'degraded'
        else:
            return 'critical'
            
    except Exception:
        return 'unknown'


def _calculate_average_health_score(component_health: Dict[str, Dict]) -> float:
    """Calculate average health score across components"""
    try:
        scores = [c.get('health_score', 0) for c in component_health.values()]
        return sum(scores) / len(scores) if scores else 0.0
    except Exception:
        return 0.0


def _score_to_grade(score: float) -> str:
    """Convert numerical score to letter grade"""
    if score >= 95:
        return 'A+'
    elif score >= 90:
        return 'A'
    elif score >= 85:
        return 'B+'
    elif score >= 80:
        return 'B'
    elif score >= 75:
        return 'C+'
    elif score >= 70:
        return 'C'
    elif score >= 65:
        return 'D+'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def _calculate_score_distribution(health_scores: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate distribution of health scores by grade"""
    distribution = {'A+': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0, 'N/A': 0}
    
    for score_data in health_scores:
        score = score_data.get('score', 0)
        grade = score_data.get('grade', 'N/A')
        
        if grade in distribution:
            distribution[grade] += 1
        else:
            # Calculate grade from score
            if score >= 95:
                distribution['A+'] += 1
            elif score >= 90:
                distribution['A'] += 1
            elif score >= 80:
                distribution['B'] += 1
            elif score >= 70:
                distribution['C'] += 1
            elif score >= 60:
                distribution['D'] += 1
            else:
                distribution['F'] += 1
    
    return distribution