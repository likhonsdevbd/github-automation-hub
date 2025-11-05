# Comprehensive Reporting & Visualization System

A powerful, automated reporting system for generating executive summaries, interactive dashboards, and scheduled reports with multiple export formats.

## 🚀 Features

### Core Functionality
- **Automated Report Generation**: Daily, weekly, monthly scheduled reports
- **Executive Summary Reports**: Stakeholder-focused reports with key metrics
- **Interactive Dashboards**: Real-time charts and visualizations
- **Multi-Format Export**: PDF, HTML, Excel, CSV exports
- **Email Notifications**: Automated email distribution
- **Custom Templates**: Branded report templates
- **Data Integration**: Connect to multiple data sources (GitHub, Analytics, APIs, Databases)
- **API Integration**: RESTful APIs for programmatic access

### Data Sources
- **GitHub**: Repository metrics, commits, issues, pull requests
- **Google Analytics**: Website traffic, user behavior
- **Custom APIs**: Any RESTful API integration
- **Databases**: SQL and NoSQL database connections
- **File Sources**: CSV, Excel, JSON file processing

### Export Formats
- **PDF**: Professional formatted reports with charts and tables
- **HTML**: Interactive web reports with CSS styling
- **Excel**: Multi-sheet workbooks with formatted data
- **CSV**: Flat file export for data analysis

### Scheduling & Automation
- **Cron-based Scheduling**: Flexible time-based triggers
- **Event-driven Reports**: Triggered by specific conditions
- **Batch Processing**: Multiple reports generated concurrently
- **Retry Logic**: Automatic retry on failure with backoff

## 📁 Project Structure

```
reporting_system/
├── core/                   # Core reporting engine
│   ├── __init__.py        # Report generation orchestration
├── data_sources/          # Data integration modules
│   ├── __init__.py        # Multi-source data collection
├── exporters/             # Export functionality (PDF, HTML, Excel, CSV)
│   ├── __init__.py        # Multi-format export engine
├── templates/             # Report templates
│   ├── executive_summary.html    # Executive summary template
│   ├── weekly_report.html        # Weekly report template
│   └── default_report.html       # Default report template
├── notifications/         # Email notification system
│   ├── __init__.py        # Multi-channel notifications
├── dashboards/            # Interactive dashboard components
│   ├── __init__.py        # Real-time dashboards using Dash
├── schedulers/            # Automated scheduling
│   ├── __init__.py        # APScheduler integration
├── utils/                 # Utility functions
│   ├── __init__.py        # Helper functions and utilities
├── config/                # Configuration files
│   └── config_template.yaml     # Configuration template
├── examples/              # Usage examples
│   └── demo_usage.py      # Comprehensive usage examples
├── tests/                 # Test suites
│   └── integration_test.py      # Integration tests
├── __init__.py            # Package initialization
├── main.py               # CLI entry point
├── setup.py              # Package setup
└── requirements.txt      # Dependencies
```

## 🔧 Quick Start

### Installation

```bash
# Clone or download the reporting system
cd code/automation-hub/reporting_system

# Install dependencies
pip install -r requirements.txt

# Initialize the system
python -m reporting_system.main init
```

### Basic Configuration

1. Copy and configure the system:
```bash
cp config/config_template.yaml config/config.yaml
```

2. Update `config/config.yaml` with your settings:
```yaml
database:
  primary:
    type: "postgresql"
    host: "localhost"
    name: "reporting_system"
    user: "your_user"
    password: "your_password"

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "your_email@gmail.com"
  password: "your_app_password"

data_sources:
  github:
    enabled: true
    token: "your_github_token"
    organization: "your_org"
```

### Generate Your First Report

```bash
# Generate a sample report
python -m reporting_system.main --generate-sample

# Generate a custom report
python -m reporting_system.main generate \
  --period weekly \
  --format pdf \
  --sources github analytics \
  --recipients stakeholder@company.com
```

### Start Interactive Dashboard

```bash
# Start the web dashboard
python -m reporting_system.main --dashboard --port 8080
```

### Set Up Scheduled Reports

```bash
# Add a daily report
python -m reporting_system.main add-schedule \
  "Daily Summary" \
  --period daily \
  --schedule "0 9 * * *" \
  --format pdf \
  --sources github analytics \
  --recipients team@company.com

# Start the scheduler service
python -m reporting_system.main start-scheduler
```

## 🎯 Usage Examples

### Programmatic Usage

```python
from reporting_system import ReportGenerator, ReportRequest

# Initialize generator
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
print(f"Report ID: {result.report_id}")
```

### Dashboard Management

```python
from reporting_system import DashboardManager

# Create dashboard manager
dashboard_manager = DashboardManager(config)

# Create custom dashboard
custom_config = {
    'dashboard': {
        'server': {'port': 8081, 'host': 'localhost'}
    }
}
dashboard = dashboard_manager.create_dashboard('custom', 'Analytics Dashboard', custom_config)

# Start dashboard
dashboard_manager.run_all_dashboards()
```

### Scheduled Reports

