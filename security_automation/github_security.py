"""
GitHub Security Integration
Integrates security scanning with GitHub security features and workflows.
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import urlparse


class GitHubSecurity:
    """GitHub security features integration"""
    
    def __init__(self, repo_url: str, token: Optional[str] = None):
        self.repo_url = repo_url
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repo_owner, self.repo_name = self._parse_repo_url(repo_url)
        self.github_api_base = "https://api.github.com"
        
        if not self.token:
            print("Warning: No GitHub token provided. Some features may not work.")
        
    def setup_security_features(self) -> Dict[str, Any]:
        """Setup GitHub security features"""
        results = {
            'status': 'started',
            'features_configured': []
        }
        
        try:
            # 1. Create security policy
            self._create_security_policy()
            results['features_configured'].append('security_policy')
            
            # 2. Create Dependabot configuration
            self._create_dependabot_config()
            results['features_configured'].append('dependabot')
            
            # 3. Create security alert workflows
            self._create_security_workflows()
            results['features_configured'].append('security_workflows')
            
            # 4. Create CODEOWNERS file
            self._create_codeowners()
            results['features_configured'].append('codeowners')
            
            # 5. Setup secret scanning
            self._setup_secret_scanning()
            results['features_configured'].append('secret_scanning')
            
            # 6. Create vulnerability disclosure
            self._create_vulnerability_disclosure()
            results['features_configured'].append('vulnerability_disclosure')
            
            results['status'] = 'completed'
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _parse_repo_url(self, repo_url: str) -> tuple:
        """Parse GitHub repository URL to get owner and name"""
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
        else:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    def _create_security_policy(self) -> None:
        """Create SECURITY.md policy file"""
        policy_content = """# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of our project seriously. If you discover a security vulnerability, please follow these steps:

### Reporting Process

1. **Do not create a public GitHub issue** for security vulnerabilities
2. Email us at [security@example.com](mailto:security@example.com) with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours of receiving your report
- **Investigation**: Within 7 days
- **Resolution**: Timeline varies based on complexity and impact

### Disclosure Policy

- We ask that you give us reasonable time to investigate and fix the vulnerability
- We will acknowledge receipt of your vulnerability report
- We will provide updates on our progress

### Security Best Practices

When reporting vulnerabilities, please include:

- Clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested remediation (if applicable)

## Security Measures

Our project implements the following security measures:

- Automated dependency vulnerability scanning
- Code security analysis
- Regular security updates
- Secure coding practices review

## Recognition

We believe in giving credit where credit is due. If you responsibly disclose a security vulnerability, we will:

- Acknowledge your contribution (unless you prefer to remain anonymous)
- Include your name in our security hall of fame (if desired)

Thank you for helping keep our project and community safe!
"""
        
        self._write_file_to_repo("SECURITY.md", policy_content)
    
    def _create_dependabot_config(self) -> None:
        """Create Dependabot configuration"""
        config_content = """version: 2
updates:
  # Enable version updates for Python
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"
      time: "06:00"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    commit-message:
      prefix: "deps"
      include: "scope"
    
  # Enable version updates for Python development dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"
      time: "06:00"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    commit-message:
      prefix: "deps-dev"
      include: "scope"
    labels:
      - "dependencies"
      - "python"
      - "security"
    
  # Enable version updates for JavaScript/Node.js
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "daily"
      time: "06:00"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    commit-message:
      prefix: "deps-js"
      include: "scope"
    labels:
      - "dependencies"
      - "javascript"
      - "security"
    
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      time: "06:00"
    commit-message:
      prefix: "ci"
      include: "scope"
    labels:
      - "github-actions"
      - "automation"
"""
        
        self._write_file_to_repo(".github/dependabot.yml", config_content)
    
    def _create_security_workflows(self) -> None:
        """Create GitHub Actions workflows for security scanning"""
        
        # 1. Security scanning workflow
        security_workflow = """name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      actions: read
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install security tools
      run: |
        pip install --upgrade pip
        pip install semgrep bandit safety
        pip install flake8 black isort mypy pylint
        
    - name: Run comprehensive security scan
      run: |
        python security_automation/security_cli.py full-scan \\
          --project-path . \\
          --output-dir ./security-reports \\
          --format json
        
    - name: Upload security scan results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-scan-results
        path: security-reports/
        
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
      if: always()
      
    - name: Setup Node.js for npm audit
      uses: actions/setup-node@v3
      with:
        node-version: '16'
        
    - name: Run npm audit
      run: |
        if [ -f package.json ]; then
          npm audit --audit-level=high --json > npm-audit-results.json || true
          npm audit fix || true
        fi
        
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const path = './security-reports/security_summary_*.txt';
          const files = glob.sync(path);
          
          if (files.length > 0) {
            const summary = fs.readFileSync(files[0], 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Security Scan Results\\n\\n```' + summary + '```'
            });
          }
