import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class MetricData:
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metric_type: MetricType

@dataclass
class AlertRule:
    name: str
    query: str
    severity: str
    threshold: float
    duration: int  # seconds
    description: str
    labels: Dict[str, str]

class PrometheusIntegration:
    """Integration with Prometheus for metrics collection"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def query(self, query: str, time: Optional[datetime] = None) -> Dict[str, Any]:
        """Execute a PromQL query"""
        try:
            params = {
                'query': query
            }
            if time:
                params['time'] = str(int(time.timestamp()))
            
            async with self.session.get(f"{self.prometheus_url}/api/v1/query", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Prometheus query failed: {response.status}")
                    return {"status": "error", "data": {}}
                    
        except Exception as e:
            logger.error(f"Prometheus query error: {e}")
            return {"status": "error", "data": {}}
    
    async def query_range(self, query: str, start: datetime, end: datetime, step: str = "30s") -> Dict[str, Any]:
        """Execute a range query over time"""
        try:
            params = {
                'query': query,
                'start': str(int(start.timestamp())),
                'end': str(int(end.timestamp())),
                'step': step
            }
            
            async with self.session.get(f"{self.prometheus_url}/api/v1/query_range", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Prometheus range query failed: {response.status}")
                    return {"status": "error", "data": {}}
                    
        except Exception as e:
            logger.error(f"Prometheus range query error: {e}")
            return {"status": "error", "data": {}}
    
    async def get_targets(self) -> Dict[str, Any]:
        """Get all scraping targets"""
        try:
            async with self.session.get(f"{self.prometheus_url}/api/v1/targets") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get targets: {response.status}")
                    return {"status": "error"}
        except Exception as e:
            logger.error(f"Error getting targets: {e}")
            return {"status": "error"}
    
    async def get_rules(self) -> Dict[str, Any]:
        """Get all configured rules"""
        try:
            async with self.session.get(f"{self.prometheus_url}/api/v1/rules") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get rules: {response.status}")
                    return {"status": "error"}
        except Exception as e:
            logger.error(f"Error getting rules: {e}")
            return {"status": "error"}
    
    async def get_series(self, match: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> Dict[str, Any]:
        """Get series data"""
        try:
            params = {'match[]': match}
            if start:
                params['start'] = str(int(start.timestamp()))
            if end:
                params['end'] = str(int(end.timestamp()))
            
            async with self.session.get(f"{self.prometheus_url}/api/v1/series", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get series: {response.status}")
                    return {"status": "error"}
        except Exception as e:
            logger.error(f"Error getting series: {e}")
            return {"status": "error"}

class GrafanaIntegration:
    """Integration with Grafana for dashboard management"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000", api_key: str = ""):
        self.grafana_url = grafana_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """Get dashboard by UID"""
        try:
            async with self.session.get(f"{self.grafana_url}/api/dashboards/uid/{uid}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get dashboard: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting dashboard: {e}")
            return {}
    
    async def create_dashboard(self, dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard"""
        try:
            payload = {
                "dashboard": dashboard,
                "overwrite": False,
                "message": "Created by Automation Hub Dashboard"
            }
            
            async with self.session.post(f"{self.grafana_url}/api/dashboards/db", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Dashboard created: {result.get('url', '')}")
                    return result
                else:
                    logger.error(f"Failed to create dashboard: {response.status}")
                    return {"error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return {"error": str(e)}
    
    async def update_dashboard(self, dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing dashboard"""
        try:
            payload = {
                "dashboard": dashboard,
                "overwrite": True,
                "message": "Updated by Automation Hub Dashboard"
            }
            
            async with self.session.post(f"{self.grafana_url}/api/dashboards/db", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Dashboard updated: {result.get('url', '')}")
                    return result
                else:
                    logger.error(f"Failed to update dashboard: {response.status}")
                    return {"error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return {"error": str(e)}
    
    async def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboards"""
        try:
            async with self.session.get(f"{self.grafana_url}/api/search") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get dashboards: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting dashboards: {e}")
            return []

class MonitoringSystem:
    """Central monitoring system combining Prometheus and Grafana"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.prometheus = PrometheusIntegration(config.get('prometheus_url', 'http://localhost:9090'))
        self.grafana = GrafanaIntegration(
            config.get('grafana_url', 'http://localhost:3000'),
            config.get('grafana_api_key', '')
        )
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics from Prometheus"""
        metrics = {}
        
        async with self.prometheus as prom:
            # CPU usage
            cpu_result = await prom.query('100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
            if cpu_result.get('status') == 'success':
                metrics['cpu_usage'] = cpu_result['data']['result']
            
            # Memory usage
            mem_result = await prom.query('(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100')
            if mem_result.get('status') == 'success':
                metrics['memory_usage'] = mem_result['data']['result']
            
            # Disk usage
            disk_result = await prom.query('(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100')
            if disk_result.get('status') == 'success':
                metrics['disk_usage'] = disk_result['data']['result']
            
            # Network I/O
            net_result = await prom.query('rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m])')
            if net_result.get('status') == 'success':
                metrics['network_io'] = net_result['data']['result']
        
        return metrics
    
    async def get_automation_metrics(self) -> Dict[str, Any]:
        """Get automation-specific metrics"""
        metrics = {}
        
        async with self.prometheus as prom:
            # Active automations
            active_result = await prom.query('automation_active_automations')
            if active_result.get('status') == 'success':
                metrics['active'] = active_result['data']['result']
            
            # Completed automations
            completed_result = await prom.query('automation_completed_operations_total')
            if completed_result.get('status') == 'success':
                metrics['completed'] = completed_result['data']['result']
            
            # Failed automations
            failed_result = await prom.query('automation_failed_operations_total')
            if failed_result.get('status') == 'success':
                metrics['failed'] = failed_result['data']['result']
            
            # Success rate
            rate_result = await prom.query('automation_success_rate')
            if rate_result.get('status') == 'success':
                metrics['success_rate'] = rate_result['data']['result']
        
        return metrics
    
    async def get_historical_data(self, metric_name: str, hours: int = 24) -> List[Tuple[datetime, float]]:
        """Get historical data for a metric"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        async with self.prometheus as prom:
            result = await prom.query_range(
                metric_name,
                start_time,
                end_time,
                step="5m"
            )
            
            if result.get('status') == 'success':
                series_data = []
                for series in result['data']['result']:
                    for point in series['values']:
                        timestamp = datetime.fromtimestamp(float(point[0]))
                        value = float(point[1])
                        series_data.append((timestamp, value))
                return series_data
        
        return []
    
    async def setup_default_dashboards(self) -> Dict[str, Any]:
        """Set up default Grafana dashboards"""
        dashboards = {
            'system_overview': {
                'dashboard': {
                    'id': None,
                    'title': 'System Overview',
                    'tags': ['automation-hub', 'system'],
                    'timezone': 'browser',
                    'panels': [
                        {
                            'title': 'CPU Usage',
                            'type': 'graph',
                            'targets': [
                                {
                                    'expr': '100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                                    'legendFormat': 'CPU Usage %'
                                }
                            ],
                            'yAxes': [
                                {
                                    'label': 'Percentage',
                                    'min': 0,
                                    'max': 100
                                }
                            ]
                        },
                        {
                            'title': 'Memory Usage',
                            'type': 'graph',
                            'targets': [
                                {
                                    'expr': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                                    'legendFormat': 'Memory Usage %'
                                }
                            ],
                            'yAxes': [
                                {
                                    'label': 'Percentage',
                                    'min': 0,
                                    'max': 100
                                }
                            ]
                        }
                    ],
                    'time': {
                        'from': 'now-1h',
                        'to': 'now'
                    },
                    'refresh': '5s'
                }
            },
            'automation_metrics': {
                'dashboard': {
                    'id': None,
                    'title': 'Automation Metrics',
                    'tags': ['automation-hub', 'automation'],
                    'timezone': 'browser',
                    'panels': [
                        {
                            'title': 'Active Automations',
                            'type': 'stat',
                            'targets': [
                                {
                                    'expr': 'automation_active_automations',
                                    'legendFormat': 'Active'
                                }
                            ]
                        },
                        {
                            'title': 'Success Rate',
                            'type': 'graph',
                            'targets': [
                                {
                                    'expr': 'automation_success_rate',
                                    'legendFormat': 'Success Rate %'
                                }
                            ],
                            'yAxes': [
                                {
                                    'label': 'Percentage',
                                    'min': 0,
                                    'max': 100
                                }
                            ]
                        }
                    ],
                    'time': {
                        'from': 'now-1h',
                        'to': 'now'
                    },
                    'refresh': '5s'
                }
            }
        }
        
        results = {}
        async with self.grafana as grafana:
            for name, dashboard_config in dashboards.items():
                result = await grafana.create_dashboard(dashboard_config['dashboard'])
                results[name] = result
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of monitoring system"""
        health = {
            'prometheus': False,
            'grafana': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check Prometheus
        try:
            async with self.prometheus as prom:
                result = await prom.query('up')
                if result.get('status') == 'success':
                    health['prometheus'] = True
        except Exception as e:
            logger.error(f"Prometheus health check failed: {e}")
        
        # Check Grafana
        try:
            async with self.grafana as grafana:
                dashboards = await grafana.get_dashboards()
                if dashboards is not None:
                    health['grafana'] = True
        except Exception as e:
            logger.error(f"Grafana health check failed: {e}")
        
        return health

# Example usage
async def main():
    config = {
        'prometheus_url': 'http://localhost:9090',
        'grafana_url': 'http://localhost:3000',
        'grafana_api_key': 'your-grafana-api-key'
    }
    
    monitoring = MonitoringSystem(config)
    
    # Get system metrics
    system_metrics = await monitoring.get_system_metrics()
    print(f"System metrics: {json.dumps(system_metrics, indent=2)}")
    
    # Get automation metrics
    automation_metrics = await monitoring.get_automation_metrics()
    print(f"Automation metrics: {json.dumps(automation_metrics, indent=2)}")
    
    # Set up dashboards
    dashboard_results = await monitoring.setup_default_dashboards()
    print(f"Dashboards created: {json.dumps(dashboard_results, indent=2)}")
    
    # Health check
    health = await monitoring.health_check()
    print(f"Health status: {json.dumps(health, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())