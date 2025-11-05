# Analytics Orchestrator - Quick Start Guide

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- Docker & Docker Compose (optional)
- Redis (for caching)

### Automated Setup

```bash
# Make scripts executable (if needed)
chmod +x setup.sh deploy.sh cli.py

# Run automated setup
./setup.sh

# Configure environment
cp .env.example .env
# Edit .env with your GitHub token and other settings

# Start the service
./scripts/start.sh
```

### Docker Setup

```bash
# Start with Docker Compose
./scripts/docker-start.sh

# Or deploy to production
./deploy.sh production
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
GITHUB_TOKEN=your_github_token
JWT_SECRET=your_secure_secret

# Optional
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Main Configuration (config/config.yaml)
- Database settings
- Cache configuration
- GitHub API settings
- Integration configurations
- Monitoring setup

## 📋 CLI Commands

```bash
# Service management
python cli.py start          # Start service
python cli.py status         # Check status
python cli.py health         # Health check

# Integration management
python cli.py integration list
python cli.py integration enable health_monitoring
python cli.py integration disable follow_automation

# Configuration
python cli.py validate-config config/config.yaml
python cli.py test_config
python cli.py metrics --format json

# Reports
python cli.py report --format json
python cli.py report --output report.json
```

## 🌐 API Access

- **Service**: http://localhost:8000
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **API Docs**: http://localhost:8000/docs

## 📊 Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

## 🔌 Integration Endpoints

```bash
# Analytics
curl http://localhost:8000/api/analytics/metrics
curl http://localhost:8000/api/analytics/reports
curl http://localhost:8000/api/analytics/trends

# Monitoring
curl http://localhost:8000/api/monitoring/health
curl http://localhost:8000/api/monitoring/status
curl http://localhost:8000/api/monitoring/alerts

# Automation Control
curl http://localhost:8000/api/automation/control
curl http://localhost:8000/api/automation/status
curl http://localhost:8000/api/automation/schedule

# Webhooks
curl http://localhost:8000/api/webhooks/github
curl http://localhost:8000/api/webhooks/status
```

## 🐛 Troubleshooting

### Common Issues

1. **Configuration Validation Failed**
   ```bash
   python cli.py validate-config config/config.yaml
   ```

2. **Dependencies Missing**
   ```bash
   pip install -r requirements.txt
   ```

3. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Or change port in config/config.yaml
   ```

4. **GitHub API Rate Limit**
   ```yaml
   # Increase delay in config/config.yaml
   github:
     rate_limit_delay: 5
   ```

5. **Database Issues**
   ```bash
   # Recreate database
   rm data/analytics.db
   python cli.py start
   ```

### Log Files
- Application logs: `logs/analytics_orchestrator.log`
- Docker logs: `docker-compose logs analytics-orchestrator`

### Health Checks
```bash
# System health
python cli.py health

# Component health
python cli.py health --component database
python cli.py health --component cache
python cli.py health --component github
```

## 🔧 Advanced Configuration

### Database Migration
```bash
# Backup data
cp -r data/ data_backup_$(date +%Y%m%d)

# Update database schema (if needed)
python -c "from core.orchestrator import AnalyticsOrchestrator; import asyncio; asyncio.run(AnalyticsOrchestrator({}).update_database())"
```

### Performance Tuning
```yaml
# config/config.yaml
server:
  workers: 4
  max_connections: 1000

database:
  pool_size: 20
  max_overflow: 40

cache:
  default_ttl: 7200
  memory_cache_size: 2000
```

### Security Setup
```bash
# Generate secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API key
python -c "import secrets; print(secrets.token_hex(16))"
```

## 📚 Additional Resources

- **Full Documentation**: See README.md
- **API Documentation**: http://localhost:8000/docs
- **Configuration Reference**: config/config.yaml.example
- **GitHub Integration**: See GitHub API documentation

## 🆘 Support

For issues and questions:
1. Check logs: `logs/analytics_orchestrator.log`
2. Run diagnostics: `python cli.py test_config`
3. Check system status: `python cli.py status`
4. Validate configuration: `python cli.py validate-config`

---

**Quick Start Complete! The Analytics Orchestrator is ready for use.**