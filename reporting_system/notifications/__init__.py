"""
Notification Manager

Handles sending notifications via email, Slack, Microsoft Teams, and other channels.
"""

import smtplib
import ssl
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from pathlib import Path

import aiohttp
import jinja2


class NotificationManager:
    """Manages sending notifications through various channels"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Email configuration
        self.email_config = config.get('email', {})
        
        # Slack configuration
        self.slack_config = config.get('slack', {})
        
        # Teams configuration
        self.teams_config = config.get('teams', {})
        
        # Discord configuration
        self.discord_config = config.get('discord', {})
        
        # Set up Jinja2 for email templates
        self.email_env = jinja2.Environment(
            loader=jinja2.DictLoader({
                'daily_summary': self._get_daily_template(),
                'weekly_summary': self._get_weekly_template(),
                'monthly_summary': self._get_monthly_template(),
                'alert': self._get_alert_template(),
                'executive_summary': self._get_executive_template()
            })
        )
    
    async def send_report_notification(self, recipients: List[str], report_type: str,
                                     file_path: str, period: str,
                                     additional_data: Optional[Dict[str, Any]] = None):
        """
        Send notification about a generated report
        
        Args:
            recipients: List of email addresses or user IDs
            report_type: Type of report generated
            file_path: Path to the generated report file
            period: Report period (daily, weekly, monthly)
            additional_data: Additional data for the notification
        """
        try:
            # Send email notification
            if recipients and self.email_config.get('enabled', True):
                await self._send_email_notification(
                    recipients, report_type, file_path, period, additional_data
                )
            
            # Send Slack notification if configured
            if self.slack_config.get('enabled'):
                await self._send_slack_notification(
                    report_type, file_path, period, additional_data
                )
            
            # Send Teams notification if configured
            if self.teams_config.get('enabled'):
                await self._send_teams_notification(
                    report_type, file_path, period, additional_data
                )
            
            # Send Discord notification if configured
            if self.discord_config.get('enabled'):
                await self._send_discord_notification(
                    report_type, file_path, period, additional_data
                )
            
            self.logger.info(f"Notifications sent for {report_type} report")
            
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {e}")
            raise
    
    async def _send_email_notification(self, recipients: List[str], report_type: str,
                                     file_path: str, period: str,
                                     additional_data: Optional[Dict[str, Any]]):
        """Send email notification"""
        try:
            # Prepare email content
            subject = f"{period.title()} {report_type.replace('_', ' ').title()} Report"
            
            # Get template
            template_name = f"{report_type}_{period}"
            template = self.email_env.get_template(template_name)
            
            # Prepare template context
            context = {
                'report_type': report_type,
                'period': period,
                'file_path': file_path,
                'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'company_name': 'Your Company',
                'additional_data': additional_data or {}
            }
            
            # Render email content
            html_content = template.render(**context)
            text_content = self._convert_html_to_text(html_content)
            
            # Send email
            await self._send_email(recipients, subject, text_content, html_content, [file_path])
            
        except Exception as e:
            self.logger.error(f"Email notification failed: {e}")
            raise
    
    async def _send_email(self, recipients: List[str], subject: str, text_content: str,
                         html_content: str, attachments: Optional[List[str]] = None):
        """Send email using SMTP"""
        try:
            # Email configuration
            smtp_server = self.email_config.get('smtp_server')
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config.get('username')
            password = self.email_config.get('password')
            use_tls = self.email_config.get('use_tls', True)
            
            if not all([smtp_server, smtp_port, username, password]):
                self.logger.warning("Email configuration incomplete")
                return
            
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = username
            msg['To'] = ', '.join(recipients)
            
            # Add text and HTML parts
            text_part = MimeText(text_content, 'plain')
            html_part = MimeText(html_content, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if Path(file_path).exists():
                        self._attach_file(msg, file_path)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls(context=context)
                server.login(username, password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent to {len(recipients)} recipients")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise
    
    def _attach_file(self, msg: MimeMultipart, file_path: str):
        """Attach file to email message"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = Path(file_path).name
                
                attachment = MimeBase('application', 'octet-stream')
                attachment.set_payload(file_data)
                encoders.encode_base64(attachment)
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {file_name}'
                )
                msg.attach(attachment)
                
        except Exception as e:
            self.logger.warning(f"Could not attach file {file_path}: {e}")
    
    async def _send_slack_notification(self, report_type: str, file_path: str,
                                     period: str, additional_data: Optional[Dict[str, Any]]):
        """Send Slack notification"""
        try:
            webhook_url = self.slack_config.get('webhook_url')
            channel = self.slack_config.get('channel', '#general')
            
            if not webhook_url:
                self.logger.warning("Slack webhook URL not configured")
                return
            
            # Prepare message
            message = {
                "channel": channel,
                "text": f"📊 {period.title()} {report_type.replace('_', ' ').title()} Report Generated",
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {
                                "title": "Report Type",
                                "value": report_type.replace('_', ' ').title(),
                                "short": True
                            },
                            {
                                "title": "Period",
                                "value": period.title(),
                                "short": True
                            },
                            {
                                "title": "Generated",
                                "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": True
                            }
                        ],
                        "actions": [
                            {
                                "type": "button",
                                "text": "View Report",
                                "url": f"file://{file_path}"
                            }
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status == 200:
                        self.logger.info("Slack notification sent successfully")
                    else:
                        self.logger.warning(f"Slack notification failed: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Slack notification failed: {e}")
    
    async def _send_teams_notification(self, report_type: str, file_path: str,
                                     period: str, additional_data: Optional[Dict[str, Any]]):
        """Send Microsoft Teams notification"""
        try:
            webhook_url = self.teams_config.get('webhook_url')
            
            if not webhook_url:
                self.logger.warning("Teams webhook URL not configured")
                return
            
            # Prepare message (Teams uses similar format to Slack)
            message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": f"{period.title()} {report_type.replace('_', ' ').title()} Report",
                "sections": [
                    {
                        "activityTitle": "📊 Report Generated",
                        "activitySubtitle": f"{period.title()} {report_type.replace('_', ' ').title()} Report",
                        "facts": [
                            {
                                "name": "Report Type",
                                "value": report_type.replace('_', ' ').title()
                            },
                            {
                                "name": "Period",
                                "value": period.title()
                            },
                            {
                                "name": "Generated",
                                "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
                            }
                        ]
                    }
                ],
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "View Report",
                        "targets": [
                            {
                                "os": "default",
                                "uri": f"file://{file_path}"
                            }
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status == 200:
                        self.logger.info("Teams notification sent successfully")
                    else:
                        self.logger.warning(f"Teams notification failed: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Teams notification failed: {e}")
    
    async def _send_discord_notification(self, report_type: str, file_path: str,
                                       period: str, additional_data: Optional[Dict[str, Any]]):
        """Send Discord notification"""
        try:
            webhook_url = self.discord_config.get('webhook_url')
            
            if not webhook_url:
                self.logger.warning("Discord webhook URL not configured")
                return
            
            # Prepare message
            message = {
                "embeds": [
                    {
                        "title": "📊 Report Generated",
                        "description": f"{period.title()} {report_type.replace('_', ' ').title()} Report",
                        "color": 3447003,  # Blue color
                        "fields": [
                            {
                                "name": "Report Type",
                                "value": report_type.replace('_', ' ').title(),
                                "inline": True
                            },
                            {
                                "name": "Period",
                                "value": period.title(),
                                "inline": True
                            },
                            {
                                "name": "Generated",
                                "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "inline": False
                            }
                        ],
                        "footer": {
                            "text": "Reporting System"
                        }
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status == 204:  # Discord returns 204 for success
                        self.logger.info("Discord notification sent successfully")
                    else:
                        self.logger.warning(f"Discord notification failed: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Discord notification failed: {e}")
    
    def _convert_html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        # Simple HTML to text conversion
        import re
        
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&nbsp;', ' ')
        
        return text.strip()
    
    def _get_daily_template(self) -> str:
        """Get daily summary email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Daily Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background: #f4f4f4; padding: 20px; text-align: center; }
                .content { margin: 20px 0; }
                .metric { background: #e8f4fd; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .footer { background: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Daily Summary Report</h1>
                <p>{{ generated_at }}</p>
            </div>
            
            <div class="content">
                <h2>Daily Overview</h2>
                <p>A summary of your daily activities and metrics.</p>
                
                <div class="metric">
                    <h3>Key Metrics</h3>
                    <p>Report Period: {{ period }}</p>
                    <p>Generated: {{ generated_at }}</p>
                </div>
                
                <h3>Attachments</h3>
                <p>Please find the detailed report attached to this email.</p>
            </div>
            
            <div class="footer">
                <p>Generated by {{ company_name }} Reporting System</p>
            </div>
        </body>
        </html>
        """
    
    def _get_weekly_template(self) -> str:
        """Get weekly summary email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Weekly Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
                .content { margin: 20px 0; }
                .summary-box { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 15px 0; }
                .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                .metric { background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .footer { background: #34495e; color: white; padding: 10px; text-align: center; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Weekly Summary Report</h1>
                <p>{{ generated_at }}</p>
            </div>
            
            <div class="content">
                <div class="summary-box">
                    <h2>Week Overview</h2>
                    <p>This report provides a comprehensive summary of activities for the week ending {{ period }}.</p>
                </div>
                
                <div class="metric-grid">
                    <div class="metric">
                        <h3>Report Period</h3>
                        <p>{{ period.title() }}</p>
                    </div>
                    <div class="metric">
                        <h3>Generated</h3>
                        <p>{{ generated_at }}</p>
                    </div>
                </div>
                
                <h3>Detailed Report</h3>
                <p>The complete analysis and metrics are available in the attached report.</p>
            </div>
            
            <div class="footer">
                <p>Generated by {{ company_name }} Reporting System</p>
            </div>
        </body>
        </html>
        """
    
    def _get_monthly_template(self) -> str:
        """Get monthly summary email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Monthly Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 30px; text-align: center; border-radius: 10px; }
                .content { margin: 30px 0; }
                .executive-summary { background: white; padding: 30px; border-radius: 10px; 
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 20px 0; }
                .highlights { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
                .highlight { background: #ffffff; padding: 20px; border-radius: 8px; 
                           border-left: 4px solid #667eea; }
                .footer { background: #2c3e50; color: white; padding: 20px; text-align: center; 
                         border-radius: 10px; margin-top: 30px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Monthly Executive Summary</h1>
                <p>{{ period.title() }} Report - {{ generated_at }}</p>
            </div>
            
            <div class="content">
                <div class="executive-summary">
                    <h2>Executive Summary</h2>
                    <p>This comprehensive monthly report provides key insights and metrics for executive review.</p>
                    
                    <div class="highlights">
                        <div class="highlight">
                            <h3>Report Period</h3>
                            <p>{{ period.title() }}</p>
                        </div>
                        <div class="highlight">
                            <h3>Generated</h3>
                            <p>{{ generated_at }}</p>
                        </div>
                    </div>
                </div>
                
                <h3>Complete Analysis</h3>
                <p>The full monthly analysis, including detailed metrics, trends, and recommendations, 
                is available in the attached comprehensive report.</p>
            </div>
            
            <div class="footer">
                <p>{{ company_name }} - Executive Reporting System</p>
                <p>Generated on {{ generated_at }}</p>
            </div>
        </body>
        </html>
        """
    
    def _get_alert_template(self) -> str:
        """Get alert email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Alert Notification</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #fff5f5; }
                .header { background: #e53e3e; color: white; padding: 20px; text-align: center; }
                .alert-box { background: #fed7d7; border: 1px solid #e53e3e; 
                           padding: 20px; border-radius: 5px; margin: 20px 0; }
                .footer { background: #2d3748; color: white; padding: 10px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Alert Notification</h1>
                <p>{{ generated_at }}</p>
            </div>
            
            <div class="alert-box">
                <h2>Alert Details</h2>
                <p><strong>Report Type:</strong> {{ report_type.replace('_', ' ').title() }}</p>
                <p><strong>Period:</strong> {{ period.title() }}</p>
                <p><strong>Generated:</strong> {{ generated_at }}</p>
            </div>
            
            <div class="footer">
                <p>{{ company_name }} Alert System</p>
            </div>
        </body>
        </html>
        """
    
    def _get_executive_template(self) -> str:
        """Get executive summary email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Executive Summary</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; 
                       background: #f8f9fa; }
                .header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                         color: white; padding: 40px; text-align: center; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .summary-card { background: white; padding: 30px; border-radius: 10px; 
                               box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 20px 0; }
                .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                          gap: 20px; margin: 30px 0; }
                .kpi-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
                .kpi-value { font-size: 2.5em; font-weight: bold; color: #1e3c72; }
                .kpi-label { color: #6c757d; margin-top: 10px; }
                .footer { background: #2d3748; color: white; padding: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Executive Summary Report</h1>
                <p>{{ period.title() }} Overview</p>
                <p>{{ generated_at }}</p>
            </div>
            
            <div class="container">
                <div class="summary-card">
                    <h2>Key Performance Indicators</h2>
                    <p>Summary of key metrics and performance indicators for executive review.</p>
                    
                    <div class="kpi-grid">
                        <div class="kpi-card">
                            <div class="kpi-value">{{ period.title() }}</div>
                            <div class="kpi-label">Reporting Period</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-value">{{ generated_at.split(' ')[0] }}</div>
                            <div class="kpi-label">Generated Date</div>
                        </div>
                    </div>
                </div>
                
                <div class="summary-card">
                    <h2>Executive Notes</h2>
                    <p>This executive summary provides high-level insights and recommendations 
                    based on comprehensive data analysis.</p>
                    <p>The detailed analysis is available in the attached comprehensive report.</p>
                </div>
            </div>
            
            <div class="footer">
                <p>{{ company_name }} - Executive Reporting</p>
                <p>Confidential - For Internal Use Only</p>
            </div>
        </body>
        </html>
        """
    
    def test_configuration(self) -> Dict[str, bool]:
        """Test notification configuration"""
        results = {}
        
        # Test email configuration
        try:
            required_email_keys = ['smtp_server', 'smtp_port', 'username', 'password']
            results['email'] = all(
                self.email_config.get(key) for key in required_email_keys
            )
        except:
            results['email'] = False
        
        # Test Slack configuration
        results['slack'] = bool(self.slack_config.get('webhook_url'))
        
        # Test Teams configuration
        results['teams'] = bool(self.teams_config.get('webhook_url'))
        
        # Test Discord configuration
        results['discord'] = bool(self.discord_config.get('webhook_url'))
        
        return results