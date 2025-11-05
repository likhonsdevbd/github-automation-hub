#!/usr/bin/env python3
"""
Reporting System Main Entry Point

Command-line interface for the comprehensive reporting and visualization system.
"""

import asyncio
import click
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add the reporting_system module to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core import ReportGenerator, ReportRequest
from dashboards import DashboardManager
from schedulers import SchedulerManager, ScheduledReport
from utils import load_config, setup_logging, ensure_directory
from notifications import NotificationManager


@click.group()
@click.option('--config', '-c', default='config/config.yaml', 
              help='Path to configuration file')
@click.pass_context
def cli(ctx, config):
    """Comprehensive Reporting and Visualization System"""
    ctx.ensure_object(dict)
    
    # Load configuration
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Configuration file not found: {config_path}", err=True)
        click.echo("Please copy config_template.yaml and update it with your settings.", err=True)
        sys.exit(1)
    
    config_data = load_config(str(config_path))
    ctx.obj['config'] = config_data
    ctx.obj['config_path'] = config_path
    
    # Setup logging
    setup_logging(config_data.get('monitoring', {}))
    ctx.obj['logger'] = logging.getLogger(__name__)


@cli.command()
@click.option('--period', '-p', default='weekly', 
              type=click.Choice(['daily', 'weekly', 'monthly']), 
              help='Report period')
@click.option('--format', '-f', default='pdf', 
              type=click.Choice(['pdf', 'html', 'excel', 'csv']), 
              help='Output format')
@click.option('--sources', '-s', multiple=True, 
              default=['github', 'analytics'], help='Data sources to include')
@click.option('--recipients', '-r', multiple=True, 
              help='Email recipients for notification')
@click.option('--template', '-t', help='Custom template name')
@click.pass_context
def generate(ctx, period, format, sources, recipients, template):
    """Generate a report"""
    config = ctx.obj['config']
    logger = logging.getLogger(__name__)
    
    click.echo(f"Generating {period} report in {format} format...")
    
    async def _generate():
        try:
            # Initialize report generator
            generator = ReportGenerator(config)
            
            # Create report request
            request = ReportRequest(
                report_type="executive_summary",
                period=period,
                data_sources=list(sources),
                format=format,
                template=template,
                recipients=list(recipients) if recipients else None
            )
            
            # Generate report
            result = await generator.generate_report(request)
            
            click.echo(f"Report generation started with ID: {result.report_id}")
            
            # Wait for completion
            while result.status in ['pending', 'processing']:
                await asyncio.sleep(2)
                result = generator.get_report_status(result.report_id)
                click.echo(f"Status: {result.status}")
            
            if result.status == 'completed':
                click.echo(f"✅ Report generated successfully: {result.file_path}")
                
                # Show file size
                if result.file_path and Path(result.file_path).exists():
                    size = Path(result.file_path).stat().st_size
                    click.echo(f"File size: {size:,} bytes")
            else:
                click.echo(f"❌ Report generation failed: {result.error_message}", err=True)
                
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_generate())


@cli.command()
@click.option('--period', '-p', default='weekly', 
              type=click.Choice(['daily', 'weekly', 'monthly']), 
              help='Report period')
@click.option('--format', '-f', default='pdf', 
              type=click.Choice(['pdf', 'html', 'excel', 'csv']), 
              help='Output format')
@click.pass_context
def sample(ctx, period, format):
    """Generate a sample report with mock data"""
    config = ctx.obj['config']
    
    click.echo(f"Generating sample {period} report...")
    
    async def _sample():
        try:
            generator = ReportGenerator(config)
            
            request = ReportRequest(
                report_type="executive_summary",
                period=period,
                data_sources=["sample"],
                format=format
            )
            
            result = await generator.generate_report(request)
            
            # Wait for completion
            while result.status in ['pending', 'processing']:
                await asyncio.sleep(1)
                result = generator.get_report_status(result.report_id)
            
            if result.status == 'completed':
                click.echo(f"✅ Sample report generated: {result.file_path}")
            else:
                click.echo(f"❌ Sample generation failed: {result.error_message}", err=True)
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_sample())


