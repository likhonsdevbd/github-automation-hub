"""
Configuration management for analytics orchestrator
"""

import yaml
import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from copy import deepcopy


@dataclass
class AnalyticsConfig:
    """Analytics configuration structure"""
    enabled: bool = True
    log_level: str = "INFO"
    data_retention_days: int = 30
    processing_interval: int = 60
    batch_size: int = 100


@dataclass
class APIConfig:
    """API gateway configuration structure"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = None
    rate_limit: int = 1000
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


@dataclass
class ComponentConfig:
    """Component configuration structure"""
    enabled: bool = False
    integration_path: str = ""
    dependencies: List[str] = None
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config is None:
            self.config = {}


@dataclass
class IntegrationConfig:
    """Integration configuration structure"""
    github:
        token: Optional[str] = None
        rate_limit_buffer: int = 1000
        cache_ttl: int = 300
    
    def __post_init__(self):
        # GitHub token from environment variable
        self.github.token = os.getenv('GITHUB_TOKEN')


@dataclass
class MonitoringConfig:
    """Monitoring configuration structure"""
    metrics_collection: bool = True
    health_checks: bool = True
    alert_threshold: float = 80.0
    check_interval: int = 60


@dataclass
class WorkflowConfig:
    """Workflow configuration structure"""
    timeout: int = 3600  # 1 hour
    retry_count: int = 3
    retry_delay: int = 300  # 5 minutes
    max_concurrent: int = 5


class ConfigManager:
    """
    Configuration manager for analytics orchestrator
    Handles loading, validation, and management of configuration settings
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration manager"""
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Configuration cache
        self._config_cache = {}
        self._config_file_modified = None
        
        # Default configuration templates
        self._default_config = self._create_default_config()
        
        # Load configuration
        self.load_config()
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            # Check if file was modified
            current_modified = self.config_path.stat().st_mtime if self.config_path.exists() else None
            
            if not force_reload and current_modified == self._config_file_modified:
                return self._config_cache.get('main', {})
            
            if self.config_path.exists():
                self.logger.info(f"Loading configuration from {self.config_path}")
                
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                
                # Validate and merge with defaults
                config = self._merge_with_defaults(config)
                
                # Validate configuration
                self._validate_config(config)
                
                # Cache configuration
                self._config_cache['main'] = config
                self._config_file_modified = current_modified
                
                self.logger.info("Configuration loaded successfully")
                return config
            
            else:
                self.logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                config = self._create_default_config()
                self.save_config(config)
                return config
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            if self._config_cache:
                self.logger.warning("Using cached configuration")
                return self._config_cache.get('main', self._create_default_config())
            else:
                self.logger.error("Using default configuration")
                return self._create_default_config()
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration (cached if available)"""
        return self.load_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write configuration
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            # Update cache
            self._config_cache['main'] = config
            self._config_file_modified = self.config_path.stat().st_mtime
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            return False
    
    def create_template(self, output_path: str = "config/config.template.yaml"):
        """Create configuration template file"""
        template_path = Path(output_path)
        
        try:
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(template_path, 'w') as f:
                f.write("# Analytics Orchestrator Configuration Template\n")
                f.write("# Copy this file to config.yaml and modify as needed\n\n")
                yaml.dump(self._create_default_config(), f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration template created at {template_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create template: {str(e)}")
            return False
    
    def validate_config(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        if config is None:
            config = self.get_config()
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # Validate analytics orchestrator section
            if 'analytics_orchestrator' not in config:
                validation_results['errors'].append("Missing 'analytics_orchestrator' section")
                validation_results['valid'] = False
            else:
                # Validate analytics config
                self._validate_analytics_config(
                    config.get('analytics_orchestrator', {}),
                    validation_results
                )
                
                # Validate API gateway config
                self._validate_api_config(
                    config.get('api_gateway', {}),
                    validation_results
                )
                
                # Validate components config
                self._validate_components_config(
                    config.get('components', {}),
                    validation_results
                )
                
                # Validate integration config
                self._validate_integration_config(
                    config.get('integrations', {}),
                    validation_results
                )
                
                # Validate monitoring config
                self._validate_monitoring_config(
                    config.get('monitoring', {}),
                    validation_results
                )
                
                # Validate workflow config
                self._validate_workflow_config(
                    config.get('workflows', {}),
                    validation_results
                )
        
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {str(e)}")
            validation_results['valid'] = False
        
        return validation_results
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            'analytics_orchestrator': {
                'enabled': True,
                'log_level': 'INFO',
                'data_retention_days': 30,
                'processing_interval': 60,
                'batch_size': 100
            },
            'api_gateway': {
                'host': '0.0.0.0',
                'port': 8000,
                'cors_origins': ['*'],
                'rate_limit': 1000,
                'api_key': None,
                'jwt_secret': None
            },
            'components': {
                'health_monitor': {
                    'enabled': True,
                    'integration_path': '../health_monitoring',
                    'dependencies': [],
                    'config': {}
                },
                'follow_automation': {
                    'enabled': True,
                    'integration_path': '../follow_automation',
                    'dependencies': [],
                    'config': {}
                },
                'security_scanner': {
                    'enabled': True,
                    'integration_path': '../security_automation',
                    'dependencies': [],
                    'config': {}
                },
                'daily_contributions': {
                    'enabled': True,
                    'integration_path': '../daily_contributions',
                    'dependencies': [],
                    'config': {}
                },
                'data_pipeline': {
                    'enabled': True,
                    'integration_path': None,
                    'dependencies': [],
                    'config': {
                        'batch_size': 100,
                        'processing_interval': 60,
                        'storage_backend': 'memory',
                        'cache_enabled': True
                    }
                }
            },
            'integrations': {
                'github': {
                    'token': os.getenv('GITHUB_TOKEN'),
                    'rate_limit_buffer': 1000,
                    'cache_ttl': 300
                },
                'health_monitor': {
                    'sync_interval': 300
                },
                'alerting': {
                    'channels': ['slack', 'email'],
                    'webhook_url': os.getenv('WEBHOOK_URL')
                }
            },
            'monitoring': {
                'metrics_collection': True,
                'health_checks': True,
                'alert_threshold': 80.0,
                'check_interval': 60
            },
            'workflows': {
                'timeout': 3600,
                'retry_count': 3,
                'retry_delay': 300,
                'max_concurrent': 5,
                'schedules': {
                    'health_monitoring': '0 2 * * *',
                    'security_scanning': '0 3 * * *',
                    'automation_tracking': '0 */4 * * *',
                    'community_analysis': '0 0 * * 0'
                }
            },
            'data_pipeline': {
                'batch_size': 100,
                'processing_interval': 60,
                'retention_days': 30,
                'storage_backends': {
                    'time_series': {
                        'type': 'memory',
                        'config': {}
                    },
                    'metrics': {
                        'type': 'memory',
                        'config': {}
                    },
                    'cache': {
                        'type': 'memory',
                        'config': {
                            'ttl': 3600
                        }
                    }
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/analytics_orchestrator.log',
                'max_size_mb': 100,
                'backup_count': 5
            },
            'security': {
                'api_authentication': False,
                'jwt_secret': os.getenv('JWT_SECRET'),
                'encryption_key': os.getenv('ENCRYPTION_KEY')
            }
        }
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration with defaults"""
        merged = deepcopy(self._default_config)
        
        # Deep merge configuration
        self._deep_merge(merged, config)
        
        return merged
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Deep merge two dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration structure"""
        required_sections = [
            'analytics_orchestrator',
            'api_gateway',
            'components',
            'integrations',
            'monitoring',
            'workflows',
            'data_pipeline',
            'logging'
        ]
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
    
    def _validate_analytics_config(self, config: Dict[str, Any], results: Dict[str, Any]):
        """Validate analytics orchestrator configuration"""
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if not isinstance(config.get('enabled'), bool):
            results['errors'].append("analytics_orchestrator.enabled must be boolean")
            results['valid'] = False
        
        log_level = config.get('log_level', 'INFO')
        if log_level not in valid_log_levels:
            results['errors'].append(f"Invalid log_level: {log_level}. Must be one of {valid_log_levels}")
            results['valid'] = False
        
        retention_days = config.get('data_retention_days', 30)
        if not isinstance(retention_days, int) or retention_days <= 0:
            results['errors'].append("data_retention_days must be positive integer")
            results['valid'] = False
    
    def _validate_api_config(self, config: Dict[str, Any], results: Dict[str, Any]):
        """Validate API gateway configuration"""
        port = config.get('port', 8000)
        if not isinstance(port, int) or port <= 0 or port > 65535:
            results['errors'].append("API port must be valid port number (1-65535)")
            results['valid'] = False
        
        rate_limit = config.get('rate_limit', 1000)
        if not isinstance(rate_limit, int) or rate_limit <= 0:
            results['errors'].append("Rate limit must be positive integer")
            results['valid'] = False
    
    def _validate_components_config(self, config: Dict[str, Any], results: Dict[str, Any]):
        """Validate components configuration"""
        required_components = ['health_monitor', 'follow_automation', 'security_scanner', 'daily_contributions']
        
        for component in required_components:
            if component not in config:
                results['errors'].append(f"Missing required component: {component}")
                results['valid'] = False
            else:
                component_config = config[component]
                if not isinstance(component_config.get('enabled'), bool):
                    results['errors'].append(f"Component {component} must have boolean 'enabled' field")
                    results['valid'] = False
        
        # Check for duplicate dependencies
        all_dependencies = []
        for component_name, component_config in config.items():
            dependencies = component_config.get('dependencies', [])
            for dep in dependencies:
                if dep in all_dependencies:
                    results['warnings'].append(f"Component {component_name} has duplicate dependency: {dep}")
                all_dependencies.append(dep)
    
    def _validate_integration_config(self, config: Dict[str, Any], results: Dict[str, Any]):
        """Validate integration configuration"""
        # Check GitHub integration
        if 'github' in config:
            github_config = config['github']
            token = github_config.get('token')
            if not token:
                results['warnings'].append("GitHub token not configured - GitHub integration will be disabled")
            
            rate_limit_buffer = github_config.get('rate_limit_buffer', 1000)
            if not isinstance(rate_limit_buffer, int) or rate_limit_buffer <= 0:
                results['errors'].append("GitHub rate_limit_buffer must be positive integer")
                results['valid'] = False
    
    def _validate_monitoring_config(self, config: Dict[str, Any], results: Dict[str, Any]):
        """Validate monitoring configuration"""
        alert_threshold = config.get('alert_threshold', 80.0)
        if not isinstance(alert_threshold, (int, float)) or alert_threshold < 0 or alert_threshold > 100:
            results['errors'].append("alert_threshold must be between 0 and 100")
            results['valid'] = False
        
        check_interval = config.get('check_interval', 60)
        if not isinstance(check_interval, int) or check_interval <= 0:
            results['errors'].append("check_interval must be positive integer")
            results['valid'] = False
    
    def _validate_workflow_config(self, config: Dict[str, Any], results: Dict[str, Any]):
        """Validate workflow configuration"""
        timeout = config.get('timeout', 3600)
        if not isinstance(timeout, int) or timeout <= 0:
            results['errors'].append("Workflow timeout must be positive integer")
            results['valid'] = False
        
        max_concurrent = config.get('max_concurrent', 5)
        if not isinstance(max_concurrent, int) or max_concurrent <= 0:
            results['errors'].append("max_concurrent must be positive integer")
            results['valid'] = False
        
        # Validate cron schedules
        if 'schedules' in config:
            schedules = config['schedules']
            valid_schedule_patterns = [
                r'^\d+ \d+ \* \* \*$',  # Daily at specific hour
                r'^\d+ \*/\d+ \* \* \*$',  # Every N hours
                r'^\d+ \d+ \* \* \d+$',  # Weekly on specific day
            ]
            
            import re
            for schedule_name, schedule_cron in schedules.items():
                is_valid = any(re.match(pattern, schedule_cron) for pattern in valid_schedule_patterns)
                if not is_valid:
                    results['warnings'].append(f"Invalid cron schedule for {schedule_name}: {schedule_cron}")
    
    def get_component_config(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific component"""
        config = self.get_config()
        return config.get('components', {}).get(component_name)
    
    def update_component_config(self, component_name: str, component_config: Dict[str, Any]) -> bool:
        """Update configuration for specific component"""
        config = self.get_config()
        
        if 'components' not in config:
            config['components'] = {}
        
        config['components'][component_name] = component_config
        
        return self.save_config(config)
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API gateway configuration"""
        config = self.get_config()
        return config.get('api_gateway', {})
    
    def get_integration_config(self, integration_name: str) -> Optional[Dict[str, Any]]:
        """Get integration configuration"""
        config = self.get_config()
        return config.get('integrations', {}).get(integration_name)
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        config = self.get_config()
        return config.get('monitoring', {})
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration"""
        config = self.get_config()
        return config.get('workflows', {})
    
    def export_config(self, output_path: str, format: str = 'yaml') -> bool:
        """Export configuration to file"""
        try:
            config = self.get_config()
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(output_file, 'w') as f:
                    json.dump(config, f, indent=2)
            elif format.lower() == 'yaml':
                with open(output_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Configuration exported to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {str(e)}")
            return False


# Utility functions for configuration management

def load_config_from_env(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load configuration values from environment variables"""
    import os
    
    # GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        if 'integrations' not in config:
            config['integrations'] = {}
        if 'github' not in config['integrations']:
            config['integrations']['github'] = {}
        config['integrations']['github']['token'] = github_token
    
    # JWT secret
    jwt_secret = os.getenv('JWT_SECRET')
    if jwt_secret:
        if 'security' not in config:
            config['security'] = {}
        config['security']['jwt_secret'] = jwt_secret
    
    # API key
    api_key = os.getenv('API_KEY')
    if api_key:
        if 'api_gateway' not in config:
            config['api_gateway'] = {}
        config['api_gateway']['api_key'] = api_key
    
    # Webhook URL
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        if 'integrations' not in config:
            config['integrations'] = {}
        if 'alerting' not in config['integrations']:
            config['integrations']['alerting'] = {}
        config['integrations']['alerting']['webhook_url'] = webhook_url
    
    return config


def validate_required_env_vars(config: Dict[str, Any]) -> List[str]:
    """Validate that required environment variables are set"""
    missing_vars = []
    
    # GitHub token is required for most integrations
    github_config = config.get('integrations', {}).get('github', {})
    if github_config.get('token') is None:
        missing_vars.append('GITHUB_TOKEN')
    
    return missing_vars


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Analytics Orchestrator Configuration Manager')
    parser.add_argument('--config', default='config/config.yaml', help='Configuration file path')
    parser.add_argument('action', choices=['validate', 'template', 'export'], help='Action to perform')
    parser.add_argument('--output', help='Output file for template/export actions')
    parser.add_argument('--format', default='yaml', choices=['yaml', 'json'], help='Export format')
    
    args = parser.parse_args()
    
    config_manager = ConfigManager(args.config)
    
    if args.action == 'validate':
        validation_results = config_manager.validate_config()
        print(f"Configuration valid: {validation_results['valid']}")
        if validation_results['errors']:
            print("Errors:")
            for error in validation_results['errors']:
                print(f"  - {error}")
        if validation_results['warnings']:
            print("Warnings:")
            for warning in validation_results['warnings']:
                print(f"  - {warning}")
        if validation_results['suggestions']:
            print("Suggestions:")
            for suggestion in validation_results['suggestions']:
                print(f"  - {suggestion}")
    
    elif args.action == 'template':
        output_path = args.output or 'config/config.template.yaml'
        config_manager.create_template(output_path)
        print(f"Configuration template created at {output_path}")
    
    elif args.action == 'export':
        output_path = args.output or 'config/config.export.yaml'
        config_manager.export_config(output_path, args.format)
        print(f"Configuration exported to {output_path}")
