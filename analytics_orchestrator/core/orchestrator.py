"""
Core analytics orchestrator module - coordinates all automation hub components
"""

from typing import Dict, List, Optional, Any
import logging
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
import yaml
import os
from datetime import datetime, timedelta

from .config_manager import ConfigManager
from .data_pipeline import DataPipeline
from .integration_manager import IntegrationManager


class ComponentStatus(Enum):
    """Component status enumeration"""
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPED = "stopped"


class WorkflowStatus(Enum):
    """Workflow status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class ComponentInfo:
    """Component information structure"""
    name: str
    status: ComponentStatus = ComponentStatus.UNKNOWN
    last_check: Optional[datetime] = None
    health_score: float = 0.0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkflowInfo:
    """Workflow information structure"""
    id: str
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0


class AnalyticsOrchestrator:
    """
    Main analytics orchestrator that coordinates all automation hub components
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the analytics orchestrator"""
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize components
        self.components: Dict[str, ComponentInfo] = {}
        self.workflows: Dict[str, WorkflowInfo] = {}
        
        # Initialize managers
        self.integration_manager = IntegrationManager(self.config)
        self.data_pipeline = DataPipeline(self.config)
        
        # Control flags
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.start_time = None
        self.total_workflows_executed = 0
        self.total_data_points_processed = 0
        
        self.logger.info("Analytics Orchestrator initialized")
    
    async def start(self):
        """Start the analytics orchestrator"""
        if self._running:
            self.logger.warning("Orchestrator is already running")
            return
        
        self.logger.info("Starting Analytics Orchestrator...")
        self.start_time = datetime.utcnow()
        self._running = True
        
        try:
            # Initialize components
            await self._initialize_components()
            
            # Start data pipeline
            await self.data_pipeline.start()
            
            # Start monitoring tasks
            await self._start_monitoring_tasks()
            
            # Start scheduled workflows
            await self._start_scheduled_workflows()
            
            self.logger.info("Analytics Orchestrator started successfully")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"Failed to start orchestrator: {str(e)}")
            await self.stop()
            raise
        finally:
            self.logger.info("Analytics Orchestrator stopped")
    
    async def stop(self):
        """Stop the analytics orchestrator"""
        if not self._running:
            return
        
        self.logger.info("Stopping Analytics Orchestrator...")
        self._running = False
        
        # Stop data pipeline
        await self.data_pipeline.stop()
        
        # Shutdown monitoring tasks
        self._shutdown_event.set()
        
        # Stop components
        await self._stop_components()
    
    async def _initialize_components(self):
        """Initialize all configured components"""
        self.logger.info("Initializing components...")
        
        components_config = self.config.get('analytics_orchestrator', {}).get('components', {})
        
        for component_name, component_config in components_config.items():
            if component_config.get('enabled', False):
                component_info = ComponentInfo(
                    name=component_name,
                    status=ComponentStatus.INITIALIZING,
                    dependencies=component_config.get('dependencies', [])
                )
                self.components[component_name] = component_info
                
                try:
                    # Initialize component integration
                    await self.integration_manager.initialize_component(
                        component_name, component_config
                    )
                    
                    component_info.status = ComponentStatus.HEALTHY
                    self.logger.info(f"Component {component_name} initialized successfully")
                    
                except Exception as e:
                    component_info.status = ComponentStatus.FAILED
                    component_info.error_message = str(e)
                    self.logger.error(f"Failed to initialize component {component_name}: {str(e)}")
    
    async def _stop_components(self):
        """Stop all components"""
        self.logger.info("Stopping components...")
        
        for component_name in self.components.keys():
            try:
                await self.integration_manager.stop_component(component_name)
                self.logger.info(f"Component {component_name} stopped")
            except Exception as e:
                self.logger.error(f"Error stopping component {component_name}: {str(e)}")
    
    async def _start_monitoring_tasks(self):
        """Start background monitoring tasks"""
        self.logger.info("Starting monitoring tasks...")
        
        # Component health monitoring
        asyncio.create_task(self._monitor_component_health())
        
        # System metrics collection
        asyncio.create_task(self._collect_system_metrics())
        
        # Workflow monitoring
        asyncio.create_task(self._monitor_workflows())
        
        # Data pipeline monitoring
        asyncio.create_task(self._monitor_data_pipeline())
    
    async def _monitor_component_health(self):
        """Monitor component health"""
        while self._running:
            try:
                for component_name, component_info in self.components.items():
                    try:
                        # Check component health
                        health_status = await self.integration_manager.check_component_health(
                            component_name
                        )
                        
                        component_info.status = ComponentStatus(health_status.get('status', 'unknown'))
                        component_info.health_score = health_status.get('health_score', 0.0)
                        component_info.last_check = datetime.utcnow()
                        component_info.error_message = health_status.get('error')
                        component_info.metrics.update(health_status.get('metrics', {}))
                        
                    except Exception as e:
                        component_info.status = ComponentStatus.FAILED
                        component_info.error_message = str(e)
                        self.logger.error(f"Health check failed for {component_name}: {str(e)}")
                
                # Wait before next health check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in component health monitoring: {str(e)}")
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        while self._running:
            try:
                # Collect orchestrator metrics
                metrics = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'uptime': (datetime.utcnow() - self.start_time).total_seconds(),
                    'components_healthy': sum(
                        1 for c in self.components.values() 
                        if c.status == ComponentStatus.HEALTHY
                    ),
                    'components_total': len(self.components),
                    'workflows_running': sum(
                        1 for w in self.workflows.values()
                        if w.status == WorkflowStatus.RUNNING
                    ),
                    'total_workflows_executed': self.total_workflows_executed,
                    'total_data_points_processed': self.total_data_points_processed
                }
                
                # Store metrics
                await self.data_pipeline.store_system_metrics(metrics)
                
                # Wait before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {str(e)}")
                await asyncio.sleep(30)
    
    async def _monitor_workflows(self):
        """Monitor running workflows"""
        while self._running:
            try:
                # Check workflow health and recovery
                for workflow_id, workflow_info in self.workflows.items():
                    if workflow_info.status == WorkflowStatus.RUNNING:
                        # Check if workflow has timed out
                        if workflow_info.start_time:
                            timeout = self.config.get('analytics_orchestrator', {}).get(
                                'workflow_timeout', 3600  # 1 hour default
                            )
                            
                            if (datetime.utcnow() - workflow_info.start_time).total_seconds() > timeout:
                                workflow_info.status = WorkflowStatus.FAILED
                                workflow_info.error_message = "Workflow timed out"
                                self.logger.error(f"Workflow {workflow_id} timed out")
                
                # Clean up completed workflows
                await self._cleanup_completed_workflows()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error monitoring workflows: {str(e)}")
                await asyncio.sleep(60)
    
    async def _monitor_data_pipeline(self):
        """Monitor data pipeline health"""
        while self._running:
            try:
                # Check data pipeline status
                pipeline_health = await self.data_pipeline.get_health_status()
                
                if not pipeline_health.get('healthy', False):
                    self.logger.warning(f"Data pipeline health issue: {pipeline_health}")
                
                # Update component status
                if 'data_pipeline' in self.components:
                    self.components['data_pipeline'].status = (
                        ComponentStatus.HEALTHY if pipeline_health.get('healthy', False)
                        else ComponentStatus.DEGRADED
                    )
                    self.components['data_pipeline'].metrics.update(pipeline_health)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error monitoring data pipeline: {str(e)}")
                await asyncio.sleep(300)
    
    async def _cleanup_completed_workflows(self):
        """Clean up old completed workflows"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            completed_workflows = [
                workflow_id for workflow_id, workflow_info in self.workflows.items()
                if workflow_info.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
                and workflow_info.end_time
                and workflow_info.end_time < cutoff_time
            ]
            
            for workflow_id in completed_workflows:
                del self.workflows[workflow_id]
                self.logger.info(f"Cleaned up workflow {workflow_id}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up workflows: {str(e)}")
    
    async def _start_scheduled_workflows(self):
        """Start scheduled workflows"""
        self.logger.info("Starting scheduled workflows...")
        
        # Health monitoring workflow
        await self._schedule_workflow(
            "health_monitoring",
            "Daily Health Monitoring",
            self._run_health_monitoring_workflow,
            schedule="0 2 * * *"  # Daily at 2 AM UTC
        )
        
        # Security scanning workflow
        await self._schedule_workflow(
            "security_scanning",
            "Daily Security Scanning",
            self._run_security_scanning_workflow,
            schedule="0 3 * * *"  # Daily at 3 AM UTC
        )
        
        # Automation tracking workflow
        await self._schedule_workflow(
            "automation_tracking",
            "Automation Tracking",
            self._run_automation_tracking_workflow,
            schedule="0 */4 * * *"  # Every 4 hours
        )
        
        # Community analysis workflow
        await self._schedule_workflow(
            "community_analysis",
            "Weekly Community Analysis",
            self._run_community_analysis_workflow,
            schedule="0 0 * * 0"  # Weekly on Sunday at midnight UTC
        )
    
    async def _schedule_workflow(self, workflow_id: str, name: str, func, schedule: str):
        """Schedule a workflow for execution"""
        # This is a simplified implementation
        # In production, you'd use a proper scheduler like APScheduler
        asyncio.create_task(self._schedule_and_run_workflow(workflow_id, name, func, schedule))
    
    async def _schedule_and_run_workflow(self, workflow_id: str, name: str, func, schedule: str):
        """Schedule and run workflow based on cron expression"""
        # Simplified cron implementation
        # In production, use proper cron parsing
        while self._running:
            try:
                # Execute workflow
                await self.execute_workflow(workflow_id, name, func)
                
                # Wait for next scheduled time
                # For now, wait based on schedule frequency
                if "* *" in schedule or "*/" in schedule:
                    if "*/4" in schedule:  # Every 4 hours
                        await asyncio.sleep(4 * 3600)
                    elif "0 2" in schedule:  # Daily at 2 AM
                        await asyncio.sleep(24 * 3600)
                    elif "0 3" in schedule:  # Daily at 3 AM
                        await asyncio.sleep(24 * 3600)
                    elif "0 0 * * 0" in schedule:  # Weekly
                        await asyncio.sleep(7 * 24 * 3600)
                    else:
                        await asyncio.sleep(3600)  # Default: 1 hour
                else:
                    await asyncio.sleep(3600)  # Default: 1 hour
                    
            except Exception as e:
                self.logger.error(f"Error in scheduled workflow {workflow_id}: {str(e)}")
                await asyncio.sleep(3600)  # Wait before retry
    
    async def execute_workflow(self, workflow_id: str, name: str, workflow_func) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_id in self.workflows:
            # Workflow already exists
            existing_workflow = self.workflows[workflow_id]
            if existing_workflow.status == WorkflowStatus.RUNNING:
                raise ValueError(f"Workflow {workflow_id} is already running")
        
        workflow_info = WorkflowInfo(
            id=workflow_id,
            name=name,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        self.workflows[workflow_id] = workflow_info
        
        try:
            self.logger.info(f"Starting workflow: {name}")
            result = await workflow_func()
            
            workflow_info.status = WorkflowStatus.COMPLETED
            workflow_info.end_time = datetime.utcnow()
            workflow_info.duration = (workflow_info.end_time - workflow_info.start_time).total_seconds()
            workflow_info.results = result
            
            self.total_workflows_executed += 1
            
            self.logger.info(f"Workflow {name} completed successfully in {workflow_info.duration:.2f} seconds")
            return result
            
        except Exception as e:
            workflow_info.status = WorkflowStatus.FAILED
            workflow_info.end_time = datetime.utcnow()
            workflow_info.duration = (workflow_info.end_time - workflow_info.start_time).total_seconds()
            workflow_info.error_message = str(e)
            
            self.logger.error(f"Workflow {name} failed: {str(e)}")
            raise
    
    async def _run_health_monitoring_workflow(self) -> Dict[str, Any]:
        """Run health monitoring workflow"""
        results = {}
        
        try:
            # Collect health metrics from health monitoring system
            health_metrics = await self.integration_manager.collect_component_data(
                'health_monitor'
            )
            
            # Process and store metrics
            await self.data_pipeline.store_component_metrics('health_monitor', health_metrics)
            
            # Generate health report
            health_report = await self.integration_manager.generate_report('health_monitor')
            await self.data_pipeline.store_report('health_monitoring', health_report)
            
            results['metrics_collected'] = len(health_metrics)
            results['report_generated'] = True
            results['data_points'] = self.data_pipeline.get_last_batch_size()
            
            self.total_data_points_processed += results['data_points']
            
        except Exception as e:
            self.logger.error(f"Health monitoring workflow failed: {str(e)}")
            results['error'] = str(e)
            raise
        
        return results
    
    async def _run_security_scanning_workflow(self) -> Dict[str, Any]:
        """Run security scanning workflow"""
        results = {}
        
        try:
            # Run security scan
            scan_results = await self.integration_manager.run_component_action(
                'security_scanner', 'run_scan'
            )
            
            # Collect security metrics
            security_metrics = await self.integration_manager.collect_component_data(
                'security_scanner'
            )
            
            # Process and store metrics
            await self.data_pipeline.store_component_metrics('security_scanner', security_metrics)
            
            # Generate security report
            security_report = await self.integration_manager.generate_report('security_scanner')
            await self.data_pipeline.store_report('security_scanning', security_report)
            
            results['scan_completed'] = True
            results['issues_found'] = scan_results.get('issues_count', 0)
            results['vulnerabilities'] = scan_results.get('vulnerabilities', [])
            results['data_points'] = self.data_pipeline.get_last_batch_size()
            
            self.total_data_points_processed += results['data_points']
            
        except Exception as e:
            self.logger.error(f"Security scanning workflow failed: {str(e)}")
            results['error'] = str(e)
            raise
        
        return results
    
    async def _run_automation_tracking_workflow(self) -> Dict[str, Any]:
        """Run automation tracking workflow"""
        results = {}
        
        try:
            # Collect automation metrics from follow automation
            automation_metrics = await self.integration_manager.collect_component_data(
                'follow_automation'
            )
            
            # Process and store metrics
            await self.data_pipeline.store_component_metrics('follow_automation', automation_metrics)
            
            # Get automation status
            automation_status = await self.integration_manager.get_component_status(
                'follow_automation'
            )
            
            # Generate automation report
            automation_report = await self.integration_manager.generate_report('follow_automation')
            await self.data_pipeline.store_report('automation_tracking', automation_report)
            
            results['status'] = automation_status
            results['data_points'] = self.data_pipeline.get_last_batch_size()
            results['report_generated'] = True
            
            self.total_data_points_processed += results['data_points']
            
        except Exception as e:
            self.logger.error(f"Automation tracking workflow failed: {str(e)}")
            results['error'] = str(e)
            raise
        
        return results
    
    async def _run_community_analysis_workflow(self) -> Dict[str, Any]:
        """Run community analysis workflow"""
        results = {}
        
        try:
            # Collect community engagement data from daily contributions
            community_data = await self.integration_manager.collect_component_data(
                'daily_contributions'
            )
            
            # Process and store data
            await self.data_pipeline.store_component_metrics('daily_contributions', community_data)
            
            # Analyze community trends
            trends = await self._analyze_community_trends(community_data)
            
            # Generate community report
            community_report = await self.integration_manager.generate_report('daily_contributions')
            await self.data_pipeline.store_report('community_analysis', community_report)
            
            results['trends'] = trends
            results['community_data_points'] = len(community_data)
            results['report_generated'] = True
            results['data_points'] = self.data_pipeline.get_last_batch_size()
            
            self.total_data_points_processed += results['data_points']
            
        except Exception as e:
            self.logger.error(f"Community analysis workflow failed: {str(e)}")
            results['error'] = str(e)
            raise
        
        return results
    
    async def _analyze_community_trends(self, community_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze community trends from collected data"""
        trends = {
            'growth_rate': 0.0,
            'engagement_level': 'stable',
            'top_contributors': [],
            'activity_patterns': {},
            'recommendations': []
        }
        
        try:
            # Simple trend analysis - in production, use more sophisticated algorithms
            if 'contributor_count' in community_data:
                trends['growth_rate'] = community_data['contributor_count'].get('growth_rate', 0)
            
            if 'engagement_score' in community_data:
                score = community_data['engagement_score']
                if score > 0.8:
                    trends['engagement_level'] = 'high'
                elif score > 0.5:
                    trends['engagement_level'] = 'medium'
                else:
                    trends['engagement_level'] = 'low'
            
            trends['recommendations'] = self._generate_community_recommendations(trends)
            
        except Exception as e:
            self.logger.error(f"Error analyzing community trends: {str(e)}")
            trends['error'] = str(e)
        
        return trends
    
    def _generate_community_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on community trends"""
        recommendations = []
        
        try:
            if trends.get('growth_rate', 0) < 0:
                recommendations.append("Community growth is declining. Consider increasing engagement activities.")
            
            if trends.get('engagement_level') == 'low':
                recommendations.append("Low engagement detected. Review community interaction strategies.")
            
            if trends.get('growth_rate', 0) > 0.5:
                recommendations.append("Strong growth detected. Maintain current engagement strategies.")
                
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            recommendations.append("Unable to generate specific recommendations.")
        
        return recommendations
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        
        component_status = {
            name: {
                'status': component.status.value,
                'health_score': component.health_score,
                'last_check': component.last_check.isoformat() if component.last_check else None,
                'error_message': component.error_message
            }
            for name, component in self.components.items()
        }
        
        workflow_status = {
            workflow_id: {
                'name': workflow.name,
                'status': workflow.status.value,
                'start_time': workflow.start_time.isoformat() if workflow.start_time else None,
                'end_time': workflow.end_time.isoformat() if workflow.end_time else None,
                'duration': workflow.duration,
                'retry_count': workflow.retry_count
            }
            for workflow_id, workflow in self.workflows.items()
        }
        
        return {
            'orchestrator': {
                'running': self._running,
                'uptime_seconds': uptime,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'total_workflows_executed': self.total_workflows_executed,
                'total_data_points_processed': self.total_data_points_processed
            },
            'components': component_status,
            'workflows': workflow_status,
            'data_pipeline': {
                'status': 'running' if self.data_pipeline.is_running() else 'stopped',
                'last_batch_size': self.data_pipeline.get_last_batch_size(),
                'queue_size': self.data_pipeline.get_queue_size()
            },
            'timestamp': datetime.utcnow().isoformat()
        }


# Main entry point
async def main():
    """Main entry point for the analytics orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analytics Orchestrator')
    parser.add_argument('--config', default='config/config.yaml', help='Configuration file path')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start orchestrator
    orchestrator = AnalyticsOrchestrator(args.config)
    
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down...")
        await orchestrator.stop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        await orchestrator.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())