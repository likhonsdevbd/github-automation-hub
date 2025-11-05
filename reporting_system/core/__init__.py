"""
Core Reporting Engine

This module provides the main functionality for generating, scheduling, and managing reports.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import uuid

from .data_sources import DataSourceManager
from .exporters import ReportExporter
from .templates import TemplateManager
from .notifications import NotificationManager
from .schedulers import SchedulerManager


@dataclass
class ReportRequest:
    """Request object for report generation"""
    report_type: str
    period: str  # daily, weekly, monthly, custom
    data_sources: List[str]
    format: str = "pdf"  # pdf, html, excel
    template: Optional[str] = None
    custom_params: Optional[Dict[str, Any]] = None
    recipients: Optional[List[str]] = None
    schedule: Optional[Dict[str, Any]] = None


@dataclass
class ReportResult:
    """Result object from report generation"""
    report_id: str
    status: str  # pending, processing, completed, failed
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ReportGenerator:
    """Main report generation engine"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_manager = DataSourceManager(config.get('data_sources', {}))
        self.exporter = ReportExporter(config.get('reports', {}))
        self.template_manager = TemplateManager(config.get('templates', {}))
        self.notification_manager = NotificationManager(config.get('email', {}))
        self.scheduler = SchedulerManager(config.get('scheduling', {}))
        
        # In-memory store for report status (in production, use database)
        self._report_store: Dict[str, ReportResult] = {}
        
    async def generate_report(self, request: ReportRequest) -> ReportResult:
        """
        Generate a report based on the request
        
        Args:
            request: ReportRequest containing all generation parameters
            
        Returns:
            ReportResult with generation status and file path
        """
        report_id = str(uuid.uuid4())
        self.logger.info(f"Starting report generation for {request.report_type}, ID: {report_id}")
        
        # Create initial result
        result = ReportResult(
            report_id=report_id,
            status="pending",
            created_at=datetime.utcnow(),
            metadata={
                "request": request.__dict__,
                "config_summary": {
                    "data_sources": request.data_sources,
                    "format": request.format,
                    "period": request.period
                }
            }
        )
        
        self._report_store[report_id] = result
        
        try:
            # Start async generation
            asyncio.create_task(self._generate_report_async(report_id, request))
            
        except Exception as e:
            self.logger.error(f"Failed to start report generation: {e}")
            result.status = "failed"
            result.error_message = str(e)
            
        return result
    
    async def _generate_report_async(self, report_id: str, request: ReportRequest):
        """Async report generation implementation"""
        try:
            result = self._report_store[report_id]
            result.status = "processing"
            
            # Step 1: Collect data from sources
            self.logger.info(f"Collecting data from sources: {request.data_sources}")
            data = await self.data_manager.collect_data(
                sources=request.data_sources,
                period=request.period,
                custom_params=request.custom_params
            )
            
            # Step 2: Process and analyze data
            self.logger.info("Processing and analyzing data")
            processed_data = self._process_data(data, request)
            
            # Step 3: Generate report content using template
            self.logger.info(f"Generating report with template: {request.template}")
            report_content = await self._generate_content(processed_data, request)
            
            # Step 4: Export to requested format
            self.logger.info(f"Exporting report to format: {request.format}")
            file_path = await self.exporter.export(
                content=report_content,
                format=request.format,
                template=request.template,
                metadata=result.metadata
            )
            
            # Step 5: Update result and send notifications
            result.status = "completed"
            result.file_path = file_path
            result.completed_at = datetime.utcnow()
            
            # Send notifications if recipients specified
            if request.recipients:
                await self._send_notifications(request, file_path)
                
            self.logger.info(f"Report generation completed: {report_id}")
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            result = self._report_store[report_id]
            result.status = "failed"
            result.error_message = str(e)
    
    def _process_data(self, raw_data: Dict[str, Any], request: ReportRequest) -> Dict[str, Any]:
        """Process and transform raw data for reporting"""
        processed = {
            "raw_data": raw_data,
            "period": request.period,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {}
        }
        
        # Calculate summary statistics
        for source, data in raw_data.items():
            if isinstance(data, dict):
                processed["summary"][source] = {
                    "total_records": len(data.get("records", [])),
                    "date_range": data.get("date_range", {}),
                    "key_metrics": self._calculate_metrics(data)
                }
        
        return processed
    
    def _calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key metrics from data"""
        records = data.get("records", [])
        if not records:
            return {}
            
        # This is a simplified example - implement based on your data structure
        metrics = {
            "total_count": len(records),
        }
        
        # Add more sophisticated metric calculations here
        return metrics
    
    async def _generate_content(self, processed_data: Dict[str, Any], request: ReportRequest) -> Dict[str, Any]:
        """Generate report content using templates"""
        template_name = request.template or f"{request.report_type}_{request.period}"
        
        return await self.template_manager.render_template(
            template_name=template_name,
            data=processed_data,
            report_type=request.report_type
        )
    
    async def _send_notifications(self, request: ReportRequest, file_path: str):
        """Send notifications with report link"""
        await self.notification_manager.send_report_notification(
            recipients=request.recipients,
            report_type=request.report_type,
            file_path=file_path,
            period=request.period
        )
    
    def get_report_status(self, report_id: str) -> Optional[ReportResult]:
        """Get the status of a report"""
        return self._report_store.get(report_id)
    
    def list_reports(self, limit: int = 50) -> List[ReportResult]:
        """List recent reports"""
        reports = list(self._report_store.values())
        reports.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        return reports[:limit]
    
    async def generate_executive_summary(self, period: str = "weekly", 
                                       data_sources: List[str] = None,
                                       format: str = "pdf") -> ReportResult:
        """Convenience method for generating executive summaries"""
        if data_sources is None:
            data_sources = ["github", "analytics"]
            
        request = ReportRequest(
            report_type="executive_summary",
            period=period,
            data_sources=data_sources,
            format=format,
            template="executive_summary"
        )
        
        return await self.generate_report(request)
    
    async def generate_automated_reports(self):
        """Generate all scheduled reports"""
        # This would typically be called by a scheduler
        # Implement based on your scheduling requirements
        pass
    
    def cleanup_old_reports(self, days: int = 30):
        """Clean up old report files"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        for report_id, result in list(self._report_store.items()):
            if (result.completed_at and result.completed_at < cutoff_date):
                # Delete file if exists
                if result.file_path and Path(result.file_path).exists():
                    Path(result.file_path).unlink()
                    
                # Remove from store
                del self._report_store[report_id]