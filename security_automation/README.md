# Security Automation Tool

A comprehensive security automation system that provides automated vulnerability scanning, dependency checking, code quality analysis, and continuous security monitoring.

## 🚀 Features

### Core Security Scanning
- **Vulnerability Scanning**: Automated scanning using Semgrep, Bandit, and custom security checks
- **Dependency Security**: Python (Safety, pip-audit) and Node.js (npm audit) dependency vulnerability checking
- **Code Quality Analysis**: Python linting and formatting with Flake8, Black, isort, MyPy, Pylint
- **Custom Security Checks**: Hardcoded secrets, SQL injection patterns, command injection detection

### GitHub Integration
- **Security Policies**: Automated SECURITY.md and vulnerability disclosure setup
- **Dependabot Configuration**: Automatic dependency update configuration
- **Security Workflows**: GitHub Actions workflows for continuous security monitoring
- **Branch Protection**: Security-focused branch protection recommendations
- **Secret Scanning**: Setup and configuration guidance

### Continuous Monitoring
- **Scheduled Scans**: Daily, weekly, and custom scheduled security scans
- **Security Dashboard**: Real-time security metrics and trends visualization
- **Alerting System**: Multi-channel notifications (GitHub Issues, Email, Slack)
- **Security Metrics**: Track security score, vulnerability trends, and improvement metrics

### Automated Reporting
- **Multiple Formats**: JSON, HTML, and Markdown report generation
- **Executive Summaries**: High-level security status for management
- **Detailed Analysis**: Comprehensive findings with remediation guidance
- **Trend Analysis**: Historical security metrics and improvement tracking

## 📋 Requirements

### Python Dependencies
```bash
pip install requests toml packaging
```

### Security Tools (Optional)
```bash
# For full functionality, install these tools:
pip install semgrep bandit safety pip-audit flake8 black isort mypy pylint radon vulture
npm install -g npm-audit
```

### GitHub Integration
- GitHub token (for API operations)
- Repository admin permissions (for workflow setup)

## 🛠️ Installation

1. **Clone or download the security automation tool**
```bash
# Download the security_automation directory
git clone <repository> security_automation
cd security_automation
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Make the CLI executable**
```bash
chmod +x security_cli.py
```

4. **Install optional security tools** (recommended)
```bash
# Python security tools
pip install semgrep bandit safety pip-audit flake8 black isort mypy pylint radon vulture

# Node.js security tools
npm install -g npm-audit
```

## 🚦 Quick Start

### Basic Security Scan
```bash
python security_cli.py full-scan --project-path ./my-project
```

### Vulnerability Scanning Only
```bash
python security_cli.py vuln-scan --project-path ./my-project --format json
```

### Dependency Security Check
```bash
python security_cli.py dependency-check --project-path ./my-project --auto-update
```

### Code Quality Analysis
```bash
python security_cli.py quality-scan --project-path ./my-project --fix
```

### Generate Report from Existing Results
```bash
python security_cli.py report --scan-results results.json --format html --output report.html
```

## 📖 Usage Examples

### Complete Setup for a New Project

1. **Run initial security assessment**
```bash
python security_cli.py full-scan --project-path ./my-project --output-dir ./security-reports
```

2. **Set up GitHub security integration**
```bash
python security_cli.py github-setup --repo-url https://github.com/username/my-project
```

3. **Configure continuous monitoring**
```bash
python security_cli.py setup-monitoring --project-path ./my-project --github-integration --schedule daily
```

### CI/CD Integration

#### GitHub Actions Integration
```yaml
# .github/workflows/security.yml
name: Security Scan
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Run security scan
      run: |
        pip install semgrep bandit safety
        python security_automation/security_cli.py full-scan --project-path .
```

#### Jenkins Integration
```groovy
pipeline {
    agent any
    stages {
        stage('Security Scan') {
            steps {
                sh 'python3 security_automation/security_cli.py full-scan --project-path .'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'security-reports/**', allowEmptyArchive: true
                }
            }
        }
    }
}
```

## 🏗️ Architecture

```
security_automation/
├── security_cli.py           # Main CLI interface
├── vulnerability_scanner.py  # Vulnerability detection
├── dependency_checker.py     # Dependency security checking
├── code_quality_scanner.py   # Code quality analysis
├── security_reporter.py      # Report generation
├── github_security.py        # GitHub integration
├── monitoring_config.py      # Continuous monitoring setup
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

### Core Components

#### VulnerabilityScanner
- **Semgrep**: Static analysis for security vulnerabilities
- **Bandit**: Python-specific security linting
- **Safety**: Python package vulnerability scanning
- **Custom Checks**: Pattern-based vulnerability detection

