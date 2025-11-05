"""
Follow-Back Detection and 7-Day Auto-Unfollow Logic
Implements comprehensive follow-back analysis with risk assessment
"""
import time
import json
from datetime import datetime, timedelta
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import requests
from ..config.settings import FollowAutomationConfig, ActionType

class RelevanceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ActivityLevel(Enum):
    INACTIVE = "inactive"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

@dataclass
class UserProfile:
    """User profile for relevance analysis"""
    username: str
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    public_repos_count: Optional[int] = None
    recent_activity_days: Optional[int] = None
    programming_languages: List[str] = field(default_factory=list)
    relevance_level: RelevanceLevel = RelevanceLevel.LOW
    activity_level: ActivityLevel = ActivityLevel.LOW
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class FollowRelationship:
    """Represents a follow relationship with metadata"""
    username: str
    followed_at: datetime
    is_following_back: bool = False
    is_mutual_collaborator: bool = False
    relevance_score: float = 0.0
    risk_score: float = 0.0
    should_unfollow: bool = False
    unfollow_reason: str = ""

class FollowBackDetector:
    """
    Main class for detecting follow-backs and managing unfollow logic
    Implements 7-day detection window with risk assessment
    """
    
    def __init__(self, config: FollowAutomationConfig, session: requests.Session):
        self.config = config
        self.session = session
        self.logger = logging.getLogger(__name__)
        
        # Tracking dictionaries
        self.following_set: Set[str] = set()
        self.followers_set: Set[str] = set()
        self.follow_history: Dict[str, datetime] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # Detection state
        self.last_detection_time = None
        self.detection_in_progress = False
        
        # Statistics
        self.total_detections = 0
        self.follow_backs_detected = 0
        self.unfollow_recommendations = 0
    
    def detect_follow_backs(self) -> Dict[str, bool]:
        """
        Main method to detect follow-backs
        Returns dict of username -> followed_back boolean
        """
        if self.detection_in_progress:
            self.logger.warning("Detection already in progress")
            return {}
        
        self.detection_in_progress = True
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting follow-back detection")
            
            # Fetch followers and following with pagination
            self._fetch_followers()
            self._fetch_following()
            
            # Analyze relationships
            follow_backs = self._analyze_follow_backs()
            
            # Update user profiles with latest data
            self._update_user_profiles()
            
            # Make unfollow decisions
            unfollow_decisions = self._make_unfollow_decisions(follow_backs)
            
            # Update statistics
            self.total_detections += 1
            self.follow_backs_detected += len(follow_backs)
            self.unfollow_recommendations += len(unfollow_decisions)
            
            self.last_detection_time = start_time
            
            # Log results
            self.logger.info(f"Detection complete: {len(follow_backs)} follow-backs, "
                           f"{len(unfollow_decisions)} unfollow recommendations")
            
            return {
                "follow_backs": follow_backs,
                "unfollow_recommendations": unfollow_decisions,
                "detection_duration": (datetime.now() - start_time).total_seconds()
            }
            
        finally:
            self.detection_in_progress = False
    
    def _fetch_followers(self) -> Set[str]:
        """Fetch followers with pagination"""
        self.logger.info("Fetching followers...")
        followers = set()
        
        page = 1
        while True:
            try:
                url = f"{self.config.api_base_url}/user/followers"
                params = {"page": page, "per_page": 100}
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 304:
                    self.logger.debug("Followers not modified")
                    break
                
                response.raise_for_status()
                data = response.json()
                
                if not data:  # Empty page means end of results
                    break
                
                # Extract usernames
                page_followers = {user["login"] for user in data}
                followers.update(page_followers)
                
                self.logger.debug(f"Fetched page {page}: {len(page_followers)} followers")
                
                # Respect rate limits
                self._respect_rate_limit(response)
                
                page += 1
                
                # Safety limit
                if page > self.config.detection.max_list_size // 100:
                    self.logger.warning("Reached max list size limit")
                    break
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching followers page {page}: {e}")
                break
        
        self.followers_set = followers
        self.logger.info(f"Total followers fetched: {len(followers)}")
        return followers
    
    def _fetch_following(self) -> Set[str]:
        """Fetch following with pagination"""
        self.logger.info("Fetching following...")
        following = set()
        
        page = 1
        while True:
            try:
                url = f"{self.config.api_base_url}/user/following"
                params = {"page": page, "per_page": 100}
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 304:
                    self.logger.debug("Following not modified")
                    break
                
                response.raise_for_status()
                data = response.json()
                
                if not data:  # Empty page means end of results
                    break
                
                # Extract usernames
                page_following = {user["login"] for user in data}
                following.update(page_following)
                
                self.logger.debug(f"Fetched page {page}: {len(page_following)} following")
                
                # Respect rate limits
                self._respect_rate_limit(response)
                
                page += 1
                
                # Safety limit
                if page > self.config.detection.max_list_size // 100:
                    self.logger.warning("Reached max list size limit")
                    break
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching following page {page}: {e}")
                break
        
        self.following_set = following
        self.logger.info(f"Total following fetched: {len(following)}")
        return following
    
    def _respect_rate_limit(self, response: requests.Response):
        """Respect rate limits from API response"""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            self.logger.warning(f"Rate limited. Waiting {retry_after} seconds")
            time.sleep(retry_after)
    
    def _analyze_follow_backs(self) -> Dict[str, bool]:
        """Analyze follow-back relationships"""
        self.logger.info("Analyzing follow-back relationships...")
        
        follow_backs = {}
        seven_days_ago = datetime.now() - timedelta(days=self.config.detection.follow_back_window_days)
        
        for username in self.following_set:
            is_following_back = username in self.followers_set
            follow_backs[username] = is_following_back
            
            # Check if follow happened within window
            follow_time = self.follow_history.get(username)
            if follow_time and follow_time > seven_days_ago:
                if is_following_back:
                    self.logger.info(f"Recent follow-back detected: {username}")
                else:
                    # This user might be a candidate for unfollow
                    pass
        
        return follow_backs
    
    def _update_user_profiles(self):
        """Update user profiles for relevance analysis"""
        self.logger.info("Updating user profiles...")
        
        # Focus on users we follow but don't follow back
        candidates = self.following_set - self.followers_set
        
        # Limit updates to avoid excessive API calls
        for username in list(candidates)[:100]:  # Max 100 profiles
            try:
                profile = self._fetch_user_profile(username)
                if profile:
                    self.user_profiles[username] = profile
                    
                    # Rate limit between profile fetches
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Error fetching profile for {username}: {e}")
    
    def _fetch_user_profile(self, username: str) -> Optional[UserProfile]:
        """Fetch detailed user profile"""
        try:
            url = f"{self.config.api_base_url}/users/{username}"
            response = self.session.get(url)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Calculate activity level
            last_active_days = self._calculate_activity_days(data)
            activity_level = self._determine_activity_level(
                data.get("public_repos", 0), 
                last_active_days
            )
            
            # Calculate relevance
            relevance_level = self._calculate_relevance(data)
            
            return UserProfile(
                username=username,
                followers_count=data.get("followers"),
                following_count=data.get("following"),
                public_repos_count=data.get("public_repos"),
                recent_activity_days=last_active_days,
                programming_languages=[],  # Would need repo analysis
                relevance_level=relevance_level,
                activity_level=activity_level
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching profile for {username}: {e}")
            return None
    
    def _calculate_activity_days(self, user_data: dict) -> int:
        """Calculate days since last activity"""
        try:
            last_activity = user_data.get("updated_at")
            if last_activity:
                last_date = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
                return (datetime.now() - last_date).days
        except:
            pass
        return 365  # Default to inactive
    
    def _determine_activity_level(self, repos_count: int, days_since_active: int) -> ActivityLevel:
        """Determine user activity level"""
        if days_since_active > 180:
            return ActivityLevel.INACTIVE
        elif days_since_active > 60 or repos_count == 0:
            return ActivityLevel.LOW
        elif days_since_active > 14 and repos_count < 5:
            return ActivityLevel.LOW
        elif repos_count > 50 or days_since_active <= 7:
            return ActivityLevel.HIGH
        else:
            return ActivityLevel.MODERATE
    
    def _calculate_relevance(self, user_data: dict) -> RelevanceLevel:
        """Calculate user relevance level"""
        followers = user_data.get("followers", 0)
        public_repos = user_data.get("public_repos", 0)
        
        # High relevance: high follower count and active repos
        if followers > 1000 and public_repos > 10:
            return RelevanceLevel.HIGH
        
        # Medium relevance: moderate activity
        if followers > 100 or public_repos > 5:
            return RelevanceLevel.MEDIUM
        
        # Low relevance: default
        return RelevanceLevel.LOW
    
    def _make_unfollow_decisions(self, follow_backs: Dict[str, bool]) -> Dict[str, str]:
        """Make unfollow decisions based on 7-day analysis"""
        self.logger.info("Making unfollow decisions...")
        
        decisions = {}
        seven_days_ago = datetime.now() - timedelta(days=self.config.detection.follow_back_window_days)
        
        for username, followed_back in follow_backs.items():
            if followed_back:
                continue  # Don't unfollow follow-backs
            
            # Check if we followed them long enough ago
            follow_time = self.follow_history.get(username)
            if not follow_time or follow_time < seven_days_ago:
                decision = self._evaluate_unfollow_user(username)
                if decision["should_unfollow"]:
                    decisions[username] = decision["reason"]
        
        return decisions
    
    def _evaluate_unfollow_user(self, username: str) -> Dict:
        """Evaluate if user should be unfollowed"""
        profile = self.user_profiles.get(username)
        
        if not profile:
            return {"should_unfollow": True, "reason": "No profile data"}
        
        # Scoring system
        risk_score = 0.0
        reasons = []
        
        # Activity-based scoring
        if profile.activity_level == ActivityLevel.INACTIVE:
            risk_score += 3.0
            reasons.append("Inactive user")
        elif profile.activity_level == ActivityLevel.LOW:
            risk_score += 2.0
            reasons.append("Low activity")
        
        # Relevance-based scoring
        if profile.relevance_level == RelevanceLevel.LOW:
            risk_score += 2.0
            reasons.append("Low relevance")
        elif profile.relevance_level == RelevanceLevel.MEDIUM:
            risk_score += 1.0
            reasons.append("Medium relevance")
        
        # Follower/following ratio
        if profile.followers_count and profile.following_count:
            ratio = profile.followers_count / max(profile.following_count, 1)
            if ratio < 0.1:  # Very few followers relative to following
                risk_score += 1.5
                reasons.append("Poor follower ratio")
        
        should_unfollow = risk_score >= self.config.detection.relevance_threshold
        reason = "; ".join(reasons) if reasons else "High risk score"
        
        return {
            "should_unfollow": should_unfollow,
            "reason": reason,
            "risk_score": risk_score,
            "activity_level": profile.activity_level.value,
            "relevance_level": profile.relevance_level.value
        }
    
    def record_follow_action(self, username: str):
        """Record follow action for tracking"""
        self.follow_history[username] = datetime.now()
        self.logger.debug(f"Recorded follow: {username}")
    
    def record_unfollow_action(self, username: str):
        """Record unfollow action"""
        if username in self.follow_history:
            del self.follow_history[username]
        if username in self.following_set:
            self.following_set.remove(username)
        self.logger.debug(f"Recorded unfollow: {username}")
    
    def get_detection_statistics(self) -> Dict:
        """Get detection statistics"""
        return {
            "total_detections": self.total_detections,
            "follow_backs_detected": self.follow_backs_detected,
            "unfollow_recommendations": self.unfollow_recommendations,
            "current_following_count": len(self.following_set),
            "current_followers_count": len(self.followers_set),
            "last_detection_time": (
                self.last_detection_time.isoformat() 
                if self.last_detection_time else None
            ),
            "user_profiles_cached": len(self.user_profiles),
            "follow_history_size": len(self.follow_history)
        }
    
    def export_detection_data(self, filepath: str):
        """Export detection data for analysis"""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "followers": list(self.followers_set),
            "following": list(self.following_set),
            "follow_history": {
                k: v.isoformat() for k, v in self.follow_history.items()
            },
            "user_profiles": {
                k: {
                    "username": v.username,
                    "relevance_level": v.relevance_level.value,
                    "activity_level": v.activity_level.value,
                    "followers_count": v.followers_count,
                    "following_count": v.following_count
                }
                for k, v in self.user_profiles.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Detection data exported to {filepath}")

class UnfollowScheduler:
    """
    Schedules unfollow actions based on risk assessment
    Implements micro-batching with safety controls
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.unfollow_queue = []
        self.executed_unfollows = set()
        self.cooldowns = {}
    
    def add_unfollow_candidates(self, candidates: Dict[str, str]):
        """Add users to unfollow queue with reasons"""
        for username, reason in candidates.items():
            if username not in self.executed_unfollows:
                self.unfollow_queue.append({
                    "username": username,
                    "reason": reason,
                    "timestamp": datetime.now(),
                    "risk_level": self._calculate_risk_level(reason)
                })
        
        # Sort by risk level (highest first for unfollows)
        self.unfollow_queue.sort(key=lambda x: x["risk_level"], reverse=True)
        
        self.logger.info(f"Added {len(candidates)} unfollow candidates")
    
    def _calculate_risk_level(self, reason: str) -> float:
        """Calculate risk level from reason string"""
        risk_keywords = {
            "inactive": 3.0,
            "low activity": 2.0,
            "low relevance": 2.0,
            "poor follower ratio": 1.5,
            "medium relevance": 1.0
        }
        
        risk_score = 0.0
        reason_lower = reason.lower()
        
        for keyword, score in risk_keywords.items():
            if keyword in reason_lower:
                risk_score += score
        
        return min(risk_score, 5.0)  # Cap at 5.0
    
    def get_next_unfollow_batch(self, max_batch_size: int = 3) -> List[Dict]:
        """Get next batch of users to unfollow"""
        batch = []
        
        for item in self.unfollow_queue[:max_batch_size]:
            # Check cooldown
            username = item["username"]
            if self._is_in_cooldown(username):
                continue
            
            batch.append(item)
        
        return batch
    
    def _is_in_cooldown(self, username: str) -> bool:
        """Check if user is in cooldown period"""
        cooldown_end = self.cooldowns.get(username)
        if not cooldown_end:
            return False
        
        if datetime.now() < cooldown_end:
            return True
        
        # Remove expired cooldown
        del self.cooldowns[username]
        return False
    
    def mark_unfollow_executed(self, username: str):
        """Mark unfollow as executed"""
        self.executed_unfollows.add(username)
        
        # Set cooldown to prevent re-following immediately
        cooldown_duration = timedelta(hours=24)  # 24-hour cooldown
        self.cooldowns[username] = datetime.now() + cooldown_duration
        
        # Remove from queue
        self.unfollow_queue = [
            item for item in self.unfollow_queue 
            if item["username"] != username
        ]
        
        self.logger.info(f"Marked unfollow executed: {username}")
    
    def get_unfollow_statistics(self) -> Dict:
        """Get unfollow scheduling statistics"""
        return {
            "pending_unfollows": len(self.unfollow_queue),
            "executed_unfollows": len(self.executed_unfollows),
            "active_cooldowns": len(self.cooldowns),
            "high_risk_unfollows": len([
                item for item in self.unfollow_queue 
                if item["risk_level"] >= 3.0
            ]),
            "medium_risk_unfollows": len([
                item for item in self.unfollow_queue 
                if 1.0 <= item["risk_level"] < 3.0
            ]),
            "low_risk_unfollows": len([
                item for item in self.unfollow_queue 
                if item["risk_level"] < 1.0
            ])
        }