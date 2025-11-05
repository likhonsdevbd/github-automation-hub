# Automation Hub

🤖 **A compliance-first, rate-limited GitHub repository growth automation system**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Security: Compliant](https://img.shields.io/badge/Security-Compliant-green.svg)]()

**⚠️ IMPORTANT SAFETY NOTICE**: This automation system is designed with safety and compliance as the primary priorities. All automation features are **disabled by default** and must be explicitly enabled after thorough configuration review and testing.

## 🎯 Overview

The Automation Hub implements a conservative, compliant approach to GitHub automation with:

- **✅ Conservative Rate Limiting**: Maximum 24 actions/hour (configurable 20-30 range)
- **🛡️ Safety-First Design**: Immediate stops on enforcement signals, exponential backoff
- **📊 Comprehensive Auditing**: Full audit trails, performance monitoring, compliance reporting
- **🔒 Security-Focused**: Minimal token scopes, environment variable configuration
- **🤝 Human-in-the-Loop**: Manual controls and override capabilities

## 🏗️ Architecture

The system follows the architecture design from `/architecture_design/docs/automation_architecture.md`:

```
automation-hub/
├── scripts/                 # Core Python modules
│   ├── automation_manager.py  # Main orchestrator
│   ├── rate_limiter.py        # Conservative rate limiting
│   ├── github_client.py       # Secure API client
│   ├── config_manager.py      # Configuration management
│   ├── telemetry.py           # Monitoring and analytics
│   └── cli.py                 # Command-line interface
├── config/                  # Configuration files
│   ├── config_template.yaml   # Full configuration template
│   └── config_safe.yaml       # Conservative safe defaults
├── data/                    # Data storage and caching
├── docs/                    # Documentation
├── workflows/               # GitHub Actions workflows
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- GitHub Personal Access Token with minimal scopes:
  - `read:user` (required for all operations)
  - `user:follow` (only if following/unfollowing is enabled)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd automation-hub
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up GitHub token** (required):
   ```bash
   export GITHUB_TOKEN="your_github_personal_access_token_here"
   ```

4. **Create configuration**:
   ```bash
   python -m scripts.cli config create-template
   cp config_template.yaml config.yaml
   ```

5. **Validate configuration**:
   ```bash
   python -m scripts.cli config validate
   ```

6. **Check safety status**:
   ```bash
   python -m scripts.cli safety --check
   ```

### First Steps (Safe Mode)

Start with **read-only analysis** to understand your current state:

```bash
# Check current status
python -m scripts.cli status --detailed

# Find potential unfollow candidates (read-only)
python -m scripts.cli unfollow-candidates --limit 10

# Generate audit report
python -m scripts.cli audit report --format summary
```

## 📖 Configuration

### Safe Configuration (Recommended for Testing)

Copy the safe configuration for conservative defaults:

```bash
cp config/config_safe.yaml config.yaml
```

### Key Configuration Areas

#### 🔧 Core Automation Settings
```yaml
automation:
  enabled: false              # KEEP DISABLED until tested
  operation_mode: "analysis"  # "analysis" (safe) or "active" (risky)
  safety_features:
    emergency_stop_on_422: true      # CRITICAL: Stop on spam signals
    exponential_backoff_on_429: true # CRITICAL: Respect rate limits
    audit_logging: true              # Full audit trail
```

#### ⚡ Rate Limiting (Conservative Defaults)
```yaml
rate_limits:
  max_actions_per_hour: 24    # Within 20-30 safe range
  base_delay_seconds: 150     # 2.5 minutes between actions
  min_gap_between_actions: 180 # 3 minutes minimum
```

#### 🔐 GitHub Integration
```yaml
github:
  token: null  # Set via environment variable
  allowed_scopes:
    - "read:user"              # Always required
    # - "user:follow"          # Only if following is enabled
```

## 🛠️ Usage

### Status Monitoring

```bash
# Basic status
python -m scripts.cli status

# Detailed status with metrics
python -m scripts.cli status --detailed

# Safety compliance check
python -m scripts.cli safety --check
```

### Follow Operations

⚠️ **Start with dry runs to test everything**:

```bash
# Test follow action (dry run)
python -m scripts.cli follow --username targetuser --dry-run

# Execute follow (after testing)
python -m scripts.cli follow --username targetuser

# Find unfollow candidates
python -m scripts.cli unfollow-candidates --limit 20

# Execute unfollow actions
python -m scripts.cli execute-unfollow --usernames user1 user2 user3
```

### Configuration Management

```bash
# Create configuration template
python -m scripts.cli config create-template

# Validate current configuration
python -m scripts.cli config validate

# Show current configuration
python -m scripts.cli config show
```

### Audit and Reporting

```bash
# Generate summary audit report
python -m scripts.cli audit report

# Export detailed telemetry data
python -m scripts.cli audit export --format json

# Export as CSV for analysis
python -m scripts.cli audit export --format csv
```

### Safety Controls

```bash
# Check current safety status
python -m scripts.cli safety --check

# Enable automation (requires explicit confirmation)
python -m scripts.cli safety --enable

# Disable automation
python -m scripts.cli safety --disable
```

## 🛡️ Safety and Compliance

### Built-in Safety Features

1. **Emergency Stop on 422 Errors**: Immediately halts automation on validation/spam signals
2. **Exponential Backoff on 429**: Respects rate limits with increasing delays
3. **Conservative Rate Limits**: Default 24 actions/hour (within safe 20-30 range)
4. **Audit Logging**: Complete trail of all actions for accountability
5. **Human-in-the-Loop**: Manual controls and override capabilities

### Compliance Guidelines

- ✅ **Always start with dry runs** to test configurations
- ✅ **Use conservative rate limits** (12-24 actions/hour for safety)
- ✅ **Monitor compliance status** regularly with `safety --check`
- ✅ **Keep audit logs** for accountability and troubleshooting
- ✅ **Enable emergency stops** (they're on by default, don't disable)

- ❌ **Never disable safety features** like emergency stops or rate limiting
- ❌ **Don't increase rate limits** beyond 30 actions/hour
- ❌ **Don't run automated following** without thorough testing
- ❌ **Don't ignore 422 or 429 errors** - they indicate enforcement

### Rate Limiting Strategy

The system implements a multi-layered approach:

- **Token Bucket Algorithm**: Smooth token consumption
- **Exponential Backoff**: Increasing delays on rate limits
- **Jittered Timing**: Human-like variability (20-40%)
- **Conditional Requests**: ETag caching to reduce API calls
- **Concurrent Action Limits**: Maximum 1 action at a time

### Error Handling

| Error Code | Meaning | Action |
|------------|---------|--------|
| 422 | Validation error / spam flag | **HARD STOP** - Stop automation |
| 429 | Rate limit exceeded | Exponential backoff |
| 403 | Access denied | Check token scopes |
| 404 | User not found | Continue (idempotent) |

## 🔄 Workflows

The system includes GitHub Actions workflows for:

### Daily Health Check
- Runs daily at 9 AM UTC
- Checks automation compliance
- Generates status reports
- Uploads audit logs

### Growth Tracking
- Runs daily at 8 AM UTC
- Tracks repository metrics
- Generates weekly summaries
- No automation actions performed

### Documentation Generation
- Runs on documentation changes
- Generates API docs automatically
- Updates GitHub Pages
- Creates documentation PRs

## 📊 Monitoring and Analytics

### Performance Metrics

- **Action Success Rate**: Percentage of successful operations
- **Rate Limit Events**: Frequency of rate limiting
- **Error Rates**: Distribution of error types
- **Compliance Score**: Overall compliance assessment (0-100)

### Key Performance Indicators (KPIs)

| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| Follow-back Ratio | Stable, modest growth | Sharp drops |
| 422 Error Rate | 0% | Any occurrence |
| 429 Error Rate | <5% | >10% |
| Action Throughput | Smooth, low-volume | Spikes |

### Audit Trail

All actions are logged with:
- Timestamp and action type
- Target username (privacy-redacted)
- Response codes and latency
- Rate limit status
- Compliance indicators

## 🔧 Advanced Usage

### Custom Configuration

Create your own configuration based on the template:

```bash
# Create template
python -m scripts.cli config create-template --output my_config.yaml

# Edit configuration
nano my_config.yaml

# Use custom config
python -m scripts.cli status --config my_config.yaml
```

### Programmatic Usage

```python
from scripts.automation_manager import AutomationManager
from scripts.config_manager import ConfigManager

# Load configuration
config_manager = ConfigManager('config.yaml')
config = config_manager.get_config()

# Initialize automation manager
manager = AutomationManager('config.yaml')
manager.start()

# Execute actions
success = manager.execute_follow_action('target_username')
candidates = manager.get_follow_back_candidates()

# Generate reports
status = manager.get_status_report()
manager.save_audit_log('my_audit.json')
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes |
| `AUTOMATION_ENABLED` | Enable automation (true/false) | No |
| `MAX_ACTIONS_PER_HOUR` | Override rate limit | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING) | No |

