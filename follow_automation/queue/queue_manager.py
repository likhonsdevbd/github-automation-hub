"""
Auto-Follow Queue Management System
Implements prioritized, stateful queue with deduplication and cool-downs
"""
import time
import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from threading import Lock, Event
from ..config.settings import FollowAutomationConfig, ActionType
from ..core.rate_limiter import ActionToken

class QueuePriority(Enum):
    """Priority levels for actions"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

class QueueStatus(Enum):
    """Queue processing status"""
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class QueueItem:
    """Represents an item in the follow/unfollow queue"""
    id: str
    action_type: ActionType
    target_username: str
    priority: QueuePriority
    timestamp: datetime = field(default_factory=datetime.now)
    max_retries: int = 3
    retry_count: int = 0
    cooldown_until: Optional[datetime] = None
    relevance_score: float = 0.0
    context_data: Dict = field(default_factory=dict)
    
    def __lt__(self, other):
        """Enable priority queue ordering"""
        return self.priority.value < other.priority.value

class Prioritizer:
    """
    Prioritizes targets based on relevance and risk assessment
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Scoring weights
        self.scoring_weights = {
            "activity_level": 0.3,
            "follower_ratio": 0.2,
            "mutual_collaboration": 0.25,
            "recent_activity": 0.15,
            "network_similarity": 0.1
        }
        
        # Priority scoring thresholds
        self.priority_thresholds = {
            QueuePriority.CRITICAL: 4.5,
            QueuePriority.HIGH: 3.5,
            QueuePriority.NORMAL: 2.5,
            QueuePriority.LOW: 1.5
        }
    
    def prioritize_target(self, username: str, context_data: Dict) -> tuple[float, QueuePriority]:
        """
        Calculate priority score for a target user
        
        Returns (relevance_score, priority_level)
        """
        score = 0.0
        
        # Activity level scoring
        activity_score = self._score_activity_level(context_data)
        score += activity_score * self.scoring_weights["activity_level"]
        
        # Follower ratio scoring
        ratio_score = self._score_follower_ratio(context_data)
        score += ratio_score * self.scoring_weights["follower_ratio"]
        
        # Mutual collaboration scoring
        collab_score = self._score_mutual_collaboration(context_data)
        score += collab_score * self.scoring_weights["mutual_collaboration"]
        
        # Recent activity scoring
        recent_score = self._score_recent_activity(context_data)
        score += recent_score * self.scoring_weights["recent_activity"]
        
        # Network similarity scoring
        network_score = self._score_network_similarity(context_data)
        score += network_score * self.scoring_weights["network_similarity"]
        
        # Determine priority level
        priority = self._determine_priority_level(score)
        
        self.logger.debug(f"Prioritized {username}: score={score:.2f}, priority={priority.name}")
        
        return score, priority
    
    def _score_activity_level(self, context_data: Dict) -> float:
        """Score based on user's activity level"""
        repos_count = context_data.get("public_repos", 0)
        last_active = context_data.get("last_active_days", 365)
        
        # Activity scoring logic
        if last_active <= 7:
            if repos_count > 10:
                return 5.0  # Highly active
            elif repos_count > 5:
                return 4.0  # Moderately active
            else:
                return 3.0  # Active with few repos
        elif last_active <= 30:
            if repos_count > 5:
                return 3.5
            else:
                return 2.5
        elif last_active <= 90:
            return 2.0
        else:
            return 1.0  # Low activity
    
    def _score_follower_ratio(self, context_data: Dict) -> float:
        """Score based on follower/following ratio"""
        followers = context_data.get("followers", 0)
        following = context_data.get("following", 0)
        
        if following == 0:
            return 3.0  # Not following anyone
        
        ratio = followers / following
        
        if ratio > 5.0:
            return 4.0  # High-quality account
        elif ratio > 2.0:
            return 3.5
        elif ratio > 1.0:
            return 3.0
        elif ratio > 0.5:
            return 2.0
        else:
            return 1.0  # Poor ratio
    
    def _score_mutual_collaboration(self, context_data: Dict) -> float:
        """Score based on mutual collaboration opportunities"""
        # Check for shared repositories
        shared_repos = context_data.get("shared_repos", [])
        starred_repos = context_data.get("starred_repos", [])
        
        if shared_repos:
            return min(len(shared_repos) * 2.0, 5.0)
        elif starred_repos:
            return min(len(starred_repos), 3.0)
        else:
            return 1.0
    
    def _score_recent_activity(self, context_data: Dict) -> float:
        """Score based on recent activity patterns"""
        last_commit = context_data.get("last_commit_days", 365)
        commit_frequency = context_data.get("avg_commits_per_month", 0)
        
        if last_commit <= 7:
            return min(commit_frequency * 0.5 + 3.0, 5.0)
        elif last_commit <= 30:
            return min(commit_frequency * 0.3 + 2.0, 4.0)
        elif last_commit <= 90:
            return min(commit_frequency * 0.2 + 1.0, 3.0)
        else:
            return 1.0
    
    def _score_network_similarity(self, context_data: Dict) -> float:
        """Score based on network similarity"""
        # This would typically involve complex network analysis
        # For now, using simplified heuristics
        
        shared_languages = context_data.get("shared_languages", [])
        common_organizations = context_data.get("common_organizations", [])
        
        score = 0.0
        
        if shared_languages:
            score += min(len(shared_languages) * 0.5, 2.0)
        
        if common_organizations:
            score += min(len(common_organizations) * 1.0, 3.0)
        
        return score
    
    def _determine_priority_level(self, score: float) -> QueuePriority:
        """Determine priority level from score"""
        for priority, threshold in sorted(self.priority_thresholds.items(), 
                                         key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return priority
        
        return QueuePriority.BACKGROUND

class FollowQueue:
    """
    Main queue management system for follow/unfollow operations
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Priority queue using heap
        self.queue: List[QueueItem] = []
        self.lock = Lock()
        
        # State tracking
        self.processed_items: Dict[str, QueueItem] = {}
        self.deduplication_set: Set[str] = set()
        self.cooldowns: Dict[str, datetime] = {}
        
        # Queue statistics
        self.stats = {
            "items_added": 0,
            "items_processed": 0,
            "items_failed": 0,
            "duplicates_prevented": 0,
            "cooldown_hits": 0
        }
        
        # Control flags
        self.status = QueueStatus.IDLE
        self.should_stop = Event()
        self.processing_callback: Optional[Callable] = None
    
    def add_action(self, action_type: ActionType, username: str, 
                  context_data: Optional[Dict] = None) -> str:
        """
        Add action to queue with automatic prioritization
        Returns item ID if added, None if prevented
        """
        if context_data is None:
            context_data = {}
        
        with self.lock:
            # Check for duplicates
            duplicate_key = f"{action_type.value}:{username}"
            if duplicate_key in self.deduplication_set:
                self.stats["duplicates_prevented"] += 1
                self.logger.warning(f"Duplicate action prevented: {duplicate_key}")
                return None
            
            # Check cooldown
            if self._is_in_cooldown(username):
                self.stats["cooldown_hits"] += 1
                self.logger.debug(f"Action blocked by cooldown: {username}")
                return None
            
            # Prioritize target
            prioritizer = Prioritizer(self.config)
            relevance_score, priority = prioritizer.prioritize_target(username, context_data)
            
            # Create queue item
            item_id = f"{action_type.value}_{username}_{int(time.time())}"
            item = QueueItem(
                id=item_id,
                action_type=action_type,
                target_username=username,
                priority=priority,
                relevance_score=relevance_score,
                context_data=context_data
            )
            
            # Add to queue
            heapq.heappush(self.queue, item)
            self.deduplication_set.add(duplicate_key)
            
            self.stats["items_added"] += 1
            
            self.logger.info(f"Added {action_type.value} action for {username} "
                           f"(priority: {priority.name}, score: {relevance_score:.2f})")
            
            return item_id
    
    def get_next_item(self) -> Optional[QueueItem]:
        """Get next item from queue (highest priority)"""
        with self.lock:
            while self.queue:
                item = heapq.heappop(self.queue)
                
                # Check if item is still valid
                if self._is_item_valid(item):
                    return item
                else:
                    self.logger.debug(f"Skipping invalid item: {item.id}")
            
            return None
    
    def _is_item_valid(self, item: QueueItem) -> bool:
        """Check if item is still valid for processing"""
        # Check cooldown
        if item.cooldown_until and datetime.now() < item.cooldown_until:
            return False
        
        # Check retry limit
        if item.retry_count >= item.max_retries:
            return False
        
        return True
    
    def mark_item_completed(self, item_id: str, success: bool, 
                          retry_after: Optional[int] = None):
        """Mark item as completed"""
        with self.lock:
            # Find item in processed items
            item = self.processed_items.get(item_id)
            if not item:
                self.logger.error(f"Item not found: {item_id}")
                return
            
            # Update statistics
            if success:
                self.stats["items_processed"] += 1
                # Remove from deduplication set
                duplicate_key = f"{item.action_type.value}:{item.target_username}"
                self.deduplication_set.discard(duplicate_key)
            else:
                self.stats["items_failed"] += 1
                item.retry_count += 1
                
                if item.retry_count < item.max_retries:
                    # Re-add to queue with higher priority and cooldown
                    item.cooldown_until = datetime.now() + timedelta(
                        minutes=item.retry_count * 5  # Increasing cooldown
                    )
                    heapq.heappush(self.queue, item)
                else:
                    # Permanent failure - remove from deduplication
                    duplicate_key = f"{item.action_type.value}:{item.target_username}"
                    self.deduplication_set.discard(duplicate_key)
            
            # Remove from processed items
            if item_id in self.processed_items:
                del self.processed_items[item_id]
    
    def _is_in_cooldown(self, username: str) -> bool:
        """Check if user is in cooldown"""
        cooldown_end = self.cooldowns.get(username)
        if cooldown_end and datetime.now() < cooldown_end:
            return True
        elif cooldown_end:
            # Remove expired cooldown
            del self.cooldowns[username]
        return False
    
    def set_cooldown(self, username: str, duration_minutes: int):
        """Set cooldown for user"""
        self.cooldowns[username] = datetime.now() + timedelta(minutes=duration_minutes)
        self.logger.info(f"Set cooldown for {username}: {duration_minutes} minutes")
    
    def get_queue_stats(self) -> Dict:
        """Get comprehensive queue statistics"""
        with self.lock:
            priority_distribution = {}
            for item in self.queue:
                priority_name = item.priority.name
                priority_distribution[priority_name] = priority_distribution.get(priority_name, 0) + 1
            
            return {
                "queue_size": len(self.queue),
                "processed_items": len(self.processed_items),
                "active_cooldowns": len(self.cooldowns),
                "deduplication_set_size": len(self.deduplication_set),
                "stats": self.stats.copy(),
                "priority_distribution": priority_distribution,
                "status": self.status.value,
                "queue_fill_rate": (
                    len(self.queue) / self.config.queue_max_size * 100
                )
            }
    
    def cleanup_expired_items(self):
        """Clean up expired items from queue"""
        with self.lock:
            original_size = len(self.queue)
            
            # Remove invalid items
            self.queue = [item for item in self.queue if self._is_item_valid(item)]
            
            # Rebuild heap (heapify is more efficient than multiple pops)
            heapq.heapify(self.queue)
            
            removed_count = original_size - len(self.queue)
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} expired items")
    
    def clear_queue(self):
        """Clear all items from queue"""
        with self.lock:
            self.queue.clear()
            self.deduplication_set.clear()
            self.processed_items.clear()
            self.cooldowns.clear()
            
            self.logger.info("Queue cleared")
    
    def pause_queue(self):
        """Pause queue processing"""
        self.status = QueueStatus.PAUSED
        self.logger.info("Queue paused")
    
    def resume_queue(self):
        """Resume queue processing"""
        self.status = QueueStatus.IDLE
        self.logger.info("Queue resumed")
    
    def export_queue_state(self, filepath: str):
        """Export current queue state for analysis"""
        with self.lock:
            state = {
                "export_timestamp": datetime.now().isoformat(),
                "queue_items": [
                    {
                        "id": item.id,
                        "action_type": item.action_type.value,
                        "username": item.target_username,
                        "priority": item.priority.name,
                        "relevance_score": item.relevance_score,
                        "timestamp": item.timestamp.isoformat(),
                        "retry_count": item.retry_count,
                        "context_data": item.context_data
                    }
                    for item in self.queue
                ],
                "statistics": self.get_queue_stats()
            }
        
        import json
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"Queue state exported to {filepath}")

class QueueProcessor:
    """
    Processes items from the queue with rate limiting and timing controls
    """
    
    def __init__(self, config: FollowAutomationConfig, 
                 queue: FollowQueue, rate_limiter, scheduler):
        self.config = config
        self.queue = queue
        self.rate_limiter = rate_limiter
        self.scheduler = scheduler
        self.logger = logging.getLogger(__name__)
        
        self.should_stop = Event()
        self.processing = False
    
    def start_processing(self):
        """Start processing queue items"""
        if self.processing:
            self.logger.warning("Processing already in progress")
            return
        
        self.processing = True
        self.logger.info("Started queue processing")
        
        try:
            while not self.should_stop.is_set():
                # Get next item
                item = self.queue.get_next_item()
                if not item:
                    self.logger.debug("Queue empty, waiting...")
                    time.sleep(5)
                    continue
                
                # Check if we can execute action
                if not self.rate_limiter.can_execute_action(item.action_type):
                    wait_time = self.rate_limiter.get_time_until_next_action()
                    self.logger.debug(f"Rate limited, waiting {wait_time:.1f}s")
                    time.sleep(min(wait_time, 300))  # Max 5 minutes
                    continue
                
                # Calculate delay
                context = {
                    "relevance_score": item.relevance_score,
                    "retry_count": item.retry_count
                }
                delay = self.scheduler.calculate_next_delay(
                    item.action_type,
                    recent_success_rate=0.9  # Placeholder
                )
                
                self.logger.info(f"Processing {item.action_type.value} for {item.target_username}")
                
                # Execute action (callback would be provided by integration)
                if self.queue.processing_callback:
                    try:
                        success = self.queue.processing_callback(item)
                        
                        # Mark completion
                        self.queue.mark_item_completed(item.id, success)
                        
                        # Record action
                        self.rate_limiter.record_action_completion(success)
                        self.scheduler.record_action_execution(item.action_type, success)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing item {item.id}: {e}")
                        self.queue.mark_item_completed(item.id, False)
                
                # Wait before next item
                time.sleep(delay)
                
        finally:
            self.processing = False
            self.logger.info("Queue processing stopped")
    
    def stop_processing(self):
        """Stop processing queue items"""
        self.should_stop.set()
        self.logger.info("Stopping queue processing...")