#### DependencyChecker
- **Requirements.txt**: Python dependency analysis
- **pyproject.toml**: Modern Python dependency management
- **package.json**: Node.js dependency security
- **Auto-updates**: Automated vulnerability fixes

#### CodeQualityScanner
- **Linting**: Flake8, Pylint for code style and quality
- **Formatting**: Black, isort for code formatting
- **Type Checking**: MyPy for type annotations
- **Complexity**: Radon for code complexity analysis

#### SecurityReporter
- **Multiple Formats**: JSON, HTML, Markdown output
- **Executive Summaries**: Management-focused reports
- **Trend Analysis**: Historical security metrics
- **Visual Dashboards**: Interactive security dashboards

#### GitHubSecurity
- **Workflow Integration**: Automated GitHub Actions setup
- **Security Policies**: Policy and guideline templates
- **Dependabot**: Automated dependency updates
- **Branch Protection**: Security-focused branch rules

#### MonitoringConfig
- **Scheduled Scans**: Automated security monitoring
- **Alerting**: Multi-channel notification system
- **Metrics Dashboard**: Real-time security visualization
- **Escalation**: Automated issue escalation

## 🔧 Configuration

### Security Tool Configuration

#### Flake8 Configuration (.flake8)
```ini
[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist,*.egg-info
ignore = E203,W503
```

#### MyPy Configuration (mypy.ini)
```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

#### Bandit Configuration (.bandit)
```yaml
[bandit]
exclude_dirs = tests,docs
skips = B101,B601
```

### Monitoring Configuration

#### Alerting Configuration (config/security/alerting.json)
```json
{
  "notification_channels": {
    "email": {
      "enabled": true,
      "recipients": ["security@example.com"]
    },
    "slack": {
      "enabled": true,
      "webhook_url": "YOUR_SLACK_WEBHOOK",
      "channel": "#security-alerts"
    }
  },
  "alert_rules": [
    {
      "name": "Critical Security Issues",
      "condition": "critical_issues > 0",
      "severity": "critical",
      "actions": ["create_github_issue", "send_email_alert"]
    }
  ]
}
```

### GitHub Integration Setup

1. **Generate GitHub Personal Access Token**
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate token with `repo`, `security_events`, `workflow` permissions
   - Store token securely (GitHub Secrets)

2. **Configure Repository Settings**
   - Enable GitHub Actions
   - Set up branch protection rules
   - Configure security policies

3. **Setup Workflow Permissions**
   - Repository Settings > Actions > General
   - Enable "Read and write permissions"
   - Allow GitHub Actions to create pull requests

## 📊 Reports and Dashboards

### Security Reports

#### HTML Report Features
- **Executive Summary**: High-level security status
- **Detailed Findings**: Comprehensive vulnerability analysis
- **Severity Breakdown**: Issues categorized by priority
- **Remediation Guidance**: Step-by-step fix instructions
- **Visual Indicators**: Color-coded severity levels

#### JSON Report Structure
```json
{
  "metadata": {
    "generated_at": "2023-12-01T10:30:00Z",
    "timestamp": "20231201_103000",
    "report_version": "1.0"
  },
  "results": {
    "vulnerabilities": { /* vulnerability scan results */ },
    "dependencies": { /* dependency check results */ },
    "code_quality": { /* code quality analysis */ }
  }
}
```

### Security Dashboard

Access the interactive dashboard at `docs/security-dashboard/index.html`

#### Dashboard Features
- **Real-time Metrics**: Current security score and issue counts
- **Historical Trends**: Security improvement tracking
- **Alert Status**: Active security alerts and notifications
- **Scan History**: Recent security scan results

## 🔔 Alerting and Notifications

### Alert Channels

#### GitHub Issues (Default)
- Automatic issue creation for security alerts
- Proper labeling and assignment
- Integration with project management

#### Email Notifications
- SMTP configuration required
- Customizable recipient lists
- Rich HTML email formatting

#### Slack Integration
- Webhook-based notifications
- Channel-specific alerts
- Rich message formatting with security metrics

### Alert Rules

1. **Critical Security Issues**
   - Trigger: Any critical vulnerability detected
   - Action: Immediate notification + GitHub issue

2. **Security Score Degradation**
   - Trigger: Security score drops below threshold
   - Action: Alert + trend analysis

3. **New Dependency Vulnerabilities**
   - Trigger: New vulnerability in dependencies
   - Action: Create tracking issue

### Escalation Rules
- **60 minutes**: Security team escalation
- **4 hours**: Management escalation
- **24 hours**: Executive notification

## 🔍 Security Checks Included

### Vulnerability Detection

#### Pattern-Based Checks
- Hardcoded secrets and API keys
- SQL injection vulnerabilities
- Command injection risks
- Insecure random number generation
- Weak cryptographic algorithms

#### Tool-Based Scanning
- **Semgrep**: Static analysis rules for OWASP Top 10
- **Bandit**: Python-specific security patterns
- **Safety**: Known vulnerability database

### Dependency Security

#### Python Dependencies
- Requirements.txt analysis
- pyproject.toml scanning
- Poetry dependency checking
- pipenv environment validation

#### Node.js Dependencies
- package.json validation
- npm audit integration
- Dependency vulnerability tracking

### Code Quality Analysis

#### Python Code Quality
- **Flake8**: PEP 8 compliance and style checking
- **Black**: Automatic code formatting
- **isort**: Import statement organization
- **MyPy**: Static type checking
- **Pylint**: Comprehensive code analysis

#### Complexity Analysis
- Cyclomatic complexity measurement
- Function complexity tracking
- Nesting depth analysis
- Code duplication detection

## 🚀 Advanced Usage

### Custom Security Rules

Add custom vulnerability patterns:

```python
# In vulnerability_scanner.py
def custom_security_check(self):
    patterns = [
        r'your_custom_pattern',
        r'another_pattern'
    ]
    # Implementation
