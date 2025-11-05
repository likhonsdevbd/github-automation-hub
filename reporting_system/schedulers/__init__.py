"""
Scheduler Manager

Handles automated report generation scheduling and management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


@dataclass
class ScheduledReport:
    """Configuration for a scheduled report"""
    report_id: str
    name: str
    report_type: str
    period: str
    data_sources: List[str]
    format: str
    schedule: str  # cron expression or interval
    recipients: Optional[List[str]] = None
    template: Optional[str] = None
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    error_count: int = 0


class SchedulerManager:
    """Manages scheduled report generation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=config.get('timezone', 'UTC')
        )
        
        # Store scheduled reports
        self.scheduled_reports: Dict[str, ScheduledReport] = {}
        
        # Event listeners
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        # Report generation callback
        self.report_generator: Optional[Callable] = None
        
    def set_report_generator(self, generator_func: Callable):
        """Set the report generation function to be used by scheduler"""
        self.report_generator = generator_func
    
    async def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler stopped")
    
    def add_scheduled_report(self, report: ScheduledReport) -> bool:
        """
        Add a new scheduled report
        
        Args:
            report: ScheduledReport configuration
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Create APScheduler job
            job_id = f"report_{report.report_id}"
            
            # Determine trigger type
            trigger = self._create_trigger(report.schedule)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_scheduled_report,
                trigger=trigger,
                args=[report.report_id],
                id=job_id,
                replace_existing=True,
                name=report.name
            )
            
            # Store report configuration
            self.scheduled_reports[report.report_id] = report
            report.next_run = self._get_next_run_time(job_id)
            
            self.logger.info(f"Added scheduled report: {report.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add scheduled report: {e}")
            return False
    
    def remove_scheduled_report(self, report_id: str) -> bool:
        """
        Remove a scheduled report
        
        Args:
            report_id: ID of the report to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        try:
            job_id = f"report_{report_id}"
            
            # Remove from scheduler
            self.scheduler.remove_job(job_id)
            
            # Remove from store
            if report_id in self.scheduled_reports:
                del self.scheduled_reports[report_id]
            
            self.logger.info(f"Removed scheduled report: {report_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove scheduled report: {e}")
            return False
    
    def update_scheduled_report(self, report_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing scheduled report
        
        Args:
            report_id: ID of the report to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successfully updated, False otherwise
        """
        try:
            if report_id not in self.scheduled_reports:
                self.logger.warning(f"Scheduled report not found: {report_id}")
                return False
            
            # Update the report configuration
            report = self.scheduled_reports[report_id]
            for key, value in updates.items():
                if hasattr(report, key):
                    setattr(report, key, value)
            
            # Recreate the scheduler job
            self.remove_scheduled_report(report_id)
            self.add_scheduled_report(report)
            
            self.logger.info(f"Updated scheduled report: {report_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update scheduled report: {e}")
            return False
    
    def get_scheduled_report(self, report_id: str) -> Optional[ScheduledReport]:
        """Get a scheduled report by ID"""
        return self.scheduled_reports.get(report_id)
    
    def list_scheduled_reports(self) -> List[ScheduledReport]:
        """List all scheduled reports"""
        return list(self.scheduled_reports.values())
    
    def get_scheduled_reports_by_status(self, enabled: bool) -> List[ScheduledReport]:
        """Get scheduled reports by enabled status"""
        return [report for report in self.scheduled_reports.values() 
                if report.enabled == enabled]
    
    async def _execute_scheduled_report(self, report_id: str):
        """Execute a scheduled report"""
        try:
            report = self.scheduled_reports.get(report_id)
            if not report or not report.enabled:
                return
            
            self.logger.info(f"Executing scheduled report: {report.name}")
            
            # Create report request
            from ..core import ReportRequest
            request = ReportRequest(
                report_type=report.report_type,
                period=report.period,
                data_sources=report.data_sources,
                format=report.format,
                template=report.template,
                recipients=report.recipients
            )
            
            # Generate report using the provided generator function
            if self.report_generator:
                result = await self.report_generator(request)
                
                # Update report statistics
                report.last_run = datetime.utcnow()
                report.run_count += 1
                report.success_count += 1
                report.next_run = self._get_next_run_time(f"report_{report_id}")
                
                self.logger.info(f"Successfully executed scheduled report: {report.name}")
            else:
                self.logger.error("Report generator function not set")
                
        except Exception as e:
            self.logger.error(f"Failed to execute scheduled report {report_id}: {e}")
            
            # Update error statistics
            if report_id in self.scheduled_reports:
                report = self.scheduled_reports[report_id]
                report.error_count += 1
                report.last_run = datetime.utcnow()
    
    def _create_trigger(self, schedule: str):
        """Create APScheduler trigger from schedule string"""
        # If it's a cron expression
        if schedule.count(' ') >= 5:  # Cron has 5 or 6 parts
            try:
                return CronTrigger.from_crontab(schedule)
            except:
                pass
        
        # If it's an interval specification
        if schedule.startswith('interval:'):
            interval_str = schedule.replace('interval:', '')
            
            if interval_str.endswith('days'):
                days = int(interval_str.replace('days', ''))
                return IntervalTrigger(days=days)
            elif interval_str.endswith('hours'):
                hours = int(interval_str.replace('hours', ''))
                return IntervalTrigger(hours=hours)
            elif interval_str.endswith('minutes'):
                minutes = int(interval_str.replace('minutes', ''))
                return IntervalTrigger(minutes=minutes)
        
        # Default to daily
        return CronTrigger(hour=9, minute=0)  # 9 AM daily
    
    def _get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Get next run time for a job"""
        try:
            job = self.scheduler.get_job(job_id)
            return job.next_run_time
        except:
            return None
    
    def _job_listener(self, event):
        """Listen for job events"""
        if event.exception:
            self.logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            self.logger.debug(f"Job {event.job_id} executed successfully")
    
    def load_scheduled_reports(self, config_path: str):
        """Load scheduled reports from configuration file"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                reports_config = config_data.get('scheduled_reports', [])
                
                for report_config in reports_config:
                    report = ScheduledReport(**report_config)
                    self.add_scheduled_report(report)
                
                self.logger.info(f"Loaded {len(reports_config)} scheduled reports")
            else:
                self.logger.info("No scheduled reports configuration file found")
                
        except Exception as e:
            self.logger.error(f"Failed to load scheduled reports: {e}")
    
    def save_scheduled_reports(self, config_path: str):
        """Save current scheduled reports to configuration file"""
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'scheduled_reports': []
            }
            
            for report in self.scheduled_reports.values():
                report_dict = {
                    'report_id': report.report_id,
                    'name': report.name,
                    'report_type': report.report_type,
                    'period': report.period,
                    'data_sources': report.data_sources,
                    'format': report.format,
                    'schedule': report.schedule,
                    'recipients': report.recipients,
                    'template': report.template,
                    'enabled': report.enabled,
                    'last_run': report.last_run.isoformat() if report.last_run else None,
                    'run_count': report.run_count,
                    'success_count': report.success_count,
                    'error_count': report.error_count
                }
                config_data['scheduled_reports'].append(report_dict)
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.scheduled_reports)} scheduled reports")
            
        except Exception as e:
            self.logger.error(f"Failed to save scheduled reports: {e}")
    
    def create_default_scheduled_reports(self):
        """Create default scheduled reports"""
        default_reports = [
            ScheduledReport(
                report_id="daily_summary",
                name="Daily Summary Report",
                report_type="executive_summary",
                period="daily",
                data_sources=["github", "analytics"],
                format="pdf",
                schedule="0 9 * * *",  # 9 AM daily
                recipients=["stakeholder@company.com"],
                template="executive_summary",
                enabled=True
            ),
            ScheduledReport(
                report_id="weekly_overview",
                name="Weekly Overview",
                report_type="executive_summary",
                period="weekly",
                data_sources=["github", "analytics", "custom_api"],
                format="html",
                schedule="0 10 * * 1",  # 10 AM every Monday
                recipients=["executives@company.com"],
                template="weekly_report",
                enabled=True
            ),
            ScheduledReport(
                report_id="monthly_executive",
                name="Monthly Executive Summary",
                report_type="executive_summary",
                period="monthly",
                data_sources=["github", "analytics", "custom_api"],
                format="pdf",
                schedule="0 8 1 * *",  # 8 AM on 1st of every month
                recipients=["ceo@company.com", "cto@company.com"],
                template="executive_summary",
                enabled=True
            )
        ]
        
        for report in default_reports:
            self.add_scheduled_report(report)
        
        self.logger.info(f"Created {len(default_reports)} default scheduled reports")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics"""
        jobs = self.scheduler.get_jobs()
        
        return {
            'running': self.scheduler.running,
            'total_jobs': len(jobs),
            'total_scheduled_reports': len(self.scheduled_reports),
            'enabled_reports': len([r for r in self.scheduled_reports.values() if r.enabled]),
            'disabled_reports': len([r for r in self.scheduled_reports.values() if not r.enabled]),
            'next_runs': [
                {
                    'report_id': report.report_id,
                    'name': report.name,
                    'next_run': report.next_run.isoformat() if report.next_run else None
                }
                for report in self.scheduled_reports.values()
            ],
            'statistics': {
                'total_runs': sum(r.run_count for r in self.scheduled_reports.values()),
                'successful_runs': sum(r.success_count for r in self.scheduled_reports.values()),
                'failed_runs': sum(r.error_count for r in self.scheduled_reports.values())
            }
        }
    
    async def run_report_now(self, report_id: str) -> bool:
        """Manually trigger a scheduled report to run immediately"""
        try:
            if report_id not in self.scheduled_reports:
                return False
            
            report = self.scheduled_reports[report_id]
            
            # Execute the report immediately
            await self._execute_scheduled_report(report_id)
            
            self.logger.info(f"Manually triggered report: {report.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to manually trigger report {report_id}: {e}")
            return False
    
    def pause_report(self, report_id: str) -> bool:
        """Pause a scheduled report"""
        try:
            job_id = f"report_{report_id}"
            self.scheduler.pause_job(job_id)
            
            if report_id in self.scheduled_reports:
                self.scheduled_reports[report_id].enabled = False
            
            self.logger.info(f"Paused scheduled report: {report_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause report {report_id}: {e}")
            return False
    
    def resume_report(self, report_id: str) -> bool:
        """Resume a paused scheduled report"""
        try:
            job_id = f"report_{report_id}"
            self.scheduler.resume_job(job_id)
            
            if report_id in self.scheduled_reports:
                self.scheduled_reports[report_id].enabled = True
            
            self.logger.info(f"Resumed scheduled report: {report_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume report {report_id}: {e}")
            return False