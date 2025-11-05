#!/bin/bash
"""
Security Automation Setup Script
Automated setup and installation of the Security Automation Tool.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class SecurityAutomationSetup:
    """Setup class for Security Automation Tool"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.platform = platform.system().lower()
        self.python_executable = sys.executable
        
    def run_setup(self):
        """Run the complete setup process"""
        print("🔒 Security Automation Tool Setup")
        print("=" * 50)
        
        try:
            # 1. Check Python version
            self.check_python_version()
            
            # 2. Install core dependencies
            self.install_core_dependencies()
            
            # 3. Install optional security tools
            self.install_security_tools()
            
            # 4. Setup GitHub integration
            self.setup_github_integration()
            
            # 5. Create configuration files
            self.create_configurations()
            
            # 6. Test installation
            self.test_installation()
            
            # 7. Display next steps
            self.show_next_steps()
            
            print("\n✅ Security Automation Tool setup completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            print("❌ Python 3.7+ is required")
            sys.exit(1)
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    
    def install_core_dependencies(self):
        """Install core dependencies"""
        print("\nInstalling core dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            sys.exit(1)
        
        try:
            subprocess.run([
                self.python_executable, "-m", "pip", "install", 
                "-r", str(requirements_file), "--upgrade"
            ], check=True, capture_output=True)
            print("✅ Core dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install core dependencies: {e}")
            sys.exit(1)
    
    def install_security_tools(self):
        """Install optional security tools"""
        print("\nInstalling security tools...")
        
        tools = [
            ("semgrep", "pip install semgrep"),
            ("bandit", "pip install bandit"),
            ("safety", "pip install safety"),
            ("flake8", "pip install flake8"),
            ("black", "pip install black"),
            ("isort", "pip install isort"),
            ("mypy", "pip install mypy"),
            ("pylint", "pip install pylint"),
            ("radon", "pip install radon"),
            ("vulture", "pip install vulture")
        ]
        
        installed_tools = []
        
        for tool_name, install_cmd in tools:
            try:
                print(f"  Installing {tool_name}...")
                subprocess.run(install_cmd.split(), check=True, capture_output=True)
                installed_tools.append(tool_name)
                print(f"  ✅ {tool_name} installed")
            except subprocess.CalledProcessError:
                print(f"  ⚠️ {tool_name} installation failed (optional)")
        
        print(f"\n✅ Installed {len(installed_tools)} security tools")
        if installed_tools:
            print(f"   Installed: {', '.join(installed_tools)}")
    
    def setup_github_integration(self):
        """Setup GitHub integration configuration"""
        print("\nSetting up GitHub integration...")
        
        # Check if GitHub CLI is available
        try:
            subprocess.run(["gh", "--version"], check=True, capture_output=True)
            github_cli_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            github_cli_available = False
        
        if github_cli_available:
            print("✅ GitHub CLI detected")
            print("   You can authenticate with: gh auth login")
        else:
            print("ℹ️ GitHub CLI not found")
            print("   Install from: https://cli.github.com/")
        
        # Check for GitHub token
        if os.getenv('GITHUB_TOKEN'):
            print("✅ GitHub token found in environment")
        else:
            print("⚠️ No GitHub token found")
            print("   Set GITHUB_TOKEN environment variable for GitHub integration")
    
    def create_configurations(self):
        """Create configuration files"""
        print("\nCreating configuration files...")
        
        # Create config directory
        config_dir = self.project_root / "config" / "security"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample alerting configuration
        self.create_alerting_config(config_dir)
        
        # Create sample monitoring configuration
        self.create_monitoring_config(config_dir)
        
        # Create pre-commit hook configuration
        self.create_precommit_config()
        
        print("✅ Configuration files created")
    
    def create_alerting_config(self, config_dir):
        """Create sample alerting configuration"""
        alerting_config = {
            "notification_channels": {
                "email": {
                    "enabled": False,
                    "recipients": ["security@example.com"],
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
                    "actions": ["create_github_issue"]
                }
            ]
        }
        
        import json
        config_file = config_dir / "alerting.json"
        with open(config_file, 'w') as f:
            json.dump(alerting_config, f, indent=2)
        
        print(f"  Created: {config_file}")
    
    def create_monitoring_config(self, config_dir):
        """Create sample monitoring configuration"""
        monitoring_config = {
            "scan_schedule": "daily",
            "tools_enabled": {
                "vulnerability_scanning": True,
                "dependency_checking": True,
                "code_quality": True
            },
            "severity_thresholds": {
                "critical": 0,
                "high": 5,
                "medium": 15
            },
            "reporting": {
                "formats": ["json", "html"],
                "output_directory": "./security-reports"
            }
        }
        
        import json
        config_file = config_dir / "monitoring.json"
        with open(config_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        print(f"  Created: {config_file}")
    
    def create_precommit_config(self):
        """Create pre-commit configuration"""
        precommit_config = """repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package.lock.json
  
  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/isort
    rev: 5.11.3
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
"""
        
        config_file = self.project_root / ".pre-commit-config.yaml"
        with open(config_file, 'w') as f:
            f.write(precommit_config)
        
        print(f"  Created: {config_file}")
    
    def test_installation(self):
        """Test the installation"""
        print("\nTesting installation...")
        
        try:
            # Test CLI import
            sys.path.insert(0, str(self.project_root))
            import vulnerability_scanner
            import dependency_checker
            import code_quality_scanner
            import security_reporter
            
            print("✅ All modules imported successfully")
            
            # Test CLI command
            result = subprocess.run([
                self.python_executable, 
                str(self.project_root / "security_cli.py"), 
                "--help"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ CLI command working")
            else:
                print("⚠️ CLI command test failed")
                
        except ImportError as e:
            print(f"❌ Import test failed: {e}")
            sys.exit(1)
    
    def show_next_steps(self):
        """Show next steps for the user"""
        print("\n" + "=" * 50)
        print("🚀 NEXT STEPS")
        print("=" * 50)
        
        print("\n1. Quick Start:")
        print("   python security_cli.py full-scan --project-path .")
        
        print("\n2. Set up GitHub integration:")
        print("   python security_cli.py github-setup --repo-url https://github.com/username/repo")
        
        print("\n3. Configure monitoring:")
        print("   python security_cli.py setup-monitoring --project-path . --schedule daily")
        
        print("\n4. Install pre-commit hooks (optional):")
        print("   pip install pre-commit")
        print("   pre-commit install")
        
        print("\n5. Configure notifications:")
        print(f"   Edit: {self.project_root}/config/security/alerting.json")
        
        print("\n6. Add to CI/CD pipeline:")
        print("   Copy GitHub Actions workflows from .github/workflows/")
        
        print("\n7. View documentation:")
        print(f"   Read: {self.project_root}/README.md")
        
        print("\n8. Security tools reference:")
        print("   - Semgrep: https://semgrep.dev/")
        print("   - Bandit: https://bandit.readthedocs.io/")
        print("   - Safety: https://pyup.io/safety/")
        
        print("\n🔧 Configuration files created:")
        print(f"   - Alerting: {self.project_root}/config/security/alerting.json")
        print(f"   - Monitoring: {self.project_root}/config/security/monitoring.json")
        print(f"   - Pre-commit: {self.project_root}/.pre-commit-config.yaml")
        
        print("\n📚 Need help? Check the README.md for detailed documentation")
    
    def uninstall(self):
        """Uninstall security automation tool"""
        print("🔄 Uninstalling Security Automation Tool...")
        
        # Remove installed packages
        tools = [
            "semgrep", "bandit", "safety", "flake8", "black", 
            "isort", "mypy", "pylint", "radon", "vulture"
        ]
        
        for tool in tools:
            try:
                subprocess.run([self.python_executable, "-m", "pip", "uninstall", "-y", tool], 
                             check=True, capture_output=True)
                print(f"  Removed: {tool}")
            except subprocess.CalledProcessError:
                print(f"  Not installed: {tool}")
        
        print("✅ Uninstall completed")


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Automation Tool Setup")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the tool")
    
    args = parser.parse_args()
    
    setup = SecurityAutomationSetup()
    
    if args.uninstall:
        setup.uninstall()
    else:
        setup.run_setup()


if __name__ == "__main__":
    main()