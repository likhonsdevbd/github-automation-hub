#!/usr/bin/env python3
"""
Setup and Installation Script for Daily Commit Automation
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import logging

class AutomationSetup:
    """Setup and configure daily commit automation"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.logger = self._setup_logging()
        self.setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def setup_logging(self):
        """Setup application logging"""
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "level": "INFO",
                    "formatter": "standard",
                    "class": "logging.StreamHandler"
                },
                "file": {
                    "level": "DEBUG",
                    "formatter": "standard",
                    "class": "logging.FileHandler",
                    "filename": "setup.log",
                    "mode": "a"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": "DEBUG",
                    "propagate": False
                }
            }
        }
        
        with open("log_config.json", "w") as f:
            json.dump(log_config, f, indent=2)
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        if sys.version_info < (3, 7):
            self.logger.error("Python 3.7 or higher is required")
            return False
        
        self.logger.info(f"Python version: {sys.version}")
        return True
    
    def install_dependencies(self):
        """Install required Python packages"""
        dependencies = [
            "black>=22.0.0",
            "isort>=5.10.0", 
            "flake8>=5.0.0",
            "pylint>=2.15.0",
            "mypy>=1.0.0",
            "pytz>=2022.0",
            "requests>=2.25.0"
        ]
        
        self.logger.info("Installing Python dependencies...")
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                self.logger.info(f"✅ Installed {dep}")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"⚠️ Failed to install {dep}: {str(e)}")
    
    def detect_project_type(self):
        """Detect the project type to customize configuration"""
        project_indicators = {
            "python": [".py", "requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "javascript": ["package.json", ".js", ".jsx", ".ts", ".tsx"],
            "go": [".go", "go.mod", "go.sum"],
            "rust": [".rs", "Cargo.toml", "Cargo.lock"],
            "java": [".java", "pom.xml", "build.gradle"],
            "c++": [".cpp", ".hpp", ".c", ".h", "CMakeLists.txt"]
        }
        
        detected = []
        for project_type, indicators in project_indicators.items():
            if any(Path(".").glob(f"**/{indicator}") for indicator in indicators):
                detected.append(project_type)
        
        self.logger.info(f"Detected project types: {detected}")
        return detected
    
    def customize_config(self, project_types):
        """Customize configuration based on project type"""
        config_path = self.base_path / "config" / "automation_config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Customize based on detected project types
        if "python" in project_types:
            config["modules"]["code_quality"]["enabled"] = True
            config["modules"]["repo_health"]["aggressive_mode"] = True
            
        if "javascript" in project_types or "typescript" in project_types:
            config["modules"]["code_quality"]["enabled"] = True
            config["customization"]["priority_file_patterns"].extend(["*.js", "*.ts", "*.jsx", "*.tsx"])
            
        # Update limits based on project size
        try:
            python_files = len(list(Path(".").glob("**/*.py")))
            if python_files > 100:
                config["limits"]["max_daily_commits"] = 8
                config["limits"]["max_file_changes"] = 15
        except:
            pass
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info("✅ Configuration customized for your project")
    
    def setup_git_hooks(self):
        """Setup Git hooks for pre-commit quality checks"""
        hooks_dir = Path(".git/hooks")
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Pre-commit hook
        pre_commit_script = """#!/bin/bash
# Pre-commit hook for Daily Commit Automation

echo "Running pre-commit quality checks..."

# Change to automation directory
cd code/automation-hub/daily_contributions

# Run quick quality check
python -c "
import sys
sys.path.append('scripts')
from code_quality_tool import CodeQualityTool
from repo_health_checker import RepoHealthChecker

print('Checking code quality...')
tool = CodeQualityTool()
tasks = tool.get_improvement_tasks()
if tasks:
    print(f'Found {len(tasks)} quality improvements')
else:
    print('Code quality looks good!')

print('Checking repository health...')
health = RepoHealthChecker()
health_tasks = health.get_improvement_tasks()
if health_tasks:
    print(f'Found {len(health_tasks)} health improvements')
else:
    print('Repository health looks good!')
"

# Don't block commits, just warn
echo "Quality check completed. Run 'python main_coordinator.py --interactive' for improvements."
"""
        
        with open(hooks_dir / "pre-commit", "w") as f:
            f.write(pre_commit_script)
        
        # Make hook executable
        os.chmod(hooks_dir / "pre-commit", 0o755)
        self.logger.info("✅ Git pre-commit hook installed")
    
    def create_sample_files(self):
        """Create sample configuration files"""
        sample_configs = {
            ".flake8": """[flake8]
max-line-length = 88
select = E,W,F
ignore = E203, E501, W503
exclude = .git, __pycache__, venv, .venv, build, dist, *.egg-info
max-complexity = 10
""",
            ".prettierrc": """{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
""",
            ".editorconfig": """# EditorConfig is awesome

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.json]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
"""
        }
        
        for filename, content in sample_configs.items():
            if not Path(filename).exists():
                with open(filename, "w") as f:
                    f.write(content)
                self.logger.info(f"✅ Created {filename}")
    
    def validate_setup(self):
        """Validate the setup is working correctly"""
        self.logger.info("Validating setup...")
        
        # Test basic imports
        try:
            sys.path.append(str(self.base_path))
            from main_coordinator import DailyCommitCoordinator
            coordinator = DailyCommitCoordinator()
            self.logger.info("✅ Core modules imported successfully")
        except Exception as e:
            self.logger.error(f"❌ Import error: {str(e)}")
            return False
        
        # Test configuration loading
        try:
            config = coordinator.load_config()
            assert isinstance(config, dict)
            self.logger.info("✅ Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"❌ Configuration error: {str(e)}")
            return False
        
        # Test basic functionality
        try:
            tasks = coordinator.get_pending_tasks()
            self.logger.info(f"✅ Found {len(tasks)} initial tasks")
        except Exception as e:
            self.logger.warning(f"⚠️ Task detection issue (this is normal): {str(e)}")
        
        return True
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n" + "="*60)
        print("🎉 DAILY COMMIT AUTOMATION SETUP COMPLETE!")
        print("="*60)
        print("\n📋 Next Steps:")
        print("1. Review configuration:")
        print("   code/automation-hub/daily_contributions/config/automation_config.json")
        print("\n2. Test the automation:")
        print("   cd code/automation-hub/daily_contributions")
        print("   python main_coordinator.py --interactive")
        print("\n3. Setup GitHub Actions (optional):")
        print("   - Copy workflows/daily_automation.yml to .github/workflows/")
        print("   - Configure GitHub Actions in your repository")
        print("\n4. Run first automation cycle:")
        print("   python main_coordinator.py")
        print("\n5. Monitor automation:")
        print("   - Check daily_contributions.log")
        print("   - Review .commit_history.json")
        print("\n📚 Documentation:")
        print("   - README.md")
        print("   - docs/ (generated documentation)")
        print("\n🛠️ Configuration:")
        print("   - Modify config/automation_config.json for customization")
        print("   - Add your own scripts in scripts/ directory")
        print("\n💡 Tips:")
        print("   - Use --dry-run first to test changes")
        print("   - Check .gitignore to exclude unwanted files")
        print("   - Customize timing in config for your schedule")
        print("\n" + "="*60)
    
    def run_setup(self):
        """Run the complete setup process"""
        self.logger.info("Starting Daily Commit Automation setup...")
        
        # Check Python version
        if not self.check_python_version():
            sys.exit(1)
        
        # Install dependencies
        self.install_dependencies()
        
        # Detect project type
        project_types = self.detect_project_type()
        
        # Customize configuration
        self.customize_config(project_types)
        
        # Setup Git hooks
        self.setup_git_hooks()
        
        # Create sample files
        self.create_sample_files()
        
        # Validate setup
        if self.validate_setup():
            self.print_next_steps()
            return True
        else:
            self.logger.error("Setup validation failed. Please check the logs.")
            return False

def main():
    """Main setup function"""
    setup = AutomationSetup()
    success = setup.run_setup()
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()