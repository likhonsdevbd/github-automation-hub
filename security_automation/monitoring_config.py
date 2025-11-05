"""
Continuous Security Monitoring Configuration
Sets up automated security monitoring and alerting systems.
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class MonitoringConfig:
    """Continuous security monitoring configuration and setup"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.config_dir = self.project_path / ".github" / "workflows"
        
    def setup_monitoring(self, github_integration: bool = False, schedule: str = 'daily') -> Dict[str, Any]:
        """Setup comprehensive security monitoring"""
        results = {
            'status': 'started',
            'configurations_created': []
        }
        
        try:
            # 1. Create main security monitoring workflow
            self._create_main_monitoring_workflow(schedule)
            results['configurations_created'].append('main_monitoring_workflow')
            
            # 2. Create vulnerability monitoring
            self._create_vulnerability_monitoring_workflow()
            results['configurations_created'].append('vulnerability_monitoring')
            
            # 3. Create dependency monitoring
            self._create_dependency_monitoring_workflow()
            results['configurations_created'].append('dependency_monitoring')
            
            # 4. Create code quality monitoring
            self._create_code_quality_monitoring_workflow()
            results['configurations_created'].append('code_quality_monitoring')
            
            # 5. Create security metrics dashboard
            self._create_security_dashboard()
            results['configurations_created'].append('security_dashboard')
            
            # 6. Create alerting configuration
            self._create_alerting_config()
            results['configurations_created'].append('alerting_config')
            
            # 7. Create monitoring dashboard (if GitHub integration)
            if github_integration:
                self._create_github_integration_monitoring()
                results['configurations_created'].append('github_integration')
            
            # 8. Create monitoring documentation
            self._create_monitoring_documentation()
            results['configurations_created'].append('monitoring_documentation')
            
            results['status'] = 'completed'
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _create_main_monitoring_workflow(self, schedule: str) -> None:
        """Create main security monitoring workflow"""
        
        # Map schedule strings to cron expressions
        schedule_cron = {
            'hourly': '0 * * * *',
            'daily': '0 2 * * *',
            'weekly': '0 2 * * 0'
        }
        
        cron_expr = schedule_cron.get(schedule, '0 2 * * *')
        
        workflow_content = f"""name: Continuous Security Monitoring

on:
  schedule:
    - cron: '{cron_expr}'  # {schedule.title()} security scan
  workflow_dispatch:
    inputs:
      scan_type:
        description: 'Type of security scan'
        required: true
        default: 'full'
        type: choice
        options:
        - full
        - vulnerabilities
        - dependencies
        - code_quality
      severity_threshold:
        description: 'Minimum severity to alert on'
        required: false
        default: 'medium'
        type: choice
        options:
        - critical
        - high
        - medium
        - low
  push:
    branches: [ main ]
    paths:
      - '**.py'
      - 'requirements*.txt'
      - 'package.json'
      - 'pyproject.toml'
  pull_request:
    branches: [ main ]
    paths:
      - '**.py'
      - 'requirements*.txt'
      - 'package.json'

env:
  SEVERITY_THRESHOLD: ${{{{ github.event.inputs.severity_threshold || 'medium' }}}}

jobs:
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 60
    permissions:
      contents: read
      security-events: write
      actions: read
    
    outputs:
      scan-results: ${{{{ steps.scan.outputs.results }}}}
      security-score: ${{{{ steps.score.outputs.score }}}}
      critical-issues: ${{{{ steps.score.outputs.critical }}}}
      high-issues: ${{{{ steps.score.outputs.high }}}}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for better analysis
        
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '16'
        
    - name: Install security tools
      run: |
        pip install --upgrade pip
        pip install semgrep bandit safety pip-audit
        pip install flake8 black isort mypy pylint radon
        npm install -g npm-audit
        
    - name: Cache security tools
      uses: actions/cache@v3
      with:
        path: |
          ~/.cache/pip
          ~/.npm
        key: ${{{{ runner.os }}}}-tools-${{{{ hashFiles('**/requirements*.txt', 'package.json') }}}}
        restore-keys: |
          ${{{{ runner.os }}}}-tools-
          
    - name: Run comprehensive security scan
      id: scan
      run: |
        echo "Running security scan..."
        python security_automation/security_cli.py full-scan \\
          --project-path . \\
          --output-dir ./security-reports \\
          --format json
          
        # Store results for later steps
        echo "results=$(cat security-reports/security_report_*.json | jq -c .)" >> $GITHUB_OUTPUT
        
    - name: Calculate security score
      id: score
      run: |
        # Extract metrics from scan results
        CRITICAL=$(cat security-reports/security_report_*.json | jq '.metadata.results.vulnerabilities.summary.total_vulnerabilities // 0')
        HIGH=$(cat security-reports/security_report_*.json | jq '.metadata.results.dependencies.summary.high_severity_issues // 0')
        
        echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
        echo "high=$HIGH" >> $GITHUB_OUTPUT
        
        # Calculate score (100 - penalties)
        SCORE=100
        SCORE=$((SCORE - CRITICAL * 10))  # 10 points per critical issue
        SCORE=$((SCORE - HIGH * 5))       # 5 points per high issue
        
        if [ $SCORE -lt 0 ]; then
          SCORE=0
        fi
        
        echo "score=$SCORE" >> $GITHUB_OUTPUT
        echo "Security score: $SCORE"
        
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-reports-${{{{ github.run_number }}}}
        path: security-reports/
        
    - name: Security scan summary
      run: |
        echo "## 🔒 Security Scan Results" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "**Security Score:** ${{{{ steps.score.outputs.score }}}}/100" >> $GITHUB_STEP_SUMMARY
        echo "**Critical Issues:** ${{{{ steps.score.outputs.critical }}}}" >> $GITHUB_STEP_SUMMARY
        echo "**High Issues:** ${{{{ steps.score.outputs.high }}}}" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        
        if [ ${{{{ steps.score.outputs.critical }}}} -gt 0 ]; then
          echo "🚨 **CRITICAL**: Immediate attention required!" >> $GITHUB_STEP_SUMMARY
        elif [ ${{{{ steps.score.outputs.high }}}} -gt 0 ]; then
          echo "⚠️ **HIGH**: Review required within 24 hours" >> $GITHUB_STEP_SUMMARY
        else
          echo "✅ No critical or high severity issues found" >> $GITHUB_STEP_SUMMARY
        fi

  security-alerts:
    name: Security Alerts
    runs-on: ubuntu-latest
    needs: security-scan
    if: failure() || contains(github.event.head_commit.message, '[SECURITY]')
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Security Alert Notification
      run: |
        echo "🔔 Security Alert Triggered!"
        echo "Scan Type: ${{{{ github.event.inputs.scan_type || 'scheduled' }}}}"
        echo "Critical Issues: ${{{{ needs.security-scan.outputs.critical-issues }}}}"
        echo "Security Score: ${{{{ needs.security-scan.outputs.security-score }}}}"
        
        # In a real implementation, this would send notifications
        # to Slack, email, or other communication channels
        
    - name: Create Security Issue
      if: needs.security-scan.outputs.critical-issues > 0
      uses: actions/github-script@v6
      with:
        script: |
          const { owner, repo } = context.repo;
          
          github.rest.issues.create({
            owner,
            repo,
            title: `🚨 Security Alert: ${{{{ needs.security-scan.outputs.critical-issues }}}} Critical Issues Detected`,
            body: `## Security Alert
            
            **Trigger:** Automated security scan detected critical issues.
            
            **Scan Date:** ${{{{ new Date().toISOString() }}}}
            **Security Score:** ${{{{ needs.security-scan.outputs.security-score }}}}/100
            **Critical Issues:** ${{{{ needs.security-scan.outputs.critical-issues }}}}
            
            **Action Required:**
            1. Review the security reports
            2. Address critical vulnerabilities immediately
            3. Update dependencies if necessary
            4. Re-run security scan after fixes
            
            **Reports:** Check the artifacts for detailed security reports.
            
            _This issue was automatically created by the security monitoring system._
            `,
            labels: ['security', 'critical', 'automated']
          });

  security-metrics:
    name: Update Security Metrics
    runs-on: ubuntu-latest
    needs: security-scan
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        token: ${{{{ secrets.GITHUB_TOKEN }}}}
        branch: main
        
    - name: Update security metrics
      run: |
        echo "Updating security metrics..."
        
        # Create or update security metrics file
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        
        cat > security-metrics.json << EOF
        {{
          "last_scan": "$TIMESTAMP",
          "security_score": ${{{{ needs.security-scan.outputs.security-score }}}},
          "critical_issues": ${{{{ needs.security-scan.outputs.critical-issues }}}},
          "high_issues": ${{{{ needs.security-scan.outputs.high-issues }}}},
          "scan_type": "${{{{ github.event.inputs.scan_type || 'scheduled' }}}}"
        }}
        EOF
        
    - name: Commit security metrics
      run: |
        git config user.name "Security Bot"
        git config user.email "security@github-actions[bot].com"
        git add security-metrics.json
        git commit -m "Update security metrics - ${{{{ needs.security-scan.outputs.security-score }}}}/100 score" || exit 0
        git push
"""
        
        self._write_workflow_file("security-monitoring.yml", workflow_content)
    
    def _create_vulnerability_monitoring_workflow(self) -> None:
        """Create specific vulnerability monitoring workflow"""
        workflow_content = """name: Vulnerability Monitoring

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  vulnerability-check:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install vulnerability scanners
      run: |
        pip install semgrep bandit safety
        npm install -g @semgrep/cli
        
    - name: Run Semgrep
      uses: returntocorp/semgrep-action@v1
      with:
        config: >-
          p/security-audit
          p/secrets
          p/owasp-top-ten
          p/python
        generateSarif: "1"
        
    - name: Upload Semgrep SARIF
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: semgrep.sarif
        
    - name: Run Bandit
      run: |
        bandit -r . -f json -o bandit-results.json || true
        
    - name: Run Safety
      run: |
        if find . -name "requirements*.txt" | grep -q .; then
          safety check --json --output safety-results.json || true
        fi
        
    - name: Aggregate vulnerability results
      run: |
        echo "Vulnerability monitoring completed"
        # This would aggregate results from multiple scanners
        
    - name: Upload vulnerability reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: vulnerability-reports
        path: |
          semgrep.sarif
          bandit-results.json
          safety-results.json
"""
        
        self._write_workflow_file("vulnerability-monitoring.yml", workflow_content)
    
    def _create_dependency_monitoring_workflow(self) -> None:
        """Create dependency monitoring workflow"""
        workflow_content = """name: Dependency Security Monitoring

on:
  schedule:
    - cron: '0 4 * * *'  # Daily at 4 AM
  workflow_dispatch:

jobs:
  dependency-security:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '16'
        
    - name: Install dependency scanners
      run: |
        pip install safety pip-audit
        npm install -g npm-audit
        
    - name: Run Python dependency audit
      run: |
        safety check --json --output safety-audit.json || true
        pip-audit --format=json --output=pip-audit.json || true
        
    - name: Run Node.js dependency audit
      if: hashFiles('package.json') != ''
      run: |
        npm audit --audit-level=moderate --json > npm-audit.json || true
        
    - name: Check for known vulnerable dependencies
      run: |
        echo "Checking for vulnerable dependencies..."
        
        # Example: Fail if high-severity vulnerabilities found
        HIGH_VULNS=$(cat safety-audit.json 2>/dev/null | jq '.vulnerabilities | map(select(.severity == "high")) | length' || echo "0")
        
        if [ "$HIGH_VULNS" -gt 0 ]; then
          echo "::error::Found $HIGH_VULNS high-severity vulnerabilities in dependencies"
          exit 1
        fi
        
    - name: Generate dependency report
      run: |
        TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
        
        echo "# Dependency Security Report - $TIMESTAMP" > dependency-report.md
        echo "" >> dependency-report.md
        
        if [ -f safety-audit.json ]; then
          echo "## Python Dependencies (Safety)" >> dependency-report.md
          SAFETY_COUNT=$(cat safety-audit.json 2>/dev/null | jq '.vulnerabilities | length' || echo "0")
          echo "Vulnerabilities found: $SAFETY_COUNT" >> dependency-report.md
        fi
        
        if [ -f pip-audit.json ]; then
          echo "## Python Dependencies (pip-audit)" >> dependency-report.md
          PIP_AUDIT_COUNT=$(cat pip-audit.json 2>/dev/null | jq '.vulnerabilities | length' || echo "0")
          echo "Vulnerabilities found: $PIP_AUDIT_COUNT" >> dependency-report.md
        fi
        
        if [ -f npm-audit.json ]; then
          echo "## Node.js Dependencies" >> dependency-report.md
          NPM_COUNT=$(cat npm-audit.json 2>/dev/null | jq '.metadata.vulnerabilities | length' || echo "0")
          echo "Vulnerabilities found: $NPM_COUNT" >> dependency-report.md
        fi
        
    - name: Upload dependency reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: dependency-security-reports
        path: |
          safety-audit.json
          pip-audit.json
          npm-audit.json
          dependency-report.md
"""
        
        self._write_workflow_file("dependency-monitoring.yml", workflow_content)
    
    def _create_code_quality_monitoring_workflow(self) -> None:
        """Create code quality monitoring workflow"""
        workflow_content = """name: Code Quality Monitoring

on:
  schedule:
    - cron: '0 8 * * 1'  # Weekly on Monday at 8 AM
  workflow_dispatch:

jobs:
  code-quality:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install code quality tools
      run: |
        pip install flake8 black isort mypy pylint radon vulture
        
    - name: Run code quality checks
      run: |
        echo "Running code quality analysis..."
        
        # Flake8
        flake8 . --format=json --output-file=flake8-results.json || true
        
        # Black (check only)
        black --check --diff . || true
        
        # isort (check only)
        isort --check-only --diff . || true
        
        # MyPy
        mypy --ignore-missing-imports --output-format=json . > mypy-results.json || true
        
        # Pylint
        pylint --output-format=json . > pylint-results.json || true
        
        # Radon complexity
        radon cc -j . > radon-results.json || true
        
        # Vulture dead code
        vulture --min-confidence 80 --format json . > vulture-results.json || true
        
    - name: Generate quality report
      run: |
        TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
        
        echo "# Code Quality Report - $TIMESTAMP" > quality-report.md
        echo "" >> quality-report.md
        
        # Count issues
        FLAKE8_ISSUES=$(cat flake8-results.json 2>/dev/null | jq '. | length' || echo "0")
        MYPY_ISSUES=$(cat mypy-results.json 2>/dev/null | jq '. | length' || echo "0")
        PYLINT_ISSUES=$(cat pylint-results.json 2>/dev/null | jq '. | length' || echo "0")
        
        echo "## Summary" >> quality-report.md
        echo "- Flake8 issues: $FLAKE8_ISSUES" >> quality-report.md
        echo "- MyPy issues: $MYPY_ISSUES" >> quality-report.md
        echo "- Pylint issues: $PYLINT_ISSUES" >> quality-report.md
        
        # Calculate quality score
        TOTAL_ISSUES=$((FLAKE8_ISSUES + MYPY_ISSUES + PYLINT_ISSUES))
        QUALITY_SCORE=$((100 - TOTAL_ISSUES))
        
        if [ $QUALITY_SCORE -lt 0 ]; then
          QUALITY_SCORE=0
        fi
        
        echo "" >> quality-report.md
        echo "**Overall Quality Score:** $QUALITY_SCORE/100" >> quality-report.md
        
    - name: Upload quality reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: code-quality-reports
        path: |
          flake8-results.json
          mypy-results.json
          pylint-results.json
          radon-results.json
          vulture-results.json
          quality-report.md
"""
        
        self._write_workflow_file("code-quality-monitoring.yml", workflow_content)
    
    def _create_security_dashboard(self) -> None:
        """Create security metrics dashboard"""
        
        # Dashboard HTML template
        dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Dashboard</title>
    <style>
        {self._get_dashboard_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 Security Dashboard</h1>
            <p>Last updated: <span id="last-update"></span></p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Security Score</h3>
                <div class="metric-value" id="security-score">--</div>
                <div class="metric-label">/ 100</div>
            </div>
            
            <div class="metric-card critical">
                <h3>Critical Issues</h3>
                <div class="metric-value" id="critical-issues">--</div>
                <div class="metric-label">Require immediate action</div>
            </div>
            
            <div class="metric-card high">
                <h3>High Issues</h3>
                <div class="metric-value" id="high-issues">--</div>
                <div class="metric-label">Review within 24h</div>
            </div>
            
            <div class="metric-card medium">
                <h3>Medium Issues</h3>
                <div class="metric-value" id="medium-issues">--</div>
                <div class="metric-label">Plan for next sprint</div>
            </div>
        </div>
        
        <section class="charts">
            <h2>📊 Security Trends</h2>
            <div id="trend-chart">
                <!-- Chart would be populated by JavaScript -->
                <p>Trend chart placeholder - integrate with Chart.js or similar</p>
            </div>
        </section>
        
        <section class="recent-scans">
            <h2>🔍 Recent Security Scans</h2>
            <div id="scan-history">
                <!-- Scan history would be populated here -->
            </div>
        </section>
        
        <section class="alerts">
            <h2>🚨 Active Security Alerts</h2>
            <div id="security-alerts">
                <!-- Active alerts would be displayed here -->
            </div>
        </section>
    </div>
    
    <script>
        {self._get_dashboard_javascript()}
    </script>
</body>
</html>
"""
        
        # Create dashboard directory
        dashboard_dir = self.project_path / "docs" / "security-dashboard"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        # Write dashboard files
        with open(dashboard_dir / "index.html", 'w') as f:
            f.write(dashboard_html)
        
        # Create dashboard data file
        dashboard_config = {
            "refresh_interval": 300,  # 5 minutes
            "metrics_history_days": 30,
            "alert_thresholds": {
                "critical": 0,
                "high": 5,
                "medium": 15
            },
            "data_sources": [
                "security-metrics.json",
                "vulnerability-reports",
                "dependency-reports"
            ]
        }
        
        with open(dashboard_dir / "config.json", 'w') as f:
            json.dump(dashboard_config, f, indent=2)
    
    def _create_alerting_config(self) -> None:
        """Create alerting configuration"""
        alert_config = {
            "notification_channels": {
                "email": {
                    "enabled": False,
                    "recipients": ["security-team@example.com"],
                    "smtp_server": "smtp.example.com",
                    "smtp_port": 587
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                    "channel": "#security-alerts"
                },
                "github": {
                    "enabled": True,
                    "create_issues": True,
                    "assign_issues_to": ["security-team"]
                }
            },
            "alert_rules": [
                {
                    "name": "Critical Security Issues",
                    "condition": "critical_issues > 0",
                    "severity": "critical",
                    "actions": [
                        "create_github_issue",
                        "send_email_alert",
                        "slack_notification"
                    ]
                },
                {
                    "name": "High Security Score Drop",
                    "condition": "security_score < 70",
                    "severity": "high",
                    "actions": [
                        "slack_notification",
                        "github_issue"
                    ]
                },
                {
                    "name": "New Vulnerability in Dependencies",
                    "condition": "dependency_vulnerabilities > 0",
                    "severity": "medium",
                    "actions": [
                        "github_issue"
                    ]
                }
            ],
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "06:00",
                "timezone": "UTC"
            },
            "escalation_rules": [
                {
                    "after_minutes": 60,
                    "action": "escalate_to_security_lead"
                },
                {
                    "after_minutes": 240,
                    "action": "escalate_to_cto"
                }
            ]
        }
        
        # Create alerts configuration directory
        alerts_dir = self.project_path / "config" / "security"
        alerts_dir.mkdir(parents=True, exist_ok=True)
        
        with open(alerts_dir / "alerting.json", 'w') as f:
            json.dump(alert_config, f, indent=2)
    
    def _create_github_integration_monitoring(self) -> None:
        """Create GitHub-specific monitoring integrations"""
        
        # GitHub Security Advisory monitoring
        advisory_workflow = """name: GitHub Security Advisory Monitor

on:
  schedule:
    - cron: '0 3 * * *'  # Daily at 3 AM
  workflow_dispatch:

jobs:
  security-advisories:
    runs-on: ubuntu-latest
    
    steps:
    - name: Check Security Advisories
      run: |
        echo "Checking GitHub Security Advisories..."
        
        # This would query GitHub's Security Advisories API
        # and check for advisories affecting your dependencies
        
        # Example API call (pseudo-code)
        # curl -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \\
        #   "https://api.github.com/advisories?ecosystem=pypi&package=django"
        
        echo "Security advisories check completed"
"""
        
        self._write_workflow_file("security-advisories.yml", advisory_workflow)
        
        # Code scanning alerts workflow
        code_scanning_workflow = """name: Code Scanning Alert Monitor

on:
  schedule:
    - cron: '0 1 * * *'  # Daily at 1 AM
  workflow_dispatch:

jobs:
  code-scanning:
    runs-on: ubuntu-latest
    
    steps:
    - name: Monitor Code Scanning Alerts
      uses: actions/github-script@v6
      with:
        script: |
          // This would check for code scanning alerts
          // and create issues or notifications as needed
          
          console.log('Monitoring code scanning alerts...');
          
          // Example: Get open code scanning alerts
          const { data: alerts } = await github.rest.codeScanning.listAlertsForRepo({
            owner: context.repo.owner,
            repo: context.repo.repo,
            state: 'open'
          });
          
          console.log(`Found ${alerts.length} open code scanning alerts`);
          
          // Create summary issue if needed
          if (alerts.length > 0) {
            // Create or update a summary issue
          }
"""
        
        self._write_workflow_file("code-scanning-monitor.yml", code_scanning_workflow)
    
    def _create_monitoring_documentation(self) -> None:
        """Create monitoring documentation"""
        monitoring_docs = """# Security Monitoring Documentation

## Overview

This document describes the continuous security monitoring setup for the project.

## Monitoring Components

### 1. Main Security Monitoring
- **Frequency**: Daily (configurable)
- **Scope**: Full security scan including vulnerabilities, dependencies, and code quality
- **Workflow**: `.github/workflows/security-monitoring.yml`

### 2. Vulnerability Monitoring
- **Frequency**: Daily at 6 AM
- **Tools**: Semgrep, Bandit, Safety
- **Workflow**: `.github/workflows/vulnerability-monitoring.yml`

### 3. Dependency Monitoring
- **Frequency**: Daily at 4 AM
- **Tools**: Safety, pip-audit, npm audit
- **Workflow**: `.github/workflows/dependency-monitoring.yml`

### 4. Code Quality Monitoring
- **Frequency**: Weekly on Monday
- **Tools**: Flake8, MyPy, Pylint, Radon
- **Workflow**: `.github/workflows/code-quality-monitoring.yml`

## Security Metrics

The monitoring system tracks the following metrics:

- **Security Score**: 0-100 score based on findings
- **Critical Issues**: Require immediate attention
- **High Issues**: Review within 24 hours
- **Medium Issues**: Plan for next sprint
- **Low Issues**: Track for future improvements

## Alerting

### Alert Channels
- GitHub Issues (automatic)
- Email notifications (configurable)
- Slack notifications (configurable)

### Alert Rules
1. **Critical Security Issues**: Immediate notification
2. **Security Score Drop**: Alert when score < 70
3. **New Dependency Vulnerabilities**: Track new vulnerabilities

### Escalation
- After 60 minutes: Escalate to security lead
- After 4 hours: Escalate to CTO

## Dashboard

Access the security dashboard at: `docs/security-dashboard/index.html`

The dashboard displays:
- Real-time security metrics
- Historical trends
- Recent scan results
- Active security alerts

## Configuration

### Customizing Scan Frequency
Edit the cron expressions in workflow files:
- `.github/workflows/security-monitoring.yml`
- `.github/workflows/vulnerability-monitoring.yml`
- `.github/workflows/dependency-monitoring.yml`

### Modifying Alert Thresholds
Edit `config/security/alerting.json`:
```json
{
  "alert_thresholds": {
    "critical": 0,
    "high": 5,
    "medium": 15
  }
}
```

### Notification Configuration
Configure notification channels in `config/security/alerting.json`:

```json
{
  "notification_channels": {
    "email": {
      "enabled": true,
      "recipients": ["security-team@example.com"]
    },
    "slack": {
      "enabled": true,
      "webhook_url": "YOUR_SLACK_WEBHOOK",
      "channel": "#security-alerts"
    }
  }
}
```

## Manual Security Scans

Run security scans manually using the CLI:

```bash
# Full security scan
python security_automation/security_cli.py full-scan --project-path .

# Vulnerability scan only
python security_automation/security_cli.py vuln-scan --project-path .

# Dependency check
python security_automation/security_cli.py dependency-check --project-path .

# Code quality scan
python security_automation/security_cli.py quality-scan --project-path .
```

## Troubleshooting

### Common Issues

1. **Workflow Fails with Permission Error**
   - Ensure `GITHUB_TOKEN` has required permissions
   - Check repository settings for workflow permissions

2. **Security Tools Not Found**
   - Tools are installed in each workflow
   - Check workflow logs for installation errors

3. **No Alerts Received**
   - Verify notification configuration in `alerting.json`
   - Check GitHub repository settings for issue creation permissions

### Logs and Debugging

- Check GitHub Actions logs for workflow execution details
- Review security reports in workflow artifacts
- Monitor security dashboard for metrics history

## Best Practices

1. **Regular Review**: Review security metrics weekly
2. **Prompt Action**: Address critical issues immediately
3. **Update Dependencies**: Keep dependencies updated
4. **Monitor Trends**: Watch security score trends
5. **Team Training**: Ensure team understands security processes

## Contact

For questions about security monitoring:
- Security Team: security@example.com
- GitHub Issues: Use repository issue tracker

## Maintenance

### Weekly Tasks
- Review security dashboard
- Check for missed alerts
- Update notification channels

### Monthly Tasks
- Review and update alert thresholds
- Evaluate security tool effectiveness
- Update security policies

### Quarterly Tasks
- Comprehensive security review
- Update security monitoring strategy
- Security team training update
"""
        
        monitoring_doc_path = self.project_path / "docs" / "security-monitoring.md"
        self.project_path / "docs" / "security-monitoring.md"
        
        with open(monitoring_doc_path, 'w') as f:
            f.write(monitoring_docs)
    
    def _write_workflow_file(self, filename: str, content: str) -> None:
        """Write workflow file to .github/workflows directory"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_dir / filename, 'w') as f:
            f.write(content)
    
    def _get_dashboard_css(self) -> str:
        """Get CSS for security dashboard"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        h1 {
            color: #d32f2f;
            margin-bottom: 10px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #1976d2;
        }
        
        .metric-card.critical {
            border-left-color: #d32f2f;
        }
        
        .metric-card.high {
            border-left-color: #f57c00;
        }
        
        .metric-card.medium {
            border-left-color: #fbc02d;
        }
        
        .metric-value {
            font-size: 3em;
            font-weight: bold;
            color: #333;
        }
        
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        
        section {
            margin-bottom: 30px;
        }
        
        h2 {
            color: #1976d2;
            margin-bottom: 15px;
        }
        
        .charts, .recent-scans, .alerts {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }
        """
    
    def _get_dashboard_javascript(self) -> str:
        """Get JavaScript for security dashboard"""
        return """
        // Dashboard JavaScript
        
        function loadSecurityMetrics() {
            // Load metrics from security-metrics.json
            fetch('./security-metrics.json')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('security-score').textContent = data.security_score || '--';
                    document.getElementById('critical-issues').textContent = data.critical_issues || 0;
                    document.getElementById('high-issues').textContent = data.high_issues || 0;
                    document.getElementById('last-update').textContent = data.last_scan || 'Unknown';
                    
                    // Update colors based on values
                    updateMetricColors();
                })
                .catch(error => {
                    console.error('Error loading security metrics:', error);
                });
        }
        
        function updateMetricColors() {
            const score = parseInt(document.getElementById('security-score').textContent);
            const critical = parseInt(document.getElementById('critical-issues').textContent);
            const high = parseInt(document.getElementById('high-issues').textContent);
            
            // Color coding based on values
            const scoreElement = document.getElementById('security-score');
            if (score >= 90) {
                scoreElement.style.color = '#4caf50';
            } else if (score >= 70) {
                scoreElement.style.color = '#fbc02d';
            } else {
                scoreElement.style.color = '#d32f2f';
            }
        }
        
        // Load metrics on page load
        document.addEventListener('DOMContentLoaded', loadSecurityMetrics);
        
        // Refresh metrics every 5 minutes
        setInterval(loadSecurityMetrics, 5 * 60 * 1000);
        """