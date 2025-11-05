"""
Analytics API routes for the analytics orchestrator
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
        # This would typically be initialized in the main app
        # For now, return a mock or create one
        from ...core.orchestrator import AnalyticsOrchestrator
        _orchestrator = AnalyticsOrchestrator()
    return _orchestrator


@router.get("/analytics/overview")
async def get_analytics_overview(
    hours: int = Query(24, description="Hours of data to include"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get analytics overview with key metrics"""
    try:
        # Get orchestrator status
        status = orchestrator.get_status()
        
        # Get component overview
        component_overview = {}
        for component_name, component_info in status.get('components', {}).items():
            component_overview[component_name] = {
                'status': component_info.get('status'),
                'health_score': component_info.get('health_score', 0),
                'last_check': component_info.get('last_check')
            }
        
        overview = {
            'timestamp': datetime.utcnow().isoformat(),
            'time_range_hours': hours,
            'orchestrator_status': {
                'running': status.get('orchestrator', {}).get('running', False),
                'uptime_seconds': status.get('orchestrator', {}).get('uptime_seconds', 0),
                'total_workflows_executed': status.get('orchestrator', {}).get('total_workflows_executed', 0),
                'total_data_points_processed': status.get('orchestrator', {}).get('total_data_points_processed', 0)
            },
            'components': component_overview,
            'workflows': {
                'running': status.get('orchestrator', {}).get('workflows_running', 0),
                'total_executed': status.get('orchestrator', {}).get('total_workflows_executed', 0)
            },
            'data_pipeline': {
                'status': status.get('data_pipeline', {}).get('status'),
                'queue_size': status.get('data_pipeline', {}).get('queue_size', 0)
            },
            'summary': {
                'health_grade': _calculate_overall_grade(component_overview),
                'active_components': sum(1 for c in component_overview.values() if c.get('status') == 'healthy'),
                'total_components': len(component_overview),
                'data_processing_rate': _calculate_processing_rate(status.get('orchestrator', {}))
            }
        }
        
        return overview
        
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics overview: {str(e)}")


