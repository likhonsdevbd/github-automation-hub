#!/usr/bin/env python3
"""
Automation Hub Dashboard - Main Application

This script starts the complete dashboard system including:
- FastAPI backend with WebSocket support
- Real-time monitoring and alerting
- Notification integrations
- Alert management and escalation
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
import yaml
import argparse

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from backend.dashboard_api import app as api_app
from integrations.notifications import NotificationManager
from alerts.alert_manager import AlertManager, SystemMonitor
from integrations.monitoring import MonitoringSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dashboard.log')
    ]
)
logger = logging.getLogger(__name__)

class DashboardApplication:
    """Main dashboard application"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        
        # Initialize components
        self.notification_manager = None
        self.alert_manager = None
        self.system_monitor = None
        self.monitoring_system = None
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    async def initialize_components(self):
        """Initialize all dashboard components"""
        try:
            logger.info("Initializing dashboard components...")
            
            # Initialize notification manager
            notification_config = self.config.get('notifications', {})
            self.notification_manager = NotificationManager(notification_config)
            
            # Initialize alert manager
            alert_config = self.config.get('alerts', {})
            self.alert_manager = AlertManager(alert_config)
            
            # Load alert rules
            alert_rules = alert_config.get('rules', [])
            for rule_data in alert_rules:
                from alerts.alert_manager import AlertRule, AlertSeverity
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
                self.alert_manager.add_alert_rule(rule)
            
            # Register notification callbacks
            self._setup_notification_callbacks()
            
            # Initialize monitoring system
            monitoring_config = self.config.get('monitoring', {})
            self.monitoring_system = MonitoringSystem(monitoring_config)
            
            # Initialize system monitor
            self.system_monitor = SystemMonitor(self.alert_manager)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _setup_notification_callbacks(self):
        """Setup notification callbacks for alert manager"""
        # Slack notification
        async def slack_callback(data):
            notification = data['alert']
            result = await self.notification_manager.send_alert(
                title=notification.name,
                message=notification.description,
                severity=notification.severity.value,
                details={
                    'alert_id': notification.id,
                    'current_value': notification.current_value,
                    'threshold': notification.threshold,
                    'status': notification.status.value
                }
            )
            logger.info(f"Slack notification sent: {result}")
        
        # Email notification
        async def email_callback(data):
            notification = data['alert']
            # Implement email notification logic
            logger.info(f"Email notification sent for: {notification.name}")
        
        # Register callbacks
        self.alert_manager.register_notification_callback('slack', slack_callback)
        self.alert_manager.register_notification_callback('email', email_callback)
    
    async def start(self):
        """Start the dashboard application"""
        try:
            await self.initialize_components()
            
            self.running = True
            
            # Start background tasks
            tasks = []
            
            # Start system monitoring
            if self.system_monitor:
                monitoring_task = asyncio.create_task(
                    self.system_monitor.start_monitoring(
                        self.config.get('alerts', {}).get('check_interval', 30)
                    )
                )
                tasks.append(monitoring_task)
                logger.info("System monitoring started")
            
            # Start health checks
            health_task = asyncio.create_task(self._health_check_loop())
            tasks.append(health_task)
            
            # Start cleanup tasks
            cleanup_task = asyncio.create_task(self._cleanup_loop())
            tasks.append(cleanup_task)
            
            # Setup signal handlers
            self._setup_signal_handlers(tasks)
            
            logger.info("Dashboard application started successfully")
            logger.info(f"API available at: http://{self.config.get('api', {}).get('host', '0.0.0.0')}:{self.config.get('api', {}).get('port', 8000)}")
            
            # Run all tasks
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Failed to start dashboard application: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the dashboard application"""
        logger.info("Stopping dashboard application...")
        
        self.running = False
        
        # Stop system monitor
        if self.system_monitor:
            await self.system_monitor.stop_monitoring()
        
        logger.info("Dashboard application stopped")
    
    async def _health_check_loop(self):
        """Periodic health check"""
        while self.running:
            try:
                # Check monitoring system health
                if self.monitoring_system:
                    health = await self.monitoring_system.health_check()
                    if not all(health.values()):
                        logger.warning(f"Monitoring system health issues: {health}")
                
                # Check alert statistics
                if self.alert_manager:
                    stats = self.alert_manager.get_alert_statistics()
                    if stats['critical_alerts'] > 0:
                        logger.warning(f"Active critical alerts: {stats['critical_alerts']}")
                
                await asyncio.sleep(60)  # Health check every minute
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old data"""
        while self.running:
            try:
                # Clean old alerts
                if self.alert_manager:
                    cutoff_time = asyncio.get_event_loop().time() - (24 * 3600)  # 24 hours
                    # Implement cleanup logic
                
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(3600)
    
    def _setup_signal_handlers(self, tasks):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.running = False
            
            # Cancel all tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Schedule stop
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'data',
        'static',
        'uploads'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Directory created/verified: {directory}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Automation Hub Dashboard')
    parser.add_argument(
        '--config', 
        default='config/dashboard.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create sample configuration file'
    )
    parser.add_argument(
        '--host',
        default=None,
        help='Host to bind to (overrides config)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to bind to (overrides config)'
    )
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Run in development mode'
    )
    
    args = parser.parse_args()
    
    # Create sample config if requested
    if args.create_config:
        create_directories()
        logger.info("Sample configuration file created")
        return
    
    # Create necessary directories
    create_directories()
    
    # Load configuration
    config_path = args.config
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return
    
    # Initialize and start application
    app = DashboardApplication(config_path)
    
    try:
        # Override host/port if specified
        if args.host or args.port:
            api_config = app.config.setdefault('api', {})
            if args.host:
                api_config['host'] = args.host
            if args.port:
                api_config['port'] = args.port
        
        # Set development mode
        if args.dev:
            app.config.setdefault('development', {})['reload'] = True
        
        await app.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Create default configuration if it doesn't exist
    config_path = Path('config/dashboard.yaml')
    if not config_path.exists():
        config_dir = config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the config template
        from shutil import copy
        copy('config/dashboard.yaml', str(config_path))
        print(f"Created configuration file: {config_path}")
        print("Please edit the configuration file and run again")
        sys.exit(0)
    
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)