@cli.command()
@click.option('--port', '-p', default=8080, help='Dashboard server port')
@click.option('--host', default='0.0.0.0', help='Dashboard server host')
@click.pass_context
def dashboard(ctx, port, host):
    """Start the interactive dashboard"""
    config = ctx.obj['config']
    
    click.echo(f"Starting dashboard on {host}:{port}...")
    click.echo("Press Ctrl+C to stop the server")
    
    try:
        dashboard_manager = DashboardManager(config)
        dashboard = dashboard_manager.get_dashboard('main')
        dashboard.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        click.echo("\nDashboard server stopped")
    except Exception as e:
        click.echo(f"Dashboard error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def schedule(ctx):
    """Manage scheduled reports"""
    pass


@cli.command()
@click.argument('name')
@click.option('--period', '-p', required=True,
              type=click.Choice(['daily', 'weekly', 'monthly']))
@click.option('--schedule', '-s', required=True, 
              help='Cron expression (e.g., "0 9 * * *" for 9 AM daily)')
@click.option('--format', '-f', default='pdf')
@click.option('--sources', '-s', multiple=True, required=True)
@click.option('--recipients', '-r', multiple=True)
@click.pass_context
def add_schedule(ctx, name, period, schedule, format, sources, recipients):
    """Add a new scheduled report"""
    config = ctx.obj['config']
    
    try:
        scheduler = SchedulerManager(config.get('scheduling', {}))
        
        # Generate report ID
        from utils import generate_unique_id
        report_id = generate_unique_id('sched_')
        
        scheduled_report = ScheduledReport(
            report_id=report_id,
            name=name,
            report_type="executive_summary",
            period=period,
            data_sources=list(sources),
            format=format,
            schedule=schedule,
            recipients=list(recipients) if recipients else None,
            enabled=True
        )
        
        success = scheduler.add_scheduled_report(scheduled_report)
        
        if success:
            click.echo(f"✅ Scheduled report '{name}' added successfully")
            click.echo(f"Report ID: {report_id}")
            click.echo(f"Schedule: {schedule}")
            click.echo(f"Period: {period}")
        else:
            click.echo("❌ Failed to add scheduled report", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def list_schedules(ctx):
    """List all scheduled reports"""
    config = ctx.obj['config']
    
    try:
        scheduler = SchedulerManager(config.get('scheduling', {}))
        reports = scheduler.list_scheduled_reports()
        
        if not reports:
            click.echo("No scheduled reports found")
            return
        
        click.echo("\nScheduled Reports:")
        click.echo("-" * 80)
        
        for report in reports:
            status = "✅ Enabled" if report.enabled else "❌ Disabled"
            last_run = report.last_run.strftime('%Y-%m-%d %H:%M:%S') if report.last_run else "Never"
            next_run = report.next_run.strftime('%Y-%m-%d %H:%M:%S') if report.next_run else "N/A"
            
            click.echo(f"Name: {report.name}")
            click.echo(f"ID: {report.report_id}")
            click.echo(f"Period: {report.period}")
            click.echo(f"Schedule: {report.schedule}")
            click.echo(f"Status: {status}")
            click.echo(f"Last Run: {last_run}")
            click.echo(f"Next Run: {next_run}")
            click.echo(f"Success Rate: {report.success_count}/{report.run_count}")
            click.echo("-" * 80)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('report_id')
@click.pass_context
def remove_schedule(ctx, report_id):
    """Remove a scheduled report"""
    config = ctx.obj['config']
    
    try:
        scheduler = SchedulerManager(config.get('scheduling', {}))
        success = scheduler.remove_scheduled_report(report_id)
        
        if success:
            click.echo(f"✅ Scheduled report '{report_id}' removed successfully")
        else:
            click.echo(f"❌ Scheduled report '{report_id}' not found", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def start_scheduler(ctx):
    """Start the scheduler service"""
    config = ctx.obj['config']
    
    click.echo("Starting scheduler service...")
    click.echo("Press Ctrl+C to stop")
    
    async def _start_scheduler():
        scheduler = SchedulerManager(config.get('scheduling', {}))
        await scheduler.start()
        
        # Load existing schedules if config file exists
        config_path = ctx.obj['config_path']
        schedule_config = config_path.parent / 'schedules.json'
        if schedule_config.exists():
            scheduler.load_scheduled_reports(str(schedule_config))
        
        # Create default schedules if none exist
        if not scheduler.list_scheduled_reports():
            click.echo("Creating default scheduled reports...")
            scheduler.create_default_scheduled_reports()
        
        try:
            # Keep the scheduler running
            while True:
                await asyncio.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            click.echo("\nStopping scheduler...")
            await scheduler.stop()
    
    try:
        asyncio.run(_start_scheduler())
    except KeyboardInterrupt:
        click.echo("\nScheduler service stopped")
    except Exception as e:
        click.echo(f"Scheduler error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status"""
    config = ctx.obj['config']
    
    click.echo("Reporting System Status")
    click.echo("=" * 50)
    
    # Configuration status
    config_path = ctx.obj['config_path']
    click.echo(f"Configuration: {config_path}")
    click.echo(f"Config loaded: {'✅' if config else '❌'}")
    
    # Data sources status
    try:
        from data_sources import DataSourceManager
        data_manager = DataSourceManager(config.get('data_sources', {}))
        source_status = data_manager.get_source_status()
        
        click.echo("\nData Sources:")
        for source_name, status_info in source_status.items():
            enabled = "✅" if status_info['enabled'] else "❌"
            click.echo(f"  {enabled} {source_name} ({status_info['type']})")
    except Exception as e:
        click.echo(f"Data sources: Error - {e}")
    
    # Scheduler status
    try:
        scheduler = SchedulerManager(config.get('scheduling', {}))
        scheduler_status = scheduler.get_scheduler_status()
        
        click.echo(f"\nScheduler:")
        click.echo(f"  Running: {'✅' if scheduler_status['running'] else '❌'}")
        click.echo(f"  Total Reports: {scheduler_status['total_scheduled_reports']}")
        click.echo(f"  Enabled: {scheduler_status['enabled_reports']}")
        click.echo(f"  Success Rate: {scheduler_status['statistics']['successful_runs']}/{scheduler_status['statistics']['total_runs']}")
    except Exception as e:
        click.echo(f"Scheduler: Error - {e}")
    
    # Notification status
    try:
        notification_manager = NotificationManager(config.get('email', {}))
        notification_status = notification_manager.test_configuration()
        
        click.echo("\nNotifications:")
        for channel, status in notification_status.items():
            status_icon = "✅" if status else "❌"
            click.echo(f"  {status_icon} {channel.title()}")
    except Exception as e:
        click.echo(f"Notifications: Error - {e}")


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the reporting system"""
    config_path = Path(ctx.obj['config_path'])
    
    click.echo("Initializing Reporting System...")
    
    # Create directory structure
    directories = [
        'config',
        'exports',
        'logs',
        'templates',
        'assets'
    ]
    
    for directory in directories:
        dir_path = config_path.parent / directory
        ensure_directory(dir_path)
        click.echo(f"✅ Created directory: {directory}")
    
    # Copy template configuration
    template_config = config_path.parent / 'config_template.yaml'
    if template_config.exists():
        click.echo("✅ Template configuration exists")
        click.echo(f"📝 Please copy {template_config} to {config_path} and update it")
    else:
        click.echo("❌ Template configuration not found")
    
    # Create example schedules
    schedules_dir = config_path.parent / 'schedules'
    ensure_directory(schedules_dir)
    
    example_schedule = {
        "scheduled_reports": [
            {
                "report_id": "daily_summary",
                "name": "Daily Summary",
                "report_type": "executive_summary",
                "period": "daily",
                "data_sources": ["github", "analytics"],
                "format": "pdf",
                "schedule": "0 9 * * *",
                "enabled": True
            }
        ]
    }
    
    schedule_file = schedules_dir / 'example.json'
    with open(schedule_file, 'w') as f:
        json.dump(example_schedule, f, indent=2)
    
    click.echo(f"✅ Created example schedule: {schedule_file}")
    
    click.echo("\n🎉 Initialization complete!")
    click.echo("\nNext steps:")
    click.echo("1. Update config/config.yaml with your settings")
    click.echo("2. Test with: python -m reporting_system.main --sample")
    click.echo("3. Start dashboard: python -m reporting_system.main --dashboard")


if __name__ == '__main__':
    cli()