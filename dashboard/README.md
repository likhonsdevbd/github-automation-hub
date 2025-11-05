# Automation Hub Dashboard

A comprehensive real-time monitoring and dashboard system for automation operations with advanced alerting, notification integrations, and metrics visualization.

## Features

### 🔄 Real-time Dashboard
- **Live System Metrics**: CPU, Memory, Disk, Network monitoring
- **Automation Status**: Active, queued, completed, and failed operations tracking
- **GitHub API Monitoring**: Rate limit tracking and usage analytics
- **Health Score**: Real-time system health scoring with visual indicators

### 📊 Monitoring & Analytics
- **Prometheus Integration**: Metrics collection and querying
- **Grafana Integration**: Automated dashboard creation and management
- **Historical Data**: Time-series charts and trend analysis
- **Performance Tracking**: System performance over time

### 🚨 Alert Management
- **Custom Alert Rules**: Flexible rule configuration with YAML
- **Severity Levels**: Critical, Warning, and Info alert classification
- **Escalation Policies**: Multi-level escalation with time-based triggers
- **Alert Acknowledgment**: Team collaboration on alert management

### 📢 Multi-Channel Notifications
- **Slack Integration**: Rich notifications with actionable buttons
- **Discord Integration**: Community-focused alert delivery
- **Microsoft Teams**: Enterprise communication integration
- **Email & SMS**: Traditional notification channels
- **Rate Limiting**: Prevent notification flooding

### 📱 Mobile-Responsive Design
- **Responsive Layout**: Optimized for desktop, tablet, and mobile
- **Touch-Friendly**: Mobile-first interaction design
- **Offline Support**: Progressive Web App capabilities
- **Dark/Light Theme**: User preference-based theming

### 🔧 API & Extensibility
- **RESTful API**: Comprehensive backend API
- **WebSocket Support**: Real-time data streaming
- **Webhook Integration**: External system integration
- **Plugin Architecture**: Extensible notification system

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd code/automation-hub/dashboard
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Configuration**
   ```bash
   cp config/dashboard.yaml config/dashboard.yaml.example
   # Edit config/dashboard.yaml with your settings
   ```

### Running the Application

#### Development Mode
```bash
# Start backend
cd backend
python dashboard_api.py

# Start frontend (in another terminal)
cd frontend
npm run dev
```

#### Production Mode
```bash
# Using the main script
python main.py --config config/dashboard.yaml

# Or with custom settings
python main.py --host 0.0.0.0 --port 8000 --dev
```

### Access the Dashboard
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Configuration

### Basic Configuration
Edit `config/dashboard.yaml`:

```yaml
# API Settings
api:
  host: "0.0.0.0"
  port: 8000
  
# Notifications
notifications:
  slack:
    webhook_url: "https://hooks.slack.com/services/..."
    enabled: true
    
# Monitoring
monitoring:
  prometheus:
    url: "http://localhost:9090"
    enabled: true
```

### Alert Rules
Configure alert rules in the configuration file:

```yaml
alerts:
  rules:
    - name: "High CPU Usage"
      description: "CPU usage above 80%"
      query: "cpu_usage"
      severity: "critical"
      threshold: 80.0
      duration: 60
      enabled: true
```

### Escalation Policies
Set up multi-level escalation:

```yaml
escalation_policies:
  critical:
    level_1:
      channels: ["slack"]
      timeout: 0
    level_2:
      channels: ["slack", "email"]
      timeout: 300  # 5 minutes
```

## API Reference

### REST Endpoints

#### Metrics
- `GET /api/metrics` - Get current system metrics
- `GET /api/system/info` - Get detailed system information

#### Alerts
- `GET /api/alerts` - Get all alerts
- `DELETE /api/alerts/{id}` - Dismiss an alert
- `POST /api/alerts/{id}/acknowledge` - Acknowledge an alert

#### Notifications
- `GET /api/notifications` - Get notification history
- `POST /api/notifications/{id}/read` - Mark notification as read
- `DELETE /api/notifications` - Clear all notifications

#### Settings
- `GET /api/settings` - Get dashboard settings
- `POST /api/settings` - Update dashboard settings

### WebSocket API
Connect to `ws://localhost:8000/ws/dashboard` for real-time updates:

