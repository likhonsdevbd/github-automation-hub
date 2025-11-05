"""
Automation Hub - GitHub Repository Growth Automation System

A compliance-first, rate-limited automation system for GitHub operations.

Features:
- Conservative rate limiting (≤24 actions/hour)
- Comprehensive audit logging
- Safety-first design with emergency stops
- Human-in-the-loop controls
- Full compliance monitoring

WARNING: All automation features are disabled by default.
Read safety guidelines before enabling any automation.
"""

__version__ = "1.0.0"
__author__ = "Automation Hub Team"
__email__ = "contact@automation-hub.dev"
__license__ = "MIT"

# Main exports
from .scripts.automation_manager import AutomationManager
from .scripts.config_manager import ConfigManager
from .scripts.github_client import GitHubClient
from .scripts.rate_limiter import RateLimiter
from .scripts.telemetry import TelemetryLogger

__all__ = [
    "AutomationManager",
    "ConfigManager", 
    "GitHubClient",
    "RateLimiter",
    "TelemetryLogger",
]

# Package metadata
__all__.extend([
    "__version__",
    "__author__",
    "__email__",
    "__license__"
])
