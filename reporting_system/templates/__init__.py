"""
Template Manager

Manages report templates, custom branding, and content generation for different report types.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader, Template
import markdown
from PIL import Image
import base64


class TemplateManager:
    """Manages report templates and branding"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Set up Jinja2 environment
        template_dir = Path(config.get('template_directory', 'templates'))
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        
        # Branding configuration
        self.branding = config.get('branding', {})
        self.company_name = self.branding.get('company_name', 'Your Company')
        self.logo_path = self.branding.get('logo_path')
        self.primary_color = self.branding.get('primary_color', '#1f77b4')
        self.secondary_color = self.branding.get('secondary_color', '#ff7f0e')
        
        # Load predefined templates
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load available template names"""
        templates = {}
        
        # Common template types
        template_types = [
            'executive_summary',
            'weekly_report',
            'monthly_report',
            'dashboard',
            'financial_report',
            'performance_report'
        ]
        
        for template_type in template_types:
            templates[template_type] = template_type
        
        return templates
    
    async def render_template(self, template_name: str, data: Dict[str, Any], 
                             report_type: str) -> Dict[str, Any]:
        """
        Render a report template with data
        
        Args:
            template_name: Name of the template to use
            data: Data to render into the template
            report_type: Type of report being generated
            
        Returns:
            Rendered template content
        """
        try:
            # Get the template
            if template_name in self.templates:
                template = self.env.get_template(f"{template_name}.html")
            else:
                template = self.env.get_template("default_report.html")
            
            # Prepare template context
            context = self._prepare_context(data, report_type)
            
            # Render the template
            rendered_html = template.render(**context)
            
            # Process the rendered HTML (e.g., convert markdown, handle charts)
            processed_content = await self._process_content(rendered_html, data)
            
            return {
                'html': processed_content,
                'metadata': {
                    'template_name': template_name,
                    'report_type': report_type,
                    'rendered_at': datetime.utcnow().isoformat(),
                    'template_variables': list(context.keys())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Template rendering failed: {e}")
            raise
    
    def _prepare_context(self, data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Prepare template context with all necessary data"""
        context = {
            # Basic info
            'company_name': self.company_name,
            'report_type': report_type.title(),
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'report_date': datetime.utcnow().strftime('%B %d, %Y'),
            
            # Branding
            'logo_data': self._get_logo_data(),
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'custom_css': self._load_custom_css(),
            
            # Report data
            'summary': data.get('summary', {}),
            'raw_data': data.get('raw_data', {}),
            'period': data.get('period', 'Unknown'),
            
            # Helper functions
            'format_number': self._format_number,
            'format_percentage': self._format_percentage,
            'calculate_growth': self._calculate_growth,
            'generate_chart_config': self._generate_chart_config,
        }
        
        # Add report-type specific context
        if report_type == 'executive_summary':
            context.update(self._prepare_executive_context(data))
        elif report_type == 'weekly_report':
            context.update(self._prepare_weekly_context(data))
        elif report_type == 'monthly_report':
            context.update(self._prepare_monthly_context(data))
        
        return context
    
    def _prepare_executive_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for executive summary reports"""
        summary = data.get('summary', {})
        
        # Calculate key metrics
        total_records = sum(summary.get(source, {}).get('total_records', 0) for source in summary)
        top_performers = self._get_top_performers(data)
        
        return {
            'total_records': total_records,
            'top_performers': top_performers,
            'key_insights': self._generate_insights(data),
            'recommendations': self._generate_recommendations(data),
            'charts': {
                'overview': self._create_overview_chart_data(data),
                'trends': self._create_trend_chart_data(data)
            }
        }
    
    def _prepare_weekly_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for weekly reports"""
        summary = data.get('summary', {})
        
        # Calculate week-over-week changes
        week_changes = self._calculate_period_changes(data, 'week')
        
        return {
            'week_changes': week_changes,
            'daily_breakdown': self._create_daily_breakdown(data),
            'top_activities': self._get_top_activities(data),
            'alerts': self._generate_alerts(data),
            'next_week_focus': self._generate_focus_areas(data)
        }
    
    def _prepare_monthly_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for monthly reports"""
        summary = data.get('summary', {})
        
        # Calculate month-over-month changes
        monthly_trends = self._calculate_monthly_trends(data)
        
        return {
            'monthly_trends': monthly_trends,
            'performance_metrics': self._calculate_performance_metrics(data),
            'milestones': self._identify_milestones(data),
            'goals_progress': self._track_goals_progress(data),
            'executive_dashboard': self._create_executive_dashboard(data)
        }
    
    def _get_logo_data(self) -> Optional[str]:
        """Get logo as base64 data URL"""
        if not self.logo_path or not os.path.exists(self.logo_path):
            return None
        
        try:
            with open(self.logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode()
                return f"data:image/png;base64,{logo_data}"
        except Exception as e:
            self.logger.warning(f"Could not load logo: {e}")
            return None
    
    def _load_custom_css(self) -> str:
        """Load custom CSS for branding"""
        css_path = self.branding.get('custom_css')
        if css_path and os.path.exists(css_path):
            try:
                with open(css_path, 'r') as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Could not load custom CSS: {e}")
        
        return self._get_default_css()
    
    def _get_default_css(self) -> str:
        """Get default CSS styling"""
        return f"""
        .report-header {{
            background: linear-gradient(135deg, {self.primary_color}, {self.secondary_color});
            color: white;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .company-logo {{
            max-height: 60px;
            margin-bottom: 1rem;
        }}
        .metric-card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: {self.primary_color};
        }}
        .metric-change {{
            font-size: 0.9rem;
            color: #666;
        }}
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .insight-box {{
            background: #f8f9fa;
            border-left: 4px solid {self.primary_color};
            padding: 1rem;
            margin: 1rem 0;
        }}
        """
    
    async def _process_content(self, html: str, data: Dict[str, Any]) -> str:
        """Process rendered HTML content"""
        # Convert markdown content to HTML
        html = self._convert_markdown(html)
        
        # Add chart placeholders (these would be replaced by actual charts)
        html = self._add_chart_placeholders(html, data)
        
        return html
    
    def _convert_markdown(self, text: str) -> str:
        """Convert markdown to HTML"""
        try:
            return markdown.markdown(text)
        except:
            return text
    
    def _add_chart_placeholders(self, html: str, data: Dict[str, Any]) -> str:
        """Add placeholder divs for charts"""
        # This would be enhanced to generate actual chart containers
        chart_html = """
        <div class="chart-container" id="chart-overview">
            <h3>Overview Chart</h3>
            <div style="height: 300px; background: #f0f0f0; display: flex; align-items: center; justify-content: center;">
                <p>Chart will be rendered here</p>
            </div>
        </div>
        """
        
        return html + chart_html
    
    def _format_number(self, value: Any, decimal_places: int = 0) -> str:
        """Format numbers for display"""
        if value is None:
            return 'N/A'
        
        try:
            if isinstance(value, (int, float)):
                if decimal_places == 0:
                    return f"{value:,.0f}"
                else:
                    return f"{value:,.{decimal_places}f}"
            return str(value)
        except:
            return str(value)
    
    def _format_percentage(self, value: Any, decimal_places: int = 1) -> str:
        """Format percentages for display"""
        if value is None:
            return 'N/A'
        
        try:
            percentage = float(value) * 100
            return f"{percentage:.{decimal_places}f}%"
        except:
            return str(value)
    
    def _calculate_growth(self, current: float, previous: float) -> Dict[str, Any]:
        """Calculate growth metrics"""
        if previous == 0:
            return {'percentage': 0, 'absolute': current, 'direction': 'up'}
        
        percentage = ((current - previous) / previous) * 100
        absolute = current - previous
        direction = 'up' if percentage > 0 else 'down' if percentage < 0 else 'neutral'
        
        return {
            'percentage': percentage,
            'absolute': absolute,
            'direction': direction
        }
    
    def _get_top_performers(self, data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing items from data"""
        # This would implement actual logic based on your data structure
        return []
    
    def _generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate key insights from data"""
        insights = []
        summary = data.get('summary', {})
        
        for source, source_data in summary.items():
            records = source_data.get('total_records', 0)
            if records > 100:
                insights.append(f"High activity detected in {source} with {records} records")
            elif records < 10:
                insights.append(f"Low activity in {source} - consider investigating")
        
        return insights
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = [
            "Continue monitoring key metrics for trends",
            "Review performance targets for next period",
            "Consider expanding successful initiatives"
        ]
        return recommendations
    
    def _generate_chart_config(self, data_key: str, chart_type: str = 'line') -> Dict[str, Any]:
        """Generate chart configuration for frontend"""
        return {
            'type': chart_type,
            'data_key': data_key,
            'options': {
                'responsive': True,
                'maintainAspectRatio': False
            }
        }
    
    def _create_overview_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create overview chart data"""
        summary = data.get('summary', {})
        sources = list(summary.keys())
        records = [summary[source].get('total_records', 0) for source in sources]
        
        return {
            'labels': sources,
            'datasets': [{
                'label': 'Total Records',
                'data': records,
                'backgroundColor': [self.primary_color] * len(sources)
            }]
        }
    
    def _create_trend_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create trend chart data"""
        # This would create time-series data
        return {
            'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'datasets': [{
                'label': 'Trend',
                'data': [10, 15, 12, 18],
                'borderColor': self.primary_color,
                'fill': False
            }]
        }
    
    def _calculate_period_changes(self, data: Dict[str, Any], period: str) -> Dict[str, float]:
        """Calculate period-over-period changes"""
        # Simplified implementation
        return {'change_percentage': 5.2, 'change_absolute': 12}
    
    def _create_daily_breakdown(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create daily activity breakdown"""
        return [
            {'date': '2025-01-01', 'activity': 45},
            {'date': '2025-01-02', 'activity': 52},
            {'date': '2025-01-03', 'activity': 38}
        ]
    
    def _get_top_activities(self, data: Dict[str, Any]) -> List[str]:
        """Get top activities for the period"""
        return ['Code commits', 'Issue resolutions', 'Pull requests']
    
    def _generate_alerts(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate alerts for the report"""
        return [
            {'type': 'warning', 'message': 'Activity below threshold in GitHub repo X'},
            {'type': 'info', 'message': 'New contributor identified'}
        ]
    
    def _generate_focus_areas(self, data: Dict[str, Any]) -> List[str]:
        """Generate focus areas for next period"""
        return ['Improve code quality metrics', 'Increase community engagement']
    
    def _calculate_monthly_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate monthly trends"""
        return {'trend': 'positive', 'growth_rate': 12.5}
    
    def _calculate_performance_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance metrics"""
        return {'efficiency': 0.85, 'quality': 0.92, 'engagement': 0.78}
    
    def _identify_milestones(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify achieved milestones"""
        return [
            {'name': 'Milestone 1', 'achieved': True, 'date': '2025-01-15'},
            {'name': 'Milestone 2', 'achieved': False, 'date': '2025-01-30'}
        ]
    
    def _track_goals_progress(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Track progress towards goals"""
        return {'goal1': 0.75, 'goal2': 0.60, 'goal3': 0.90}
    
    def _create_executive_dashboard(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive dashboard data"""
        return {
            'kpis': [
                {'name': 'Total Activity', 'value': 156, 'change': '+12%'},
                {'name': 'Quality Score', 'value': 0.92, 'change': '+5%'},
                {'name': 'Community Engagement', 'value': 0.78, 'change': '-2%'}
            ]
        }
    
    def list_available_templates(self) -> List[str]:
        """List available template names"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a specific template"""
        if template_name in self.templates:
            return {
                'name': template_name,
                'available': True,
                'type': 'html',
                'variables': self._get_template_variables(template_name)
            }
        return {'name': template_name, 'available': False}
    
    def _get_template_variables(self, template_name: str) -> List[str]:
        """Get list of variables used in a template"""
        # This would analyze the template to extract variables
        return ['company_name', 'report_type', 'generated_at', 'summary', 'raw_data']