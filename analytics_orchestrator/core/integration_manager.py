"""
Integration manager for coordinating all automation hub components
"""

import asyncio
import logging
import os
import sys
import importlib.util
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import yaml
import subprocess


@dataclass
class ComponentIntegration:
    """Component integration structure"""
    name: str
    enabled: bool
    integration_path: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "unknown"
    error_message: Optional[str] = None
    last_health_check: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class IntegrationManager:
    """
    Integration manager that coordinates and integrates with all automation hub components
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize integration manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Component integrations
        self.components: Dict[str, ComponentIntegration] = {}
        
        # Integration modules cache
        self._integration_modules = {}
        
        # Status tracking
        self._status_history = []
        
        # Initialize integrations
        self._initialize_integrations()
        
        self.logger.info("Integration manager initialized")
    
    def _initialize_integrations(self):
        """Initialize component integrations"""
        components_config = self.config.get('components', {})
        
        for component_name, component_config in components_config.items():
            if component_config.get('enabled', False):
                integration = ComponentIntegration(
                    name=component_name,
                    enabled=True,
                    integration_path=component_config.get('integration_path', ''),
                    config=component_config.get('config', {}),
                    dependencies=component_config.get('dependencies', [])
                )
                
                self.components[component_name] = integration
                self.logger.info(f"Component integration initialized: {component_name}")
    
    async def initialize_component(self, component_name: str, config: Dict[str, Any]) -> bool:
        """Initialize a specific component integration"""
        try:
            if component_name not in self.components:
                self.logger.error(f"Component {component_name} not found in configuration")
                return False
            
            component = self.components[component_name]
            component.status = "initializing"
            
            # Check dependencies
            for dependency in component.dependencies:
                if dependency not in self.components:
                    raise ValueError(f"Dependency {dependency} not found")
                if not self.components[dependency].enabled:
                    raise ValueError(f"Dependency {dependency} is not enabled")
            
            # Load and initialize the component
            module = await self._load_component_module(component_name)
            if module:
                self._integration_modules[component_name] = module
                component.status = "initialized"
                component.last_health_check = datetime.utcnow()
                self.logger.info(f"Component {component_name} initialized successfully")
                return True
            else:
                component.status = "failed"
                component.error_message = "Failed to load component module"
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize component {component_name}: {str(e)}")
            if component_name in self.components:
                self.components[component_name].status = "failed"
                self.components[component_name].error_message = str(e)
            return False
    
    async def stop_component(self, component_name: str) -> bool:
        """Stop a component integration"""
        try:
            if component_name not in self.components:
                return False
            
            component = self.components[component_name]
            component.status = "stopping"
            
            # Perform cleanup if component has cleanup method
            if component_name in self._integration_modules:
                module = self._integration_modules[component_name]
                if hasattr(module, 'cleanup') and callable(module.cleanup):
                    await module.cleanup()
            
            component.status = "stopped"
            self.logger.info(f"Component {component_name} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop component {component_name}: {str(e)}")
            return False
    
    async def _load_component_module(self, component_name: str):
        """Load and return the component module"""
        try:
            component = self.components[component_name]
            integration_path = component.integration_path
            
            if not integration_path:
                return None
            
            # Convert relative path to absolute
            if integration_path.startswith('../'):
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                absolute_path = os.path.join(base_path, integration_path[3:])
            else:
                absolute_path = integration_path
            
            # Try to load as Python module
            if os.path.exists(os.path.join(absolute_path, 'main_orchestrator.py')):
                return await self._load_orchestrator_module(component_name, absolute_path)
            
            # Try to load as script
            elif os.path.exists(os.path.join(absolute_path, 'main.py')):
                return await self._load_script_module(component_name, absolute_path)
            
            else:
                self.logger.warning(f"No suitable entry point found for component {component_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load component module {component_name}: {str(e)}")
            return None
    
    async def _load_orchestrator_module(self, component_name: str, path: str):
        """Load orchestrator module"""
        try:
            # Add the component path to Python path
            if path not in sys.path:
                sys.path.insert(0, path)
            
            # Import the orchestrator module
            spec = importlib.util.spec_from_file_location(
                f"{component_name}_orchestrator",
                os.path.join(path, 'main_orchestrator.py')
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load orchestrator module for {component_name}: {str(e)}")
            return None
    
    async def _load_script_module(self, component_name: str, path: str):
        """Load script module"""
        try:
            # Add the component path to Python path
            if path not in sys.path:
                sys.path.insert(0, path)
            
            # Import the main module
            spec = importlib.util.spec_from_file_location(
                f"{component_name}_main",
                os.path.join(path, 'main.py')
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load script module for {component_name}: {str(e)}")
            return None
    
    async def check_component_health(self, component_name: str) -> Dict[str, Any]:
        """Check health of a specific component"""
        try:
            if component_name not in self.components:
                return {
                    'status': 'not_found',
                    'healthy': False,
                    'error': f"Component {component_name} not found"
                }
            
            component = self.components[component_name]
            component.last_health_check = datetime.utcnow()
            
            # Check basic component status
            if component.status == "failed":
                return {
                    'status': component.status,
                    'healthy': False,
                    'error': component.error_message,
                    'last_check': component.last_health_check.isoformat()
                }
            
            # Try to get health check from component module
            if component_name in self._integration_modules:
                module = self._integration_modules[component_name]
                
                # Try different health check methods
                if hasattr(module, 'health_check') and callable(module.health_check):
                    try:
                        health_result = await module.health_check()
                        return {
                            'status': component.status,
                            'healthy': health_result.get('healthy', True),
                            'health_score': health_result.get('score', 100),
                            'metrics': health_result.get('metrics', {}),
                            'error': health_result.get('error'),
                            'last_check': component.last_health_check.isoformat()
                        }
                    except Exception as e:
                        self.logger.error(f"Health check failed for {component_name}: {str(e)}")
            
            # Default health check result
            return {
                'status': component.status,
                'healthy': component.status in ['initialized', 'running', 'healthy'],
                'health_score': 100 if component.status in ['initialized', 'running', 'healthy'] else 50,
                'metrics': component.metrics,
                'error': component.error_message,
                'last_check': component.last_health_check.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed for {component_name}: {str(e)}")
            return {
                'status': 'error',
                'healthy': False,
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def collect_component_data(self, component_name: str) -> Dict[str, Any]:
        """Collect data from a specific component"""
        try:
            if component_name not in self.components:
                raise ValueError(f"Component {component_name} not found")
            
            component = self.components[component_name]
            data = {}
            
            # Try to collect data from component module
            if component_name in self._integration_modules:
                module = self._integration_modules[component_name]
                
                # Try different data collection methods
                if hasattr(module, 'get_metrics') and callable(module.get_metrics):
                    try:
                        data.update(await module.get_metrics())
                    except Exception as e:
                        self.logger.error(f"Failed to get metrics from {component_name}: {str(e)}")
                
                if hasattr(module, 'get_status') and callable(module.get_status):
                    try:
                        status_data = await module.get_status()
                        data['status'] = status_data
                    except Exception as e:
                        self.logger.error(f"Failed to get status from {component_name}: {str(e)}")
                
                # Component-specific data collection
                if component_name == 'health_monitor':
                    data.update(await self._collect_health_monitor_data(module))
                elif component_name == 'follow_automation':
                    data.update(await self._collect_follow_automation_data(module))
                elif component_name == 'security_scanner':
                    data.update(await self._collect_security_scanner_data(module))
                elif component_name == 'daily_contributions':
                    data.update(await self._collect_daily_contributions_data(module))
            
            # Add component metadata
            data['component_name'] = component_name
            data['collection_timestamp'] = datetime.utcnow().isoformat()
            
            # Update component metrics
            component.metrics.update(data)
            
            self.logger.debug(f"Collected data from component {component_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to collect data from component {component_name}: {str(e)}")
            return {
                'component_name': component_name,
                'error': str(e),
                'collection_timestamp': datetime.utcnow().isoformat()
            }
    
    async def _collect_health_monitor_data(self, module) -> Dict[str, Any]:
        """Collect data from health monitoring component"""
        data = {}
        try:
            # Try to get health scores
            if hasattr(module, 'get_health_scores'):
                scores = await module.get_health_scores()
                data['health_scores'] = scores
            
            # Try to get repository metrics
            if hasattr(module, 'get_repository_metrics'):
                metrics = await module.get_repository_metrics()
                data['repository_metrics'] = metrics
            
            # Try to get alerts
            if hasattr(module, 'get_alerts'):
                alerts = await module.get_alerts()
                data['alerts'] = alerts
            
            # Try to run a health check and get results
            if hasattr(module, 'run_health_check'):
                health_result = await module.run_health_check()
                data['health_check_result'] = health_result
            
        except Exception as e:
            self.logger.error(f"Failed to collect health monitor data: {str(e)}")
            data['error'] = str(e)
        
        return data
    
    async def _collect_follow_automation_data(self, module) -> Dict[str, Any]:
        """Collect data from follow automation component"""
        data = {}
        try:
            # Try to get automation status
            if hasattr(module, 'get_automation_status'):
                status = await module.get_automation_status()
                data['automation_status'] = status
            
            # Try to get follow metrics
            if hasattr(module, 'get_follow_metrics'):
                metrics = await module.get_follow_metrics()
                data['follow_metrics'] = metrics
            
            # Try to get rate limit status
            if hasattr(module, 'get_rate_limit_status'):
                rate_limit = await module.get_rate_limit_status()
                data['rate_limit'] = rate_limit
            
            # Try to get safety status
            if hasattr(module, 'get_safety_status'):
                safety = await module.get_safety_status()
                data['safety_status'] = safety
            
        except Exception as e:
            self.logger.error(f"Failed to collect follow automation data: {str(e)}")
            data['error'] = str(e)
        
        return data
    
    async def _collect_security_scanner_data(self, module) -> Dict[str, Any]:
        """Collect data from security scanner component"""
        data = {}
        try:
            # Try to get scan results
            if hasattr(module, 'get_latest_scan_results'):
                scan_results = await module.get_latest_scan_results()
                data['scan_results'] = scan_results
            
            # Try to get vulnerability counts
            if hasattr(module, 'get_vulnerability_counts'):
                vuln_counts = await module.get_vulnerability_counts()
                data['vulnerability_counts'] = vuln_counts
            
            # Try to get security metrics
            if hasattr(module, 'get_security_metrics'):
                security_metrics = await module.get_security_metrics()
                data['security_metrics'] = security_metrics
            
            # Try to get compliance status
            if hasattr(module, 'get_compliance_status'):
                compliance = await module.get_compliance_status()
                data['compliance_status'] = compliance
            
        except Exception as e:
            self.logger.error(f"Failed to collect security scanner data: {str(e)}")
            data['error'] = str(e)
        
        return data
    
    async def _collect_daily_contributions_data(self, module) -> Dict[str, Any]:
        """Collect data from daily contributions component"""
        data = {}
        try:
            # Try to get contribution metrics
            if hasattr(module, 'get_contribution_metrics'):
                metrics = await module.get_contribution_metrics()
                data['contribution_metrics'] = metrics
            
            # Try to get activity data
            if hasattr(module, 'get_activity_data'):
                activity = await module.get_activity_data()
                data['activity_data'] = activity
            
            # Try to get growth metrics
            if hasattr(module, 'get_growth_metrics'):
                growth = await module.get_growth_metrics()
                data['growth_metrics'] = growth
            
            # Try to get community data
            if hasattr(module, 'get_community_data'):
                community = await module.get_community_data()
                data['community_data'] = community
            
        except Exception as e:
            self.logger.error(f"Failed to collect daily contributions data: {str(e)}")
            data['error'] = str(e)
        
        return data
    
    async def get_component_status(self, component_name: str) -> Dict[str, Any]:
        """Get status of a specific component"""
        try:
            if component_name not in self.components:
                raise ValueError(f"Component {component_name} not found")
            
            component = self.components[component_name]
            
            # Get health status
            health_status = await self.check_component_health(component_name)
            
            # Get recent data
            recent_data = component.metrics.get('recent_data', {})
            
            return {
                'component_name': component_name,
                'status': component.status,
                'enabled': component.enabled,
                'health': health_status,
                'last_health_check': component.last_health_check.isoformat() if component.last_health_check else None,
                'error_message': component.error_message,
                'dependencies': component.dependencies,
                'recent_metrics': recent_data,
                'uptime': self._calculate_uptime(component),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get status for component {component_name}: {str(e)}")
            return {
                'component_name': component_name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _calculate_uptime(self, component: ComponentIntegration) -> Optional[float]:
        """Calculate component uptime"""
        try:
            # This would need to track component start time
            # For now, return None as we don't track start times
            return None
        except Exception:
            return None
    
    async def run_component_action(self, component_name: str, action: str, **kwargs) -> Dict[str, Any]:
        """Run an action on a specific component"""
        try:
            if component_name not in self.components:
                raise ValueError(f"Component {component_name} not found")
            
            component = self.components[component_name]
            
            if component_name in self._integration_modules:
                module = self._integration_modules[component_name]
                
                # Try to find and run the action
                if hasattr(module, action) and callable(getattr(module, action)):
                    action_func = getattr(module, action)
                    result = await action_func(**kwargs)
                    return {
                        'action': action,
                        'result': result,
                        'success': True,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    raise ValueError(f"Action {action} not found in component {component_name}")
            else:
                raise ValueError(f"Component {component_name} module not loaded")
                
        except Exception as e:
            self.logger.error(f"Failed to run action {action} on component {component_name}: {str(e)}")
            return {
                'action': action,
                'error': str(e),
                'success': False,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def generate_report(self, component_name: str) -> Dict[str, Any]:
        """Generate a report for a specific component"""
        try:
            if component_name not in self.components:
                raise ValueError(f"Component {component_name} not found")
            
            component = self.components[component_name]
            
            # Get component status and data
            status = await self.get_component_status(component_name)
            data = await self.collect_component_data(component_name)
            
            # Generate component-specific report
            if component_name == 'health_monitor':
                return await self._generate_health_monitor_report(status, data)
            elif component_name == 'follow_automation':
                return await self._generate_follow_automation_report(status, data)
            elif component_name == 'security_scanner':
                return await self._generate_security_scanner_report(status, data)
            elif component_name == 'daily_contributions':
                return await self._generate_daily_contributions_report(status, data)
            else:
                # Generic report
                return {
                    'component_name': component_name,
                    'report_type': 'generic',
                    'status': status,
                    'data': data,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to generate report for component {component_name}: {str(e)}")
            return {
                'component_name': component_name,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def _generate_health_monitor_report(self, status: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health monitoring report"""
        try:
            health_scores = data.get('health_scores', [])
            alerts = data.get('alerts', [])
            
            # Calculate overall health
            if health_scores:
                avg_score = sum(score.get('score', 0) for score in health_scores) / len(health_scores)
                grade = self._score_to_grade(avg_score)
            else:
                avg_score = 0
                grade = 'N/A'
            
            # Analyze alerts
            critical_alerts = [alert for alert in alerts if alert.get('severity') == 'critical']
            high_alerts = [alert for alert in alerts if alert.get('severity') == 'high']
            
            report = {
                'component_name': 'health_monitor',
                'report_type': 'health_summary',
                'overall_health': {
                    'score': avg_score,
                    'grade': grade,
                    'status': 'healthy' if avg_score > 80 else 'degraded' if avg_score > 60 else 'critical'
                },
                'repository_health': health_scores,
                'alerts_summary': {
                    'total': len(alerts),
                    'critical': len(critical_alerts),
                    'high': len(high_alerts),
                    'resolved': len([alert for alert in alerts if alert.get('status') == 'resolved'])
                },
                'key_metrics': data.get('repository_metrics', {}),
                'recommendations': self._generate_health_recommendations(health_scores, alerts),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate health monitor report: {str(e)}")
            return {'error': str(e), 'generated_at': datetime.utcnow().isoformat()}
    
    async def _generate_follow_automation_report(self, status: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate follow automation report"""
        try:
            automation_status = data.get('automation_status', {})
            follow_metrics = data.get('follow_metrics', {})
            safety_status = data.get('safety_status', {})
            
            report = {
                'component_name': 'follow_automation',
                'report_type': 'automation_summary',
                'automation_status': {
                    'enabled': automation_status.get('enabled', False),
                    'mode': automation_status.get('mode', 'unknown'),
                    'safe_mode': safety_status.get('safe_mode', False)
                },
                'performance_metrics': {
                    'total_actions': follow_metrics.get('total_actions', 0),
                    'successful_actions': follow_metrics.get('successful_actions', 0),
                    'success_rate': follow_metrics.get('success_rate', 0),
                    'rate_limit_hits': follow_metrics.get('rate_limit_hits', 0)
                },
                'safety_compliance': {
                    'compliance_score': safety_status.get('compliance_score', 0),
                    'emergency_stops': safety_status.get('emergency_stops', 0),
                    'last_safety_check': safety_status.get('last_safety_check')
                },
                'recommendations': self._generate_automation_recommendations(automation_status, safety_status),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate follow automation report: {str(e)}")
            return {'error': str(e), 'generated_at': datetime.utcnow().isoformat()}
    
    async def _generate_security_scanner_report(self, status: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security scanner report"""
        try:
            scan_results = data.get('scan_results', {})
            vulnerability_counts = data.get('vulnerability_counts', {})
            compliance_status = data.get('compliance_status', {})
            
            # Calculate security score
            total_vulns = sum(vulnerability_counts.values())
            if total_vulns == 0:
                security_score = 100
            elif total_vulns < 5:
                security_score = 80
            elif total_vulns < 20:
                security_score = 60
            else:
                security_score = 40
            
            report = {
                'component_name': 'security_scanner',
                'report_type': 'security_summary',
                'security_score': security_score,
                'vulnerability_summary': vulnerability_counts,
                'scan_results': {
                    'last_scan': scan_results.get('last_scan'),
                    'status': scan_results.get('status', 'unknown'),
                    'issues_found': total_vulns
                },
                'compliance_status': compliance_status,
                'recommendations': self._generate_security_recommendations(vulnerability_counts, compliance_status),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate security scanner report: {str(e)}")
            return {'error': str(e), 'generated_at': datetime.utcnow().isoformat()}
    
    async def _generate_daily_contributions_report(self, status: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate daily contributions report"""
        try:
            contribution_metrics = data.get('contribution_metrics', {})
            growth_metrics = data.get('growth_metrics', {})
            community_data = data.get('community_data', {})
            
            report = {
                'component_name': 'daily_contributions',
                'report_type': 'contributions_summary',
                'contribution_activity': {
                    'total_contributions': contribution_metrics.get('total_contributions', 0),
                    'daily_average': contribution_metrics.get('daily_average', 0),
                    'weekly_total': contribution_metrics.get('weekly_total', 0)
                },
                'growth_metrics': {
                    'new_contributors': growth_metrics.get('new_contributors', 0),
                    'growth_rate': growth_metrics.get('growth_rate', 0),
                    'retention_rate': growth_metrics.get('retention_rate', 0)
                },
                'community_insights': {
                    'active_contributors': community_data.get('active_contributors', 0),
                    'engagement_level': community_data.get('engagement_level', 'unknown'),
                    'top_contributors': community_data.get('top_contributors', [])
                },
                'recommendations': self._generate_contribution_recommendations(contribution_metrics, growth_metrics),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate daily contributions report: {str(e)}")
            return {'error': str(e), 'generated_at': datetime.utcnow().isoformat()}
    
    def _score_to_grade(self, score: float) -> str:
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
    
    def _generate_health_recommendations(self, health_scores: List[Dict], alerts: List[Dict]) -> List[str]:
        """Generate health monitoring recommendations"""
        recommendations = []
        
        try:
            if health_scores:
                low_score_count = sum(1 for score in health_scores if score.get('score', 0) < 70)
                if low_score_count > 0:
                    recommendations.append(f"{low_score_count} repositories have health scores below 70 - review maintenance practices")
            
            critical_alerts = [alert for alert in alerts if alert.get('severity') == 'critical']
            if critical_alerts:
                recommendations.append(f"Address {len(critical_alerts)} critical health alerts immediately")
            
            if not recommendations:
                recommendations.append("Repository health is currently good - maintain current practices")
                
        except Exception as e:
            self.logger.debug(f"Failed to generate health recommendations: {str(e)}")
            recommendations.append("Review repository health metrics for optimization opportunities")
        
        return recommendations
    
    def _generate_automation_recommendations(self, automation_status: Dict, safety_status: Dict) -> List[str]:
        """Generate automation recommendations"""
        recommendations = []
        
        try:
            if not automation_status.get('enabled', False):
                recommendations.append("Consider enabling automation for improved efficiency")
            
            if safety_status.get('compliance_score', 100) < 90:
                recommendations.append("Review safety compliance settings and ensure all safeguards are active")
            
            if automation_status.get('mode') != 'safe':
                recommendations.append("Run automation in safe mode for better compliance")
            
            if not recommendations:
                recommendations.append("Automation is running safely and efficiently")
                
        except Exception as e:
            self.logger.debug(f"Failed to generate automation recommendations: {str(e)}")
            recommendations.append("Review automation settings for optimization")
        
        return recommendations
    
    def _generate_security_recommendations(self, vulnerability_counts: Dict, compliance_status: Dict) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        try:
            critical_vulns = vulnerability_counts.get('critical', 0)
            if critical_vulns > 0:
                recommendations.append(f"Address {critical_vulns} critical vulnerabilities immediately")
            
            high_vulns = vulnerability_counts.get('high', 0)
            if high_vulns > 5:
                recommendations.append(f"Review and patch {high_vulns} high-severity vulnerabilities")
            
            if not compliance_status.get('compliant', True):
                recommendations.append("Review and address compliance issues")
            
            if not recommendations:
                recommendations.append("Security posture is good - maintain current practices")
                
        except Exception as e:
            self.logger.debug(f"Failed to generate security recommendations: {str(e)}")
            recommendations.append("Continue regular security scanning and monitoring")
        
        return recommendations
    
    def _generate_contribution_recommendations(self, contribution_metrics: Dict, growth_metrics: Dict) -> List[str]:
        """Generate contribution recommendations"""
        recommendations = []
        
        try:
            if growth_metrics.get('growth_rate', 0) < 0:
                recommendations.append("Focus on community engagement to improve contributor growth")
            
            if growth_metrics.get('retention_rate', 100) < 80:
                recommendations.append("Work on contributor retention strategies")
            
            if contribution_metrics.get('daily_average', 0) < 1:
                recommendations.append("Encourage more frequent contributions")
            
            if not recommendations:
                recommendations.append("Community contribution levels are healthy")
                
        except Exception as e:
            self.logger.debug(f"Failed to generate contribution recommendations: {str(e)}")
            recommendations.append("Monitor community growth and engagement metrics")
        
        return recommendations
    
    def get_all_components_status(self) -> Dict[str, Any]:
        """Get status of all components"""
        status_summary = {
            'total_components': len(self.components),
            'enabled_components': sum(1 for c in self.components.values() if c.enabled),
            'healthy_components': 0,
            'degraded_components': 0,
            'failed_components': 0,
            'components': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for component_name, component in self.components.items():
            component_status = {
                'enabled': component.enabled,
                'status': component.status,
                'error': component.error_message,
                'last_check': component.last_health_check.isoformat() if component.last_health_check else None
            }
            
            status_summary['components'][component_name] = component_status
            
            # Count by health status
            if component.status in ['healthy', 'initialized', 'running']:
                status_summary['healthy_components'] += 1
            elif component.status in ['degraded', 'warning']:
                status_summary['degraded_components'] += 1
            elif component.status in ['failed', 'error']:
                status_summary['failed_components'] += 1
        
        return status_summary


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        # Sample configuration
        config = {
            'components': {
                'health_monitor': {
                    'enabled': True,
                    'integration_path': '../health_monitoring',
                    'config': {}
                },
                'follow_automation': {
                    'enabled': True,
                    'integration_path': '../follow_automation',
                    'config': {}
                }
            }
        }
        
        # Initialize integration manager
        integration_manager = IntegrationManager(config)
        
        # Initialize components
        for component_name in ['health_monitor', 'follow_automation']:
            await integration_manager.initialize_component(component_name, {})
        
        # Get component status
        status = integration_manager.get_all_components_status()
        print(f"Integration status: {status}")
        
        # Collect data from a component
        if 'health_monitor' in integration_manager.components:
            data = await integration_manager.collect_component_data('health_monitor')
            print(f"Health monitor data: {data}")
        
        # Generate report
        report = await integration_manager.generate_report('health_monitor')
        print(f"Health monitor report: {report}")
    
    asyncio.run(main())