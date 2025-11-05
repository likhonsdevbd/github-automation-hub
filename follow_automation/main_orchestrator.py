"""
Main Follow Automation Orchestrator
Coordinates all components of the follow/unfollow automation system
"""
import os
import sys
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import FollowAutomationConfig, ActionType
from core.rate_limiter import RateLimiter, ActionQueue
from core.security_manager import SecurityManager
from scheduling.timing_system import HumanLikeScheduler
from queue.queue_manager import FollowQueue, QueueProcessor
from detection.follow_back_detector import FollowBackDetector, UnfollowScheduler
from tracking.roi_optimizer import MetricsCollector, ROICalculator, OptimizationEngine, AnalyticsDashboard

@dataclass
class AutomationState:
    """Current automation state"""
    is_running: bool = False
    last_follow_action: Optional[datetime] = None
    last_unfollow_action: Optional[datetime] = None
    total_follows: int = 0
    total_unfollows: int = 0
    session_id: str = ""

class FollowAutomationOrchestrator:
    """
    Main orchestrator class that coordinates all automation components
    """
    
    def __init__(self, config_file: Optional[str] = None):
        # Load configuration
        self.config = FollowAutomationConfig()
        if config_file:
            self._load_config_from_file(config_file)
        else:
            self._load_env_config()
        
        # Validate configuration
        self.config.validate()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.state = AutomationState()
        self.state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize components
        self._initialize_components()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(f"Follow automation orchestrator initialized: {self.state.session_id}")
    
    def _load_config_from_file(self, config_file: str):
        """Load configuration from file (if implemented)"""
        # Placeholder for future configuration file loading
        pass
    
    def _load_env_config(self):
        """Load configuration from environment variables"""
        self.config.get_env_config()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'follow_automation_{datetime.now().strftime("%Y%m%d")}.log')
            ]
        )
    
    def _initialize_components(self):
        """Initialize all automation components"""
        self.logger.info("Initializing automation components...")
        
        # Core components
        self.rate_limiter = RateLimiter(self.config)
        self.security_manager = SecurityManager(self.config)
        self.scheduler = HumanLikeScheduler(self.config)
        
        # Queue management
        self.follow_queue = FollowQueue(self.config)
        self.action_queue = ActionQueue(self.config)
        
        # Detection and analysis
        self.follow_back_detector = FollowBackDetector(
            self.config, 
            self.security_manager.session_manager.session
        )
        self.unfollow_scheduler = UnfollowScheduler(self.config)
        
        # Metrics and tracking
        db_path = f"metrics_{self.state.session_id}.db"
        self.metrics_collector = MetricsCollector(self.config, db_path)
        self.roi_calculator = ROICalculator(self.config, self.metrics_collector)
        self.optimizer = OptimizationEngine(self.config, self.metrics_collector)
        self.dashboard = AnalyticsDashboard(
            self.metrics_collector, 
            self.roi_calculator, 
            self.optimizer
        )
        
        # Queue processor
        self.queue_processor = QueueProcessor(
            self.config,
            self.follow_queue,
            self.rate_limiter,
            self.scheduler
        )
        
        # Set up processing callback
        self.follow_queue.processing_callback = self._execute_action
        
        self.logger.info("All components initialized successfully")
    
    def _execute_action(self, queue_item) -> bool:
        """Execute action via API"""
        try:
            action_type = queue_item.action_type
            username = queue_item.target_username
            
            self.logger.info(f"Executing {action_type.value} for {username}")
            
            # Prepare request
            prep = self.security_manager.prepare_request(
                self.config.api_base_url + self.config.endpoints["follow"]
                if action_type == ActionType.FOLLOW else
                self.config.api_base_url + self.config.endpoints["unfollow"]
            )
            
            # Execute API call
            endpoint_path = self.config.endpoints["follow"].format(username=username) \
                           if action_type == ActionType.FOLLOW else \
                           self.config.endpoints["unfollow"].format(username=username)
            
            full_url = f"{self.config.api_base_url}{endpoint_path}"
            method = "PUT" if action_type == ActionType.FOLLOW else "DELETE"
            
            response = self.security_manager.execute_request(method, full_url)
            
            # Record metrics
            success = response.status_code in [204, 304]
            
            from tracking.roi_optimizer import ActionMetrics
            metrics = ActionMetrics(
                timestamp=datetime.now(),
                action_type=action_type,
                target_username=username,
                success=success,
                response_code=response.status_code,
                relevance_score=queue_item.relevance_score
            )
            
            self.metrics_collector.record_action(metrics)
            
            # Update follow back detector
            if action_type == ActionType.FOLLOW:
                self.follow_back_detector.record_follow_action(username)
            else:
                self.follow_back_detector.record_unfollow_action(username)
            
            # Update state
            if action_type == ActionType.FOLLOW:
                self.state.total_follows += 1
                self.state.last_follow_action = datetime.now()
            else:
                self.state.total_unfollows += 1
                self.state.last_unfollow_action = datetime.now()
            
            self.rate_limiter.record_action_completion(
                success, 
                response.status_code,
                int(response.headers.get("Retry-After", 0))
            )
            
            self.logger.info(f"{action_type.value} completed: {username} "
                           f"({'success' if success else 'failed'}) - "
                           f"status: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing action for {queue_item.target_username}: {e}")
            self.rate_limiter.record_action_completion(False)
            return False
    
    def start_automation(self):
        """Start the automation system"""
        if self.state.is_running:
            self.logger.warning("Automation is already running")
            return
        
        self.state.is_running = True
        self.logger.info("Starting follow automation system...")
        
        # Start queue processor in separate thread
        processor_thread = threading.Thread(
            target=self.queue_processor.start_processing,
            daemon=True
        )
        processor_thread.start()
        
        # Start follow-back detection loop
        detection_thread = threading.Thread(
            target=self._follow_back_detection_loop,
            daemon=True
        )
        detection_thread.start()
        
        # Start metrics reporting loop
        reporting_thread = threading.Thread(
            target=self._reporting_loop,
            daemon=True
        )
        reporting_thread.start()
        
        self.logger.info("Automation system started successfully")
    
    def stop_automation(self):
        """Stop the automation system gracefully"""
        if not self.state.is_running:
            self.logger.warning("Automation is not running")
            return
        
        self.logger.info("Stopping automation system...")
        
        # Signal stop
        self.state.is_running = False
        self.queue_processor.stop_processing()
        
        # Cleanup
        self.security_manager.cleanup()
        
        # Export final reports
        self._export_final_reports()
        
        self.logger.info("Automation system stopped")
    
    def _follow_back_detection_loop(self):
        """Background loop for follow-back detection"""
        while self.state.is_running:
            try:
                # Run detection every check interval
                interval_hours = self.config.detection.check_interval_hours
                self.logger.info("Running follow-back detection...")
                
                detection_results = self.follow_back_detector.detect_follow_backs()
                
                if detection_results.get("unfollow_recommendations"):
                    # Add unfollow recommendations to queue
                    for username, reason in detection_results["unfollow_recommendations"].items():
                        context_data = {
                            "unfollow_reason": reason,
                            "detection_date": datetime.now().isoformat()
                        }
                        
                        item_id = self.follow_queue.add_action(
                            ActionType.UNFOLLOW,
                            username,
                            context_data
                        )
                        
                        if item_id:
                            self.logger.info(f"Added unfollow recommendation: {username} - {reason}")
                
                # Sleep until next detection
                for _ in range(interval_hours * 60):  # Sleep in 1-minute intervals
                    if not self.state.is_running:
                        break
                    time.sleep(60)
                    
            except Exception as e:
                self.logger.error(f"Error in follow-back detection loop: {e}")
                time.sleep(300)  # 5-minute cooldown on error
    
    def _reporting_loop(self):
        """Background loop for metrics reporting"""
        while self.state.is_running:
            try:
                # Report every 30 minutes
                time.sleep(1800)
                
                if self.state.is_running:
                    dashboard_data = self.dashboard.get_dashboard_data()
                    self.logger.info(f"Metrics update - Actions today: "
                                   f"{dashboard_data['recent_performance']['actions_last_24h']}")
                    
            except Exception as e:
                self.logger.error(f"Error in reporting loop: {e}")
                time.sleep(300)  # 5-minute cooldown on error
    
    def add_follow_action(self, username: str, context_data: Optional[Dict] = None) -> bool:
        """Add follow action to queue"""
        if context_data is None:
            context_data = {}
        
        item_id = self.follow_queue.add_action(ActionType.FOLLOW, username, context_data)
        
        if item_id:
            self.logger.info(f"Added follow action: {username}")
            return True
        else:
            self.logger.warning(f"Failed to add follow action: {username}")
            return False
    
    def add_unfollow_action(self, username: str, reason: str = "manual") -> bool:
        """Add unfollow action to queue"""
        context_data = {"unfollow_reason": reason}
        item_id = self.follow_queue.add_action(ActionType.UNFOLLOW, username, context_data)
        
        if item_id:
            self.logger.info(f"Added unfollow action: {username} - {reason}")
            return True
        else:
            self.logger.warning(f"Failed to add unfollow action: {username}")
            return False
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "session_id": self.state.session_id,
            "is_running": self.state.is_running,
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_follows": self.state.total_follows,
                "total_unfollows": self.state.total_unfollows,
                "last_follow": (
                    self.state.last_follow_action.isoformat() 
                    if self.state.last_follow_action else None
                ),
                "last_unfollow": (
                    self.state.last_unfollow_action.isoformat() 
                    if self.state.last_unfollow_action else None
                )
            },
            "components": {
                "rate_limiter": self.rate_limiter.get_statistics(),
                "queue": self.follow_queue.get_queue_stats(),
                "detection": self.follow_back_detector.get_detection_statistics(),
                "unfollow_scheduler": self.unfollow_scheduler.get_unfollow_statistics(),
                "security": self.security_manager.get_security_status()
            },
            "metrics": self.dashboard.get_dashboard_data()
        }
    
    def export_reports(self, output_dir: str = "reports") -> List[str]:
        """Export all reports to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        reports = []
        
        try:
            # Dashboard report
            dashboard_file = output_path / f"dashboard_{self.state.session_id}.json"
            dashboard_data = self.dashboard.get_dashboard_data()
            with open(dashboard_file, 'w') as f:
                import json
                json.dump(dashboard_data, f, indent=2)
            reports.append(str(dashboard_file))
            
            # Optimization report
            optimization_file = output_path / f"optimization_{self.state.session_id}.json"
            self.optimizer.export_report(str(optimization_file))
            reports.append(str(optimization_file))
            
            # Detection report
            detection_file = output_path / f"detection_{self.state.session_id}.json"
            self.follow_back_detector.export_detection_data(str(detection_file))
            reports.append(str(detection_file))
            
            # Queue state report
            queue_file = output_path / f"queue_{self.state.session_id}.json"
            self.follow_queue.export_queue_state(str(queue_file))
            reports.append(str(queue_file))
            
            # Compliance report
            compliance_file = output_path / f"compliance_{self.state.session_id}.json"
            self.security_manager.compliance_monitor.export_compliance_report(
                str(compliance_file)
            )
            reports.append(str(compliance_file))
            
            self.logger.info(f"Exported {len(reports)} reports to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error exporting reports: {e}")
        
        return reports
    
    def _export_final_reports(self):
        """Export final reports on shutdown"""
        try:
            reports = self.export_reports("final_reports")
            self.logger.info(f"Final reports exported: {len(reports)} files")
        except Exception as e:
            self.logger.error(f"Error exporting final reports: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop_automation()
        sys.exit(0)
    
    def run_interactive_mode(self):
        """Run in interactive mode for manual control"""
        print(f"\n=== Follow Automation System ===")
        print(f"Session ID: {self.state.session_id}")
        print("Commands:")
        print("  follow <username> - Add follow action")
        print("  unfollow <username> - Add unfollow action")
        print("  status - Show system status")
        print("  reports - Export reports")
        print("  start - Start automation")
        print("  stop - Stop automation")
        print("  quit - Exit")
        print("================================\n")
        
        while True:
            try:
                command = input("> ").strip().split()
                if not command:
                    continue
                
                action = command[0].lower()
                
                if action == "quit":
                    break
                elif action == "follow" and len(command) > 1:
                    username = command[1]
                    self.add_follow_action(username)
                elif action == "unfollow" and len(command) > 1:
                    username = command[1]
                    self.add_unfollow_action(username)
                elif action == "status":
                    status = self.get_system_status()
                    print(f"\nSystem Status:")
                    print(f"Running: {status['is_running']}")
                    print(f"Total follows: {status['statistics']['total_follows']}")
                    print(f"Total unfollows: {status['statistics']['total_unfollows']}")
                    print(f"Queue size: {status['components']['queue']['queue_size']}")
                elif action == "reports":
                    reports = self.export_reports()
                    print(f"\nExported {len(reports)} reports")
                elif action == "start":
                    self.start_automation()
                    print("Automation started")
                elif action == "stop":
                    self.stop_automation()
                    print("Automation stopped")
                else:
                    print("Unknown command or invalid usage")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        self.stop_automation()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Follow/Unfollow Automation System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--daemon", action="store_true",
                       help="Run as daemon (start and monitor)")
    
    args = parser.parse_args()
    
    try:
        orchestrator = FollowAutomationOrchestrator(args.config)
        
        if args.interactive:
            orchestrator.run_interactive_mode()
        elif args.daemon:
            orchestrator.start_automation()
            print("Automation running in daemon mode. Press Ctrl+C to stop.")
            
            try:
                while orchestrator.state.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                orchestrator.stop_automation()
        else:
            # Run a single detection cycle
            print("Running single detection cycle...")
            orchestrator.start_automation()
            
            # Add some example follow actions
            orchestrator.add_follow_action("octocat")
            orchestrator.add_follow_action("torvalds")
            
            # Let it run for a bit
            time.sleep(30)
            
            orchestrator.stop_automation()
            print("Cycle complete. Check logs for results.")
    
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()