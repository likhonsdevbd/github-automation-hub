"""
Configuration Manager - Centralized configuration management.

Handles loading, validation, and management of configuration files
with environment variable support and default values.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import yaml


class ConfigManager:
    """
    Configuration manager for the automation hub.
    
    Features:
    - JSON/YAML configuration file support
    - Environment variable overrides
    - Validation of required settings
    - Default value management
    - Configuration templates
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._config = {}
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from file and environment."""
        # Default configuration
        default_config = self._get_default_config()
        
        # Load from file if specified
        if self.config_path and Path(self.config_path).exists():
            file_config = self._load_from_file(self.config_path)
            self._config = self._merge_configs(default_config, file_config)
        else:
            self._config = default_config
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
        
        self.logger.info("Configuration loaded successfully")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'automation': {
                'enabled': False,  # Disabled by default for safety
                'operation_mode': 'analysis',  # 'analysis' or 'active'
                'max_concurrent_actions': 1,
                'safety_features': {
                    'emergency_stop_on_422': True,
                    'exponential_backoff_on_429': True,
                    'audit_logging': True,
                    'rate_limit_monitoring': True
                }
            },
            'rate_limits': {
                'max_actions_per_hour': 24,
                'max_api_calls_per_hour': 5000,
                'base_delay_seconds': 150,
                'min_delay_seconds': 60,
                'min_gap_between_actions': 180,
                'jitter_factor': 0.3,
                'backoff_multiplier': 2.0,
                'max_backoff_seconds': 3600
            },
            'github': {
                'token': None,  # Must be provided via env var
                'api_base_url': 'https://api.github.com',
                'timeout_seconds': 30,
                'max_retries': 3,
                'allowed_scopes': ['read:user', 'user:follow']
            },
            'follow_unfollow': {
                'auto_follow_enabled': False,
                'auto_unfollow_enabled': False,
                'follow_back_detection_window_days': 7,
                'prioritization_strategy': 'relevance_score',
                'excluded_users': [],
                'inclusion_criteria': {
                    'min_followers': 1,
                    'max_followers': 10000,
                    'min_public_repos': 0,
                    'max_public_repos': 100,
                    'account_age_min_days': 30
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'automation_hub.log',
                'max_file_size_mb': 10,
                'backup_count': 5,
                'audit_log_retention_days': 30
            },
            'telemetry': {
                'enabled': True,
                'metrics_endpoint': None,
                'event_logging': True,
                'performance_tracking': True,
                'privacy_mode': True
            },
            'security': {
                'encrypt_logs': False,
                'redact_sensitive_data': True,
                'max_audit_retention_days': 90,
                'token_rotation_days': 90,
                'require_mfa': True
            },
            'notifications': {
                'enabled': False,
                'webhook_url': None,
                'email_notifications': False,
                'email_address': None,
                'alert_thresholds': {
                    '422_error_rate': 0.01,
                    '429_error_rate': 0.05,
                    'consecutive_failures': 3
                }
            }
        }
    
    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON or YAML file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith(('.yml', '.yaml')):
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {file_path}: {str(e)}")
            return {}
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries recursively."""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'GITHUB_TOKEN': ['github', 'token'],
            'AUTOMATION_ENABLED': ['automation', 'enabled'],
            'MAX_ACTIONS_PER_HOUR': ['rate_limits', 'max_actions_per_hour'],
            'LOG_LEVEL': ['logging', 'level'],
            'NOTIFICATION_WEBHOOK': ['notifications', 'webhook_url'],
            'METRICS_ENDPOINT': ['telemetry', 'metrics_endpoint']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(env_value)
                self._set_nested_value(config_path, converted_value)
                self.logger.debug(f"Applied environment override: {env_var} = {env_value}")
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string if no conversion possible
        return value
    
    def _set_nested_value(self, path: list, value: Any):
        """Set a nested configuration value."""
        config = self._config
        for key in path[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[path[-1]] = value
    
    def _validate_config(self):
        """Validate required configuration settings."""
        errors = []
        
        # Required GitHub token
        if not self._config['github']['token']:
            errors.append("GitHub token is required (set GITHUB_TOKEN environment variable)")
        
        # Validate rate limits are reasonable
        max_actions = self._config['rate_limits']['max_actions_per_hour']
        if max_actions <= 0 or max_actions > 100:
            errors.append("max_actions_per_hour must be between 1 and 100")
        
        # Validate delays
        if self._config['rate_limits']['base_delay_seconds'] < 30:
            errors.append("base_delay_seconds should be at least 30 seconds")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {err}" for err in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self._config.copy()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Configuration key in dot notation (e.g., 'github.token')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Configuration key in dot notation
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        self.logger.debug(f"Updated configuration: {key_path} = {value}")
    
    def save_config(self, file_path: str = None):
        """Save current configuration to file."""
        if not file_path:
            file_path = self.config_path or "config.json"
        
        try:
            with open(file_path, 'w') as f:
                if file_path.endswith(('.yml', '.yaml')):
                    yaml.dump(self._config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self._config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {file_path}: {str(e)}")
    
    def create_template_config(self, file_path: str = "config_template.yaml"):
        """Create a configuration template file."""
        template_config = self._get_default_config()
        
        # Add helpful comments
        template_config['_comments'] = {
            'github.token': 'Required: GitHub Personal Access Token with minimal scopes',
            'automation.enabled': 'Enable/disable automation (default: false for safety)',
            'rate_limits.max_actions_per_hour': 'Maximum automation actions per hour (recommended: 24)',
            'follow_unfollow.auto_follow_enabled': 'Enable automatic following (disabled by default)',
            'notifications.webhook_url': 'Optional: Webhook URL for notifications'
        }
        
        try:
            with open(file_path, 'w') as f:
                yaml.dump(template_config, f, default_flow_style=False, indent=2)
            self.logger.info(f"Configuration template created at {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to create template config: {str(e)}")
    
    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        for key_path, value in updates.items():
            self.set(key_path, value)
        
        # Re-validate after updates
        self._validate_config()
        self.logger.info("Configuration updated")
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety and compliance status."""
        return {
            'automation_enabled': self.get('automation.enabled'),
            'auto_follow_enabled': self.get('follow_unfollow.auto_follow_enabled'),
            'auto_unfollow_enabled': self.get('follow_unfollow.auto_unfollow_enabled'),
            'rate_limit_safety': {
                'max_actions_per_hour': self.get('rate_limits.max_actions_per_hour'),
                'base_delay_seconds': self.get('rate_limits.base_delay_seconds'),
                'exponential_backoff_enabled': self.get('automation.safety_features.exponential_backoff_on_429')
            },
            'compliance_features': {
                'emergency_stop_on_422': self.get('automation.safety_features.emergency_stop_on_422'),
                'audit_logging': self.get('automation.safety_features.audit_logging'),
                'rate_limit_monitoring': self.get('automation.safety_features.rate_limit_monitoring')
            }
        }