"""
        
        self._write_file_to_repo(".github/workflows/security-scan.yml", security_workflow)
        
        # 2. Dependency vulnerability workflow
        dep_workflow = """name: Dependency Security Check

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  dependency-check:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install safety pip-audit
        
    - name: Run Safety check
      run: |
        if find . -name "requirements*.txt" | grep -q .; then
          safety check --json --output safety-report.json || true
        fi
        
    - name: Run pip-audit
      run: |
        pip-audit --format=json --output=pip-audit-report.json || true
        
    - name: Setup Node.js for npm audit
      uses: actions/setup-node@v3
      with:
        node-version: '16'
        
    - name: Run npm audit
      if: hashFiles('package.json') != ''
      run: |
        npm audit --audit-level=moderate --json > npm-audit-full-report.json || true
        npm audit --json > npm-audit-security-report.json || true
        
    - name: Upload dependency reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: dependency-security-reports
        path: |
          safety-report.json
          pip-audit-report.json
          npm-audit-*.json
          
    - name: Check for high-severity vulnerabilities
      run: |
        echo "Checking for high-severity vulnerabilities..."
        # This would contain logic to fail the build if critical issues are found
        if [ -f safety-report.json ]; then
          HIGH_VULNS=$(cat safety-report.json | jq '.vulnerabilities | map(select(.severity == "high")) | length')
          if [ "$HIGH_VULNS" -gt 0 ]; then
            echo "::error::Found $HIGH_VULNS high-severity vulnerabilities"
            exit 1
          fi
        fi
"""
        
        self._write_file_to_repo(".github/workflows/dependency-security.yml", dep_workflow)
    
    def _create_codeowners(self) -> None:
        """Create CODEOWNERS file for security reviews"""
        codeowners_content = """# Global owners - these will be requested for review for all changes
* @security-team

# Security-related files
SECURITY.md @security-team
.github/dependabot.yml @security-team
.github/workflows/security-*.yml @security-team
.github/workflows/dependency-*.yml @security-team

# Infrastructure and configuration
*.ini @devops-team
*.yaml @devops-team
*.yml @devops-team
Dockerfile* @devops-team
docker-compose* @devops-team
terraform/ @devops-team
ansible/ @devops-team

# API and database changes
api/ @backend-team
src/models/ @backend-team
src/database/ @backend-team
*.sql @backend-team

# Frontend changes
frontend/ @frontend-team
src/components/ @frontend-team
src/pages/ @frontend-team

# Dependencies
package.json @security-team @maintainers
requirements*.txt @security-team @maintainers
Pipfile @security-team @maintainers
pyproject.toml @security-team @maintainers
poetry.lock @security-team @maintainers
"""
        
        self._write_file_to_repo(".github/CODEOWNERS", codeowners_content)
    
    def _setup_secret_scanning(self) -> None:
        """Setup GitHub secret scanning (this is mostly automatic for public repos)"""
        # Note: This is handled automatically by GitHub for most cases
        # We can document the setup and provide guidance
        
        secret_scanning_guide = """# Secret Scanning Setup

## GitHub Secret Scanning

GitHub automatically scans repositories for accidentally committed secrets:

### Supported Secret Types
- AWS Access Keys
- Google API keys
- GitHub personal access tokens
- Stripe API keys
- Twilio API keys
- And many more...

### Configuration
For private repositories, you may need to enable secret scanning in repository settings:

1. Go to repository Settings
2. Navigate to "Security" section
3. Enable "Secret scanning"

### Pre-commit Hooks

To prevent secrets from being committed in the first place:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### Setup Commands
```bash
pre-commit install
```

### For Advanced Secret Scanning
Consider using additional tools:
- GitLeaks
- TruffleHog
- GitGuardian
"""
        
        self._write_file_to_repo(".github/secret-scanning-guide.md", secret_scanning_guide)
    
    def _create_vulnerability_disclosure(self) -> None:
        """Create vulnerability disclosure documentation"""
        disclosure_content = """# Vulnerability Disclosure

## Reporting Security Issues

We take security seriously and appreciate the security community's efforts to responsibly disclose vulnerabilities to us.

### Scope
This vulnerability disclosure policy applies to all services and applications developed and maintained by our organization.

### How to Report
1. **Email**: Send details to security@example.com
2. **Encrypt**: Use our PGP key if available
3. **Include**: Detailed description, steps to reproduce, and potential impact