## 🐛 Troubleshooting

### Common Issues

1. **"Configuration validation failed"**
   - Ensure `GITHUB_TOKEN` environment variable is set
   - Check that configuration file is valid YAML

2. **"422 error - stopping automation"**
   - Indicates spam/enforcement signal
   - **Do not continue** - review safety settings
   - Wait before attempting again with reduced frequency

3. **"429 rate limit exceeded"**
   - Normal rate limiting behavior
   - System will automatically back off
   - Consider increasing delays if frequent

4. **"GitHub token is invalid"**
   - Verify token has correct scopes
   - Check token hasn't expired
   - Regenerate token if necessary

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG
python -m scripts.cli status --detailed
```

### Log Analysis

Check audit logs for detailed activity:

```bash
# View recent logs
tail -f automation_hub.log

# Search for specific events
grep "422" automation_hub.log
grep "compliance" automation_hub.log
```

## 📝 Contributing

When contributing to this project:

1. **Follow safety-first principles** - all changes must maintain or improve safety
2. **Update tests** - ensure all changes have appropriate test coverage
3. **Document changes** - update documentation for any new features
4. **Validate configuration** - test with both safe and template configurations

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black scripts/
flake8 scripts/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This automation tool is designed to operate within GitHub's Terms of Service and Acceptable Use Policies. Users are responsible for:

- Ensuring compliance with GitHub's current policies
- Regular monitoring of automation behavior
- Proper configuration of safety features
- Understanding the risks of automation

The developers are not responsible for any policy violations or account restrictions resulting from misuse of this tool.

## 🔗 References

- [GitHub API Rate Limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [GitHub Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies)
- [GitHub REST API Best Practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)

---

**Made with ❤️ for compliant GitHub automation**
