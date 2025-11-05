#!/usr/bin/env python3
"""
Example usage of the Reporting System

This script demonstrates how to use the comprehensive reporting system
programmatically.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the reporting_system module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reporting_system.core import ReportGenerator, ReportRequest
from reporting_system.dashboards import DashboardManager
from reporting_system.schedulers import SchedulerManager, ScheduledReport
from reporting_system.utils import load_config, setup_logging


async def example_basic_report_generation():
    """Example: Generate a basic report"""
    print("=== Basic Report Generation Example ===")
    
    # Load configuration
    config = load_config('config/config.yaml')
    
    # Initialize report generator
    generator = ReportGenerator(config)
    
    # Create report request
    request = ReportRequest(
        report_type="executive_summary",
        period="weekly",
        data_sources=["github", "analytics"],
        format="pdf",
        recipients=["stakeholder@company.com"]
    )
    
    # Generate report
    result = await generator.generate_report(request)
    print(f"Report generation started: {result.report_id}")
    
    # Wait for completion
    while result.status in ['pending', 'processing']:
        await asyncio.sleep(2)
        result = generator.get_report_status(result.report_id)
        print(f"Status: {result.status}")
    
    if result.status == 'completed':
        print(f"✅ Report generated: {result.file_path}")
    else:
        print(f"❌ Generation failed: {result.error_message}")


async def example_custom_report():
    """Example: Generate a custom report with parameters"""
    print("\n=== Custom Report Example ===")
    
    config = load_config('config/config.yaml')
    generator = ReportGenerator(config)
    
    # Custom parameters for specific data
    custom_params = {
        'github': {
            'organization': 'my-org',
            'repositories': ['repo1', 'repo2']
        },
        'date_range': {
            'start': '2025-01-01',
            'end': '2025-01-31'
        }
    }
    
    request = ReportRequest(
        report_type="weekly_report",
        period="weekly",
        data_sources=["github"],
        format="html",
        custom_params=custom_params,
        template="weekly_report"
    )
    
    result = await generator.generate_report(request)
    print(f"Custom report ID: {result.report_id}")
    
    # Monitor progress
    while result.status in ['pending', 'processing']:
        await asyncio.sleep(1)
        result = generator.get_report_status(result.report_id)
    
    if result.status == 'completed':
        print(f"✅ Custom report: {result.file_path}")


async def example_scheduled_reports():
    """Example: Set up scheduled reports"""
    print("\n=== Scheduled Reports Example ===")
    
    config = load_config('config/config.yaml')
    
    # Initialize scheduler
    scheduler = SchedulerManager(config.get('scheduling', {}))
    
    # Create scheduled reports
    daily_report = ScheduledReport(
        report_id="daily_summary",
        name="Daily Activity Summary",
        report_type="executive_summary",
        period="daily",
        data_sources=["github", "analytics"],
        format="pdf",
        schedule="0 8 * * *",  # 8 AM daily
        recipients=["manager@company.com"],
        enabled=True
    )
    
    weekly_report = ScheduledReport(
        report_id="weekly_overview",
        name="Weekly Performance Overview",
        report_type="executive_summary",
        period="weekly",
        data_sources=["github", "analytics", "custom_api"],
        format="html",
        schedule="0 9 * * 1",  # 9 AM on Monday
        recipients=["team@company.com", "executives@company.com"],
        enabled=True
    )
    
    # Add to scheduler
    success1 = scheduler.add_scheduled_report(daily_report)
    success2 = scheduler.add_scheduled_report(weekly_report)
    
    if success1 and success2:
        print("✅ Scheduled reports added successfully")
        
        # List all scheduled reports
        reports = scheduler.list_scheduled_reports()
        print(f"Total scheduled reports: {len(reports)}")
        
        for report in reports:
            print(f"- {report.name} ({report.period})")
    else:
        print("❌ Failed to add scheduled reports")


async def example_dashboard():
    """Example: Start interactive dashboard"""
    print("\n=== Dashboard Example ===")
    
    config = load_config('config/config.yaml')
    
    # Create dashboard manager
    dashboard_manager = DashboardManager(config)
    
    # Create custom dashboard
    custom_config = {
        'dashboard': {
            'server': {
                'port': 8081,
                'host': 'localhost'
            }
        }
    }
    
    dashboard = dashboard_manager.create_dashboard('custom', 'Custom Analytics Dashboard', custom_config)
    
    print("✅ Custom dashboard created")
    print("Dashboard available at: http://localhost:8081")
    print("Note: Run dashboard with --dashboard flag to start the server")


async def example_data_sources():
    """Example: Working with data sources"""
    print("\n=== Data Sources Example ===")
    
    config = load_config('config/config.yaml')
    
    from reporting_system.data_sources import DataSourceManager
    
    # Initialize data manager
    data_manager = DataSourceManager(config.get('data_sources', {}))
    
    # Collect data from sources
    data = await data_manager.collect_data(
        sources=["github", "analytics"],
        period="weekly"
    )
    
    print("Data collected from sources:")
    for source, source_data in data.items():
        print(f"- {source}: {len(source_data.get('records', []))} records")
    
    # Get source status
    status = data_manager.get_source_status()
    print("\nSource status:")
    for source_name, status_info in status.items():
        enabled = "✅" if status_info['enabled'] else "❌"
        print(f"- {enabled} {source_name}")


async def example_notifications():
    """Example: Email notifications"""
    print("\n=== Notifications Example ===")
    
    config = load_config('config/config.yaml')
    
    from reporting_system.notifications import NotificationManager
    
    # Initialize notification manager
    notifier = NotificationManager(config.get('email', {}))
    
    # Test configuration
    status = notifier.test_configuration()
    print("Notification configuration status:")
    for channel, is_configured in status.items():
        icon = "✅" if is_configured else "❌"
        print(f"- {icon} {channel.title()}")
    
    if status.get('email'):
        print("Email is configured and ready to send notifications")
    else:
        print("Email is not configured - please update config.yaml")


def example_batch_processing():
    """Example: Batch processing multiple reports"""
    print("\n=== Batch Processing Example ===")
    
    async def _batch():
        config = load_config('config/config.yaml')
        generator = ReportGenerator(config)
        
        # Create multiple report requests
        requests = [
            ReportRequest(
                report_type="executive_summary",
                period="daily",
                data_sources=["github"],
                format="pdf"
            ),
            ReportRequest(
                report_type="executive_summary",
                period="weekly",
                data_sources=["analytics"],
                format="html"
            ),
            ReportRequest(
                report_type="executive_summary",
                period="monthly",
                data_sources=["github", "analytics"],
                format="excel"
            )
        ]
        
        # Generate all reports concurrently
        tasks = [generator.generate_report(req) for req in requests]
        results = await asyncio.gather(*tasks)
        
        print(f"Generated {len(results)} reports concurrently:")
        for i, result in enumerate(results):
            status_icon = "✅" if result.status == 'completed' else "❌"
            print(f"{i+1}. {status_icon} Report {i+1} - {result.status}")
    
    asyncio.run(_batch())


def main():
    """Run all examples"""
    print("🚀 Reporting System Examples")
    print("=" * 50)
    
    # Setup logging
    setup_logging({'log_level': 'INFO'})
    
    # Run examples
    try:
        # Uncomment the examples you want to run
        # asyncio.run(example_basic_report_generation())
        # asyncio.run(example_custom_report())
        # asyncio.run(example_scheduled_reports())
        # asyncio.run(example_dashboard())
        # asyncio.run(example_data_sources())
        # asyncio.run(example_notifications())
        # example_batch_processing()
        
        print("\n💡 Uncomment examples in main() to run them")
        print("\nTo get started:")
        print("1. Update config/config.yaml with your settings")
        print("2. Run: python examples/demo_usage.py")
        print("3. Or use CLI: python -m reporting_system.main --generate --sample")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        logging.exception("Example error")


if __name__ == '__main__':
    main()