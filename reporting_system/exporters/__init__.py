"""
Report Exporters

Handles exporting reports to various formats including PDF, HTML, Excel, and CSV.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template, Environment, FileSystemLoader
import pandas as pd


class ReportExporter:
    """Handles export of reports to various formats"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Set up Jinja2 environment for HTML templates
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        
        # Default export configuration
        self.export_config = config.get('export', {})
        
    async def export(self, content: Dict[str, Any], format: str, 
                    template: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Export report content to specified format
        
        Args:
            content: Report content data
            format: Export format (pdf, html, excel, csv)
            template: Template name to use
            metadata: Additional metadata for the report
            
        Returns:
            Path to exported file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.export_config.get('storage', {}).get('base_path', 'exports'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"report_{timestamp}.{format}"
        file_path = output_dir / filename
        
        try:
            if format.lower() == "pdf":
                await self._export_pdf(content, file_path, template, metadata)
            elif format.lower() == "html":
                await self._export_html(content, file_path, template, metadata)
            elif format.lower() == "excel":
                await self._export_excel(content, file_path, metadata)
            elif format.lower() == "csv":
                await self._export_csv(content, file_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Successfully exported report to {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise
    
    async def _export_pdf(self, content: Dict[str, Any], file_path: Path, 
                         template: Optional[str], metadata: Optional[Dict[str, Any]]):
        """Export to PDF format"""
        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
        
        # Build document content
        story = []
        
        # Title page
        story.append(Paragraph("Report", title_style))
        story.append(Spacer(1, 20))
        
        if metadata:
            report_info = metadata.get('config_summary', {})
            story.append(Paragraph(f"Period: {report_info.get('period', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
            story.append(Spacer(1, 30))
        
        # Summary section
        if 'summary' in content:
            story.append(Paragraph("Executive Summary", heading_style))
            for source, summary in content['summary'].items():
                story.append(Paragraph(f"<b>{source.title()}</b>", styles['Heading3']))
                if 'total_records' in summary:
                    story.append(Paragraph(f"Total Records: {summary['total_records']}", styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Data tables
        if 'raw_data' in content:
            for source, data in content['raw_data'].items():
                if 'records' in data and data['records']:
                    story.append(Paragraph(f"{source.title()} Data", heading_style))
                    
                    # Create table from records
                    table_data = self._create_table_data(data['records'])
                    if table_data:
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
    
    def _create_table_data(self, records: list) -> Optional[list]:
        """Create table data from records list"""
        if not records:
            return None
        
        # Get all unique keys from records
        all_keys = set()
        for record in records:
            if isinstance(record, dict):
                all_keys.update(record.keys())
        
        # Remove 'raw' key if present (used for complex data)
        all_keys.discard('raw')
        keys = sorted(list(all_keys))
        
        # Create header row
        table_data = [keys]
        
        # Add data rows (limit to first 50 records for readability)
        for record in records[:50]:
            if isinstance(record, dict):
                row = [str(record.get(key, '')) for key in keys]
                table_data.append(row)
        
        return table_data
    
    async def _export_html(self, content: Dict[str, Any], file_path: Path, 
                          template: Optional[str], metadata: Optional[Dict[str, Any]]):
        """Export to HTML format"""
        # Prepare template context
        context = {
            'content': content,
            'metadata': metadata or {},
            'generated_at': datetime.utcnow().isoformat(),
            'company_name': 'Your Company',  # Could be loaded from config
        }
        
        # Use custom template if provided
        template_name = f"{template}.html" if template else "default_report.html"
        
        try:
            # Try to load custom template
            jinja_template = self.jinja_env.get_template(template_name)
            html_content = jinja_template.render(context)
        except:
            # Fall back to basic HTML template
            html_content = self._generate_basic_html(context)
        
        # Write HTML file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_basic_html(self, context: Dict[str, Any]) -> str:
        """Generate basic HTML template"""
        content = context['content']
        metadata = context['metadata']
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Report - {metadata.get('config_summary', {}).get('period', 'Report')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .section {{ margin-bottom: 30px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Report</h1>
                <p>Generated: {context['generated_at']}</p>
            </div>
        """
        
        # Add summary section
        if 'summary' in content:
            html += '<div class="section"><h2>Executive Summary</h2><div class="summary">'
            for source, summary in content['summary'].items():
                html += f'<h3>{source.title()}</h3>'
                if 'total_records' in summary:
                    html += f'<p>Total Records: {summary["total_records"]}</p>'
            html += '</div></div>'
        
        # Add raw data tables
        if 'raw_data' in content:
            for source, data in content['raw_data'].items():
                if 'records' in data and data['records']:
                    html += f'<div class="section"><h2>{source.title()} Data</h2>'
                    html += self._records_to_html_table(data['records'][:50])  # Limit to 50 records
                    html += '</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _records_to_html_table(self, records: list) -> str:
        """Convert records to HTML table"""
        if not records:
            return '<p>No data available</p>'
        
        # Get all unique keys
        all_keys = set()
        for record in records:
            if isinstance(record, dict):
                all_keys.update(record.keys())
        
        all_keys.discard('raw')
        keys = sorted(list(all_keys))
        
        # Generate table
        html = '<table><thead><tr>'
        for key in keys:
            html += f'<th>{key.title()}</th>'
        html += '</tr></thead><tbody>'
        
        for record in records:
            if isinstance(record, dict):
                html += '<tr>'
                for key in keys:
                    value = record.get(key, '')
                    html += f'<td>{value}</td>'
                html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    async def _export_excel(self, content: Dict[str, Any], file_path: Path, 
                           metadata: Optional[Dict[str, Any]]):
        """Export to Excel format"""
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            # Summary sheet
            if 'summary' in content:
                summary_data = []
                for source, summary in content['summary'].items():
                    summary_data.append({
                        'Source': source,
                        'Total Records': summary.get('total_records', 0),
                        'Date Range Start': summary.get('date_range', {}).get('start', ''),
                        'Date Range End': summary.get('date_range', {}).get('end', '')
                    })
                
                if summary_data:
                    df_summary = pd.DataFrame(summary_data)
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Data sheets
            if 'raw_data' in content:
                for source, data in content['raw_data'].items():
                    if 'records' in data and data['records']:
                        # Convert records to DataFrame
                        records = data['records']
                        if records and isinstance(records[0], dict):
                            df = pd.DataFrame(records)
                            # Remove complex 'raw' column if present
                            if 'raw' in df.columns:
                                df = df.drop('raw', axis=1)
                            df.to_excel(writer, sheet_name=source[:30], index=False)  # Excel sheet name limit
    
    async def _export_csv(self, content: Dict[str, Any], file_path: Path):
        """Export to CSV format (flatten all data into single CSV)"""
        all_records = []
        
        if 'raw_data' in content:
            for source, data in content['raw_data'].items():
                if 'records' in data and data['records']:
                    for record in data['records']:
                        if isinstance(record, dict):
                            record['source'] = source
                            all_records.append(record)
        
        if all_records:
            df = pd.DataFrame(all_records)
            # Remove complex 'raw' column if present
            if 'raw' in df.columns:
                df = df.drop('raw', axis=1)
            df.to_csv(file_path, index=False)
        else:
            # Create empty CSV with headers
            df = pd.DataFrame({'message': ['No data available']})
            df.to_csv(file_path, index=False)
    
    def generate_chart(self, data: list, chart_type: str = 'line', 
                      title: str = 'Chart', output_path: Optional[str] = None) -> str:
        """
        Generate a chart from data
        
        Args:
            data: List of data points
            chart_type: Type of chart (line, bar, pie, scatter)
            title: Chart title
            output_path: Optional output file path
            
        Returns:
            Path to generated chart image
        """
        plt.style.use('seaborn-v0_8')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == 'line':
            ax.plot(data)
        elif chart_type == 'bar':
            ax.bar(range(len(data)), data)
        elif chart_type == 'pie':
            ax.pie(data)
        elif chart_type == 'scatter':
            x_data = range(len(data))
            ax.scatter(x_data, data)
        
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        if not output_path:
            output_path = f"chart_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path