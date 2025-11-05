#!/usr/bin/env python3
"""
Utilities and Helper Functions for Daily Commit Automation
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

class AutomationUtils:
    """Utility functions for daily commit automation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def ensure_directory(path: str | Path):
        """Ensure directory exists, create if not"""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Create a safe filename from any string"""
        # Remove or replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        return ''.join(c if c in safe_chars else '_' for c in filename)
    
    @staticmethod
    def calculate_file_hash(filepath: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def get_file_stats(filepath: Path) -> Dict[str, Any]:
        """Get comprehensive file statistics"""
        try:
            stat = filepath.stat()
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_file": filepath.is_file(),
                "is_dir": filepath.is_dir(),
                "extension": filepath.suffix.lower()
            }
        except Exception:
            return {}
    
    @staticmethod
    def run_command(cmd: List[str], timeout: int = 30, capture_output: bool = True) -> Dict[str, Any]:
        """Run a shell command safely"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "command": " ".join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(cmd)
            }
    
    @staticmethod
    def backup_file(filepath: Path, backup_dir: str = ".automation_backups") -> Optional[Path]:
        """Create a backup of a file"""
        try:
            if not filepath.exists():
                return None
            
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            # Create backup with timestamp
            timestamp = AutomationUtils.get_timestamp()
            backup_filename = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_file = backup_path / backup_filename
            
            # Copy file
            import shutil
            shutil.copy2(filepath, backup_file)
            
            return backup_file
        except Exception:
            return None
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in format suitable for filenames"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def check_git_repository() -> bool:
        """Check if current directory is a git repository"""
        return Path(".git").exists() and Path(".git").is_dir()
    
    @staticmethod
    def get_git_status() -> Dict[str, Any]:
        """Get current git repository status"""
        if not AutomationUtils.check_git_repository():
            return {"is_git_repo": False}
        
        status = {"is_git_repo": True}
        
        # Get current branch
        result = AutomationUtils.run_command(["git", "branch", "--show-current"])
        if result["success"]:
            status["current_branch"] = result["stdout"].strip()
        
        # Get remote URL
        result = AutomationUtils.run_command(["git", "remote", "get-url", "origin"])
        if result["success"]:
            status["remote_url"] = result["stdout"].strip()
        
        # Check for uncommitted changes
        result = AutomationUtils.run_command(["git", "status", "--porcelain"])
        if result["success"]:
            status["has_changes"] = bool(result["stdout"].strip())
            status["status_lines"] = result["stdout"].strip().split('\n') if result["stdout"].strip() else []
        
        # Get last commit info
        result = AutomationUtils.run_command(["git", "log", "-1", "--format=%H|%an|%ad|%s"])
        if result["success"]:
            parts = result["stdout"].strip().split('|', 3)
            if len(parts) >= 4:
                status["last_commit"] = {
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                }
        
        return status
    
    @staticmethod
    def has_git_changes() -> bool:
        """Check if there are uncommitted git changes"""
        result = AutomationUtils.run_command(["git", "diff", "--quiet"])
        return result["returncode"] != 0
    
    @staticmethod
    def stage_git_changes() -> bool:
        """Stage all git changes"""
        result = AutomationUtils.run_command(["git", "add", "."])
        return result["success"]
    
    @staticmethod
    def commit_changes(message: str, author: Optional[str] = None) -> bool:
        """Commit changes with message"""
        cmd = ["git", "commit", "-m", message]
        if author:
            cmd.extend(["--author", author])
        
        result = AutomationUtils.run_command(cmd)
        return result["success"]
    
    @staticmethod
    def get_project_info() -> Dict[str, Any]:
        """Get information about the current project"""
        info = {
            "project_name": Path.cwd().name,
            "project_path": str(Path.cwd()),
            "python_version": None,
            "languages": [],
            "package_managers": [],
            "config_files": []
        }
        
        # Detect Python
        if any(Path(".").glob("**/*.py")):
            info["languages"].append("python")
            
            # Try to get Python version
            result = AutomationUtils.run_command(["python", "--version"])
            if result["success"]:
                info["python_version"] = result["stdout"].strip()
        
        # Detect other languages
        if any(Path(".").glob("**/*.js")):
            info["languages"].append("javascript")
        if any(Path(".").glob("**/*.ts")):
            info["languages"].append("typescript")
        if any(Path(".").glob("**/*.go")):
            info["languages"].append("go")
        if any(Path(".").glob("**/*.rs")):
            info["languages"].append("rust")
        if any(Path(".").glob("**/*.java")):
            info["languages"].append("java")
        
        # Detect package managers
        if Path("requirements.txt").exists() or Path("pyproject.toml").exists():
            info["package_managers"].append("pip")
        if Path("package.json").exists():
            info["package_managers"].append("npm")
        if Path("go.mod").exists():
            info["package_managers"].append("go")
        if Path("Cargo.toml").exists():
            info["package_managers"].append("cargo")
        if Path("pom.xml").exists():
            info["package_managers"].append("maven")
        
        # Detect config files
        config_patterns = [
            ".flake8", ".prettierrc", ".eslintrc", "pyproject.toml",
            "package.json", "go.mod", "Cargo.toml", "pom.xml"
        ]
        
        for pattern in config_patterns:
            if Path(pattern).exists():
                info["config_files"].append(pattern)
        
        return info
    
    @staticmethod
    def validate_json_file(filepath: Path) -> bool:
        """Validate that a JSON file is properly formatted"""
        try:
            with open(filepath, 'r') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False
    
    @staticmethod
    def update_json_file(filepath: Path, updates: Dict[str, Any]) -> bool:
        """Update a JSON file with new values"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Apply updates
            data.update(updates)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def cleanup_old_files(directory: Path, pattern: str, days_old: int = 30) -> int:
        """Clean up old files matching a pattern"""
        if not directory.exists():
            return 0
        
        import time
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        cleaned_count = 0
        for file_path in directory.glob(pattern):
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            except Exception:
                continue
        
        return cleaned_count
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information"""
        import platform
        import sys
        
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "node": platform.node(),
            "cwd": os.getcwd(),
            "user": os.getenv("USER", os.getenv("USERNAME", "unknown"))
        }
    
    @staticmethod
    def create_backup_archive(source_dir: Path, backup_name: str) -> Optional[Path]:
        """Create a backup archive of a directory"""
        import tarfile
        
        try:
            backup_path = Path(f"{backup_name}.tar.gz")
            
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(source_dir, arcname=source_dir.name)
            
            return backup_path
        except Exception:
            return None
    
    @staticmethod
    def restore_from_archive(archive_path: Path, target_dir: Path) -> bool:
        """Restore files from a backup archive"""
        import tarfile
        
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(target_dir.parent)
            return True
        except Exception:
            return False
    
    @staticmethod
    def send_notification(title: str, message: str, webhook_url: Optional[str] = None):
        """Send notification (placeholder for future implementation)"""
        # This is a placeholder for notification functionality
        # Could integrate with Slack, Discord, email, etc.
        
        if webhook_url:
            import requests
            try:
                payload = {"title": title, "text": message}
                response = requests.post(webhook_url, json=payload)
                return response.status_code == 200
            except Exception:
                return False
        
        # Fallback to logging
        logging.info(f"NOTIFICATION: {title} - {message}")
        return True
    
    @staticmethod
    def log_performance_metrics(metrics: Dict[str, float]):
        """Log performance metrics"""
        self = AutomationUtils()
        self.logger.info("Performance Metrics:")
        for metric, value in metrics.items():
            self.logger.info(f"  {metric}: {value:.2f}")
    
    @staticmethod
    def sanitize_commit_message(message: str) -> str:
        """Sanitize commit message to ensure it's safe"""
        # Remove newlines and excessive whitespace
        sanitized = " ".join(message.split())
        
        # Limit length
        if len(sanitized) > 72:
            sanitized = sanitized[:72] + "..."
        
        return sanitized
    
    @staticmethod
    def extract_meaningful_changes(changes: List[str], max_changes: int = 5) -> List[str]:
        """Extract and prioritize meaningful changes from a list"""
        # Simple prioritization logic
        priority_keywords = ["fix", "feature", "doc", "test", "refactor"]
        
        def get_priority(change: str) -> int:
            change_lower = change.lower()
            for i, keyword in enumerate(priority_keywords):
                if keyword in change_lower:
                    return i
            return len(priority_keywords)
        
        # Sort by priority and limit
        prioritized = sorted(changes, key=get_priority)
        return prioritized[:max_changes]