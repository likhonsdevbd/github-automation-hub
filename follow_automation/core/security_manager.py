"""
Anti-Detection Strategies and Security System
Implements compliant anti-detection without evasion tactics
"""
import time
import hashlib
import random
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
import logging
from ..config.settings import FollowAutomationConfig

class DetectionLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class SecurityProfile:
    """Security profile for API requests"""
    user_agent: str
    request_headers: Dict[str, str]
    timing_profile: str
    risk_level: DetectionLevel

class UserAgentRotator:
    """
    Rotates user agents for legitimate request patterns
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # GitHub API user agents (realistic patterns)
        self.user_agents = [
            "GitHubDesktop/3.3.5 (Windows; x64)",
            "GitHubDesktop/3.3.5 (macOS; x64)",
            "GitHubDesktop/3.3.5 (Linux; x86_64)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.current_index = 0
        self.rotation_schedule: Dict[str, datetime] = {}
    
    def get_user_agent(self, action_type: str = "api") -> str:
        """Get rotated user agent"""
        if not self.config.security.user_agent_rotation:
            return self.user_agents[0]
        
        # Check if we should rotate
        if action_type in self.rotation_schedule:
            next_rotation = self.rotation_schedule[action_type]
            if datetime.now() < next_rotation:
                # Return current agent
                return self.user_agents[self.current_index]
        
        # Rotate to next agent
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        
        # Schedule next rotation (random interval)
        rotation_interval = random.uniform(30, 120)  # 30-120 minutes
        self.rotation_schedule[action_type] = datetime.now() + timedelta(minutes=rotation_interval)
        
        agent = self.user_agents[self.current_index]
        self.logger.debug(f"Rotated user agent: {agent}")
        
        return agent
    
    def add_custom_user_agent(self, user_agent: str):
        """Add custom user agent to rotation"""
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)
            self.logger.info(f"Added custom user agent: {user_agent}")

class SessionManager:
    """
    Manages HTTP sessions for persistent connections
    Implements legitimate session handling patterns
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        self.last_activity = datetime.now()
        
        # Session settings
        self.session.timeout = 30
        self.session.max_redirects = 5
        
        # Security headers
        self.default_headers = {
            "Accept": "application/vnd.github.v3+json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with proper configuration"""
        # Set default headers
        self.session.headers.update(self.default_headers)
        
        # Configure session behavior
        self.session.max_redirects = 5
        self.session.allow_redirects = True
        
        # Set up adapters with retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info(f"Session initialized: {self.session_id}")
    
    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with session management"""
        # Update activity timestamp
        self.last_activity = datetime.now()
        
        # Add session-specific headers
        headers = kwargs.get("headers", {})
        headers.update(self.default_headers)
        kwargs["headers"] = headers
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)
            
            # Update activity on successful requests
            if response.status_code < 400:
                self.last_activity = datetime.now()
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise
    
    def get_session_info(self) -> Dict:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "last_activity": self.last_activity.isoformat(),
            "session_age_seconds": (datetime.now() - self.last_activity).total_seconds(),
            "persistent": self.config.security.session_persistence
        }
    
    def close_session(self):
        """Close session gracefully"""
        if self.session:
            self.session.close()
            self.logger.info(f"Session closed: {self.session_id}")

class RequestPatternManager:
    """
    Manages request patterns to avoid detection
    Implements legitimate timing and pattern variations
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Pattern history for analysis
        self.request_history: List[datetime] = []
        self.pattern_variance_threshold = 0.3
        
        # Burst management
        self.current_burst_size = 0
        self.max_burst_size = 3
        self.burst_cooldown = 0
    
    def analyze_request_pattern(self) -> Dict:
        """Analyze current request pattern"""
        if len(self.request_history) < 5:
            return {"pattern_analysis": "insufficient_data"}
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(self.request_history)):
            interval = (self.request_history[i] - self.request_history[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return {"pattern_analysis": "no_intervals"}
        
        # Calculate statistics
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        cv = std_dev / mean_interval if mean_interval > 0 else 0
        
        # Assess pattern
        if cv < self.pattern_variance_threshold:
            pattern_type = "too_regular"
            risk_level = "medium"
        elif cv > 1.0:
            pattern_type = "irregular"
            risk_level = "low"
        else:
            pattern_type = "normal"
            risk_level = "low"
        
        return {
            "pattern_analysis": pattern_type,
            "risk_level": risk_level,
            "coefficient_variation": cv,
            "mean_interval_seconds": mean_interval,
            "std_dev_seconds": std_dev,
            "recent_interval": intervals[-1] if intervals else None
        }
    
    def should_request_be_delayed(self) -> float:
        """Determine if request should be delayed and for how long"""
        analysis = self.analyze_request_pattern()
        
        # If pattern is too regular, add extra delay
        if analysis.get("pattern_analysis") == "too_regular":
            extra_delay = random.uniform(5, 15)
            self.logger.debug(f"Adding extra delay due to regular pattern: {extra_delay:.1f}s")
            return extra_delay
        
        # Check burst limits
        if self.current_burst_size >= self.max_burst_size:
            burst_delay = random.uniform(30, 60)
            self.logger.debug(f"Burst limit reached, delaying: {burst_delay:.1f}s")
            return burst_delay
        
        return 0.0
    
    def record_request(self):
        """Record request execution"""
        self.request_history.append(datetime.now())
        self.current_burst_size += 1
        
        # Clean old history (keep last 100 requests)
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]
        
        # Reset burst counter after cooldown
        if self.burst_cooldown <= 0:
            pass  # No cooldown needed
        else:
            self.burst_cooldown -= 1
    
    def reset_burst_counter(self):
        """Reset burst counter after inter-burst delay"""
        self.current_burst_size = 0
        self.burst_cooldown = 5  # 5 requests cooldown

class ComplianceMonitor:
    """
    Monitors compliance with platform policies and rate limits
    Implements early warning system for detection
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Compliance tracking
        self.api_calls_history: List[Dict] = []
        self.rate_limit_events: List[Dict] = []
        self.enforcement_alerts: List[Dict] = []
        
        # Thresholds
        self.rate_limit_threshold = 10  # Requests per minute
        self.error_rate_threshold = 0.05  # 5% error rate
        self.cooldown_events_threshold = 3  # Max cooldown events per hour
    
    def record_api_call(self, endpoint: str, method: str, 
                       response_code: int, response_time_ms: Optional[float] = None):
        """Record API call for compliance monitoring"""
        call_record = {
            "timestamp": datetime.now(),
            "endpoint": endpoint,
            "method": method,
            "response_code": response_code,
            "response_time_ms": response_time_ms
        }
        
        self.api_calls_history.append(call_record)
        
        # Analyze for compliance issues
        self._analyze_compliance(call_record)
        
        # Clean old records (keep last 1000 calls)
        if len(self.api_calls_history) > 1000:
            self.api_calls_history = self.api_calls_history[-1000:]
    
    def _analyze_compliance(self, call_record: Dict):
        """Analyze single call for compliance issues"""
        response_code = call_record["response_code"]
        
        # Handle different response codes
        if response_code == 429:
            self._handle_rate_limit(call_record)
        elif response_code == 422:
            self._handle_validation_error(call_record)
        elif response_code >= 400:
            self._handle_api_error(call_record)
    
    def _handle_rate_limit(self, call_record: Dict):
        """Handle rate limit response"""
        self.rate_limit_events.append({
            "timestamp": datetime.now(),
            "endpoint": call_record["endpoint"],
            "method": call_record["method"],
            "severity": "high"
        })
        
        # Check rate limit frequency
        recent_limits = self._get_recent_rate_limits(minutes=60)
        if len(recent_limits) > 3:
            self._trigger_enforcement_alert(
                "Frequent rate limits detected",
                "High frequency of 429 responses",
                "medium"
            )
        
        self.logger.warning("Rate limit response received")
    
    def _handle_validation_error(self, call_record: Dict):
        """Handle validation error (422)"""
        self._trigger_enforcement_alert(
            "Validation error detected",
            "Potential spam or policy violation",
            "critical"
        )
        
        self.logger.error("Validation error (422) received - potential enforcement")
    
    def _handle_api_error(self, call_record: Dict):
        """Handle other API errors"""
        if call_record["response_code"] >= 500:
            self.logger.warning(f"Server error: {call_record['response_code']}")
        else:
            self.logger.info(f"Client error: {call_record['response_code']}")
    
    def _get_recent_rate_limits(self, minutes: int) -> List[Dict]:
        """Get rate limit events from last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            event for event in self.rate_limit_events
            if event["timestamp"] > cutoff
        ]
    
    def _trigger_enforcement_alert(self, title: str, message: str, severity: str):
        """Trigger enforcement alert"""
        alert = {
            "timestamp": datetime.now(),
            "title": title,
            "message": message,
            "severity": severity
        }
        
        self.enforcement_alerts.append(alert)
        
        self.logger.critical(f"Enforcement alert ({severity}): {title} - {message}")
    
    def get_compliance_status(self) -> Dict:
        """Get current compliance status"""
        now = datetime.now()
        
        # Calculate recent metrics
        recent_calls = [
            call for call in self.api_calls_history
            if call["timestamp"] > now - timedelta(minutes=10)
        ]
        
        recent_errors = [
            call for call in recent_calls
            if call["response_code"] >= 400
        ]
        
        error_rate = len(recent_errors) / max(len(recent_calls), 1)
        
        # Get rate limit events
        recent_rate_limits = self._get_recent_rate_limits(60)
        
        # Determine overall compliance level
        if error_rate > 0.1 or len(recent_rate_limits) > 5:
            compliance_level = "poor"
        elif error_rate > 0.05 or len(recent_rate_limits) > 2:
            compliance_level = "fair"
        elif error_rate > 0.02 or len(recent_rate_limits) > 0:
            compliance_level = "good"
        else:
            compliance_level = "excellent"
        
        return {
            "compliance_level": compliance_level,
            "recent_calls_10min": len(recent_calls),
            "error_rate_10min": error_rate,
            "rate_limit_events_1h": len(recent_rate_limits),
            "enforcement_alerts": len(self.enforcement_alerts),
            "active_alerts": [
                alert for alert in self.enforcement_alerts
                if alert["timestamp"] > now - timedelta(hours=1)
            ]
        }
    
    def export_compliance_report(self, filepath: str):
        """Export compliance report"""
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "compliance_status": self.get_compliance_status(),
            "rate_limit_events": [
                {
                    "timestamp": event["timestamp"].isoformat(),
                    "endpoint": event["endpoint"],
                    "severity": event["severity"]
                }
                for event in self.rate_limit_events[-50:]  # Last 50 events
            ],
            "enforcement_alerts": [
                {
                    "timestamp": alert["timestamp"].isoformat(),
                    "title": alert["title"],
                    "severity": alert["severity"]
                }
                for alert in self.enforcement_alerts[-20:]  # Last 20 alerts
            ]
        }
        
        import json
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Compliance report exported to {filepath}")

