#!/usr/bin/env python3
"""
Timing Manager
Manages timing and scheduling for natural commit patterns
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import pytz

class TimingManager:
    """Manages timing for natural commit patterns"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.commit_history_file = ".commit_history.json"
        self.last_commit_time = self._load_last_commit_time()
        self.timezone = pytz.timezone(self.config.get("timezone", "UTC"))
        
        # Load commit patterns from config
        self.working_hours_start = self.config.get("working_hours_start", 9)
        self.working_hours_end = self.config.get("working_hours_end", 17)
        self.commit_frequency = self.config.get("commit_frequency", "2-4_per_day")
        self.break_between_commits = self.config.get("break_between_commits", [2, 8])  # hours
        self.avoid_weekends = self.config.get("avoid_weekends", True)
        self.random_offset = self.config.get("random_offset", 30)  # minutes
        
        # Time zones that might indicate different working patterns
        self.timezones = {
            "US_EAST": "America/New_York",
            "US_WEST": "America/Los_Angeles", 
            "EUROPE": "Europe/London",
            "ASIA": "Asia/Tokyo",
            "AUSTRALIA": "Australia/Sydney"
        }
    
    def _load_last_commit_time(self) -> Optional[datetime]:
        """Load the timestamp of the last commit"""
        try:
            if Path(self.commit_history_file).exists():
                with open(self.commit_history_file, 'r') as f:
                    history = json.load(f)
                    if history:
                        last_commit = history[-1]
                        return datetime.fromisoformat(last_commit['timestamp'])
        except Exception as e:
            self.logger.warning(f"Could not load commit history: {str(e)}")
        return None
    
    def _save_commit_time(self, commit_time: datetime):
        """Save commit time to history"""
        try:
            history = []
            if Path(self.commit_history_file).exists():
                with open(self.commit_history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new commit
            history.append({
                "timestamp": commit_time.isoformat(),
                "date": commit_time.strftime("%Y-%m-%d"),
                "hour": commit_time.hour,
                "minute": commit_time.minute
            })
            
            # Keep only last 100 commits
            history = history[-100:]
            
            with open(self.commit_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Could not save commit history: {str(e)}")
    
    def is_good_time_for_commit(self) -> bool:
        """Determine if now is a good time to make commits"""
        current_time = datetime.now(self.timezone)
        
        # Check if we should avoid weekends
        if self.avoid_weekends and current_time.weekday() >= 5:  # Saturday=5, Sunday=6
            self.logger.info("Skipping weekend commits")
            return False
        
        # Check working hours
        if not self._is_within_working_hours(current_time):
            return False
        
        # Check commit frequency limits
        if self._exceeds_daily_commit_limit(current_time):
            return False
        
        # Check minimum time since last commit
        if not self._enough_time_since_last_commit():
            return False
        
        # Check random probability
        if not self._should_commit_now(current_time):
            return False
        
        return True
    
    def _is_within_working_hours(self, current_time: datetime) -> bool:
        """Check if current time is within working hours"""
        hour = current_time.hour
        
        # Check if within working hours (with some flexibility)
        if (hour >= self.working_hours_start - 1 and 
            hour <= self.working_hours_end + 1):
            return True
        
        # Check for lunch break (12-13h usually not good for commits)
        if 12 <= hour <= 13:
            return False
        
        return False
    
    def _exceeds_daily_commit_limit(self, current_time: datetime) -> bool:
        """Check if we've exceeded today's commit limit"""
        try:
            daily_limit = self._get_daily_commit_limit()
            today = current_time.strftime("%Y-%m-%d")
            
            if Path(self.commit_history_file).exists():
                with open(self.commit_history_file, 'r') as f:
                    history = json.load(f)
                
                today_commits = [
                    commit for commit in history 
                    if commit.get('date') == today
                ]
                
                if len(today_commits) >= daily_limit:
                    self.logger.info(f"Daily commit limit ({daily_limit}) reached")
                    return True
        except Exception as e:
            self.logger.warning(f"Could not check daily limit: {str(e)}")
        
        return False
    
    def _get_daily_commit_limit(self) -> int:
        """Get daily commit limit based on frequency setting"""
        frequency_map = {
            "1_per_day": 1,
            "2_per_day": 2,
            "2-3_per_day": 3,
            "2-4_per_day": 4,
            "3-5_per_day": 5,
            "5_per_day": 5,
            "unlimited": 10
        }
        return frequency_map.get(self.commit_frequency, 3)
    
    def _enough_time_since_last_commit(self) -> bool:
        """Check if enough time has passed since last commit"""
        if not self.last_commit_time:
            return True
        
        # Get min break time from config
        min_break_hours = self.break_between_commits[0]
        min_break_delta = timedelta(hours=min_break_hours)
        
        time_since_last = datetime.now(self.timezone) - self.last_commit_time.replace(tzinfo=self.timezone)
        
        if time_since_last < min_break_delta:
            self.logger.info(f"Not enough time since last commit: {time_since_last}")
            return False
        
        return True
    
    def _should_commit_now(self, current_time: datetime) -> bool:
        """Determine if we should commit now based on various factors"""
        # Check time-based probability
        hour = current_time.hour
        
        # Peak productivity hours (9-11, 14-16)
        if 9 <= hour <= 11 or 14 <= hour <= 16:
            probability = 0.7  # 70% chance
        # Shoulder hours (8, 12-13, 17)
        elif hour in [8, 12, 13, 17]:
            probability = 0.4  # 40% chance
        # Low activity hours
        else:
            probability = 0.1  # 10% chance
        
        return random.random() < probability
    
    def can_make_commit(self) -> bool:
        """Check if we can make a commit right now"""
        return self.is_good_time_for_commit()
    
    def get_next_good_time(self) -> datetime:
        """Calculate the next good time for commits"""
        current_time = datetime.now(self.timezone)
        
        # Try next hour
        next_time = current_time.replace(
            minute=0, 
            second=0, 
            microsecond=0
        ) + timedelta(hours=1)
        
        # Add random offset within the hour
        random_minutes = random.randint(0, 59)
        next_time += timedelta(minutes=random_minutes)
        
        # Adjust for working hours if needed
        if not self._is_within_working_hours(next_time):
            # Find next working hour
            while not self._is_within_working_hours(next_time):
                next_time += timedelta(hours=1)
        
        return next_time
    
    def record_commit(self):
        """Record that a commit was made"""
        commit_time = datetime.now(self.timezone)
        self.last_commit_time = commit_time
        self._save_commit_time(commit_time)
        
        # Add some randomness to the next commit time
        self._set_next_commit_probability()
    
    def _set_next_commit_probability(self):
        """Set probability for next commit based on time since last commit"""
        # This could be used to implement more sophisticated timing
        pass
    
    def get_commit_pattern_analysis(self) -> Dict:
        """Analyze past commit patterns"""
        if not Path(self.commit_history_file).exists():
            return {"status": "no_history", "message": "No commit history available"}
        
        try:
            with open(self.commit_history_file, 'r') as f:
                history = json.load(f)
            
            if not history:
                return {"status": "no_commits", "message": "No commits in history"}
            
            # Analyze patterns
            analysis = self._analyze_commit_patterns(history)
            return analysis
        except Exception as e:
            self.logger.error(f"Could not analyze commit patterns: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _analyze_commit_patterns(self, history: List[Dict]) -> Dict:
        """Analyze commit patterns from history"""
        if not history:
            return {"status": "empty"}
        
        # Convert to datetime objects
        commits = []
        for entry in history:
            try:
                dt = datetime.fromisoformat(entry['timestamp'])
                commits.append(dt)
            except ValueError:
                continue
        
        if not commits:
            return {"status": "invalid_data"}
        
        commits.sort()
        
        # Calculate statistics
        total_commits = len(commits)
        days_with_commits = len(set(c.date() for c in commits))
        
        # Hour distribution
        hour_counts = {}
        for commit in commits:
            hour = commit.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Day of week distribution
        dow_counts = {}
        for commit in commits:
            dow = commit.strftime("%A")
            dow_counts[dow] = dow_counts.get(dow, 0) + 1
        
        # Time gaps between commits
        gaps = []
        for i in range(1, len(commits)):
            gap = commits[i] - commits[i-1]
            gaps.append(gap.total_seconds() / 3600)  # hours
        
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        # Peak hours
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 0
        peak_day = max(dow_counts.items(), key=lambda x: x[1])[0] if dow_counts else "Unknown"
        
        return {
            "status": "analyzed",
            "total_commits": total_commits,
            "days_with_commits": days_with_commits,
            "commits_per_day": round(total_commits / max(days_with_commits, 1), 2),
            "peak_hour": peak_hour,
            "peak_day": peak_day,
            "average_gap_hours": round(avg_gap, 2),
            "hour_distribution": dict(sorted(hour_counts.items())),
            "day_distribution": dow_counts,
            "last_commit": commits[-1].isoformat(),
            "recommendations": self._generate_timing_recommendations(hour_counts, dow_counts, avg_gap)
        }
    
    def _generate_timing_recommendations(self, hour_counts: Dict, dow_counts: Dict, avg_gap: float) -> List[str]:
        """Generate recommendations based on timing patterns"""
        recommendations = []
        
        # Analyze hour patterns
        if hour_counts:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            recommendations.append(f"Your most active commit hour is {peak_hour}:00")
            
            # Check for concentrated activity
            if max(hour_counts.values()) > sum(hour_counts.values()) * 0.4:
                recommendations.append("Try spreading commits more evenly throughout the day")
        
        # Analyze day patterns
        if dow_counts:
            total_dow_commits = sum(dow_counts.values())
            weekend_commits = dow_counts.get("Saturday", 0) + dow_counts.get("Sunday", 0)
            
            if weekend_commits > 0:
                recommendations.append("Weekend commits detected - consider if this aligns with your goals")
            
            if self.avoid_weekends and weekend_commits > 0:
                recommendations.append("Weekend commits detected but weekends should be avoided per config")
        
        # Analyze timing gaps
        if avg_gap < 1:
            recommendations.append("Commits are very frequent - consider increasing gaps between commits")
        elif avg_gap > 12:
            recommendations.append("Large gaps between commits - consider more frequent contributions")
        
        # Check against working hours
        working_hours_commits = sum(
            count for hour, count in hour_counts.items() 
            if self.working_hours_start <= hour < self.working_hours_end
        )
        
        if working_hours_commits < len(hour_counts) * 0.6:
            recommendations.append("Consider aligning commit times with standard working hours")
        
        if not recommendations:
            recommendations.append("Commit timing patterns look good")
        
        return recommendations
    
    def simulate_natural_timing(self) -> Dict:
        """Simulate natural commit timing patterns"""
        patterns = {}
        
        # Simulate different activity levels
        activity_levels = {
            "light": {"frequency": 1, "peak_hours": [10, 15], "probability": 0.3},
            "normal": {"frequency": 3, "peak_hours": [9, 11, 14, 16], "probability": 0.6},
            "heavy": {"frequency": 5, "peak_hours": [8, 9, 10, 11, 14, 15, 16, 17], "probability": 0.8}
        }
        
        # Generate sample timing for a week
        sample_day = datetime.now(self.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        
        for level, config in activity_levels.items():
            daily_times = []
            
            # Generate commit times based on pattern
            for _ in range(config["frequency"]):
                # Select from peak hours with some variation
                if random.random() < config["probability"]:
                    hour = random.choice(config["peak_hours"])
                    # Add some variation around the hour
                    minute = random.randint(0, 59)
                    
                    # Add natural variation (avoid exact hour marks)
                    if minute == 0:
                        minute = random.randint(5, 55)
                    
                    commit_time = sample_day.replace(hour=hour, minute=minute)
                    daily_times.append(commit_time.strftime("%H:%M"))
            
            patterns[level] = sorted(daily_times)
        
        return {
            "sample_timing": patterns,
            "recommendation": "Choose a level that matches your desired activity",
            "note": "These are example patterns - actual timing will vary naturally"
        }
    
    def get_timing_summary(self) -> Dict:
        """Get summary of current timing configuration"""
        current_time = datetime.now(self.timezone)
        
        return {
            "current_time": current_time.isoformat(),
            "timezone": str(self.timezone),
            "working_hours": f"{self.working_hours_start}:00 - {self.working_hours_end}:00",
            "commit_frequency": self.commit_frequency,
            "daily_limit": self._get_daily_commit_limit(),
            "avoid_weekends": self.avoid_weekends,
            "break_between_commits_hours": self.break_between_commits,
            "last_commit": self.last_commit_time.isoformat() if self.last_commit_time else "never",
            "can_commit_now": self.can_make_commit(),
            "next_good_time": self.get_next_good_time().isoformat(),
            "pattern_analysis": self.get_commit_pattern_analysis()
        }