### What to Include
- Vulnerability description
- Steps to reproduce
- Potential impact assessment
- Suggested fixes (if any)
- Proof of concept (if applicable)

### Response Process
1. **Acknowledgment**: We respond within 48 hours
2. **Investigation**: We investigate and validate the issue
3. **Fix Development**: We develop and test fixes
4. **Public Disclosure**: We coordinate disclosure timeline
5. **Credit**: We acknowledge security researchers (if desired)

### Safe Harbor
We consider security research conducted under this policy to be:
- Authorized in accordance with applicable laws
- Exempt from DMCA takedown notices
- Exempt from circumvention provisions of applicable laws

### Recognition
We maintain a security hall of fame for researchers who responsibly disclose vulnerabilities.

### Questions
If you have questions about this policy, please contact us at security@example.com.
"""
        
        self._write_file_to_repo(".github/vulnerability-disclosure.md", disclosure_content)
    
    def _write_file_to_repo(self, file_path: str, content: str) -> None:
        """Write file to repository (simulated - in reality would use GitHub API)"""
        # In a real implementation, this would use the GitHub API to create/update files
        # For this demonstration, we'll create the files locally
        
        if not self.token:
            print(f"Warning: No GitHub token available. Would create: {file_path}")
            # Create file locally for demonstration
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            return
        
        try:
            # This is a simplified version - in reality, you'd use the GitHub API
            # For now, we'll create the files locally
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
                
            print(f"Created: {file_path}")
            
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
    
    def setup_branch_protection(self) -> Dict[str, Any]:
        """Setup branch protection rules for security"""
        protection_config = """# Branch Protection Configuration

## Recommended Branch Protection Rules

For the `main` branch, enable the following settings:

### Required Status Checks
- ✅ security-scan
- ✅ dependency-check
- ✅ code-quality
- ✅ tests
- ✅ linting

### Strict Status Checks
- Require branches to be up to date before merging
- Require status checks to pass before merging
- Require review from code owners

### Review Requirements
- Require at least 1 reviewer for code changes
- Require review from code owners for sensitive areas
- Dismiss stale reviews when new commits are pushed

### Restrictions
- Restrict pushes to main branch
- Allow administrators to bypass requirements (not recommended)

## API Configuration

You can also configure branch protection via GitHub API:

```bash
# Enable branch protection
curl -X PUT \\
  -H "Accept: application/vnd.github.v3+json" \\
  -H "Authorization: token YOUR_TOKEN" \\
  https://api.github.com/repos/OWNER/REPO/branches/main/protection \\
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["security-scan", "dependency-check"]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews": true
    },
    "restrictions": null
  }'
```

## Manual Setup Instructions

1. Go to repository Settings
2. Navigate to "Branches"
3. Click "Add rule" for main branch
4. Configure the following:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require pull request reviews before merging
   - ✅ Dismiss stale reviews
   - ✅ Require review from Code Owners
   - ✅ Restrict pushes to matching branches (optional)
"""
        
        # Create branch protection documentation
        self._write_file_to_repo(".github/branch-protection.md", protection_config)
        
        return {
            'status': 'completed',
            'message': 'Branch protection configuration documentation created',
            'config_file': '.github/branch-protection.md'
        }
    
    def create_security_advisories(self) -> Dict[str, Any]:
        """Create security advisory templates and workflow"""
        
        # Security advisory workflow
        advisory_workflow = """name: Security Advisory

on:
  issues:
    types: [opened]
  pull_request:
    types: [opened]

jobs:
  security-advisory:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.title, '[SECURITY]') || contains(github.event.pull_request.title, '[SECURITY]')
    
    steps:
    - name: Security Advisory Label
      uses: actions/github-script@v6
      with:
        script: |
          const { owner, repo } = context.repo;
          const issue_number = context.issue.number;
          
          github.rest.issues.addLabels({
            owner,
            repo,
            issue_number,
            labels: ['security', 'advisory']
          });
          
    - name: Notify Security Team
      run: |
        echo "Security advisory detected. Notifying security team..."
        # In a real implementation, this would send notifications
        # to Slack, email, or other communication channels
"""
        
        self._write_file_to_repo(".github/workflows/security-advisory.yml", advisory_workflow)
        
        # Security issue templates
        security_issue_template = """---
name: Security Vulnerability
about: Report a security vulnerability
title: '[SECURITY] '
labels: ['security', 'vulnerability']
assignees: ['security-team']

---

<!--
IMPORTANT: Do not include sensitive information in this issue.

