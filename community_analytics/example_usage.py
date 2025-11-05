"""
Example usage of the Community Analytics System

This module demonstrates how to use the community analytics system to analyze
a GitHub repository's community health, engagement, and growth patterns.
"""

import asyncio
import json
import os
from datetime import datetime

# Import the community analytics modules
from community_analytics.analytics_orchestrator import CommunityAnalyticsOrchestrator
from community_analytics.core.lifecycle_tracker import MemberLifecycleTracker
from community_analytics.core.engagement_scorer import EngagementScorer
from community_analytics.core.health_indicators import CommunityHealthIndicator
from community_analytics.core.retention_analyzer import RetentionAnalyzer
from community_analytics.core.network_analyzer import SocialNetworkAnalyzer

# For demo purposes, we'll simulate the GitHub API client
class MockGitHubAPIClient:
    """Mock GitHub API client for demonstration purposes"""
    
    def __init__(self, token: str = "demo_token"):
        self.token = token
    
    async def get_contributors(self, owner: str, repo: str):
        # Return mock contributor data
        return [
            {"login": "user1", "id": 1, "contributions": 45},
            {"login": "user2", "id": 2, "contributions": 32},
            {"login": "user3", "id": 3, "contributions": 28},
            {"login": "user4", "id": 4, "contributions": 15},
            {"login": "user5", "id": 5, "contributions": 8}
        ]
    
    async def get_issues(self, owner: str, repo: str, state: str = "all", since=None):
        # Return mock issues data
        return [
            {
                "id": 1,
                "number": 1,
                "title": "Bug report",
                "state": "closed",
                "user": {"login": "user1"},
                "created_at": "2023-10-01T10:00:00Z",
                "comments": 3
            },
            {
                "id": 2,
                "number": 2,
                "title": "Feature request",
                "state": "open",
                "user": {"login": "user2"},
                "created_at": "2023-10-15T14:30:00Z",
                "comments": 1
            }
        ]
    
    async def get_pull_requests(self, owner: str, repo: str, state: str = "all"):
        # Return mock PR data
        return [
            {
                "id": 1,
                "number": 1,
                "title": "Add new feature",
                "state": "closed",
                "merged_at": "2023-10-05T16:00:00Z",
                "user": {"login": "user1"},
                "created_at": "2023-10-01T12:00:00Z",
                "additions": 150,
                "deletions": 20,
                "review_comments": 2
            },
            {
                "id": 2,
                "number": 2,
                "title": "Fix bug",
                "state": "open",
                "user": {"login": "user2"},
                "created_at": "2023-10-20T09:15:00Z",
                "additions": 25,
                "deletions": 10,
                "review_comments": 1
            }
        ]
    
    async def get_commits(self, owner: str, repo: str, since=None):
        # Return mock commit data
        return [
            {
                "sha": "abc123",
                "commit": {
                    "author": {"name": "User One", "email": "user1@example.com", "date": "2023-10-01T10:00:00Z"},
                    "message": "Add new feature\n\nCo-authored-by: User Two <user2@example.com>"
                },
                "author": {"login": "user1"}
            },
            {
                "sha": "def456",
                "commit": {
                    "author": {"name": "User Two", "email": "user2@example.com", "date": "2023-10-02T11:30:00Z"},
                    "message": "Fix bug in feature"
                },
                "author": {"login": "user2"}
            }
        ]
    
    async def get_issue_comments(self, owner: str, repo: str, since=None):
        # Return mock comment data
        return [
            {
                "id": 1,
                "body": "Thanks for the bug report!",
                "created_at": "2023-10-01T11:00:00Z",
                "user": {"login": "maintainer"}
            },
            {
                "id": 2,
                "body": "I'll investigate this issue.",
                "created_at": "2023-10-01T15:30:00Z",
                "user": {"login": "user1"}
            }
        ]
    
    async def get_review_comments(self, owner: str, repo: str, since=None):
        # Return mock review data
        return [
            {
                "id": 1,
                "body": "Great work! Just a few minor suggestions.",
                "created_at": "2023-10-02T14:00:00Z",
                "user": {"login": "maintainer"}
            }
        ]
    
    async def get_repository_info(self, owner: str, repo: str):
        # Return mock repository info
        return {
            "name": repo,
            "owner": {"login": owner},
            "created_at": "2023-01-01T00:00:00Z",
            "default_branch": "main",
            "stargazers_count": 150,
            "forks_count": 25,
            "open_issues_count": 5
        }