```javascript
const socket = io('http://localhost:8000');

socket.on('metrics_update', (data) => {
  console.log('Metrics updated:', data);
});

socket.on('new_alert', (alert) => {
  console.log('New alert:', alert);
});
```

## Monitoring Integration

### Prometheus Setup
1. Install and configure Prometheus
2. Add scrape configurations:
   ```yaml
   scrape_configs:
     - job_name: 'automation-hub'
       static_configs:
         - targets: ['localhost:8000']
       metrics_path: '/metrics'
   ```

### Grafana Setup
1. Configure Grafana datasource for Prometheus
2. Import pre-built dashboards from the `grafana/` directory
3. Set up alerting rules

## Alert Management

### Creating Custom Alert Rules
1. Define rules in YAML format:
   ```yaml
   - name: "Custom Metric Alert"
     description: "Custom metric threshold exceeded"
     query: "custom_metric_value"
     severity: "warning"
     threshold: 100.0
     duration: 300
     labels:
       service: "my-service"
     annotations:
       summary: "Custom metric threshold exceeded"
   ```

2. Load rules via configuration or API:
   ```python
   from alerts.alert_manager import AlertRule, AlertSeverity
   
   rule = AlertRule(
       name="Custom Alert",
       description="Custom description",
       query="metric_name",
       severity=AlertSeverity.WARNING,
       threshold=50.0,
       duration=60
   )
   
   alert_manager.add_alert_rule(rule)
   ```

### Escalation Configuration
Set up escalation levels for different alert severities:

```yaml
escalation_policies:
  critical:
    level_1: {channels: ["slack"], timeout: 0}
    level_2: {channels: ["slack", "email"], timeout: 300}
    level_3: {channels: ["slack", "email", "sms"], timeout: 900}
```

## Notification Channels

### Slack Integration
1. Create a Slack app and incoming webhook
2. Configure webhook URL in settings:
   ```yaml
   notifications:
     slack:
       webhook_url: "https://hooks.slack.com/services/..."
       channel: "#automation-alerts"
       enabled: true
   ```

### Discord Integration
1. Create a Discord webhook
2. Configure in settings:
   ```yaml
   notifications:
     discord:
       webhook_url: "https://discord.com/api/webhooks/..."
       enabled: true
   ```

### Email Notifications
Configure SMTP settings:
```yaml
notifications:
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_email: "dashboard@yourcompany.com"
    to_emails: ["admin@yourcompany.com"]
    enabled: true
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py", "--config", "config/dashboard.yaml"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CONFIG_PATH=config/dashboard.yaml
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Production Deployment
1. Use HTTPS/SSL certificates
2. Configure reverse proxy (nginx, Apache)
3. Set up monitoring and logging
4. Configure backup strategies
5. Use process manager (systemd, supervisor)

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check CORS configuration
   - Verify API endpoint is accessible
   - Check firewall settings

2. **Notifications Not Sending**
   - Verify webhook URLs are valid
   - Check network connectivity
   - Review notification logs

3. **High Memory Usage**
   - Enable caching
   - Optimize alert rules
   - Adjust refresh intervals

### Debug Mode
Run with debug logging:
```bash
python main.py --config config/dashboard.yaml --dev
```

### Health Checks
Monitor system health:
```bash
curl http://localhost:8000/health
```

## Development

### Project Structure
```
dashboard/
├── backend/              # FastAPI backend
│   ├── dashboard_api.py  # Main API application
│   └── requirements.txt  # Python dependencies
├── frontend/             # React frontend
│   ├── src/             # Source code
│   ├── public/          # Static assets
│   └── package.json     # Node dependencies
├── integrations/         # External integrations
│   ├── notifications.py # Notification system
│   └── monitoring.py    # Prometheus/Grafana
├── alerts/              # Alert management
│   └── alert_manager.py # Alert logic
├── config/              # Configuration files
│   └── dashboard.yaml   # Main config
├── docs/               # Documentation
└── main.py            # Main application
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update documentation
5. Submit a pull request

### Testing
```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

## License
MIT License - see LICENSE file for details.

## Support
- Documentation: [docs/](./docs/)
- Issues: GitHub Issues
- Email: support@automation-hub.com