@router.get("/analytics/metrics")
async def get_metrics(
    source: Optional[str] = Query(None, description="Filter by source"),
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    hours: int = Query(24, description="Hours of data to retrieve"),
    limit: int = Query(100, description="Maximum number of data points"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get metrics data"""
    try:
        # Get data pipeline instance
        data_pipeline = orchestrator.data_pipeline
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Query data based on filters
        query_params = {
            'start_time': start_time,
            'end_time': end_time,
            'limit': limit
        }
        
        if source:
            query_params['source'] = source
        
        if metric:
            query_params['metric'] = metric
        
        # Query data from time series store
        data_points = await data_pipeline.query_data(query_params)
        
        # Format response
        metrics = []
        for point in data_points:
            metrics.append({
                'timestamp': point.timestamp.isoformat(),
                'source': point.source,
                'metric': point.metric_name,
                'value': point.value,
                'tags': point.tags,
                'metadata': point.metadata
            })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'query_params': query_params,
            'total_points': len(metrics),
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/analytics/trends")
async def get_trends(
    source: Optional[str] = Query(None, description="Filter by source"),
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    days: int = Query(7, description="Days of data for trend analysis"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get trend analysis for metrics"""
    try:
        # Get data pipeline
        data_pipeline = orchestrator.data_pipeline
        
        # Get recent data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        query_params = {
            'start_time': start_time,
            'end_time': end_time
        }
        
        if source:
            query_params['source'] = source
        
        if metric:
            query_params['metric'] = metric
        
        # Query data
        data_points = await data_pipeline.query_data(query_params)
        
        # Analyze trends using the analyzer
        from ...data.processors.analyzer import DataAnalyzer
        analyzer = DataAnalyzer()
        
        # Group data by source and metric
        grouped_data = _group_data_points(data_points)
        
        trends = []
        for (metric_name, source_name), points in grouped_data.items():
            # Perform trend analysis
            trend_result = await analyzer._analyze_trends(metric_name, source_name, points)
            
            if trend_result:
                trends.append({
                    'source': source_name,
                    'metric': metric_name,
                    'trend_direction': trend_result.get('trend_direction'),
                    'trend_strength': trend_result.get('trend_strength'),
                    'slope': trend_result.get('slope'),
                    'r_squared': trend_result.get('r_squared'),
                    'change_rate': trend_result.get('change_rate'),
                    'confidence': trend_result.get('confidence'),
                    'data_points_count': len(points)
                })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_period_days': days,
            'total_trends_analyzed': len(trends),
            'trends': trends,
            'summary': {
                'increasing_trends': sum(1 for t in trends if t.get('trend_direction') == 'increasing'),
                'decreasing_trends': sum(1 for t in trends if t.get('trend_direction') == 'decreasing'),
                'stable_trends': sum(1 for t in trends if t.get('trend_direction') == 'stable'),
                'strong_trends': sum(1 for t in trends if t.get('trend_strength') == 'strong')
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@router.get("/analytics/anomalies")
async def get_anomalies(
    source: Optional[str] = Query(None, description="Filter by source"),
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    hours: int = Query(24, description="Hours of data to analyze"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get anomaly detection results"""
    try:
        # Get data pipeline
        data_pipeline = orchestrator.data_pipeline
        
        # Get recent data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query_params = {
            'start_time': start_time,
            'end_time': end_time
        }
        
        if source:
            query_params['source'] = source
        
        if metric:
            query_params['metric'] = metric
        
        # Query data
        data_points = await data_pipeline.query_data(query_params)
        
        # Analyze anomalies
        from ...data.processors.analyzer import DataAnalyzer
        analyzer = DataAnalyzer()
        
        # Group data by source and metric
        grouped_data = _group_data_points(data_points)
        
        anomalies = []
        for (metric_name, source_name), points in grouped_data.items():
            # Perform anomaly detection
            anomaly_result = await analyzer._detect_anomalies(metric_name, source_name, points)
            
            if anomaly_result and anomaly_result.get('total_anomalies', 0) > 0:
                anomalies.append({
                    'source': source_name,
                    'metric': metric_name,
                    'total_anomalies': anomaly_result.get('total_anomalies'),
                    'anomaly_rate': anomaly_result.get('anomaly_rate'),
                    'anomaly_indices': anomaly_result.get('anomaly_indices', []),
                    'detection_methods': anomaly_result.get('detection_methods', []),
                    'data_points_count': anomaly_result.get('data_points_count', 0)
                })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_period_hours': hours,
            'total_anomaly_sources': len(anomalies),
            'anomalies': anomalies,
            'summary': {
                'total_anomalies_detected': sum(a.get('total_anomalies', 0) for a in anomalies),
                'sources_with_anomalies': len(anomalies),
                'average_anomaly_rate': sum(a.get('anomaly_rate', 0) for a in anomalies) / len(anomalies) if anomalies else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get anomalies: {str(e)}")


@router.get("/analytics/performance")
async def get_performance_metrics(
    component: Optional[str] = Query(None, description="Filter by component"),
    hours: int = Query(24, description="Hours of data to analyze"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get performance metrics and analysis"""
    try:
        # Get data pipeline
        data_pipeline = orchestrator.data_pipeline
        
        # Get recent data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query_params = {
            'start_time': start_time,
            'end_time': end_time
        }
        
        if component:
            query_params['source'] = component
        
        # Query data
        data_points = await data_pipeline.query_data(query_params)
        
        # Perform performance analysis
        from ...data.processors.analyzer import DataAnalyzer
        analyzer = DataAnalyzer()
        
        # Group data by source and metric
        grouped_data = _group_data_points(data_points)
        
        performance_metrics = []
        for (metric_name, source_name), points in grouped_data.items():
            # Perform performance analysis
            performance_result = await analyzer._performance_analysis(metric_name, source_name, points)
            
            if performance_result:
                performance_data = performance_result.get('performance', {})
                
                performance_metrics.append({
                    'source': source_name,
                    'metric': metric_name,
                    'stability': performance_data.get('stability', {}),
                    'reliability': performance_data.get('reliability', {}),
                    'trend': performance_data.get('trend', {}),
                    'summary': performance_data.get('summary', {}),
                    'data_points_count': len(points)
                })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_period_hours': hours,
            'total_performance_analyses': len(performance_metrics),
            'performance_metrics': performance_metrics,
            'summary': {
                'stable_sources': sum(1 for p in performance_metrics if p.get('stability', {}).get('stability_rating') == 'high'),
                'reliable_sources': sum(1 for p in performance_metrics if p.get('reliability', {}).get('reliability_rating') == 'high'),
                'sources_analyzed': len(performance_metrics)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.post("/analytics/collect/{component}")
async def trigger_data_collection(
    component: str = Path(..., description="Component name"),
    background_tasks: BackgroundTasks = None,
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Trigger data collection for a specific component"""
    try:
        # Validate component
        if component not in orchestrator.components:
            raise HTTPException(status_code=404, detail=f"Component {component} not found")
        
        # Check if component is healthy
        component_info = orchestrator.components[component]
        if component_info.status != 'healthy':
            raise HTTPException(status_code=400, detail=f"Component {component} is not healthy: {component_info.status}")
        
        # Trigger data collection in background
        async def collect_data():
            try:
                await orchestrator.integration_manager.collect_component_data(component)
            except Exception as e:
                logger.error(f"Background data collection failed for {component}: {str(e)}")
        
        if background_tasks:
            background_tasks.add_task(collect_data)
        else:
            # Run synchronously if no background tasks available
            await collect_data()
        
        return {
            'message': f'Data collection triggered for component {component}',
            'component': component,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'initiated'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger data collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger data collection: {str(e)}")


@router.get("/analytics/reports")
async def get_analytics_reports(
    component: Optional[str] = Query(None, description="Filter by component"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    hours: int = Query(24, description="Hours of data for reports"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get available analytics reports"""
    try:
        # This would typically query a reports store
        # For now, return mock reports
        
        reports = []
        
        # Health monitoring report
        if not component or component == 'health_monitor':
            reports.append({
                'id': 'health_monitoring_report',
                'component': 'health_monitor',
                'type': 'health_summary',
                'title': 'Health Monitoring Report',
                'description': 'Comprehensive health analysis of repositories',
                'generated_at': datetime.utcnow().isoformat(),
                'period_hours': hours,
                'status': 'available'
            })
        
        # Follow automation report
        if not component or component == 'follow_automation':
            reports.append({
                'id': 'follow_automation_report',
                'component': 'follow_automation',
                'type': 'automation_summary',
                'title': 'Follow Automation Report',
                'description': 'Automation performance and safety analysis',
                'generated_at': datetime.utcnow().isoformat(),
                'period_hours': hours,
                'status': 'available'
            })
        
        # Security scanner report
        if not component or component == 'security_scanner':
            reports.append({
                'id': 'security_scanner_report',
                'component': 'security_scanner',
                'type': 'security_summary',
                'title': 'Security Scanner Report',
                'description': 'Security vulnerabilities and compliance status',
                'generated_at': datetime.utcnow().isoformat(),
                'period_hours': hours,
                'status': 'available'
            })
        
        # Daily contributions report
        if not component or component == 'daily_contributions':
            reports.append({
                'id': 'daily_contributions_report',
                'component': 'daily_contributions',
                'type': 'contributions_summary',
                'title': 'Daily Contributions Report',
                'description': 'Community contribution and growth analysis',
                'generated_at': datetime.utcnow().isoformat(),
                'period_hours': hours,
                'status': 'available'
            })
        
        # Filter by report type if specified
        if report_type:
            reports = [r for r in reports if r['type'] == report_type]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_reports': len(reports),
            'reports': reports
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics reports: {str(e)}")


@router.get("/analytics/reports/{report_id}")
async def get_analytics_report(
    report_id: str = Path(..., description="Report ID"),
    component: Optional[str] = Query(None, description="Component name"),
    orchestrator: AnalyticsOrchestrator = Depends(get_orchestrator)
):
    """Get a specific analytics report"""
    try:
        # Map report IDs to components
        report_mapping = {
            'health_monitoring_report': 'health_monitor',
            'follow_automation_report': 'follow_automation',
            'security_scanner_report': 'security_scanner',
            'daily_contributions_report': 'daily_contributions'
        }
        
        target_component = report_mapping.get(report_id)
        if not target_component:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Check if component is available
        if target_component not in orchestrator.components:
            raise HTTPException(status_code=404, detail=f"Component {target_component} not found")
        
        # Generate report
        report = await orchestrator.integration_manager.generate_report(target_component)
        
        return {
            'report_id': report_id,
            'component': target_component,
            'generated_at': datetime.utcnow().isoformat(),
            'report': report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics report: {str(e)}")


# Helper functions
def _calculate_overall_grade(component_overview: Dict[str, Dict[str, Any]]) -> str:
    """Calculate overall grade from component health scores"""
    try:
        health_scores = [
            component.get('health_score', 0)
            for component in component_overview.values()
            if component.get('status') == 'healthy'
        ]
        
        if not health_scores:
            return 'N/A'
        
        avg_score = sum(health_scores) / len(health_scores)
        
        if avg_score >= 95:
            return 'A+'
        elif avg_score >= 90:
            return 'A'
        elif avg_score >= 85:
            return 'B+'
        elif avg_score >= 80:
            return 'B'
        elif avg_score >= 75:
            return 'C+'
        elif avg_score >= 70:
            return 'C'
        elif avg_score >= 65:
            return 'D+'
        elif avg_score >= 60:
            return 'D'
        else:
            return 'F'
            
    except Exception:
        return 'N/A'


def _calculate_processing_rate(orchestrator_status: Dict[str, Any]) -> float:
    """Calculate data processing rate"""
    try:
        uptime_seconds = orchestrator_status.get('uptime_seconds', 0)
        data_points = orchestrator_status.get('total_data_points_processed', 0)
        
        if uptime_seconds > 0:
            return data_points / uptime_seconds
        return 0.0
        
    except Exception:
        return 0.0


def _group_data_points(data_points):
    """Group data points by metric name and source"""
    from collections import defaultdict
    
    grouped = defaultdict(list)
    
    for point in data_points:
        if hasattr(point, 'metric_name') and hasattr(point, 'source'):
            key = (point.metric_name, point.source)
            grouped[key].append(point)
        elif isinstance(point, dict):
            key = (point.get('metric_name', 'unknown'), point.get('source', 'unknown'))
            grouped[key].append(point)
    
    return dict(grouped)