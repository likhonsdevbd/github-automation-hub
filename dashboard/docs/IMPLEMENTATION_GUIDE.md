# Automation Hub Dashboard - Implementation Guide

## System Overview

The Automation Hub Dashboard is a comprehensive real-time monitoring system built with:
- **Frontend**: React + TypeScript with Chart.js for data visualization
- **Backend**: FastAPI with WebSocket support for real-time updates
- **Monitoring**: Prometheus integration for metrics collection
- **Visualization**: Grafana dashboards for advanced analytics
- **Notifications**: Multi-channel alerting (Slack, Discord, Teams, Email, SMS)
- **Alerting**: Configurable alert rules with escalation policies

## Architecture Components

### 1. Real-time Dashboard (React Frontend)
**Location**: `frontend/src/`

**Key Features**:
- Live system metrics visualization
- Real-time WebSocket updates
- Mobile-responsive design
- Dark/light theme support
- Custom dashboard layouts

**Core Components**:
- `Dashboard.jsx` - Main dashboard view
- `Metrics.jsx` - Historical metrics and charts
- `Alerts.jsx` - Alert management interface
- `Notifications.jsx` - Notification center
- `Settings.jsx` - Dashboard configuration

**Widgets**:
- SystemMetrics - CPU, Memory, Disk, Network
- AutomationStatus - Task queue status
- GithubMetrics - API rate limit monitoring
- HealthScore - System health scoring
- AlertSummary - Active alerts overview
- QuickActions - System control panel

### 2. FastAPI Backend
**Location**: `backend/dashboard_api.py`

**Features**:
- RESTful API endpoints
- WebSocket support for real-time updates
- CORS configuration
- Health check endpoints
- Mock data generation for testing

**API Endpoints**:
- `GET /api/metrics` - Current system metrics
- `GET /api/alerts` - Alert management
- `GET /api/notifications` - Notification history
- `POST /api/settings` - Configuration updates
- `WebSocket /ws/dashboard` - Real-time data streaming

### 3. Alert Management System
**Location**: `alerts/alert_manager.py`

**Capabilities**:
- Configurable alert rules (YAML-based)
- Multi-level escalation policies
- Alert acknowledgment workflow
- Rate limiting for notifications
- Automatic alert resolution

**Alert Rules Structure**:
```yaml
- name: "High CPU Usage"
  description: "CPU usage above threshold"
  query: "cpu_usage"
  severity: "critical"  # critical, warning, info
  threshold: 80.0
  duration: 60  # seconds
  labels: {monitor: "system"}
  annotations: {summary: "High CPU usage detected"}
```

**Escalation Levels**:
- Level 1: Immediate notification (Slack)
- Level 2: 5 minutes (Slack + Discord)
- Level 3: 15 minutes (Email + SMS)
- Level 4: 30 minutes (PagerDuty)

### 4. Notification Integration
**Location**: `integrations/notifications.py`

**Supported Channels**:
- **Slack**: Rich message cards with actions
- **Discord**: Embed notifications
- **Microsoft Teams**: Card-based messages
- **Email**: SMTP-based delivery
- **SMS**: Twilio integration

**Features**:
- Rate limiting to prevent spam
- Retry logic for failed deliveries
- Template-based notifications
- Multi-channel broadcasting

### 5. Monitoring Integration
**Location**: `integrations/monitoring.py`

**Prometheus Integration**:
- Metrics collection and querying
- Historical data retrieval
- Health monitoring
- Custom metrics support

**Grafana Integration**:
- Automated dashboard creation
- Panel configuration
- Data source management
- Alert rule setup

## Deployment Options

### Development Mode
```bash
# Quick setup
./start.sh setup

# Start development servers
./start.sh start development

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Docker Deployment
```bash
# Full stack with monitoring
./start.sh start docker

# Access:
# Dashboard: http://localhost:8000
# Grafana: http://localhost:3001 (admin/admin123)
# Prometheus: http://localhost:9090
```

### Production Deployment
```bash
# Using configuration file
cp config/dashboard.yaml.example config/dashboard.yaml
# Edit configuration with your settings
python main.py --config config/dashboard.yaml
```

## Configuration Guide

### Basic Setup (config/dashboard.yaml)

#### API Configuration
```yaml
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_origins:
    - "https://yourdomain.com"
```

#### Notification Channels
```yaml
notifications:
  slack:
    webhook_url: "https://hooks.slack.com/services/..."
    channel: "#automation-alerts"
    enabled: true
    
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@domain.com"
    password: "your-app-password"
    enabled: true
