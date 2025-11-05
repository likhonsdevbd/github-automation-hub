"""
Automation Manager - Core orchestration engine for the automation hub.
Handles rate limiting, scheduling, and coordination of automation workflows.
"""

import time
import logging
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from .rate_limiter import RateLimiter
from .github_client import GitHubClient
from .config_manager import ConfigManager
from .telemetry import TelemetryLogger


@dataclass
class ActionRecord:
    """Record of an automation action for audit purposes."""
    action_type: str
    target_username: str
    timestamp: datetime
    status: str
    response_code: Optional[int] = None
    error_message: Optional[str] = None
    rate_limit_remaining: Optional[int] = None


class AutomationManager:
    """
    Main automation orchestrator that manages rate-limited GitHub operations.
    
    This class coordinates all automation activities while enforcing:
    - Conservative rate limits (≤24 actions/hour by default)
    - Jittered pacing for human-like behavior
    - Immediate stop on 422 (validation/spam signals)
    - Exponential backoff on 429 (rate limit exceeded)
    - Comprehensive audit logging
    """
    
    def __init__(self, config_path: str = None):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        self.rate_limiter = RateLimiter(self.config['rate_limits'])
        self.github_client = GitHubClient(self.config['github'])
        self.telemetry = TelemetryLogger(self.config['logging'])
        
        self.logger = logging.getLogger(__name__)
        self.action_history: List[ActionRecord] = []
        self.is_running = False
        
        # Initialize counters
        self.stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            '422_errors': 0,
            '429_errors': 0,
            'start_time': datetime.now()
        }
        
        self.logger.info("Automation Manager initialized with compliant settings")
    
    def start(self):
        """Start the automation manager."""
        self.is_running = True
        self.logger.info("Automation Manager started")
    
    def stop(self):
        """Stop the automation manager."""
        self.is_running = False
        self.logger.info("Automation Manager stopped")
    
    def execute_follow_action(self, username: str, priority: str = 'normal') -> bool:
        """
        Execute a follow action with full safety controls.
        
        Args:
            username: Target username to follow
            priority: Priority level (high, normal, low)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_running:
            self.logger.warning("Automation manager is not running")
            return False
        
        if not self.rate_limiter.can_execute_action('follow'):
            self.logger.warning(f"Rate limit exceeded for follow action on {username}")
            return False
        
        try:
            self.logger.info(f"Following user: {username}")
            
            # Execute the follow action
            response = self.github_client.follow_user(username)
            response_code = response.status_code if response else 0
            
            # Record the action
            action_record = ActionRecord(
                action_type='follow',
                target_username=username,
                timestamp=datetime.now(),
                status='success' if response_code == 204 else 'failed',
                response_code=response_code,
                rate_limit_remaining=self.rate_limiter.get_remaining_calls()
            )
            
            self.action_history.append(action_record)
            self._update_stats(response_code)
            
            # Handle different response codes
            if response_code == 204:
                self.logger.info(f"Successfully followed {username}")
                self.rate_limiter.record_action('follow')
                return True
            
            elif response_code == 422:
                # 422 = validation failed or spam flag - HARD STOP
                self.logger.error(f"422 error for {username} - stopping automation")
                self.stats['422_errors'] += 1
                self.telemetry.record_event('enforcement_signal', {
                    'username': username,
                    'response_code': response_code,
                    'action': 'follow'
                })
                self.emergency_stop("422 enforcement signal detected")
                return False
            
            elif response_code == 429:
                # Rate limit exceeded - exponential backoff
                self.logger.warning(f"429 rate limit exceeded for {username}")
                self.stats['429_errors'] += 1
                self.rate_limiter.handle_rate_limit_hit()
                return False
            
            else:
                self.logger.warning(f"Unexpected response code {response_code} for {username}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error following {username}: {str(e)}")
            action_record = ActionRecord(
                action_type='follow',
                target_username=username,
                timestamp=datetime.now(),
                status='error',
                error_message=str(e),
                rate_limit_remaining=self.rate_limiter.get_remaining_calls()
            )
            self.action_history.append(action_record)
            self.stats['failed_actions'] += 1
            return False
    
    def execute_unfollow_action(self, username: str) -> bool:
        """
        Execute an unfollow action with safety controls.
        
        Args:
            username: Target username to unfollow
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_running:
            self.logger.warning("Automation manager is not running")
            return False
        
        if not self.rate_limiter.can_execute_action('unfollow'):
            self.logger.warning(f"Rate limit exceeded for unfollow action on {username}")
            return False
        
        try:
            self.logger.info(f"Unfollowing user: {username}")
            
            # Execute the unfollow action
            response = self.github_client.unfollow_user(username)
            response_code = response.status_code if response else 0
            
            # Record the action
            action_record = ActionRecord(
                action_type='unfollow',
                target_username=username,
                timestamp=datetime.now(),
                status='success' if response_code == 204 else 'failed',
                response_code=response_code,
                rate_limit_remaining=self.rate_limiter.get_remaining_calls()
            )
            
            self.action_history.append(action_record)
            self._update_stats(response_code)
            
            # Handle different response codes
            if response_code == 204:
                self.logger.info(f"Successfully unfollowed {username}")
                self.rate_limiter.record_action('unfollow')
                return True
            
            elif response_code == 404:
                # 404 = not following or user doesn't exist - treat as success
                self.logger.info(f"Already not following {username} or user not found")
                return True
            
            elif response_code == 429:
                # Rate limit exceeded - exponential backoff
                self.logger.warning(f"429 rate limit exceeded for {username}")
                self.stats['429_errors'] += 1
                self.rate_limiter.handle_rate_limit_hit()
                return False
            
            else:
                self.logger.warning(f"Unexpected response code {response_code} for {username}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error unfollowing {username}: {str(e)}")
            action_record = ActionRecord(
                action_type='unfollow',
                target_username=username,
                timestamp=datetime.now(),
                status='error',
                error_message=str(e),
                rate_limit_remaining=self.rate_limiter.get_remaining_calls()
            )
            self.action_history.append(action_record)
            self.stats['failed_actions'] += 1
            return False
    
    def get_follow_back_candidates(self) -> List[Dict[str, Any]]:
        """
        Find users who haven't followed back within the configured window.
        
        Returns:
            List of user dictionaries with unfollow priority scores
        """
        try:
            # Get current following and followers lists
            following = self.github_client.get_following_list()
            followers = self.github_client.get_followers_list()
            
            following_usernames = {user['login'] for user in following}
            follower_usernames = {user['login'] for user in followers}
            
            # Find non-reciprocal follows
            non_reciprocal = following_usernames - follower_usernames
            
            candidates = []
            for username in non_reciprocal:
                # Calculate priority score based on user activity
                user_data = self.github_client.get_user_data(username)
                if user_data:
                    priority_score = self._calculate_unfollow_priority(user_data)
                    candidates.append({
                        'username': username,
                        'priority_score': priority_score,
                        'last_activity': user_data.get('updated_at'),
                        'public_repos': user_data.get('public_repos', 0),
                        'followers_count': user_data.get('followers', 0)
                    })
            
            # Sort by priority score (highest = best unfollow candidate)
            candidates.sort(key=lambda x: x['priority_score'], reverse=True)
            
            self.logger.info(f"Found {len(candidates)} unfollow candidates")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error getting follow-back candidates: {str(e)}")
            return []
    
    def _calculate_unfollow_priority(self, user_data: Dict[str, Any]) -> float:
        """
        Calculate unfollow priority score based on user characteristics.
        
        Higher score = better candidate for unfollow.
        Based on research showing unfollowing is more likely for:
        - Low activity users
        - Low programming language similarity
        """
        score = 0.0
        
        # Factor 1: Account age (newer accounts get lower priority to unfollow)
        created_at = user_data.get('created_at')
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                age_days = (datetime.now() - created_date.replace(tzinfo=None)).days
                if age_days < 90:  # New accounts
                    score -= 2.0
                elif age_days < 365:  # Less than 1 year
                    score -= 1.0
                else:  # Older accounts
                    score += 1.0
            except:
                pass
        
        # Factor 2: Repository activity
        public_repos = user_data.get('public_repos', 0)
        followers = user_data.get('followers', 0)
        
        if public_repos == 0 and followers < 10:
            score += 3.0  # Very low activity
        elif public_repos < 5 and followers < 20:
            score += 1.5  # Low activity
        elif public_repos > 20 or followers > 100:
            score -= 2.0  # Active user - don't unfollow
        
        # Factor 3: Account health indicators
        if not user_data.get('bio'):
            score += 0.5  # No bio might indicate low engagement
        if user_data.get('public_repos', 0) == 0:
            score += 1.0  # No public repos
        
        return score
    
    def _update_stats(self, response_code: int):
        """Update internal statistics."""
        self.stats['total_actions'] += 1
        
        if response_code == 204:
            self.stats['successful_actions'] += 1
        elif response_code == 422:
            self.stats['422_errors'] += 1
        elif response_code == 429:
            self.stats['429_errors'] += 1
        else:
            self.stats['failed_actions'] += 1
    
    def emergency_stop(self, reason: str):
        """
        Emergency stop - immediately halt all automation activities.
        
        This is triggered by 422 errors or other enforcement signals.
        """
        self.logger.critical(f"EMERGENCY STOP: {reason}")
        self.is_running = False
        self.telemetry.record_event('emergency_stop', {
            'reason': reason,
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        runtime = datetime.now() - self.stats['start_time']
        
        return {
            'is_running': self.is_running,
            'runtime_hours': runtime.total_seconds() / 3600,
            'stats': self.stats,
            'rate_limit_status': self.rate_limiter.get_status(),
            'recent_actions': [asdict(action) for action in self.action_history[-10:]],
            'follow_back_ratio': self._calculate_follow_back_ratio(),
            'compliance_status': self._get_compliance_status()
        }
    
    def _calculate_follow_back_ratio(self) -> float:
        """Calculate current follow-back ratio."""
        try:
            following = len(self.github_client.get_following_list())
            followers = len(self.github_client.get_followers_list())
            
            if following > 0:
                return followers / following
            return 0.0
        except:
            return 0.0
    
    def _get_compliance_status(self) -> Dict[str, Any]:
        """Assess current compliance status based on error rates."""
        total_actions = self.stats['total_actions']
        
        if total_actions == 0:
            return {'status': 'no_data'}
        
        compliance_issues = []
        
        if self.stats['422_errors'] > 0:
            compliance_issues.append('422_errors_detected')
        
        if self.stats['429_errors'] > total_actions * 0.1:  # >10% 429 rate
            compliance_issues.append('high_429_rate')
        
        if not self.is_running:
            compliance_issues.append('automation_paused')
        
        return {
            'status': 'compliant' if not compliance_issues else 'issues_detected',
            'issues': compliance_issues,
            'total_actions': total_actions,
            'error_rate': (self.stats['422_errors'] + self.stats['429_errors']) / total_actions
        }
    
    def save_audit_log(self, filepath: str = None):
        """Save audit log to file."""
        if not filepath:
            filepath = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        audit_data = {
            'session_start': self.stats['start_time'].isoformat(),
            'session_end': datetime.now().isoformat(),
            'stats': self.stats,
            'actions': [asdict(action) for action in self.action_history],
            'configuration': self.config
        }
        
        with open(filepath, 'w') as f:
            json.dump(audit_data, f, indent=2, default=str)
        
        self.logger.info(f"Audit log saved to {filepath}")
