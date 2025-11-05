"""
API Package

Contains the API gateway and route handlers for the analytics orchestrator system.
"""

from .gateway import APIGateway
from .routes.analytics import router as analytics_router
from .routes.monitoring import router as monitoring_router
from .routes.automation import router as automation_router
from .routes.webhooks import router as webhooks_router

__all__ = [
    "APIGateway",
    "analytics_router",
    "monitoring_router", 
    "automation_router",
    "webhooks_router",
]