```

### Integration with External Tools

#### Snyk Integration
```python
# Add to dependency_checker.py
def check_snyk(self):
    # Snyk API integration
    pass
```

#### SonarQube Integration
```python
# Add to code_quality_scanner.py
def check_sonarqube(self):
    # SonarQube API integration
    pass
```

### Custom Report Formats

Extend the SecurityReporter class:

```python
def export_xml_report(self, scan_results, timestamp):
    # Custom XML formatting
    pass

def export_csv_report(self, scan_results, timestamp):
    # Custom CSV formatting
    pass
```

## 🛡️ Security Best Practices

### 1. Regular Security Scans
- Daily automated scans for active projects
- Weekly comprehensive security reviews
- Pre-commit hooks for immediate feedback

### 2. Dependency Management
- Enable automated dependency updates
- Regular security advisory monitoring
- Pin dependency versions for reproducibility

### 3. Code Security
- Implement secure coding practices
- Use static analysis tools in development
- Regular security training for developers

### 4. Monitoring and Alerting
- Configure appropriate alert thresholds
- Set up escalation procedures
- Monitor security metrics trends

### 5. Incident Response
- Document security incident procedures
- Maintain security contact lists
- Regular security drills and testing

## 🐛 Troubleshooting

### Common Issues

#### Tools Not Found
```bash
# Error: semgrep not found
pip install semgrep

# Error: bandit not found
pip install bandit
```

#### Permission Issues
```bash
# GitHub API access denied
# Solution: Ensure GITHUB_TOKEN has required permissions
export GITHUB_TOKEN="your_token_here"
```

#### Scan Timeouts
```bash
# Large projects may timeout
# Solution: Increase timeout or scan specific directories
python security_cli.py vuln-scan --project-path ./src  # Scan specific directory
```

### Debug Mode

Enable verbose logging:
```bash
export SECURITY_DEBUG=1
python security_cli.py full-scan --project-path .
```

### Log Analysis

Check workflow logs in GitHub Actions:
1. Go to Actions tab in repository
2. Select failed workflow run
3. Review step-by-step logs
4. Check for tool installation errors

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**
```bash
pip install -r requirements-dev.txt
```

4. **Run tests**
```bash
python -m pytest tests/
```

### Adding New Security Tools

1. **Extend VulnerabilityScanner class**
```python
def _run_new_tool(self):
    # Implementation
    pass
```

2. **Add to tool configuration**
```python
self.linters['new_tool'] = {
    'command': ['new_tool', '.'],
    'install_cmd': 'pip install new_tool'
}
```

3. **Update documentation**
4. **Add tests**

### Reporting Issues

When reporting issues, include:
- Operating system and Python version
- Security tool versions
- Error messages and logs
- Sample code that triggers the issue
- Expected vs actual behavior

## 📚 Additional Resources

### Security Tools Documentation
- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [GitHub Security Features](https://docs.github.com/en/code-security)

### Security Standards
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/archive/2021/2021_cwe_top25.html)

### Security Communities
- [OWASP](https://owasp.org/)
- [Security Focus](https://www.securityfocus.com/)
- [Reddit r/netsec](https://www.reddit.com/r/netsec/)

## 📄 License

This security automation tool is provided under the MIT License. See LICENSE file for details.

## ⚠️ Disclaimer

This tool is designed to assist with security analysis but should not be considered a complete security solution. Always complement automated scanning with manual security reviews and follow security best practices.

---

**Questions or Issues?**  
Create an issue in the repository or contact the security team.

**Stay Secure! 🔒**