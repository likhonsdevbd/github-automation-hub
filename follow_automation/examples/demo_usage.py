#!/usr/bin/env python3
"""
Example usage script for the Follow Automation System
Demonstrates safe automation with proper configuration
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add automation modules to path
sys.path.append(str(Path(__file__).parent.parent))

from main_orchestrator import FollowAutomationOrchestrator
from config.settings import FollowAutomationConfig, ActionType

def setup_example_environment():
    """Set up example environment for testing"""
    # Set required environment variables
    os.environ["GITHUB_TOKEN"] = "your_github_token_here"
    
    # Optional: Set custom limits
    os.environ["MAX_ACTIONS_PER_HOUR"] = "6"  # Conservative 6 per hour
    
    print("Environment configured for follow automation")

def demonstrate_safe_following():
    """Demonstrate safe following patterns"""
    print("\n=== Safe Follow Automation Demo ===")
    
    # Initialize orchestrator
    orchestrator = FollowAutomationOrchestrator()
    
    # Add some high-relevance targets
    high_relevance_targets = [
        {
            "username": "octocat",
            "context": {
                "public_repos": 50,
                "followers": 100000,
                "following": 200,
                "shared_languages": ["JavaScript", "Python"],
                "activity_level": "high",
                "relevance_score": 4.5
            }
        },
        {
            "username": "torvalds", 
            "context": {
                "public_repos": 100,
                "followers": 200000,
                "following": 100,
                "shared_languages": ["C", "C++"],
                "activity_level": "moderate",
                "relevance_score": 4.0
            }
        },
        {
            "username": "gaearon",  # Dan Abramov
            "context": {
                "public_repos": 80,
                "followers": 50000,
                "following": 500,
                "shared_languages": ["JavaScript", "TypeScript"],
                "activity_level": "high",
                "relevance_score": 3.8
            }
        }
    ]
    
    print("Adding high-relevance follow targets...")
    for target in high_relevance_targets:
        success = orchestrator.add_follow_action(
            target["username"],
            target["context"]
        )
        print(f"  {target['username']}: {'Added' if success else 'Failed'}")
    
    return orchestrator

def demonstrate_unfollow_scheduling():
    """Demonstrate unfollow scheduling based on risk analysis"""
    print("\n=== Unfollow Scheduling Demo ===")
    
    orchestrator = FollowAutomationOrchestrator()
    
    # Simulate users that should be unfollowed
    unfollow_candidates = [
        {
            "username": "inactive_user",
            "reason": "Inactive for 180+ days, low relevance",
            "context": {
                "last_active_days": 365,
                "public_repos": 0,
                "followers": 10,
                "following": 5000,
                "activity_level": "inactive"
            }
        },
        {
            "username": "spam_account",
            "reason": "Poor follower ratio, low activity",
            "context": {
                "last_active_days": 90,
                "public_repos": 0,
                "followers": 50,
                "following": 10000,
                "activity_level": "low"
            }
        },
        {
            "username": "unrelated_tech",
            "reason": "Different technology stack",
            "context": {
                "last_active_days": 30,
                "public_repos": 20,
                "followers": 500,
                "following": 2000,
                "shared_languages": [],  # No overlap
                "activity_level": "moderate"
            }
        }
    ]
    
    print("Adding unfollow candidates...")
    for candidate in unfollow_candidates:
        success = orchestrator.add_unfollow_action(
            candidate["username"],
            candidate["reason"]
        )
        print(f"  {candidate['username']}: {'Scheduled' if success else 'Failed'}")
    
    return orchestrator

def demonstrate_monitoring():
    """Demonstrate system monitoring and reporting"""
    print("\n=== System Monitoring Demo ===")
    
    orchestrator = FollowAutomationOrchestrator()
    
    # Run a brief automation cycle
    orchestrator.start_automation()
    
    # Add some actions
    orchestrator.add_follow_action("octocat")
    
    # Monitor for a short period
    print("Monitoring automation for 10 seconds...")
    for i in range(10):
        if not orchestrator.state.is_running:
            break
        
        status = orchestrator.get_system_status()
        print(f"  Update {i+1}/10:")
        print(f"    Running: {status['is_running']}")
        print(f"    Queue size: {status['components']['queue']['queue_size']}")
        print(f"    Actions today: {status['statistics']['total_follows']}")
        
        # Show compliance status
        compliance = status['components']['security']['compliance_status']
        print(f"    Compliance level: {compliance['compliance_level']}")
        
        import time
        time.sleep(1)
    
    # Generate reports
    print("\nGenerating reports...")
    reports = orchestrator.export_reports("demo_reports")
    print(f"  Exported {len(reports)} reports:")
    for report in reports:
        print(f"    - {report}")
    
    orchestrator.stop_automation()
    
    return status

def demonstrate_batch_processing():
    """Demonstrate batch processing for multiple users"""
    print("\n=== Batch Processing Demo ===")
    
    orchestrator = FollowAutomationOrchestrator()
    
    # Example user lists from file or external source
    collaborator_targets = [
        {
            "username": "githubteacher",
            "context": {"activity_level": "high", "shared_organizations": ["github"]}
        },
        {
            "username": "tj",
            "context": {"activity_level": "high", "shared_languages": ["JavaScript"]}
        },
        {
            "username": "getify",
            "context": {"activity_level": "moderate", "shared_languages": ["JavaScript"]}
        },
        {
            "username": "substack",
            "context": {"activity_level": "moderate", "shared_languages": ["JavaScript"]}
        },
        {
            "username": "过兰秋_真白",  # Example international developer
            "context": {"activity_level": "low", "shared_languages": ["Python"]}
        }
    ]
    
    print(f"Processing batch of {len(collaborator_targets)} targets...")
    
    # Add all targets
    for target in collaborator_targets:
        success = orchestrator.add_follow_action(
            target["username"],
            target["context"]
        )
        print(f"  {target['username']}: {'Added' if success else 'Failed'}")
    
    print("\nBatch processing complete. Targets queued with prioritization.")
    return orchestrator

def run_comprehensive_demo():
    """Run a comprehensive demonstration of all features"""
    print("=" * 60)
    print("Follow/Unfollow Automation System - Comprehensive Demo")
    print("=" * 60)
    
    try:
        # Setup
        setup_example_environment()
        
        # Demonstrate different features
        print("\n1. Safe Following")
        orchestrator1 = demonstrate_safe_following()
        
        print("\n2. Unfollow Scheduling")
        orchestrator2 = demonstrate_unfollow_scheduling()
        
        print("\n3. Batch Processing")  
        orchestrator3 = demonstrate_batch_processing()
        
        print("\n4. System Monitoring")
        final_status = demonstrate_monitoring()
        
        # Show final summary
        print("\n" + "=" * 60)
        print("Demo Summary")
        print("=" * 60)
        print(f"Session ID: {final_status['session_id']}")
        print(f"Total follows: {final_status['statistics']['total_follows']}")
        print(f"Total unfollows: {final_status['statistics']['total_unfollows']}")
        print(f"Compliance level: {final_status['components']['security']['compliance_status']['compliance_level']}")
        
        # Show rate limiting effectiveness
        rl_stats = final_status['components']['rate_limiter']
        print(f"Rate limit success: {rl_stats['success_rate_percent']}%")
        print(f"Rate limit events: {rl_stats['rate_limit_events']}")
        
        print("\nDemo completed successfully!")
        print("Check the generated reports in the demo_reports directory.")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_demo()