```python
from reporting_system import SchedulerManager, ScheduledReport

# Initialize scheduler
scheduler = SchedulerManager(config)

# Create scheduled report
report = ScheduledReport(
    report_id="weekly_summary",
    name="Weekly Performance Summary",
    report_type="executive_summary",
    period="weekly",
    data_sources=["github", "analytics"],
    format="html",
    schedule="0 9 * * 1",  # 9 AM every Monday
    recipients=["team@company.com"]
)

# Add to scheduler
scheduler.add_scheduled_report(report)
```

## 📊 Dashboard Features

### Interactive Components
- **Real-time KPI Cards**: Live metrics with trend indicators
- **Dynamic Charts**: Line charts, pie charts, bar charts
- **Data Tables**: Sortable, filterable data tables
- **Status Indicators**: System health and alert panels

### Dashboard Widgets
- **MetricCardWidget**: Display key performance indicators
- **ChartWidget**: Various chart types with real-time data
- **TableWidget**: Interactive data tables
- **AlertWidget**: System alerts and notifications

### Customization
- **Themes**: Multiple visual themes (Bootstrap, Dark, Corporate)
- **Branding**: Custom logos, colors, and styling
- **Layout**: Responsive grid-based layouts
- **Refresh Intervals**: Configurable data refresh rates

## 🔄 Data Sources Integration

### GitHub Integration
```yaml
github:
  enabled: true
  token: "your_personal_access_token"
  organization: "your_org"
  api_rate_limit: 5000
```

### Google Analytics
```yaml
google_analytics:
  enabled: true
  property_id: "your_property_id"
  service_account_key: "path/to/service_account.json"
```

### Custom APIs
```yaml
custom_api:
  enabled: true
  endpoint: "https://api.company.com"
  api_key: "your_api_key"
  rate_limit: 1000
```

## 📧 Notification System

### Email Notifications
- **HTML Templates**: Professional email templates
- **Attachments**: Report files attached to emails
- **Multiple Recipients**: Send to multiple email addresses
- **Scheduling**: Automated report delivery

### Other Channels
- **Slack**: Webhook notifications
- **Microsoft Teams**: Team notifications
- **Discord**: Community notifications

## 📅 Scheduling

### Cron Expressions
```python
# Daily at 9 AM
"0 9 * * *"

# Weekly on Monday at 10 AM
"0 10 * * 1"

# Monthly on 1st at 8 AM
"0 8 1 * *"
```

### Schedule Management
- **Add/Remove**: Manage scheduled reports via CLI
- **Pause/Resume**: Temporarily disable reports
- **Status Monitoring**: Track success/failure rates
- **Run History**: View execution history

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL="postgresql://user:pass@localhost/db"

# Email
SMTP_SERVER="smtp.gmail.com"
SMTP_USERNAME="your_email"
SMTP_PASSWORD="your_password"

# GitHub
GITHUB_TOKEN="your_github_token"
GITHUB_ORG="your_organization"
```

### Custom Templates
Create custom HTML templates in the `templates/` directory:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Custom Report</title>
    <style>
        /* Your custom styling */
    </style>
</head>
<body>
    <h1>{{ report_type.title() }} Report</h1>
    <p>Generated: {{ generated_at }}</p>
    
    <!-- Your custom content -->
    {{ content }}
</body>
</html>
```

## 🧪 Testing

### Run Integration Tests
```bash
# Run all tests
python -m reporting_system.tests.integration_test

# Run specific test
python -c "from reporting_system.tests.integration_test import tester; tester.test_data_sources()"
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Load and stress testing
- **Configuration Tests**: Settings validation

## 📈 Monitoring & Logging

### Logging
```python
# Configure logging levels
monitoring:
  log_level: "INFO"
  log_file: "logs/reporting_system.log"
  log_max_size_mb: 100
  log_backup_count: 5
```

### Metrics
```python
# Prometheus metrics integration
from reporting_system.utils import PrometheusMetrics

metrics = PrometheusMetrics()
metrics.increment_report_generated()
metrics.set_processing_time(1.5)
```

### Health Checks
- **System Status**: Database, API, scheduler health
- **Data Source Status**: Connection and rate limit monitoring
- **Report Status**: Generation success/failure tracking

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "-m", "reporting_system.main", "--dashboard", "--port", "8080"]
```

### Production Considerations
- **Database**: Use PostgreSQL for production data
- **Cache**: Implement Redis for performance
- **Load Balancing**: Multiple dashboard instances
- **Security**: API key management and authentication

## 🆘 Troubleshooting

### Common Issues

1. **Configuration Not Found**
   ```bash
   python -m reporting_system.main init
   ```

2. **GitHub API Rate Limits**
   ```yaml
   data_sources:
     github:
       rate_limit: 5000  # Your rate limit
   ```

3. **Email Sending Fails**
   - Check SMTP settings
   - Verify app passwords for Gmail
   - Test with `python -c "from reporting_system.notifications import NotificationManager; NotificationManager(config).test_configuration()"`

4. **Dashboard Won't Start**
   - Check port availability
   - Verify Dash dependencies installed
   - Check configuration file syntax

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m reporting_system.main --dashboard --debug
```

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run code formatting
black reporting_system/
flake8 reporting_system/

# Run tests
pytest reporting_system/tests/
```

### Code Structure
- Follow Python PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation for changes

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/yourusername/reporting-system/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/reporting-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/reporting-system/discussions)
- **Email**: support@reporting.system

---

**Built with ❤️ for automated reporting and data visualization**