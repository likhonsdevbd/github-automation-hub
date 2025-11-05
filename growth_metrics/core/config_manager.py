"""
Configuration Manager
====================

Centralized configuration management for the growth metrics system:
- Environment-based configuration
- Validation and defaults
- Dynamic configuration updates
- Configuration caching and persistence
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GitHubConfig:
    """GitHub API configuration"""
    token: str = ""
    base_url: str = "https://api.github.com"
    api_version: str = "2022-11-28"
    timeout: int = 30
    max_retries: int = 3
    per_page: int = 100
    organizations: List[str] = field(default_factory=list)
    repositories: List[str] = field(default_factory=list)
    rate_limit_budget: int = 2000  # Conservative budget


@dataclass 
class CollectionConfig:
    """Data collection configuration"""
    schedule: str = "0 2 * * *"  # Daily at 2 AM UTC
    batch_size: int = 100
    cache_ttl: int = 300  # 5 minutes
    enable_caching: bool = True
    enable_rate_limiting: bool = True
    enable_circuit_breaker: bool = True
    timeout_per_request: int = 30
    max_concurrent_requests: int = 5
    historical_days: int = 365  # How many days of history to collect
    snapshot_interval: int = 24  # Hours between snapshots


@dataclass
class StorageConfig:
    """Data storage configuration"""
    backend: str = "sqlite"  # sqlite, postgres, filesystem
    connection_string: str = "sqlite:///growth_metrics.db"
    batch_size: int = 1000
    enable_compression: bool = True
    retention_days: int = 365
    backup_enabled: bool = True
    backup_interval: int = 24  # Hours
    data_directory: str = "./data"
    create_indexes: bool = True


@dataclass
class AnalyticsConfig:
    """Analytics and reporting configuration"""
    health_score_weights: Dict[str, float] = field(default_factory=lambda: {
        'contributors': 0.30,
        'pr_throughput': 0.20, 
        'review_velocity': 0.20,
        'issue_freshness': 0.15,
        'fork_growth': 0.15
    })
    anomaly_detection_enabled: bool = True
    forecasting_enabled: bool = True
    forecasting_days: int = 30
    trend_analysis_period: int = 90
    community_engagement_tracking: bool = True
    release_tracking: bool = True


@dataclass
class NotificationConfig:
    """Notification and alerting configuration"""
    email_enabled: bool = False
    slack_enabled: bool = False
    webhook_enabled: bool = True
    github_issues_enabled: bool = True
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    slack_webhook_url: str = ""
    github_webhook_secret: str = ""
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'health_score_drop': 10.0,  # 10% drop
        'contributors_stagnation': 4,  # 4 weeks
        'review_velocity_slowdown': 2.0,  # 2x baseline
        'issue_freshness_degradation': 21  # days
    })


@dataclass
class SystemConfig:
    """Overall system configuration"""
    environment: str = "development"  # development, staging, production
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    metrics_enabled: bool = True
    profiling_enabled: bool = False
    telemetry_enabled: bool = True
    performance_monitoring: bool = True


@dataclass
class WorkflowConfig:
    """GitHub Actions workflow configuration"""
    workflows_enabled: bool = True
    daily_metrics_workflow: bool = True
    health_check_workflow: bool = True
    reporting_workflow: bool = True
    alert_workflow: bool = True
    schedule_offset_minutes: int = 15  # Random offset to avoid thundering herd
    workflow_timeout: int = 3600  # 1 hour


class ConfigManager:
    """
    Centralized configuration manager with validation and defaults
    """
    
    def __init__(self, config_path: str = None, env_prefix: str = "GM"):
        self.config_path = config_path
        self.env_prefix = env_prefix.upper()
        
        # Configuration sections
        self.github = GitHubConfig()
        self.collection = CollectionConfig()
        self.storage = StorageConfig()
        self.analytics = AnalyticsConfig()
        self.notifications = NotificationConfig()
        self.system = SystemConfig()
        self.workflows = WorkflowConfig()
        
        # Internal state
        self._config_cache = {}
        self._last_loaded = None
        self._watchers = []  # Configuration change watchers
        
    def load_from_file(self, file_path: str) -> None:
        """Load configuration from YAML/JSON file"""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return
            
        try:
            with open(path, 'r') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
                    
            self._load_from_dict(config_data)
            logger.info(f"Configuration loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            raise
            
    def load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        config_data = {}
        
        # GitHub configuration
        github_vars = {
            'GITHUB_TOKEN': 'github.token',
            'GITHUB_BASE_URL': 'github.base_url',
            'GITHUB_TIMEOUT': 'github.timeout',
            'GITHUB_MAX_RETRIES': 'github.max_retries',
            'GITHUB_ORG': 'github.organizations',
            'GITHUB_REPO': 'github.repositories',
            'GITHUB_RATE_LIMIT_BUDGET': 'github.rate_limit_budget'
        }
        
        for env_var, config_path in github_vars.items():
            value = os.getenv(f"{self.env_prefix}_{env_var}")
            if value is not None:
                self._set_nested_value(config_data, config_path, value)
                
        # Storage configuration
        storage_vars = {
            'STORAGE_BACKEND': 'storage.backend',
            'STORAGE_CONNECTION': 'storage.connection_string',
            'STORAGE_DATA_DIR': 'storage.data_directory'
        }
        
        for env_var, config_path in storage_vars.items():
            value = os.getenv(f"{self.env_prefix}_{env_var}")
            if value is not None:
                self._set_nested_value(config_data, config_path, value)
                
        # System configuration
        system_vars = {
            'ENVIRONMENT': 'system.environment',
            'DEBUG': 'system.debug',
            'LOG_LEVEL': 'system.log_level',
            'METRICS_ENABLED': 'system.metrics_enabled'
        }
        
        for env_var, config_path in system_vars.items():
            value = os.getenv(f"{self.env_prefix}_{env_var}")
            if value is not None:
                self._set_nested_value(config_data, config_path, value)
                
        if config_data:
            self._load_from_dict(config_data)
            logger.info("Configuration loaded from environment variables")
            
    def _load_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Load configuration from dictionary"""
        
        # Load GitHub configuration
        if 'github' in config_data:
            github_data = config_data['github']
            self.github = self._update_config_dataclass(self.github, github_data)
            
        # Load collection configuration
        if 'collection' in config_data:
            collection_data = config_data['collection']
            self.collection = self._update_config_dataclass(self.collection, collection_data)
            
        # Load storage configuration
        if 'storage' in config_data:
            storage_data = config_data['storage']
            self.storage = self._update_config_dataclass(self.storage, storage_data)
            
        # Load analytics configuration
        if 'analytics' in config_data:
            analytics_data = config_data['analytics']
            self.analytics = self._update_config_dataclass(self.analytics, analytics_data)
            
        # Load notifications configuration
        if 'notifications' in config_data:
            notifications_data = config_data['notifications']
            self.notifications = self._update_config_dataclass(self.notifications, notifications_data)
            
        # Load system configuration
        if 'system' in config_data:
            system_data = config_data['system']
            self.system = self._update_config_dataclass(self.system, system_data)
            
        # Load workflow configuration
        if 'workflows' in config_data:
            workflows_data = config_data['workflows']
            self.workflows = self._update_config_dataclass(self.workflows, workflows_data)
            
        self._last_loaded = datetime.now()
        
    def _update_config_dataclass(self, dataclass_obj: Any, data: Dict[str, Any]) -> Any:
        """Update dataclass with data dictionary"""
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(dataclass_obj, key):
                    current_value = getattr(dataclass_obj, key)
                    
                    # Handle nested dictionaries
                    if isinstance(current_value, dict) and isinstance(value, dict):
                        setattr(dataclass_obj, key, {**current_value, **value})
                    elif isinstance(value, str) and current_value:
                        # Type conversion for common cases
                        if key in ['timeout', 'max_retries', 'per_page', 'batch_size', 'timeout_per_request']:
                            try:
                                value = int(value)
                            except ValueError:
                                pass
                        elif key in ['enable_caching', 'enable_rate_limiting', 'debug', 'metrics_enabled']:
                            if isinstance(value, str):
                                value = value.lower() in ('true', '1', 'yes', 'on')
                            else:
                                value = bool(value)
                                
                    setattr(dataclass_obj, key, value)
        return dataclass_obj
        
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        current[keys[-1]] = value
        
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = path.split('.')
        current = self
        
        for key in keys:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                return default
                
        return current
        
    def set(self, path: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = path.split('.')
        current = self
        
        for key in keys[:-1]:
            if not hasattr(current, key):
                setattr(current, key, type(getattr(self, keys[-2], {}))())
            current = getattr(current, key)
            
        setattr(current, keys[-1], value)
        self._notify_watchers(path, value)
        
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate GitHub token
        if not self.github.token:
            errors.append("GitHub token is required")
            
        # Validate storage backend
        if self.storage.backend not in ['sqlite', 'postgres', 'filesystem']:
            errors.append(f"Invalid storage backend: {self.storage.backend}")
            
        # Validate retention period
        if self.storage.retention_days < 1:
            errors.append("Storage retention days must be positive")
            
        # Validate weights
        if abs(sum(self.analytics.health_score_weights.values()) - 1.0) > 0.01:
            errors.append("Health score weights must sum to 1.0")
            
        # Validate organizations/repositories
        if not self.github.organizations and not self.github.repositories:
            errors.append("Must specify at least one organization or repository")
            
        return errors
        
    def add_watcher(self, callback: callable) -> None:
        """Add configuration change watcher"""
        self._watchers.append(callback)
        
    def _notify_watchers(self, path: str, value: Any) -> None:
        """Notify watchers of configuration changes"""
        for watcher in self._watchers:
            try:
                watcher(path, value)
            except Exception as e:
                logger.error(f"Configuration watcher failed: {e}")
                
    def save_to_file(self, file_path: str) -> None:
        """Save current configuration to file"""
        config_dict = {
            'github': asdict(self.github),
            'collection': asdict(self.collection),
            'storage': asdict(self.storage),
            'analytics': asdict(self.analytics),
            'notifications': asdict(self.notifications),
            'system': asdict(self.system),
            'workflows': asdict(self.workflows)
        }
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)
                
        logger.info(f"Configuration saved to {file_path}")
        
    def get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration with all values"""
        return {
            'github': asdict(self.github),
            'collection': asdict(self.collection),
            'storage': asdict(self.storage),
            'analytics': asdict(self.analytics),
            'notifications': asdict(self.notifications),
            'system': asdict(self.system),
            'workflows': asdict(self.workflows)
        }
        
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.system.environment.lower() == 'production'
        
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled"""
        return self.system.debug or not self.is_production()
        
    def get_cache_ttl(self) -> int:
        """Get cache TTL based on environment"""
        base_ttl = self.collection.cache_ttl
        
        if self.is_production():
            return base_ttl
        else:
            return min(base_ttl, 60)  # Shorter cache in development