```

#### Monitoring Configuration
```yaml
monitoring:
  prometheus:
    url: "http://localhost:9090"
    enabled: true
    
  grafana:
    url: "http://localhost:3000"
    api_key: "your-grafana-api-key"
    enabled: true
```

### Alert Rules Configuration

Create alert rules in your configuration file:

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
      
    - name: "High Memory Usage"
      description: "Memory usage above 85%"
      query: "memory_usage"
      severity: "warning"
      threshold: 85.0
      duration: 300
      enabled: true
```

### Escalation Policies

Configure multi-level escalation:

```yaml
escalation_policies:
  critical:
    level_1:
      channels: ["slack"]
      timeout: 0
    level_2:
      channels: ["slack", "email"]
      timeout: 300  # 5 minutes
    level_3:
      channels: ["slack", "email", "sms"]
      timeout: 900  # 15 minutes
```

## API Usage Examples

### WebSocket Connection (JavaScript)
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/dashboard');

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'metrics_update':
            updateDashboard(data.data);
            break;
        case 'new_alert':
            showAlert(data.data);
            break;
    }
};
```

### REST API Calls (Python)
```python
import requests

# Get current metrics
response = requests.get('http://localhost:8000/api/metrics')
metrics = response.json()

# Dismiss alert
requests.delete(f'http://localhost:8000/api/alerts/{alert_id}')

# Update settings
settings = {'refresh_interval': 10000}
requests.post('http://localhost:8000/api/settings', json=settings)
```

## Monitoring Setup

### Prometheus Configuration
The system includes a Prometheus configuration file (`prometheus.yml`) with:
- Automation Hub metrics scraping
- Node Exporter integration
- Redis monitoring
- Custom alert rules

### Grafana Setup
Automated dashboard provisioning includes:
- Prometheus data source configuration
- Default dashboard templates
- Alert notification channels
- User authentication setup

### Alert Rules
Define Prometheus-compatible alert rules:

```yaml
groups:
  - name: automation-hub-alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage > 80
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: High CPU usage detected
          description: CPU usage is {{ $value }}%
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   - Check CORS configuration in backend
   - Verify firewall settings
   - Check API endpoint accessibility

2. **Notifications Not Sending**
   - Verify webhook URLs
   - Check network connectivity
   - Review notification logs

3. **High Memory Usage**
   - Enable Redis caching
   - Optimize alert rules
   - Adjust refresh intervals

### Debug Mode
```bash
# Run with debug logging
python main.py --config config/dashboard.yaml --dev
```

### Health Checks
```bash
# Check system health
curl http://localhost:8000/health

# Check detailed system info
curl http://localhost:8000/api/system/info
```

## Security Considerations

### Production Security Checklist
- [ ] Change default secret keys
- [ ] Enable HTTPS/SSL
- [ ] Configure proper CORS origins
- [ ] Set up authentication
- [ ] Enable rate limiting
- [ ] Use secure SMTP settings
- [ ] Configure firewall rules
- [ ] Enable audit logging

### API Authentication
Implement authentication middleware:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    # Validate JWT token
    # Return user object
    pass
```

## Performance Optimization

### Caching Strategy
- Use Redis for session storage
- Cache metric data for 30 seconds
- Enable client-side caching
- Implement database connection pooling

### Scaling Considerations
- Load balancing for multiple instances
- Database sharding for large datasets
- CDN for static assets
- Horizontal scaling of workers

## Custom Development

### Adding New Widgets
1. Create widget component in `frontend/src/components/widgets/`
2. Add to dashboard layout
3. Implement WebSocket data handling
4. Add responsive styling

### Custom Notification Channels
1. Implement notification class in `integrations/notifications.py`
2. Register callback in alert manager
3. Add configuration options
4. Test notification delivery

### Custom Alert Rules
1. Define rule in YAML configuration
2. Implement query logic if needed
3. Add to escalation policies
4. Test rule evaluation

## Support and Maintenance

### Log Locations
- Application logs: `logs/dashboard.log`
- Backend logs: Check application output
- Docker logs: `docker-compose logs dashboard`

### Monitoring Metrics
Track these key metrics:
- System CPU/Memory usage
- API response times
- WebSocket connection count
- Alert frequency
- Notification delivery success rate

### Backup Strategy
- Database: Regular automated backups
- Configuration: Version control
- Logs: Log rotation and archival
- Dashboards: Export Grafana configurations

## Conclusion

This dashboard system provides a comprehensive solution for monitoring automation systems with real-time updates, intelligent alerting, and flexible notification options. The modular architecture allows for easy customization and scaling as your automation needs grow.