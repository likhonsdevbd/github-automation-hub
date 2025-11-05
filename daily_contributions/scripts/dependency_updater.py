#!/usr/bin/env python3
"""
Dependency Updater
Automatically checks for and updates project dependencies
"""

import os
import json
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

class DependencyUpdater:
    """Manages dependency updates across different package managers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.package_managers = self._detect_package_managers()
        self.last_update_file = ".last_dependency_update"
    
    def _detect_package_managers(self) -> Dict[str, bool]:
        """Detect which package managers are present in the project"""
        managers = {
            "pip": self._has_pip_requirements(),
            "npm": self._has_package_json(),
            "pipenv": self._has_pipfile(),
            "poetry": self._has_pyproject_toml(),
            "conda": self._has_conda_environment()
        }
        
        active_managers = {k: v for k, v in managers.items() if v}
        self.logger.info(f"Detected package managers: {list(active_managers.keys())}")
        return active_managers
    
    def _has_pip_requirements(self) -> bool:
        """Check if project uses pip requirements"""
        return Path("requirements.txt").exists() or Path("requirements-dev.txt").exists()
    
    def _has_package_json(self) -> bool:
        """Check if project uses npm"""
        return Path("package.json").exists()
    
    def _has_pipfile(self) -> bool:
        """Check if project uses Pipenv"""
        return Path("Pipfile").exists() or Path("Pipfile.lock").exists()
    
    def _has_pyproject_toml(self) -> bool:
        """Check if project uses Poetry"""
        return Path("pyproject.toml").exists()
    
    def _has_conda_environment(self) -> bool:
        """Check if project uses Conda"""
        return Path("environment.yml").exists() or Path("environment.yaml").exists()
    
    def get_pending_updates(self) -> List[Dict]:
        """Get list of pending dependency updates"""
        tasks = []
        
        if not self.package_managers:
            self.logger.info("No package managers detected")
            return tasks
        
        # Check if we should update based on timing
        if not self._should_check_for_updates():
            return tasks
        
        for manager in self.package_managers:
            if manager == "pip":
                update_task = self._check_pip_updates()
                if update_task:
                    tasks.append(update_task)
            
            elif manager == "npm":
                update_task = self._check_npm_updates()
                if update_task:
                    tasks.append(update_task)
            
            elif manager == "poetry":
                update_task = self._check_poetry_updates()
                if update_task:
                    tasks.append(update_task)
        
        # If no specific updates, suggest general dependency check
        if not tasks and self.package_managers:
            tasks.append({
                "type": "dependency_audit",
                "description": "Review and organize project dependencies",
                "priority": 4,
                "action": self._audit_dependencies
            })
        
        return tasks
    
    def _should_check_for_updates(self) -> bool:
        """Check if we should check for updates based on timing"""
        try:
            if not Path(self.last_update_file).exists():
                return True
            
            last_update = datetime.fromtimestamp(Path(self.last_update_file).stat().st_mtime)
            days_since_update = (datetime.now() - last_update).days
            
            # Check for updates every 7 days
            return days_since_update >= 7
        except Exception as e:
            self.logger.warning(f"Could not check update timing: {str(e)}")
            return True
    
    def _check_pip_updates(self) -> Optional[Dict]:
        """Check for pip package updates"""
        try:
            # Try to run pip list --outdated
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                outdated_packages = json.loads(result.stdout)
                if outdated_packages:
                    return {
                        "type": "pip_update",
                        "description": f"Update {len(outdated_packages)} outdated pip packages",
                        "priority": 2,
                        "action": self._update_pip_packages,
                        "packages": outdated_packages,
                        "manager": "pip"
                    }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError) as e:
            self.logger.warning(f"Could not check pip updates: {str(e)}")
        
        return None
    
    def _check_npm_updates(self) -> Optional[Dict]:
        """Check for npm package updates"""
        try:
            # Try to run npm outdated
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                outdated_packages = json.loads(result.stdout)
                if outdated_packages:
                    return {
                        "type": "npm_update",
                        "description": f"Update {len(outdated_packages)} outdated npm packages",
                        "priority": 2,
                        "action": self._update_npm_packages,
                        "packages": list(outdated_packages.keys()),
                        "manager": "npm"
                    }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError) as e:
            self.logger.warning(f"Could not check npm updates: {str(e)}")
        
        return None
    
    def _check_poetry_updates(self) -> Optional[Dict]:
        """Check for Poetry package updates"""
        try:
            # Try to run poetry show --outdated
            result = subprocess.run(
                ["poetry", "show", "--outdated"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                outdated_packages = len([line for line in lines if '→' in line])
                
                if outdated_packages > 0:
                    return {
                        "type": "poetry_update",
                        "description": f"Update {outdated_packages} outdated Poetry packages",
                        "priority": 2,
                        "action": self._update_poetry_packages,
                        "manager": "poetry"
                    }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.logger.warning(f"Could not check Poetry updates: {str(e)}")
        
        return None
    
    def _audit_dependencies(self, task: Dict) -> bool:
        """Audit and organize dependencies"""
        try:
            audit_content = self._generate_dependency_audit()
            with open("DEPENDENCY_AUDIT.md", 'w') as f:
                f.write(audit_content)
            
            self._update_last_update_time()
            self.logger.info("Generated dependency audit")
            return True
        except Exception as e:
            self.logger.error(f"Failed to audit dependencies: {str(e)}")
            return False
    
    def _update_pip_packages(self, task: Dict) -> bool:
        """Update pip packages"""
        try:
            packages = task.get('packages', [])
            if not packages:
                # Try to update all packages
                result = subprocess.run(
                    ["pip", "install", "--upgrade", "-r", "requirements.txt"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            else:
                # Update specific packages
                package_names = [pkg['name'] for pkg in packages[:5]]  # Limit to 5
                cmd = ["pip", "install", "--upgrade"] + package_names
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Regenerate requirements file if it exists
            if Path("requirements.txt").exists():
                subprocess.run(["pip", "freeze"], 
                             stdout=open("requirements.txt", "w"), 
                             stderr=subprocess.DEVNULL)
            
            self._update_last_update_time()
            self.logger.info("Updated pip packages")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update pip packages: {str(e)}")
            return False
    
    def _update_npm_packages(self, task: Dict) -> bool:
        """Update npm packages"""
        try:
            result = subprocess.run(
                ["npm", "update"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            self._update_last_update_time()
            self.logger.info("Updated npm packages")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update npm packages: {str(e)}")
            return False
    
    def _update_poetry_packages(self, task: Dict) -> bool:
        """Update Poetry packages"""
        try:
            result = subprocess.run(
                ["poetry", "update"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            self._update_last_update_time()
            self.logger.info("Updated Poetry packages")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update Poetry packages: {str(e)}")
            return False
    
    def _update_last_update_time(self):
        """Update the last update timestamp"""
        try:
            Path(self.last_update_file).touch()
        except Exception as e:
            self.logger.warning(f"Could not update timestamp: {str(e)}")
    
    def _generate_dependency_audit(self) -> str:
        """Generate dependency audit report"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        audit_sections = []
        
        # Add detected package managers
        audit_sections.append("## 📦 Detected Package Managers")
        for manager, present in self.package_managers.items():
            status = "✅ Active" if present else "❌ Not found"
            audit_sections.append(f"- **{manager.title()}**: {status}")
        
        # Analyze each package manager
        audit_sections.append("\n## 🔍 Dependency Analysis")
        
        if "pip" in self.package_managers:
            audit_sections.extend(self._analyze_pip_dependencies())
        
        if "npm" in self.package_managers:
            audit_sections.extend(self._analyze_npm_dependencies())
        
        if "poetry" in self.package_managers:
            audit_sections.extend(self._analyze_poetry_dependencies())
        
        # Add recommendations
        audit_sections.append("\n## 💡 Recommendations")
        audit_sections.extend([
            "1. Regularly update dependencies to get security patches",
            "2. Review dependency licenses for compliance",
            "3. Consider using dependency pinning for production",
            "4. Keep development and production dependencies separate",
            "5. Monitor for breaking changes in major version updates"
        ])
        
        audit_sections.append(f"\n---\n*Generated on {current_time}*")
        
        return "\n".join(audit_sections)
    
    def _analyze_pip_dependencies(self) -> List[str]:
        """Analyze pip dependencies"""
        sections = []
        
        if Path("requirements.txt").exists():
            with open("requirements.txt", 'r') as f:
                requirements = f.readlines()
            
            sections.append("\n### 🐍 Python Dependencies (pip)")
            sections.append(f"- Total packages: {len([r for r in requirements if r.strip() and not r.startswith('#')])}")
            
            # Check for pinning
            pinned = sum(1 for r in requirements if re.search(r'==', r) and r.strip())
            total = len([r for r in requirements if r.strip() and not r.startswith('#')])
            
            if pinned > 0:
                coverage = (pinned / total * 100) if total > 0 else 0
                sections.append(f"- Version pinned packages: {pinned}/{total} ({coverage:.1f}%)")
            
            if not pinned:
                sections.append("- ⚠️ Consider pinning versions for reproducibility")
        
        return sections
    
    def _analyze_npm_dependencies(self) -> List[str]:
        """Analyze npm dependencies"""
        sections = []
        
        if Path("package.json").exists():
            try:
                with open("package.json", 'r') as f:
                    package_data = json.load(f)
                
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                
                sections.append("\n### 🟢 Node.js Dependencies (npm)")
                sections.append(f"- Production dependencies: {len(deps)}")
                sections.append(f"- Development dependencies: {len(dev_deps)}")
                
                # Check for outdated packages
                sections.append("- Check for outdated packages regularly with `npm outdated`")
            except (json.JSONDecodeError, KeyError):
                sections.append("\n### 🟢 Node.js Dependencies (npm)")
                sections.append("- ⚠️ Could not analyze package.json")
        
        return sections
    
    def _analyze_poetry_dependencies(self) -> List[str]:
        """Analyze Poetry dependencies"""
        sections = []
        
        if Path("pyproject.toml").exists():
            sections.append("\n### 🎭 Python Dependencies (Poetry)")
            sections.append("- Using Poetry for dependency management")
            sections.append("- Run `poetry update` to check for updates")
        
        return sections
    
    def update_dependency(self, task: Dict) -> bool:
        """Update a specific dependency"""
        manager = task.get("manager")
        task_type = task.get("type")
        
        if task_type == "pip_update":
            return self._update_pip_packages(task)
        elif task_type == "npm_update":
            return self._update_npm_packages(task)
        elif task_type == "poetry_update":
            return self._update_poetry_packages(task)
        elif task_type == "dependency_audit":
            return self._audit_dependencies(task)
        
        return False