async def demonstrate_comprehensive_analysis():
    """Demonstrate comprehensive community analytics"""
    
    print("🚀 Community Analytics System Demo")
    print("=" * 50)
    
    # Initialize mock client and orchestrator
    client = MockGitHubAPIClient(token="demo_token")
    orchestrator = CommunityAnalyticsOrchestrator()
    
    # Repository to analyze
    owner = "octocat"
    repo = "Hello-World"
    
    print(f"Analyzing repository: {owner}/{repo}")
    print()
    
    try:
        # Generate comprehensive analysis
        print("📊 Generating comprehensive community analysis...")
        report = await orchestrator.generate_comprehensive_analysis(
            client=client,
            owner=owner,
            repo=repo,
            analysis_period_days=180
        )
        
        # Display results
        print(f"✅ Analysis completed!")
        print()
        
        # Executive Summary
        print("📋 EXECUTIVE SUMMARY")
        print("-" * 30)
        print(f"Overall Community Score: {report.overall_community_score:.1f}/100")
        print(f"Community Grade: {report.community_grade}")
        print(f"Analysis Period: {report.analysis_period_days} days")
        print()
        
        # Key Insights
        print("🔍 KEY INSIGHTS")
        print("-" * 20)
        for i, insight in enumerate(report.key_insights, 1):
            print(f"{i}. {insight}")
        print()
        
        # Priority Recommendations
        print("💡 PRIORITY RECOMMENDATIONS")
        print("-" * 30)
        for i, rec in enumerate(report.priority_recommendations, 1):
            print(f"{i}. {rec}")
        print()
        
        # Detailed Analysis Results (if available)
        if report.lifecycle_analysis:
            print("👥 LIFECYCLE ANALYSIS")
            print("-" * 25)
            lifecycle = report.lifecycle_analysis
            if isinstance(lifecycle, dict):
                if 'current_metrics' in lifecycle:
                    metrics = lifecycle['current_metrics']
                    print(f"Total Members: {metrics.get('total_members', 'N/A')}")
                    print(f"Active Members: {metrics.get('active_members', 'N/A')}")
                    print(f"At-Risk Members: {metrics.get('at_risk_members', 'N/A')}")
                    print(f"Retention Rate (3m): {metrics.get('retention_rates', {}).get('3_months', 'N/A'):.1f}%")
                else:
                    print("Lifecycle analysis completed - detailed metrics available")
            print()
        
        if report.health_analysis:
            print("🏥 HEALTH ANALYSIS")
            print("-" * 20)
            health = report.health_analysis
            if isinstance(health, dict):
                print(f"Overall Score: {health.get('overall_score', 'N/A')}")
                print(f"Health Grade: {health.get('health_grade', 'N/A')}")
                if 'category_scores' in health:
                    scores = health['category_scores']
                    print(f"Activity Score: {scores.get('activity', 'N/A'):.1f}")
                    print(f"Quality Score: {scores.get('quality', 'N/A'):.1f}")
                    print(f"Velocity Score: {scores.get('velocity', 'N/A'):.1f}")
            print()
        
        # Predictive Insights
        if report.predictions:
            print("🔮 PREDICTIVE INSIGHTS")
            print("-" * 25)
            predictions = report.predictions
            if 'engagement_forecast' in predictions:
                forecast = predictions['engagement_forecast']
                print(f"Engagement Trend: {forecast.get('overall_trend', 'N/A')}")
                print(f"Trend Strength: {forecast.get('trend_strength', 0):.2f}")
                print(f"Model Confidence: {forecast.get('model_confidence', 0):.2f}")
            
            if 'churn_risk' in predictions:
                churn = predictions['churn_risk']
                print(f"Predicted Churn (30d): {churn.get('predicted_churn_30d', 'N/A')}")
                print(f"Predicted Churn (90d): {churn.get('predicted_churn_90d', 'N/A')}")
            print()
        
        # Action Items
        if report.immediate_actions:
            print("⚡ IMMEDIATE ACTIONS")
            print("-" * 25)
            for action in report.immediate_actions[:3]:  # Show first 3
                if isinstance(action, dict):
                    print(f"- {action.get('action', 'Unknown action')}")
                    print(f"  Priority: {action.get('priority', 'N/A')}")
                    print(f"  Timeline: {action.get('timeline', 'N/A')}")
            print()
        
        # Save report to file
        print("💾 SAVING REPORT")
        print("-" * 20)
        report_filename = f"community_analysis_{owner}_{repo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        
        print(f"Report saved to: {report_filename}")
        print()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("This is expected with the mock client - the system would work with real GitHub API data")


