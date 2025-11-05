"""
Interactive Dashboard System

Provides real-time dashboards and interactive visualizations using Dash.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from .data_sources import DataSourceManager


class DashboardServer:
    """Interactive dashboard server using Dash"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        # Dashboard configuration
        self.dashboard_config = config.get('dashboard', {})
        self.server_config = self.dashboard_config.get('server', {})
        
        # Data manager for real-time updates
        self.data_manager = DataSourceManager(config.get('data_sources', {}))
        
        # Store for dashboard data
        self.dashboard_data: Dict[str, Any] = {}
        
        # Set up the layout
        self._setup_layout()
        self._setup_callbacks()
        
        # Default refresh interval
        self.refresh_interval = self.dashboard_config.get('default_refresh_interval', 300)  # seconds
    
    def _setup_layout(self):
        """Set up the dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Reporting Dashboard", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Controls
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Dashboard Controls", className="card-title"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Dropdown(
                                        id='period-dropdown',
                                        options=[
                                            {'label': 'Last 24 Hours', 'value': 'daily'},
                                            {'label': 'Last Week', 'value': 'weekly'},
                                            {'label': 'Last Month', 'value': 'monthly'},
                                            {'label': 'Last Quarter', 'value': 'quarterly'}
                                        ],
                                        value='weekly'
                                    )
                                ], width=6),
                                dbc.Col([
                                    dcc.Dropdown(
                                        id='source-dropdown',
                                        options=[
                                            {'label': 'All Sources', 'value': 'all'},
                                            {'label': 'GitHub', 'value': 'github'},
                                            {'label': 'Analytics', 'value': 'analytics'},
                                            {'label': 'Custom API', 'value': 'api'}
                                        ],
                                        value='all'
                                    )
                                ], width=6)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("Refresh Data", id="refresh-btn", color="primary", className="me-2"),
                                    dbc.Button("Export Report", id="export-btn", color="success")
                                ])
                            ], className="mt-3")
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=self.refresh_interval * 1000,  # in milliseconds
                n_intervals=0
            ),
            
            # KPI Cards Row
            dbc.Row(id='kpi-cards', className="mb-4"),
            
            # Charts Row
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='main-chart')
                ], width=8),
                dbc.Col([
                    dcc.Graph(id='status-chart')
                ], width=4)
            ], className="mb-4"),
            
            # Data Table Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Recent Activity"),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id='data-table',
                                columns=[
                                    {"name": "Source", "id": "source"},
                                    {"name": "Type", "id": "type"},
                                    {"name": "Count", "id": "count"},
                                    {"name": "Date", "id": "date"}
                                ],
                                sort_action="native",
                                filter_action="native",
                                page_action="native",
                                page_current=0,
                                page_size=10,
                                style_cell={'textAlign': 'left'},
                                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                                style_data_conditional=[
                                    {
                                        'if': {'filter_query': '{count} > 100'},
                                        'backgroundColor': '#d4edda',
                                        'color': 'black',
                                    },
                                    {
                                        'if': {'filter_query': '{count} < 10'},
                                        'backgroundColor': '#f8d7da',
                                        'color': 'black',
                                    }
                                ]
                            )
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Alerts and Status
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("System Status"),
                        dbc.CardBody(id='system-status')
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Recent Alerts"),
                        dbc.CardBody(id='alerts-panel')
                    ])
                ], width=6)
            ])
            
        ], fluid=True)
    
    def _setup_callbacks(self):
        """Set up Dash callbacks for interactivity"""
        
        @self.app.callback(
            Output('kpi-cards', 'children'),
            [Input('interval-component', 'n_intervals'),
             Input('refresh-btn', 'n_clicks')],
            [State('period-dropdown', 'value'),
             State('source-dropdown', 'value')]
        )
        def update_kpi_cards(n, n_clicks, period, source):
            """Update KPI cards"""
            try:
                data = self._get_dashboard_data(period, source)
                kpi_data = data.get('kpis', [])
                
                cards = []
                for kpi in kpi_data:
                    color = "success" if kpi.get('change', 0) > 0 else "danger" if kpi.get('change', 0) < 0 else "secondary"
                    
                    card = dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{kpi.get('value', 0):,}", className="card-title"),
                                html.P(kpi.get('name', 'KPI'), className="card-text"),
                                html.Small(
                                    f"{kpi.get('change', 0):+.1f}%",
                                    className=f"text-{color}"
                                )
                            ])
                        ], color=color, outline=True)
                    ], width=3)
                    cards.append(card)
                
                return cards
                
            except Exception as e:
                self.logger.error(f"Failed to update KPI cards: {e}")
                return []
        
        @self.app.callback(
            Output('main-chart', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('refresh-btn', 'n_clicks')],
            [State('period-dropdown', 'value'),
             State('source-dropdown', 'value')]
        )
        def update_main_chart(n, n_clicks, period, source):
            """Update main chart"""
            try:
                data = self._get_dashboard_data(period, source)
                chart_data = data.get('main_chart', {})
                
                if not chart_data:
                    # Return empty chart
                    fig = go.Figure()
                    fig.update_layout(title="No Data Available")
                    return fig
                
                # Create main chart
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Activity Over Time', 'Source Distribution'),
                    vertical_spacing=0.1
                )
                
                # Add time series data
                if 'timeseries' in chart_data:
                    timeseries = chart_data['timeseries']
                    fig.add_trace(
                        go.Scatter(
                            x=timeseries.get('dates', []),
                            y=timeseries.get('values', []),
                            mode='lines+markers',
                            name='Activity'
                        ),
                        row=1, col=1
                    )
                
                # Add distribution data
                if 'distribution' in chart_data:
                    distribution = chart_data['distribution']
                    fig.add_trace(
                        go.Pie(
                            labels=distribution.get('labels', []),
                            values=distribution.get('values', []),
                            name="Distribution"
                        ),
                        row=2, col=1
                    )
                
                fig.update_layout(height=600, showlegend=True, title_text="Dashboard Overview")
                return fig
                
            except Exception as e:
                self.logger.error(f"Failed to update main chart: {e}")
                return go.Figure()
        
        @self.app.callback(
            Output('status-chart', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('refresh-btn', 'n_clicks')]
        )
        def update_status_chart(n, n_clicks):
            """Update status chart"""
            try:
                data = self._get_dashboard_data('current', 'all')
                status_data = data.get('status', {})
                
                # Create status gauge chart
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=status_data.get('overall_score', 0),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "System Health"},
                    delta={'reference': 80},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                
                fig.update_layout(height=300)
                return fig
                
            except Exception as e:
                self.logger.error(f"Failed to update status chart: {e}")
                return go.Figure()
        
        @self.app.callback(
            Output('data-table', 'data'),
            [Input('interval-component', 'n_intervals'),
             Input('refresh-btn', 'n_clicks')],
            [State('period-dropdown', 'value'),
             State('source-dropdown', 'value')]
        )
        def update_data_table(n, n_clicks, period, source):
            """Update data table"""
            try:
                data = self._get_dashboard_data(period, source)
                table_data = data.get('table_data', [])
                return table_data
                
            except Exception as e:
                self.logger.error(f"Failed to update data table: {e}")
                return []
        
        @self.app.callback(
            Output('system-status', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_system_status(n):
            """Update system status"""
            try:
                status = self._get_system_status()
                
                items = []
                for service, service_status in status.items():
                    color = "success" if service_status.get('status') == 'healthy' else "danger"
                    status_text = "🟢" if color == "success" else "🔴"
                    
                    items.append(
                        dbc.ListGroupItem([
                            html.Span(f"{status_text} {service.title()}", className="me-2"),
                            html.Small(service_status.get('details', ''), className="text-muted")
                        ])
                    )
                
                return dbc.ListGroup(items, flush=True)
                
            except Exception as e:
                self.logger.error(f"Failed to update system status: {e}")
                return html.P("Error loading system status")
        
        @self.app.callback(
            Output('alerts-panel', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_alerts_panel(n):
            """Update alerts panel"""
            try:
                alerts = self._get_recent_alerts()
                
                if not alerts:
                    return html.P("No recent alerts", className="text-muted")
                
                alert_items = []
                for alert in alerts:
                    color = "warning" if alert.get('severity') == 'medium' else "danger" if alert.get('severity') == 'high' else "info"
                    
                    alert_items.append(
                        dbc.Alert([
                            html.H6(alert.get('title', 'Alert'), className="alert-heading"),
                            html.P(alert.get('message', '')),
                            html.Small(alert.get('timestamp', ''), className="text-muted")
                        ], color=color, dismissable=True)
                    )
                
                return alert_items
                
            except Exception as e:
                self.logger.error(f"Failed to update alerts panel: {e}")
                return html.P("Error loading alerts")
    
    def _get_dashboard_data(self, period: str, source: str) -> Dict[str, Any]:
        """Get data for dashboard display"""
        try:
            # In a real implementation, this would fetch from the data manager
            # For now, return mock data
            
            if (period, source) in self.dashboard_data:
                return self.dashboard_data[(period, source)]
            
            # Generate mock data
            mock_data = {
                'kpis': [
                    {'name': 'Total Activity', 'value': 1250, 'change': 12.5},
                    {'name': 'Success Rate', 'value': 98.2, 'change': -0.3},
                    {'name': 'Response Time', 'value': 245, 'change': -5.2},
                    {'name': 'Users', 'value': 156, 'change': 8.1}
                ],
                'main_chart': {
                    'timeseries': {
                        'dates': pd.date_range(start='2025-01-01', end='2025-01-31', freq='D'),
                        'values': [100 + i + (i % 7) * 10 for i in range(31)]
                    },
                    'distribution': {
                        'labels': ['GitHub', 'Analytics', 'API'],
                        'values': [45, 35, 20]
                    }
                },
                'status': {
                    'overall_score': 87
                },
                'table_data': [
                    {'source': 'github', 'type': 'commit', 'count': 156, 'date': '2025-01-15'},
                    {'source': 'analytics', 'type': 'pageview', 'count': 1240, 'date': '2025-01-15'},
                    {'source': 'api', 'type': 'request', 'count': 89, 'date': '2025-01-15'},
                    {'source': 'github', 'type': 'issue', 'count': 12, 'date': '2025-01-14'},
                    {'source': 'analytics', 'type': 'session', 'count': 567, 'date': '2025-01-14'}
                ]
            }
            
            # Store the data
            self.dashboard_data[(period, source)] = mock_data
            
            return mock_data
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {}
    
    def _get_system_status(self) -> Dict[str, Dict[str, str]]:
        """Get system status information"""
        # Mock system status
        return {
            'database': {
                'status': 'healthy',
                'details': 'Connected, 45ms latency'
            },
            'api': {
                'status': 'healthy',
                'details': 'All endpoints responding'
            },
            'scheduler': {
                'status': 'healthy',
                'details': '3 reports scheduled'
            },
            'notifications': {
                'status': 'warning',
                'details': 'Email queue backing up'
            }
        }
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent system alerts"""
        # Mock alerts
        return [
            {
                'title': 'High API Usage',
                'message': 'API usage is 85% above normal',
                'severity': 'medium',
                'timestamp': '2025-01-15 14:30'
            },
            {
                'title': 'Report Generation Delay',
                'message': 'Weekly report is 15 minutes overdue',
                'severity': 'low',
                'timestamp': '2025-01-15 14:15'
            }
        ]
    
    def run(self, **kwargs):
        """Run the dashboard server"""
        host = self.server_config.get('host', '0.0.0.0')
        port = self.server_config.get('port', 8080)
        debug = self.server_config.get('debug', False)
        
        self.logger.info(f"Starting dashboard server on {host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug, **kwargs)


class DashboardManager:
    """Manager for multiple dashboards"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.dashboards: Dict[str, DashboardServer] = {}
        
        # Create default dashboard
        self.create_dashboard('main', 'Main Dashboard')
    
    def create_dashboard(self, dashboard_id: str, title: str, custom_config: Optional[Dict[str, Any]] = None) -> DashboardServer:
        """Create a new dashboard"""
        try:
            config = self.config.copy()
            if custom_config:
                config.update(custom_config)
            
            dashboard = DashboardServer(config)
            self.dashboards[dashboard_id] = dashboard
            
            self.logger.info(f"Created dashboard: {title} ({dashboard_id})")
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Failed to create dashboard {dashboard_id}: {e}")
            raise
    
    def get_dashboard(self, dashboard_id: str) -> Optional[DashboardServer]:
        """Get a dashboard by ID"""
        return self.dashboards.get(dashboard_id)
    
    def list_dashboards(self) -> List[Dict[str, str]]:
        """List all available dashboards"""
        return [
            {'id': dashboard_id, 'title': f"Dashboard {dashboard_id}"}
            for dashboard_id in self.dashboards.keys()
        ]
    
    def remove_dashboard(self, dashboard_id: str) -> bool:
        """Remove a dashboard"""
        try:
            if dashboard_id in self.dashboards:
                del self.dashboards[dashboard_id]
                self.logger.info(f"Removed dashboard: {dashboard_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove dashboard {dashboard_id}: {e}")
            return False
    
    def run_all_dashboards(self):
        """Run all dashboards (note: only one can run at a time in this implementation)"""
        # In a real implementation, you might use different ports or a reverse proxy
        main_dashboard = self.dashboards.get('main')
        if main_dashboard:
            main_dashboard.run()


class DashboardWidget:
    """Base class for dashboard widgets"""
    
    def __init__(self, widget_id: str, title: str):
        self.widget_id = widget_id
        self.title = title
        self.data = {}
    
    def update_data(self, data: Dict[str, Any]):
        """Update widget data"""
        self.data = data
    
    def render(self) -> Dict[str, Any]:
        """Render the widget (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement render method")


class MetricCardWidget(DashboardWidget):
    """Widget for displaying metric cards"""
    
    def __init__(self, widget_id: str, title: str, value: float = 0, change: float = 0):
        super().__init__(widget_id, title)
        self.value = value
        self.change = change
    
    def render(self) -> Dict[str, Any]:
        return {
            'type': 'metric_card',
            'title': self.title,
            'value': self.value,
            'change': self.change,
            'change_direction': 'up' if self.change > 0 else 'down' if self.change < 0 else 'neutral'
        }


class ChartWidget(DashboardWidget):
    """Widget for displaying charts"""
    
    def __init__(self, widget_id: str, title: str, chart_type: str = 'line'):
        super().__init__(widget_id, title)
        self.chart_type = chart_type
        self.chart_data = {}
    
    def render(self) -> Dict[str, Any]:
        return {
            'type': 'chart',
            'title': self.title,
            'chart_type': self.chart_type,
            'data': self.chart_data
        }


class TableWidget(DashboardWidget):
    """Widget for displaying data tables"""
    
    def __init__(self, widget_id: str, title: str, columns: List[str] = None):
        super().__init__(widget_id, title)
        self.columns = columns or []
        self.rows = []
    
    def render(self) -> Dict[str, Any]:
        return {
            'type': 'table',
            'title': self.title,
            'columns': self.columns,
            'rows': self.rows
        }