#!/usr/bin/env python3
"""
Daily Commit Automation Coordinator
Main orchestrator for automated repository contributions
"""

import os
import sys
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from repo_health_checker import RepoHealthChecker
from dependency_updater import DependencyUpdater
from doc_automation import DocumentationAutomator
from code_quality_tool import CodeQualityTool
from timing_manager import TimingManager

class DailyCommitCoordinator:
    """Main coordinator for daily commit automation"""
    
    def __init__(self, config_path: str = "config/automation_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.timing_manager = TimingManager(self.config.get("timing", {}))
        self.repo_health = RepoHealthChecker()
        self.dep_updater = DependencyUpdater()
        self.doc_automator = DocumentationAutomator()
        self.code_quality = CodeQualityTool()
        
        # Setup logging
        self.setup_logging()
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "timing": {
                "working_hours_start": 9,
                "working_hours_end": 17,
                "commit_frequency": "2-4_per_day",
                "break_between_commits": [2, 8],  # hours
                "avoid_weekends": True
            },
            "modules": {
                "repo_health": {"enabled": True, "priority": 1},
                "dependency_updates": {"enabled": True, "priority": 2},
                "documentation": {"enabled": True, "priority": 3},
                "code_quality": {"enabled": True, "priority": 4}
            },
            "limits": {
                "max_daily_commits": 5,
                "max_file_changes": 10,
                "max_lines_added": 500
            }
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daily_contributions.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get list of pending tasks based on repository state"""
        tasks = []
        
        if self.config["modules"]["repo_health"]["enabled"]:
            health_tasks = self.repo_health.get_improvement_tasks()
            tasks.extend(health_tasks)
            
        if self.config["modules"]["dependency_updates"]["enabled"]:
            dep_tasks = self.dep_updater.get_pending_updates()
            tasks.extend(dep_tasks)
            
        if self.config["modules"]["documentation"]["enabled"]:
            doc_tasks = self.doc_automator.get_documentation_tasks()
            tasks.extend(doc_tasks)
            
        if self.config["modules"]["code_quality"]["enabled"]:
            quality_tasks = self.code_quality.get_improvement_tasks()
            tasks.extend(quality_tasks)
        
        # Sort by priority
        tasks.sort(key=lambda x: x.get("priority", 5))
        return tasks
    
    def execute_task(self, task: Dict) -> bool:
        """Execute a single task"""
        try:
            task_type = task.get("type")
            self.logger.info(f"Executing task: {task_type} - {task.get('description', 'No description')}")
            
            if task_type == "readme_update":
                return self.repo_health.update_readme(task)
            elif task_type == "todo_cleanup":
                return self.repo_health.cleanup_todos(task)
            elif task_type == "dependency_update":
                return self.dep_updater.update_dependency(task)
            elif task_type == "documentation":
                return self.doc_automator.improve_documentation(task)
            elif task_type == "code_formatting":
                return self.code_quality.format_code(task)
            elif task_type == "code_linting":
                return self.code_quality.apply_linting(task)
            else:
                self.logger.warning(f"Unknown task type: {task_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing task {task.get('type', 'unknown')}: {str(e)}")
            return False
    
    def commit_changes(self, task: Dict, changes_made: List[str]) -> bool:
        """Create commit with natural message"""
        try:
            commit_message = self.generate_natural_commit_message(task, changes_made)
            return self.git_commit(commit_message)
        except Exception as e:
            self.logger.error(f"Error committing changes: {str(e)}")
            return False
    
    def generate_natural_commit_message(self, task: Dict, changes: List[str]) -> str:
        """Generate natural-looking commit messages"""
        
        task_type = task.get("type")
        
        message_templates = {
            "readme_update": [
                "docs: update README with additional project information",
                "docs: enhance README documentation with setup instructions",
                "docs: improve README structure and readability",
                "docs: update project documentation in README"
            ],
            "todo_cleanup": [
                "chore: organize TODO items and remove completed tasks",
                "chore: update task tracking and project organization",
                "chore: clean up development notes and priorities",
                "chore: improve project task management structure"
            ],
            "dependency_update": [
                "deps: update project dependencies to latest versions",
                "deps: upgrade library packages for improved compatibility",
                "deps: update npm/package dependencies",
                "deps: refresh project dependencies"
            ],
            "documentation": [
                "docs: improve code documentation and comments",
                "docs: enhance function and module documentation",
                "docs: add missing documentation for better maintainability",
                "docs: update code documentation structure"
            ],
            "code_formatting": [
                "style: apply consistent code formatting",
                "style: improve code structure and formatting",
                "style: standardize code formatting across project",
                "style: enhance code readability with formatting"
            ],
            "code_linting": [
                "refactor: improve code quality and resolve linting issues",
                "refactor: enhance code structure and best practices",
                "refactor: improve code maintainability and cleanliness",
                "refactor: optimize code quality and consistency"
            ]
        }
        
        templates = message_templates.get(task_type, ["chore: improve project structure"])
        return random.choice(templates)
    
    def git_commit(self, message: str) -> bool:
        """Execute git commit with message"""
        try:
            # Check if there are changes to commit
            result = os.system("git diff --quiet")
            if result == 0:  # No changes
                return False
                
            # Add all changes
            os.system("git add .")
            
            # Commit with message
            os.system(f'git commit -m "{message}"')
            
            self.logger.info(f"Committed changes: {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Git commit failed: {str(e)}")
            return False
    
    def should_commit_today(self) -> bool:
        """Determine if commits should be made today"""
        return self.timing_manager.is_good_time_for_commit()
    
    def run_daily_cycle(self) -> bool:
        """Run the complete daily automation cycle"""
        self.logger.info("Starting daily commit automation cycle")
        
        if not self.should_commit_today():
            self.logger.info("Not a good time for commits today, skipping")
            return True
        
        # Get pending tasks
        tasks = self.get_pending_tasks()
        if not tasks:
            self.logger.info("No pending tasks found")
            return True
        
        # Apply limits
        max_commits = self.config["limits"]["max_daily_commits"]
        tasks = tasks[:max_commits]
        
        # Execute tasks
        successful_commits = 0
        for task in tasks:
            if successful_commits >= max_commits:
                break
                
            # Check if enough time has passed since last commit
            if not self.timing_manager.can_make_commit():
                self.logger.info("Not enough time since last commit")
                break
            
            # Execute task
            success = self.execute_task(task)
            if success:
                changes_made = [f"Applied {task.get('type', 'unknown')} improvements"]
                if self.commit_changes(task, changes_made):
                    successful_commits += 1
                    self.timing_manager.record_commit()
        
        self.logger.info(f"Daily cycle completed. Made {successful_commits} commits")
        return True
    
    def run_interactive(self):
        """Run in interactive mode for testing"""
        print("Daily Commit Automation - Interactive Mode")
        print("=" * 50)
        
        # Check if we should commit today
        if not self.should_commit_today():
            print("❌ Not a good time for commits today")
            return
        
        # Show pending tasks
        tasks = self.get_pending_tasks()
        print(f"\n📋 Found {len(tasks)} pending tasks:")
        
        for i, task in enumerate(tasks[:5], 1):
            print(f"  {i}. {task.get('type', 'unknown')}: {task.get('description', 'No description')}")
        
        # Ask user if they want to proceed
        response = input("\n🤔 Proceed with automation? (y/N): ").lower().strip()
        if response != 'y':
            print("⏹️  Automation cancelled by user")
            return
        
        # Run the cycle
        self.run_daily_cycle()
        print("✅ Automation completed!")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily Commit Automation Coordinator")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--config", "-c", default="config/automation_config.json", help="Config file path")
    
    args = parser.parse_args()
    
    coordinator = DailyCommitCoordinator(args.config)
    
    if args.interactive:
        coordinator.run_interactive()
    else:
        coordinator.run_daily_cycle()

if __name__ == "__main__":
    main()