async def demonstrate_focused_analysis():
    """Demonstrate focused analysis for specific areas"""
    
    print("\n🎯 FOCUSED ANALYSIS DEMO")
    print("=" * 40)
    
    client = MockGitHubAPIClient()
    orchestrator = CommunityAnalyticsOrchestrator()
    
    # Analyze specific areas
    analysis_types = ["lifecycle", "health", "retention", "network"]
    
    for analysis_type in analysis_types:
        print(f"\n📈 {analysis_type.upper()} ANALYSIS")
        print("-" * (len(analysis_type) + 15))
        
        try:
            result = await orchestrator.generate_focused_analysis(
                client, "octocat", "Hello-World", analysis_type
            )
            
            if isinstance(result, dict):
                if 'error' in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"✅ {analysis_type.capitalize()} analysis completed successfully")
                    print(f"Result keys: {list(result.keys())}")
            else:
                print(f"✅ {analysis_type.capitalize()} analysis completed")
                
        except Exception as e:
            print(f"❌ {analysis_type.capitalize()} analysis failed: {e}")


async def demonstrate_individual_modules():
    """Demonstrate individual analytics modules"""
    
    print("\n🔧 INDIVIDUAL MODULES DEMO")
    print("=" * 35)
    
    client = MockGitHubAPIClient()
    
    # Lifecycle Tracker
    print("\n👥 LIFECYCLE TRACKER")
    print("-" * 25)
    try:
        tracker = MemberLifecycleTracker()
        result = await tracker.analyze_member_lifecycle(client, "octocat", "Hello-World", 90)
        print(f"✅ Lifecycle analysis completed")
        print(f"Total members analyzed: {getattr(result, 'total_members', 'N/A')}")
    except Exception as e:
        print(f"❌ Lifecycle analysis failed: {e}")
    
    # Engagement Scorer
    print("\n⭐ ENGAGEMENT SCORER")
    print("-" * 25)
    try:
        scorer = EngagementScorer()
        result = await scorer.calculate_engagement_scores(client, "octocat", "Hello-World", 90)
        print(f"✅ Engagement scoring completed")
        print(f"Total engagement score: {getattr(result, 'total_engagement_score', 'N/A'):.1f}")
    except Exception as e:
        print(f"❌ Engagement scoring failed: {e}")
    
    # Health Indicator
    print("\n🏥 HEALTH INDICATOR")
    print("-" * 25)
    try:
        health_indicator = CommunityHealthIndicator()
        result = await health_indicator.calculate_community_health(client, "octocat", "Hello-World", 90)
        print(f"✅ Health assessment completed")
        print(f"Health score: {getattr(result, 'overall_score', 'N/A'):.1f}")
        print(f"Health grade: {getattr(result, 'health_grade', 'N/A')}")
    except Exception as e:
        print(f"❌ Health assessment failed: {e}")


async def main():
    """Main demonstration function"""
    
    print("🎉 Welcome to the Community Analytics System!")
    print("This demo will showcase the key features using mock data.")
    print()
    
    # Run demonstrations
    await demonstrate_comprehensive_analysis()
    await demonstrate_focused_analysis()
    await demonstrate_individual_modules()
    
    print("\n✨ DEMO COMPLETE")
    print("=" * 20)
    print("To use this system with real data:")
    print("1. Replace MockGitHubAPIClient with real GitHubAPIClient")
    print("2. Provide your GitHub token")
    print("3. Run the analysis on your repository")
    print()
    print("For more information, see the README.md file.")


if __name__ == "__main__":
    asyncio.run(main())