class SecurityManager:
    """
    Main security coordination class
    """
    
    def __init__(self, config: FollowAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.user_agent_rotator = UserAgentRotator(config)
        self.session_manager = SessionManager(config)
        self.pattern_manager = RequestPatternManager(config)
        self.compliance_monitor = ComplianceMonitor(config)
        
        # Security profile
        self.current_profile = self._create_security_profile()
    
    def _create_security_profile(self) -> SecurityProfile:
        """Create current security profile"""
        return SecurityProfile(
            user_agent=self.user_agent_rotator.get_user_agent(),
            request_headers=self.session_manager.default_headers,
            timing_profile="conservative",
            risk_level=DetectionLevel.LOW
        )
    
    def prepare_request(self, endpoint: str, method: str = "GET") -> Dict:
        """Prepare request with security measures"""
        # Apply timing delays if needed
        delay = self.pattern_manager.should_request_be_delayed()
        if delay > 0:
            time.sleep(delay)
        
        # Get current security profile
        user_agent = self.user_agent_rotator.get_user_agent()
        headers = self.session_manager.default_headers.copy()
        headers["User-Agent"] = user_agent
        
        # Update profile
        self.current_profile = SecurityProfile(
            user_agent=user_agent,
            request_headers=headers,
            timing_profile="conservative",
            risk_level=DetectionLevel.LOW
        )
        
        return {
            "headers": headers,
            "delay": delay
        }
    
    def execute_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute request with full security measures"""
        # Prepare request
        prep = self.prepare_request(url, method)
        
        # Merge prepared headers with request headers
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update(prep["headers"])
        
        # Execute request
        try:
            response = self.session_manager.make_request(method, url, **kwargs)
            
            # Record for compliance monitoring
            self.compliance_monitor.record_api_call(
                endpoint=url,
                method=method,
                response_code=response.status_code,
                response_time_ms=getattr(response, "elapsed", None) and response.elapsed.total_seconds() * 1000
            )
            
            # Record in pattern manager
            self.pattern_manager.record_request()
            
            return response
            
        except requests.exceptions.RequestException as e:
            # Record error
            self.compliance_monitor.record_api_call(
                endpoint=url,
                method=method,
                response_code=0  # Error status
            )
            raise
    
    def get_security_status(self) -> Dict:
        """Get current security status"""
        return {
            "security_profile": {
                "user_agent": self.current_profile.user_agent,
                "timing_profile": self.current_profile.timing_profile,
                "risk_level": self.current_profile.risk_level.value
            },
            "session_info": self.session_manager.get_session_info(),
            "pattern_analysis": self.pattern_manager.analyze_request_pattern(),
            "compliance_status": self.compliance_monitor.get_compliance_status()
        }
    
    def cleanup(self):
        """Cleanup security resources"""
        self.session_manager.close_session()
        self.logger.info("Security resources cleaned up")