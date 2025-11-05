#!/usr/bin/env python3
"""
Analytics Orchestrator Entrypoint

Docker entrypoint script that handles initialization and startup.
"""

import os
import sys
import asyncio
import signal
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_environment():
    """Setup environment variables and configuration"""
    
    # Set default environment variables if not set
    os.environ.setdefault('ENVIRONMENT', 'production')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///data/analytics.db')
    os.environ.setdefault('CACHE_URL', 'redis://redis:6379/0')
    os.environ.setdefault('TIMEZONE', 'UTC')
    
    # Create necessary directories
    directories = ['data', 'logs', 'config', 'backups']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Ensure config file exists
    config_file = Path('config/config.yaml')
    if not config_file.exists():
        example_config = Path('config/config.yaml.example')
        if example_config.exists():
            import shutil
            shutil.copy(example_config, config_file)
            print("Created config/config.yaml from example")
        else:
            print("WARNING: No configuration file found")
    
    # Ensure environment file exists
    env_file = Path('.env')
    if not env_file.exists():
        example_env = Path('.env.example')
        if example_env.exists():
            import shutil
            shutil.copy(example_env, env_file)
            print("Created .env from example")
            print("WARNING: Please edit .env with your actual configuration")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import core.orchestrator
        import core.config_manager
        import api.gateway
        print("✅ Core dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        sys.exit(1)
    
    # Check external services
    if os.environ.get('CHECK_DEPENDENCIES', 'true').lower() == 'true':
        print("Checking external services...")
        
        # Check Redis
        try:
            import redis
            r = redis.from_url(os.environ.get('CACHE_URL', 'redis://localhost:6379/0'))
            r.ping()
            print("✅ Redis connection successful")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
        
        # Check database connectivity
        try:
            import sqlite3
            db_url = os.environ.get('DATABASE_URL', 'sqlite:///data/analytics.db')
            if db_url.startswith('sqlite://'):
                db_path = db_url.replace('sqlite:///', '')
                if not os.path.exists(os.path.dirname(db_path)):
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                conn = sqlite3.connect(db_path)
                conn.close()
                print("✅ Database connection successful")
        except Exception as e:
            print(f"⚠️ Database connection failed: {e}")

async def run_health_check():
    """Run a basic health check"""
    try:
        from core.config_manager import ConfigManager
        config_manager = ConfigManager('config/config.yaml')
        config = config_manager.load_config()
        print("✅ Configuration loaded successfully")
        
        from core.orchestrator import AnalyticsOrchestrator
        orchestrator = AnalyticsOrchestrator(config)
        await orchestrator.initialize()
        
        # Quick health check
        health_status = await orchestrator.check_system_health()
        all_healthy = all(
            component.get('status') == 'healthy' 
            for component in health_status.values()
        )
        
        if all_healthy:
            print("✅ System health check passed")
        else:
            print("⚠️ Some components are not healthy:")
            for component, status in health_status.items():
                if status.get('status') != 'healthy':
                    print(f"  - {component}: {status.get('status', 'unknown')}")
        
        await orchestrator.shutdown()
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    return True

def start_orchestrator():
    """Start the orchestrator service"""
    async def main():
        try:
            # Setup environment
            setup_environment()
            
            # Check dependencies
            check_dependencies()
            
            # Initialize orchestrator
            from core.config_manager import ConfigManager
            from core.orchestrator import AnalyticsOrchestrator
            
            config_manager = ConfigManager('config/config.yaml')
            config = config_manager.load_config()
            
            orchestrator = AnalyticsOrchestrator(config)
            
            # Handle shutdown signals
            def signal_handler(signum, frame):
                print(f"\n🛑 Received signal {signum}, shutting down...")
                asyncio.create_task(orchestrator.shutdown())
                
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Initialize and start
            print("🚀 Initializing Analytics Orchestrator...")
            await orchestrator.initialize()
            
            print("🌟 Starting Analytics Orchestrator...")
            await orchestrator.start()
            
            print("✅ Analytics Orchestrator is running")
            
            # Keep running
            while orchestrator.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Received keyboard interrupt")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'orchestrator' in locals():
                await orchestrator.shutdown()
            print("👋 Analytics Orchestrator stopped")
            
    asyncio.run(main())

def run_cli():
    """Run CLI interface"""
    from cli import cli
    cli()

def main():
    """Main entrypoint function"""
    parser = argparse.ArgumentParser(description='Analytics Orchestrator Entrypoint')
    parser.add_argument('command', nargs='?', choices=['start', 'health', 'cli'], 
                       default='start', help='Command to execute')
    parser.add_argument('--health-check-only', action='store_true',
                       help='Run only health check and exit')
    parser.add_argument('--check-deps', action='store_true',
                       help='Check dependencies and exit')
    
    args = parser.parse_args()
    
    # Handle special flags
    if args.health_check_only:
        return asyncio.run(run_health_check())
    
    if args.check_deps:
        setup_environment()
        check_dependencies()
        return
    
    # Execute command
    if args.command == 'start':
        start_orchestrator()
    elif args.command == 'health':
        asyncio.run(run_health_check())
    elif args.command == 'cli':
        run_cli()

if __name__ == '__main__':
    main()