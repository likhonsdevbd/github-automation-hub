"""
Follow/Unfollow Automation System
A comprehensive automation system for GitHub with safety controls
"""

__version__ = "1.0.0"
__author__ = "Automation Hub"
__description__ = "Follow/Unfollow automation system with safety controls"

# Import main classes for convenience
from .main_orchestrator import FollowAutomationOrchestrator
from .config.settings import FollowAutomationConfig, ActionType
from .config.templates import ConfigTemplate, ConfigValidator

__all__ = [
    "FollowAutomationOrchestrator",
    "FollowAutomationConfig", 
    "ActionType",
    "ConfigTemplate",
    "ConfigValidator"
]