"""
API Gateway for analytics orchestrator - RESTful API for external integrations
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import sys

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import yaml

from .routes.analytics import analytics_router
from .routes.monitoring import monitoring_router
from .routes.automation import automation_router
from .routes.webhooks import webhooks_router
from .middleware.auth import AuthenticationMiddleware
from .middleware.rate_limiting import RateLimitMiddleware
from .middleware.logging import LoggingMiddleware


class AnalyticsAPIGateway:
    """
    Main API Gateway for the analytics orchestrator system
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize API Gateway"""
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Analytics Orchestrator API",
            description="RESTful API for analytics orchestrator system",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
        
        # Setup exception handlers
        self._setup_exception_handlers()
        
        self.logger.info("API Gateway initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                return config.get('api_gateway', {})
            else:
                # Return default configuration
                return {
                    'host': '0.0.0.0',
                    'port': 8000,
                    'cors_origins': ['*'],
                    'rate_limit': 1000,
                    'api_key': None,
                    'jwt_secret': None
                }
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            return {
                'host': '0.0.0.0',
                'port': 8000,
                'cors_origins': ['*'],
                'rate_limit': 1000
            }
    
    def _setup_middleware(self):
        """Setup API middleware"""
        # CORS middleware
        cors_origins = self.config.get('cors_origins', ['*'])
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins if cors_origins != ['*'] else ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # GZip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Rate limiting
        self.app.add_middleware(
            RateLimitMiddleware,
            rate_limit=self.config.get('rate_limit', 1000)
        )
        
        # Authentication (if configured)
        if self.config.get('api_key') or self.config.get('jwt_secret'):
            self.app.add_middleware(AuthenticationMiddleware)
        
        # Logging
        self.app.add_middleware(LoggingMiddleware)
    
    def _setup_routes(self):
        """Setup API routes"""
        # Health check endpoint
        @self.app.get("/health", tags=["Health"])
        async def health_check():
            """Health check endpoint"""
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0',
                'service': 'analytics-orchestrator-api'
            }
        
        @self.app.get("/", tags=["Root"])
        async def root():
            """Root endpoint with API information"""
            return {
                'service': 'Analytics Orchestrator API',
                'version': '1.0.0',
                'documentation': '/docs',
                'health': '/health',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        @self.app.get("/metrics", tags=["Monitoring"])
        async def get_metrics():
            """Get system metrics"""
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': {
                    'api_requests_total': 0,  # TODO: Implement actual metrics
                    'api_requests_active': 0,
                    'system_uptime': 0,
                    'memory_usage': 0,
                    'cpu_usage': 0
                }
            }
        
        # Include route modules
        self.app.include_router(
            analytics_router,
            prefix="/api/v1",
            tags=["Analytics"]
        )
        
        self.app.include_router(
            monitoring_router,
            prefix="/api/v1",
            tags=["Monitoring"]
        )
        
        self.app.include_router(
            automation_router,
            prefix="/api/v1",
            tags=["Automation"]
        )
        
        self.app.include_router(
            webhooks_router,
            prefix="/api/v1",
            tags=["Webhooks"]
        )
    
    def _setup_exception_handlers(self):
        """Setup global exception handlers"""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    'error': {
                        'code': exc.status_code,
                        'message': exc.detail,
                        'type': 'http_exception'
                    },
                    'timestamp': datetime.utcnow().isoformat(),
                    'path': str(request.url.path)
                }
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            self.logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    'error': {
                        'code': 500,
                        'message': 'Internal server error',
                        'type': 'internal_error'
                    },
                    'timestamp': datetime.utcnow().isoformat(),
                    'path': str(request.url.path)
                }
            )
    
    def run(self, host: str = None, port: int = None, debug: bool = False):
        """Run the API Gateway server"""
        try:
            # Use config values if not provided
            host = host or self.config.get('host', '0.0.0.0')
            port = port or self.config.get('port', 8000)
            
            self.logger.info(f"Starting Analytics Orchestrator API Gateway on {host}:{port}")
            
            # Run with uvicorn
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="info" if not debug else "debug",
                access_log=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start API Gateway: {str(e)}")
            raise
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance"""
        return self.app


# Global gateway instance
gateway: Optional[AnalyticsAPIGateway] = None


def get_gateway() -> AnalyticsAPIGateway:
    """Get the global gateway instance"""
    global gateway
    if gateway is None:
        gateway = AnalyticsAPIGateway()
    return gateway


def create_app(config_path: str = "config/config.yaml") -> FastAPI:
    """Create and configure FastAPI application"""
    gateway = AnalyticsAPIGateway(config_path)
    return gateway.get_app()


# CLI entry point
def main():
    """Main entry point for the API Gateway"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analytics Orchestrator API Gateway')
    parser.add_argument('--config', default='config/config.yaml', help='Configuration file path')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "debug" if args.debug else "info"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create and run gateway
        gateway = AnalyticsAPIGateway(args.config)
        gateway.run(host=args.host, port=args.port, debug=args.debug)
        
    except KeyboardInterrupt:
        print("\nShutting down API Gateway...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()