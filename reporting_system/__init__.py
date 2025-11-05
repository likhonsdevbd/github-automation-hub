"""
Comprehensive Reporting and Visualization System

A powerful, automated reporting system for generating executive summaries,
interactive dashboards, and scheduled reports with multiple export formats.

Features:
- Automated report generation (daily, weekly, monthly)
- Executive summary reports for stakeholders
- Interactive dashboards and charts
- PDF and HTML export capabilities
- Email notification system
- Custom report templates and branding
- Multi-data source integration
- Scheduled report automation

Modules:
- core: Main reporting engine and orchestration
- data_sources: Data collection from various sources
- exporters: Multi-format report export (PDF, HTML, Excel, CSV)
- templates: Customizable report templates
- notifications: Email and notification system
- dashboards: Interactive web dashboards
- schedulers: Automated report scheduling
- utils: Utility functions and helpers

Usage:
    from reporting_system import ReportGenerator
    
    generator = ReportGenerator(config)
    result = await generator.generate_report(request)
    
    # Start dashboard
    from reporting_system import DashboardManager
    dashboard_manager = DashboardManager(config)
    dashboard_manager.run_all_dashboards()
    
    # Schedule reports
    from reporting_system import SchedulerManager
    scheduler = SchedulerManager(config)
    scheduler.start()

Author: Reporting System Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Reporting System Team"
__email__ = "team@reporting.system"
__license__ = "MIT"

# Core exports
from .core import ReportGenerator, ReportRequest, ReportResult
from .data_sources import DataSourceManager
from .exporters import ReportExporter
from .templates import TemplateManager
from .notifications import NotificationManager
from .dashboards import DashboardManager, DashboardServer
from .schedulers import SchedulerManager, ScheduledReport
from . import utils

# Convenience imports
__all__ = [
    # Core components
    'ReportGenerator',
    'ReportRequest', 
    'ReportResult',
    'DataSourceManager',
    'ReportExporter',
    'TemplateManager',
    'NotificationManager',
    'DashboardManager',
    'DashboardServer',
    'SchedulerManager',
    'ScheduledReport',
    
    # Utils
    'utils',
    
    # Version info
    '__version__',
    '__author__',
    '__email__',
    '__license__',
]

# Package metadata
__title__ = "Comprehensive Reporting System"
__description__ = "Automated reporting and visualization system with dashboards and multi-format exports"
__url__ = "https://github.com/yourusername/reporting-system"
__download_url__ = f"{__url__}/archive/v{__version__}.tar.gz"

# Create a simple version info
version_info = {
    'major': 1,
    'minor': 0,
    'patch': 0,
    'release': 'stable',
    'full': __version__,
    'description': __description__
}


def get_version_info():
    """Get detailed version information"""
    return version_info.copy()


def create_report_generator(config_path=None, config_dict=None):
    """
    Convenience function to create a report generator
    
    Args:
        config_path: Path to configuration file
        config_dict: Configuration dictionary
        
    Returns:
        ReportGenerator instance
    """
    from .utils import load_config
    
    if config_dict:
        config = config_dict
    elif config_path:
        config = load_config(config_path)
    else:
        # Try default locations
        default_paths = [
            'config/config.yaml',
            'config/config.yml',
            '../config/config.yaml'
        ]
        
        config = {}
        for path in default_paths:
            if Path(path).exists():
                config = load_config(path)
                break
    
    if not config:
        raise ValueError("No configuration found. Please provide config_path or config_dict")
    
    return ReportGenerator(config)


def create_dashboard_manager(config_path=None, config_dict=None):
    """
    Convenience function to create a dashboard manager
    
    Args:
        config_path: Path to configuration file
        config_dict: Configuration dictionary
        
    Returns:
        DashboardManager instance
    """
    from .utils import load_config
    
    if config_dict:
        config = config_dict
    elif config_path:
        config = load_config(config_path)
    else:
        config = {}
    
    return DashboardManager(config)


def run_quick_demo(config_path=None):
    """
    Run a quick demo of the reporting system
    
    Args:
        config_path: Path to configuration file
    """
    import asyncio
    
    async def demo():
        print("🚀 Quick Demo of Reporting System")
        print("=" * 40)
        
        try:
            # Create generator
            generator = create_report_generator(config_path)
            
            # Create sample request
            from .core import ReportRequest
            request = ReportRequest(
                report_type="executive_summary",
                period="weekly",
                data_sources=["sample"],
                format="html"
            )
            
            print("Generating sample report...")
            result = await generator.generate_report(request)
            
            # Wait for completion
            while result.status in ['pending', 'processing']:
                await asyncio.sleep(1)
                result = generator.get_report_status(result.report_id)
            
            if result.status == 'completed':
                print(f"✅ Sample report generated: {result.file_path}")
            else:
                print(f"❌ Report generation failed: {result.error_message}")
            
        except Exception as e:
            print(f"Demo error: {e}")
    
    asyncio.run(demo())


# Package initialization
def _initialize_package():
    """Initialize package-level settings"""
    # Set up logging if not already configured
    import logging
    
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


# Initialize package
_initialize_package()

# Add package metadata to __doc__
__doc__ = f"""
{__title__} v{__version__}

{__description__}

Key Features:
• Automated report generation (daily, weekly, monthly)
• Executive summary reports for stakeholders  
• Interactive dashboards and charts
• PDF and HTML export capabilities
• Email notification system
• Custom report templates and branding
• Multi-data source integration
• Scheduled report automation

Quick Start:
    from reporting_system import ReportGenerator, ReportRequest
    
    # Create generator
    generator = ReportGenerator(config)
    
    # Generate report
    request = ReportRequest(
        report_type="executive_summary",
        period="weekly", 
        data_sources=["github", "analytics"],
        format="pdf"
    )
    result = await generator.generate_report(request)

Documentation: {__url__}
License: {__license__}
"""

print(f"""
📊 {__title__} v{__version__} loaded successfully!

Quick commands:
- Generate sample report: python -m reporting_system.main --sample
- Start dashboard: python -m reporting_system.main --dashboard  
- Run tests: python -m reporting_system.tests.integration_test
- View help: python -m reporting_system.main --help

Documentation: {__url__}
""")