For sensitive security reports, please email security@example.com
instead of creating a public GitHub issue.
-->

## Vulnerability Description
<!-- Describe the vulnerability -->

## Affected Version
<!-- Which versions are affected -->

## Steps to Reproduce
<!-- How can someone reproduce this issue -->

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->

## Environment
- OS: 
- Version: 
- Browser (if applicable): 

## Additional Context
<!-- Add any other context about the problem here -->

## Severity Assessment
<!--
- Critical: System compromise, data loss
- High: Significant security impact
- Medium: Minor security impact
- Low: Minimal security impact
-->
"""
        
        self._write_file_to_repo(".github/ISSUE_TEMPLATE/security_vulnerability.md", security_issue_template)
        
        # Security PR template
        security_pr_template = """## Security Considerations

<!--
Check all that apply to this pull request
-->

- [ ] This PR does not introduce any security vulnerabilities
- [ ] This PR addresses a security vulnerability
- [ ] This PR has been reviewed for security implications
- [ ] Dependencies have been reviewed for security issues

## Security Changes

<!-- Describe any security-related changes -->

## Testing

<!-- How has this been tested for security implications -->

## Related Issues

<!-- Link to any related security issues -->
"""
        
        self._write_file_to_repo(".github/PULL_REQUEST_TEMPLATE/security.md", security_pr_template)
        
        return {
            'status': 'completed',
            'files_created': [
                '.github/workflows/security-advisory.yml',
                '.github/ISSUE_TEMPLATE/security_vulnerability.md',
                '.github/PULL_REQUEST_TEMPLATE/security.md'
            ]
        }
    
    def setup_security_monitoring(self) -> Dict[str, Any]:
        """Setup ongoing security monitoring configurations"""
        
        # Security monitoring workflow
        monitoring_workflow = """name: Continuous Security Monitoring

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  security-monitoring:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
        
    - name: Security monitoring scan
      run: |
        echo "Running continuous security monitoring..."
        python security_automation/security_cli.py full-scan --project-path . --format json
        
    - name: Security metrics
      run: |
        echo "Collecting security metrics..."
        # Extract metrics from scan results
        # Example: count of critical, high, medium, low issues
        
    - name: Security trend analysis
      if: github.ref == 'refs/heads/main'
      run: |
        echo "Analyzing security trends..."
        # Compare with previous scans
        # Generate trend reports
        
    - name: Security dashboard update
      if: github.ref == 'refs/heads/main'
      run: |
        echo "Updating security dashboard..."
        # Update security metrics dashboard
        # This could update a GitHub Pages site with security metrics
        
    - name: Alert on critical issues
      if: failure() || contains(github.event.head_commit.message, '[SECURITY CRITICAL]')
      run: |
        echo "Critical security issues detected!"
        # Send alerts to security team
        # This could post to Slack, email, etc.
"""
        
        self._write_file_to_repo(".github/workflows/security-monitoring.yml", monitoring_workflow)
        
        # Security metrics dashboard
        dashboard_config = """# Security Metrics Dashboard

## Setup GitHub Pages for Security Dashboard

1. Create a GitHub Pages site in your repository settings
2. Use the `gh-pages` branch for the dashboard
3. Add a workflow to update the dashboard daily

## Dashboard Content

### Security Metrics
- Number of open security vulnerabilities
- Vulnerability severity distribution
- Dependency vulnerability trends
- Code quality metrics
- Security scan frequency

### Visualization Options
- GitHub Issues for tracking
- GitHub Actions badges for CI status
- Custom HTML/CSS dashboard
- Third-party security dashboards

## Update Frequency
Daily via GitHub Actions workflow

## Access Control
- Repository maintainers and security team
- Read-only access for other team members
"""
        
        self._write_file_to_repo(".github/security-dashboard.md", dashboard_config)
        
        return {
            'status': 'completed',
            'files_created': [
                '.github/workflows/security-monitoring.yml',
                '.github/security-dashboard.md'
            ]
        }
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status of the repository"""
        if not self.token:
            return {
                'status': 'no_token',
                'message': 'GitHub token required for API access'
            }
        
        try:
            # This would use the GitHub API to get repository security features status
            # For demonstration, we'll return a mock response
            
            return {
                'status': 'success',
                'features': {
                    'secret_scanning': 'enabled',
                    'dependency_graph': 'enabled',
                    'dependabot_alerts': 'enabled',
                    'code_scanning': 'not_configured',
                    'vulnerability_alerts': 'enabled'
                },
                'security_score': 85,
                'recommendations': [
                    'Enable CodeQL analysis',
                    'Configure branch protection rules',
                    'Set up security policy'
                ]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }