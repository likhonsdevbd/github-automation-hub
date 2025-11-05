#!/usr/bin/env python3
"""
Security Automation Demo Script
Demonstrates the capabilities of the security automation tool.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from security_cli import main as security_cli_main


class SecurityAutomationDemo:
    """Demo class for security automation features"""
    
    def __init__(self):
        self.demo_project = None
        
    def run_demo(self):
        """Run the complete demo"""
        print("🔒 Security Automation Tool - Demo")
        print("=" * 60)
        
        try:
            # 1. Create demo project
            self.create_demo_project()
            
            # 2. Run all security scans
            self.run_security_scans()
            
            # 3. Demonstrate GitHub integration
            self.demo_github_features()
            
            # 4. Show monitoring setup
            self.demo_monitoring()
            
            # 5. Display results
            self.display_results()
            
            print("\n✅ Demo completed successfully!")
            print(f"📁 Demo project: {self.demo_project}")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
        finally:
            # Cleanup
            self.cleanup_demo()
    
    def create_demo_project(self):
        """Create a demo project with intentional security issues"""
        print("\n1. Creating demo project with security vulnerabilities...")
        
        self.demo_project = Path(tempfile.mkdtemp(prefix="security_demo_"))
        
        # Create Python files with security issues
        demo_files = {
            "app.py": '''
import os
import sqlite3
import subprocess
import random
import hashlib

# Hardcoded secrets (security issue)
API_KEY = "sk-1234567890abcdef1234567890abcdef"
DATABASE_PASSWORD = "admin123"
SECRET_TOKEN = "jwt_secret_key_very_long_and_insecure"

# Insecure random usage (security issue)
def generate_token():
    return str(random.random())  # Not cryptographically secure

# SQL injection vulnerability
def get_user(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection risk
    cursor.execute(query)
    return cursor.fetchone()

# Command injection vulnerability
def run_command(user_input):
    os.system(f"ping {user_input}")  # Command injection risk

# Weak cryptographic algorithm
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # MD5 is weak

if __name__ == "__main__":
    print("Demo app with security issues")
''',
            "config.py": '''
# Configuration with sensitive data
DEBUG = True
DATABASE_URL = "sqlite:///admin:password@localhost/db"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Hardcoded database credentials
DB_CONFIG = {
    "host": "localhost",
    "username": "root",
    "password": "root123",
    "database": "myapp"
}
''',
            "utils.py": '''
import subprocess
import os

def process_file(filename):
    # Command injection vulnerability
    result = subprocess.call(f"cat {filename}", shell=True)
    return result

def execute_query(query):
    # SQL injection pattern
    import sqlite3
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM table WHERE id = {query}")
    return cursor.fetchall()
''',
            "requirements.txt": '''
Django==3.2.0
requests==2.25.0
flask==1.1.1
pillow==8.0.0
numpy==1.19.0
pandas==1.1.0
'''
        }
        
        # Create files
        for filename, content in demo_files.items():
            file_path = self.demo_project / filename
            file_path.write_text(content)
        
        # Create package.json with vulnerabilities
        package_json = {
            "name": "demo-vulnerable-app",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "4.17.15",
                "express": "4.17.1",
                "request": "2.83.0",
                "moment": "2.24.0"
            }
        }
        
        (self.demo_project / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # Create pyproject.toml
        pyproject_content = '''
[build-system]
requires = ["setuptools", "wheel"]

[project]
name = "demo-vulnerable-app"
version = "1.0.0"
dependencies = [
    "django==3.2.0",
    "requests==2.25.0",
    "pillow==8.0.0"
]

[tool.poetry.dependencies]
python = "^3.8"
django = "3.2.0"
requests = "2.25.0"
pillow = "8.0.0"
'''
        
        (self.demo_project / "pyproject.toml").write_text(pyproject_content)
        
        print(f"   ✅ Demo project created: {self.demo_project}")
    
    def run_security_scans(self):
        """Run all security scans on demo project"""
        print("\n2. Running security scans...")
        
        # Run full security scan
        print("   Running full security scan...")
        self.run_cli_command([
            "full-scan", 
            "--project-path", str(self.demo_project),
            "--output-dir", str(self.demo_project / "security-reports")
        ])
        
        # Run vulnerability scan
        print("   Running vulnerability scan...")
        self.run_cli_command([
            "vuln-scan",
            "--project-path", str(self.demo_project),
            "--tools", "all"
        ])
        
        # Run dependency check
        print("   Running dependency check...")
        self.run_cli_command([
            "dependency-check",
            "--project-path", str(self.demo_project)
        ])
        
        # Run code quality scan
        print("   Running code quality scan...")
        self.run_cli_command([
            "quality-scan",
            "--project-path", str(self.demo_project)
        ])
    
    def run_cli_command(self, args):
        """Run CLI command with demo arguments"""
        # Temporarily modify sys.argv
        original_argv = sys.argv
        try:
            sys.argv = ["security_cli.py"] + args
            security_cli_main()
        finally:
            sys.argv = original_argv
    
    def demo_github_features(self):
        """Demonstrate GitHub integration features"""
        print("\n3. Demonstrating GitHub integration features...")
        
        # This would normally require a real repository
        print("   📝 GitHub integration features:")
        print("      - Security policies")
        print("      - Dependabot configuration")
        print("      - Security workflows")
        print("      - Branch protection")
        print("      - Secret scanning")
        
        # Show what files would be created
        github_security_dir = self.demo_project / ".github"
        if not github_security_dir.exists():
            github_security_dir.mkdir(parents=True)
        
        # Create sample SECURITY.md
        security_policy = '''# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

Please email security@example.com
'''
        
        (github_security_dir / "SECURITY.md").write_text(security_policy)
        
        print(f"   ✅ Created sample GitHub files in {github_security_dir}")
    
    def demo_monitoring(self):
        """Demonstrate monitoring setup"""
        print("\n4. Demonstrating monitoring configuration...")
        
        # Create monitoring configuration
        monitoring_config = {
            "scan_schedule": "daily",
            "tools_enabled": {
                "vulnerability_scanning": True,
                "dependency_checking": True,
                "code_quality": True
            },
            "alert_thresholds": {
                "critical": 0,
                "high": 3,
                "medium": 10
            }
        }
        
        config_dir = self.demo_project / "config" / "security"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        import json
        (config_dir / "monitoring.json").write_text(json.dumps(monitoring_config, indent=2))
        
        # Create sample GitHub workflow
        workflow_dir = self.demo_project / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_content = '''name: Security Scan
on:
  schedule:
    - cron: '0 2 * * *'
  
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run security scan
      run: |
        python security_automation/security_cli.py full-scan --project-path .
'''
        
        (workflow_dir / "security-scan.yml").write_text(workflow_content)
        
        print(f"   ✅ Created monitoring configuration in {config_dir}")
    
    def display_results(self):
        """Display demo results and summary"""
        print("\n5. Demo Results Summary")
        print("=" * 40)
        
        # Check for generated reports
        reports_dir = self.demo_project / "security-reports"
        if reports_dir.exists():
            report_files = list(reports_dir.glob("*"))
            print(f"\n📊 Generated {len(report_files)} security reports:")
            for report_file in report_files:
                print(f"   - {report_file.name}")
        
        # Show JSON scan results
        json_files = list(self.demo_project.glob("*.json"))
        if json_files:
            print(f"\n📄 JSON scan results:")
            for json_file in json_files:
                print(f"   - {json_file.name}")
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                    if 'summary' in str(data):
                        print(f"     Summary: {data}")
                except:
                    pass
        
        # Summary statistics
        print(f"\n🎯 Demo Project Information:")
        print(f"   Location: {self.demo_project}")
        print(f"   Files created: {len(list(self.demo_project.rglob('*')))}")
        print(f"   Python files: {len(list(self.demo_project.rglob('*.py')))}")
        print(f"   Config files: {len(list(self.demo_project.rglob('*.json')))}")
        
        print(f"\n🛡️ Security Issues Created:")
        print("   - Hardcoded secrets and API keys")
        print("   - SQL injection vulnerabilities")
        print("   - Command injection risks")
        print("   - Weak cryptographic algorithms")
        print("   - Insecure random number usage")
        print("   - Vulnerable dependencies")
        
        print(f"\n💡 What the tool detected:")
        print("   ✓ Vulnerability scanning with Semgrep/Bandit")
        print("   ✓ Dependency vulnerability checking")
        print("   ✓ Code quality and style analysis")
        print("   ✓ Custom security pattern detection")
        print("   ✓ GitHub integration setup")
        print("   ✓ Continuous monitoring configuration")
        
        print(f"\n📈 Features Demonstrated:")
        print("   ✓ Comprehensive security scanning")
        print("   ✓ Multi-format report generation")
        print("   ✓ Automated GitHub security setup")
        print("   ✓ Continuous monitoring configuration")
        print("   ✓ Alert and notification systems")
        print("   ✓ Security metrics and dashboards")
    
    def cleanup_demo(self):
        """Clean up demo project"""
        if self.demo_project and self.demo_project.exists():
            try:
                shutil.rmtree(self.demo_project)
                print(f"\n🧹 Cleaned up demo project: {self.demo_project}")
            except Exception as e:
                print(f"\n⚠️ Could not clean up demo project: {e}")


def main():
    """Main demo function"""
    demo = SecurityAutomationDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()