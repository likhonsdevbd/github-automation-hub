"""
Analytics Orchestrator Package

A comprehensive analytics orchestration system that coordinates multiple analytics
components, manages data pipelines, and provides API endpoints for external integrations.
"""

__version__ = "1.0.0"
__author__ = "Automation Hub Team"

from .core.orchestrator import AnalyticsOrchestrator
from .core.config_manager import ConfigManager
from .core.data_pipeline import DataPipeline
from .core.integration_manager import IntegrationManager

__all__ = [
    "AnalyticsOrchestrator",
    "ConfigManager", 
    "DataPipeline",
    "IntegrationManager",
]