"""
Community Analytics Orchestrator

Coordinates all community analytics modules to provide comprehensive analysis
and insights for repository community health, engagement, and growth.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from core.lifecycle_tracker import MemberLifecycleTracker
from core.engagement_scorer import EngagementScorer
from core.health_indicators import CommunityHealthIndicator
from core.retention_analyzer import RetentionAnalyzer
from core.network_analyzer import SocialNetworkAnalyzer
from models.prediction_engine import EngagementPredictionEngine

from github_api_client import GitHubAPIClient


@dataclass
class CommunityAnalyticsReport:
    """Comprehensive community analytics report"""
    timestamp: datetime
    repository: str
    analysis_period_days: int
    
    # Executive summary
    overall_community_score: float
    community_grade: str
    key_insights: List[str]
    priority_recommendations: List[str]
    
    # Detailed analysis results
    lifecycle_analysis: Optional[Dict[str, Any]] = None
    engagement_analysis: Optional[Dict[str, Any]] = None
    health_analysis: Optional[Dict[str, Any]] = None
    retention_analysis: Optional[Dict[str, Any]] = None
    network_analysis: Optional[Dict[str, Any]] = None
    
    # Predictive insights
    predictions: Optional[Dict[str, Any]] = None
    
    # Action items
    immediate_actions: List[Dict[str, str]] = None
    long_term_strategies: List[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class CommunityAnalyticsOrchestrator:
    """
    Orchestrate comprehensive community analytics across all dimensions.
    
    This class coordinates multiple analytics modules to provide a complete
    view of community health, engagement, and growth patterns.
    """
    
    def __init__(self):
        """Initialize the analytics orchestrator"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize all analytics modules
        self.lifecycle_tracker = MemberLifecycleTracker()
        self.engagement_scorer = EngagementScorer()
        self.health_indicator = CommunityHealthIndicator()
        self.retention_analyzer = RetentionAnalyzer()
        self.network_analyzer = SocialNetworkAnalyzer()
        self.prediction_engine = EngagementPredictionEngine()
        
        # Configuration
        self.default_analysis_period = 180  # days
        self.report_retention_days = 90  # days
        
        # Historical reports
        self.report_history: List[CommunityAnalyticsReport] = []
    
    async def generate_comprehensive_analysis(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        analysis_period_days: Optional[int] = None
    ) -> CommunityAnalyticsReport:
        """
        Generate comprehensive community analytics report.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            analysis_period_days: Period to analyze (default: 180 days)
            
        Returns:
            CommunityAnalyticsReport with comprehensive analysis
        """
        
        if analysis_period_days is None:
            analysis_period_days = self.default_analysis_period
        
        self.logger.info(f"Starting comprehensive analysis for {owner}/{repo} ({analysis_period_days} days)")
        
        # Execute all analytics modules in parallel
        lifecycle_task = asyncio.create_task(
            self.lifecycle_tracker.analyze_member_lifecycle(
                client, owner, repo, analysis_period_days
            )
        )
        
        engagement_task = asyncio.create_task(
            self.engagement_scorer.calculate_engagement_scores(
                client, owner, repo, analysis_period_days
            )
        )
        
        health_task = asyncio.create_task(
            self.health_indicator.calculate_community_health(
                client, owner, repo, analysis_period_days
            )
        )
        
        retention_task = asyncio.create_task(
            self.retention_analyzer.analyze_contributor_retention(
                client, owner, repo, analysis_period_days
            )
        )
        
        network_task = asyncio.create_task(
            self.network_analyzer.analyze_social_network(
                client, owner, repo, analysis_period_days
            )
        )
        
        # Wait for all analyses to complete
        lifecycle_results, engagement_results, health_results, retention_results, network_results = await asyncio.gather(
            lifecycle_task, engagement_task, health_task, retention_task, network_task,
            return_exceptions=True
        )
        
        # Handle any exceptions
        lifecycle_results = lifecycle_results if not isinstance(lifecycle_results, Exception) else None
        engagement_results = engagement_results if not isinstance(engagement_results, Exception) else None
        health_results = health_results if not isinstance(health_results, Exception) else None
        retention_results = retention_results if not isinstance(retention_results, Exception) else None
        network_results = network_results if not isinstance(network_results, Exception) else None
        
        # Generate predictive insights
        predictions = await self._generate_predictive_insights(
            client, owner, repo, lifecycle_results, engagement_results, health_results
        )
        
        # Compile comprehensive report
        report = self._compile_comprehensive_report(
            owner, repo, analysis_period_days, 
            lifecycle_results, engagement_results, health_results,
            retention_results, network_results, predictions
        )
        
        # Store report for historical analysis
        self.report_history.append(report)
        
        # Clean old reports
        self._cleanup_old_reports()
        
        self.logger.info(f"Comprehensive analysis completed for {owner}/{repo}")
        
        return report
    
    async def _generate_predictive_insights(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        lifecycle_results: Any,
        engagement_results: Any,
        health_results: Any
    ) -> Dict[str, Any]:
        """Generate predictive insights based on analysis results"""
        
        predictions = {}
        
        try:
            # Prepare data for prediction models
            historical_metrics = await self._prepare_historical_metrics(client, owner, repo)
            
            # Engagement trend prediction
            if historical_metrics and len(historical_metrics) >= 7:
                engagement_forecast = await self.prediction_engine.predict_engagement_trend(
                    historical_metrics, prediction_days=30
                )
                predictions['engagement_forecast'] = engagement_forecast
                
                # Convert to dict for serialization
                predictions['engagement_forecast'] = {
                    'predicted_engagement_score': engagement_forecast.predicted_engagement_score,
                    'predicted_active_contributors': engagement_forecast.predicted_active_contributors,
                    'overall_trend': engagement_forecast.overall_trend,
                    'trend_strength': engagement_forecast.trend_strength,
                    'model_confidence': engagement_forecast.model_confidence
                }
            
            # Churn risk assessment
            if lifecycle_results and hasattr(lifecycle_results, 'at_risk_members'):
                # Extract contributor profiles for churn prediction
                contributor_profiles = getattr(lifecycle_results, 'contributor_profiles', [])
                if contributor_profiles:
                    churn_assessment = await self.prediction_engine.assess_churn_risk(
                        [asdict(profile) for profile in contributor_profiles]
                    )
                    predictions['churn_risk'] = {
                        'high_risk_contributors': churn_assessment.high_risk_contributors,
                        'predicted_churn_30d': churn_assessment.predicted_churn_next_30_days,
                        'predicted_churn_90d': churn_assessment.predicted_churn_next_90_days,
                        'common_risk_factors': churn_assessment.common_risk_factors[:5]
                    }
            
            # Community health outlook
            if health_results and hasattr(health_results, 'overall_score'):
                # Prepare current metrics and historical trends
                current_metrics = {
                    'community_health_score': health_results.overall_score,
                    'contributor_retention': getattr(health_results, 'retention_rate_3_months', 50),
                    'issue_resolution_rate': getattr(health_results, 'quality_score', 50),
                    'community_engagement_score': getattr(health_results, 'community_engagement', 50)
                }
                
                historical_trends = self._extract_health_trends()
                
                health_prediction = await self.prediction_engine.predict_community_health(
                    current_metrics, historical_trends
                )
                predictions['health_outlook'] = {
                    'predicted_health_score': health_prediction.predicted_value,
                    'confidence_interval': health_prediction.confidence_interval,
                    'risk_factors': health_prediction.risk_factors,
                    'recommended_actions': health_prediction.recommended_actions
                }
                
        except Exception as e:
            self.logger.error(f"Error generating predictive insights: {e}")
            predictions['error'] = str(e)
        
        return predictions
    
    async def _prepare_historical_metrics(
        self, 
        client: GitHubAPIClient, 
        owner: str, 
        repo: str,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Prepare historical metrics for prediction models"""
        
        # This is a simplified implementation
        # In a real system, you'd retrieve actual historical data
        
        historical_metrics = []
        base_date = datetime.now() - timedelta(days=days)
        
        # Generate synthetic historical data for demonstration
        import random
        random.seed(42)  # For reproducible results
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            
            # Add some realistic variation
            engagement_base = 50 + 10 * math.sin(i * 2 * math.pi / 30)  # Monthly cycle
            engagement_variation = random.gauss(0, 5)
            engagement_score = max(0, min(100, engagement_base + engagement_variation))
            
            metrics = {
                'date': date,
                'engagement_score': engagement_score,
                'total_contributors': max(10, int(50 + random.gauss(0, 10))),
                'active_contributors': max(5, int(30 + random.gauss(0, 8))),
                'community_health_score': max(0, min(100, engagement_score + random.gauss(0, 10))),
                'contribution_frequency': max(0.5, 2.0 + random.gauss(0, 0.5)),
                'issue_response_time': max(1, 24 + random.gauss(0, 8)),
                'pr_merge_rate': max(0.1, min(1.0, 0.7 + random.gauss(0, 0.1)))
            }
            
            historical_metrics.append(metrics)
        
        return historical_metrics
    
    def _extract_health_trends(self) -> List[Dict[str, Any]]:
        """Extract health trends from historical reports"""
        
        if not self.report_history:
            return []
        
        # Get last 6 reports for trend analysis
        recent_reports = self.report_history[-6:] if len(self.report_history) >= 6 else self.report_history
        
        trends = []
        for report in recent_reports:
            if report.health_analysis:
                trends.append({
                    'timestamp': report.timestamp,
                    'community_health_score': report.health_analysis.get('overall_score', 50),
                    'trend_direction': 'improving'  # Would need to calculate actual trend
                })
        
        return trends
    
    def _compile_comprehensive_report(
        self,
        owner: str,
        repo: str,
        analysis_period_days: int,
        lifecycle_results: Any,
        engagement_results: Any,
        health_results: Any,
        retention_results: Any,
        network_results: Any,
        predictions: Dict[str, Any]
    ) -> CommunityAnalyticsReport:
        """Compile comprehensive analytics report"""
        
        # Calculate overall community score
        overall_score = self._calculate_overall_community_score(
            lifecycle_results, engagement_results, health_results, 
            retention_results, network_results
        )
        
        # Determine community grade
        community_grade = self._calculate_community_grade(overall_score)
        
        # Extract key insights
        key_insights = self._extract_key_insights(
            lifecycle_results, engagement_results, health_results,
            retention_results, network_results
        )
        
        # Generate priority recommendations
        priority_recommendations = self._generate_priority_recommendations(
            lifecycle_results, health_results, retention_results, network_results
        )
        
        # Create action items
        immediate_actions, long_term_strategies = self._generate_action_items(
            lifecycle_results, health_results, retention_results, network_results, predictions
        )
        
        # Convert results to dictionaries
        lifecycle_dict = self._results_to_dict(lifecycle_results) if lifecycle_results else None
        engagement_dict = self._results_to_dict(engagement_results) if engagement_results else None
        health_dict = self._results_to_dict(health_results) if health_results else None
        retention_dict = self._results_to_dict(retention_results) if retention_results else None
        network_dict = self._results_to_dict(network_results) if network_results else None
        
        return CommunityAnalyticsReport(
            timestamp=datetime.now(),
            repository=f"{owner}/{repo}",
            analysis_period_days=analysis_period_days,
            overall_community_score=overall_score,
            community_grade=community_grade,
            key_insights=key_insights,
            priority_recommendations=priority_recommendations,
            lifecycle_analysis=lifecycle_dict,
            engagement_analysis=engagement_dict,
            health_analysis=health_dict,
            retention_analysis=retention_dict,
            network_analysis=network_dict,
            predictions=predictions,
            immediate_actions=immediate_actions,
            long_term_strategies=long_term_strategies
        )
    
    def _calculate_overall_community_score(
        self,
        lifecycle_results: Any,
        engagement_results: Any,
        health_results: Any,
        retention_results: Any,
        network_results: Any
    ) -> float:
        """Calculate overall community score from all analyses"""
        
        scores = []
        weights = []
        
        # Health score (highest weight)
        if health_results and hasattr(health_results, 'overall_score'):
            scores.append(health_results.overall_score)
            weights.append(0.3)
        
        # Engagement score
        if engagement_results and hasattr(engagement_results, 'total_engagement_score'):
            scores.append(engagement_results.total_engagement_score)
            weights.append(0.25)
        
        # Retention score
        if retention_results and hasattr(retention_results, 'retention_rate_30'):
            scores.append(retention_results.retention_rate_30)
            weights.append(0.25)
        
        # Network health score
        if network_results and hasattr(network_results, 'network_density'):
            # Convert network density to 0-100 scale
            network_score = min(100, network_results.network_density * 500)  # Scale factor
            scores.append(network_score)
            weights.append(0.2)
        
        if not scores:
            return 50.0  # Default neutral score
        
        # Weighted average
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight
    
    def _calculate_community_grade(self, overall_score: float) -> str:
        """Calculate community grade from overall score"""
        
        if overall_score >= 90:
            return "A+"
        elif overall_score >= 85:
            return "A"
        elif overall_score >= 80:
            return "A-"
        elif overall_score >= 75:
            return "B+"
        elif overall_score >= 70:
            return "B"
        elif overall_score >= 65:
            return "B-"
        elif overall_score >= 60:
            return "C+"
        elif overall_score >= 55:
            return "C"
        elif overall_score >= 50:
            return "C-"
        else:
            return "D"
    
    def _extract_key_insights(
        self,
        lifecycle_results: Any,
        engagement_results: Any,
        health_results: Any,
        retention_results: Any,
        network_results: Any
    ) -> List[str]:
        """Extract key insights from all analyses"""
        
        insights = []
        
        # Lifecycle insights
        if lifecycle_results and hasattr(lifecycle_results, 'at_risk_count'):
            at_risk_count = lifecycle_results.at_risk_count
            total_members = lifecycle_results.total_members
            if at_risk_count > total_members * 0.2:
                insights.append(f"High percentage of at-risk members ({at_risk_count}/{total_members})")
        
        # Engagement insights
        if engagement_results and hasattr(engagement_results, 'highly_engaged_count'):
            highly_engaged = engagement_results.highly_engaged_count
            if highly_engaged < 5:
                insights.append("Limited number of highly engaged contributors")
        
        # Health insights
        if health_results:
            if hasattr(health_results, 'health_grade') and health_results.health_grade in ['D', 'F']:
                insights.append(f"Community health grade is {health_results.health_grade} - requires attention")
            
            if hasattr(health_results, 'critical_indicators') and health_results.critical_indicators > 0:
                insights.append(f"{health_results.critical_indicators} critical health indicators need immediate attention")
        
        # Retention insights
        if retention_results and hasattr(retention_results, 'monthly_churn_rate'):
            churn_rate = retention_results.monthly_churn_rate
            if churn_rate > 15:
                insights.append(f"High monthly churn rate of {churn_rate:.1f}%")
        
        # Network insights
        if network_results and hasattr(network_results, 'isolated_nodes'):
            isolated = network_results.isolated_nodes
            total_nodes = network_results.total_nodes
            if isolated > total_nodes * 0.3:
                insights.append(f"Large number of isolated contributors ({isolated}/{total_nodes})")
        
        # Default insight if none specific
        if not insights:
            insights.append("Community showing stable engagement patterns")
        
        return insights[:5]  # Top 5 insights
    
    def _generate_priority_recommendations(
        self,
        lifecycle_results: Any,
        health_results: Any,
        retention_results: Any,
        network_results: Any
    ) -> List[str]:
        """Generate priority recommendations based on analyses"""
        
        recommendations = []
        
        # Health-based recommendations
        if health_results and hasattr(health_results, 'priority_actions'):
            recommendations.extend(health_results.priority_actions[:3])
        
        # Retention-based recommendations
        if retention_results and hasattr(retention_results, 'retention_recommendations'):
            recommendations.extend(retention_results.retention_recommendations[:2])
        
        # Network-based recommendations
        if network_results and hasattr(network_results, 'network_recommendations'):
            recommendations.extend(network_results.network_recommendations[:2])
        
        # Lifecycle-based recommendations
        if lifecycle_results and hasattr(lifecycle_results, 'predicted_lost_next_month'):
            predicted_lost = lifecycle_results.predicted_lost_next_month
            if predicted_lost > 0:
                recommendations.append(f"Implement retention strategies to prevent loss of {predicted_lost} contributors")
        
        # Remove duplicates and limit
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:7]
    
    def _generate_action_items(
        self,
        lifecycle_results: Any,
        health_results: Any,
        retention_results: Any,
        network_results: Any,
        predictions: Dict[str, Any]
    ) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Generate immediate actions and long-term strategies"""
        
        immediate_actions = []
        long_term_strategies = []
        
        # Immediate actions based on critical issues
        if health_results and hasattr(health_results, 'critical_indicators') and health_results.critical_indicators > 0:
            immediate_actions.append({
                'action': 'Address critical health indicators',
                'priority': 'High',
                'timeline': '1-2 weeks',
                'description': f'Focus on {health_results.critical_indicators} critical health metrics'
            })
        
        if retention_results and hasattr(retention_results, 'high_risk_contributors'):
            high_risk_count = len(retention_results.high_risk_contributors)
            if high_risk_count > 0:
                immediate_actions.append({
                    'action': 'Outreach to high-risk contributors',
                    'priority': 'High',
                    'timeline': '1 week',
                    'description': f'Personal contact with {high_risk_count} high-risk contributors'
                })
        
        # Long-term strategies
        if network_results and hasattr(network_results, 'core_contributors'):
            core_count = network_results.core_contributors
            if core_count < 10:
                long_term_strategies.append({
                    'strategy': 'Develop core contributor pipeline',
                    'priority': 'Medium',
                    'timeline': '3-6 months',
                    'description': 'Focus on developing more core contributors'
                })
        
        if health_results and hasattr(health_results, 'inclusivity_score') and health_results.inclusivity_score < 60:
            long_term_strategies.append({
                'strategy': 'Improve community inclusivity',
                'priority': 'Medium',
                'timeline': '6-12 months',
                'description': 'Implement programs to improve diverse participation'
            })
        
        # Predictions-based strategies
        if 'churn_risk' in predictions:
            predicted_churn = predictions['churn_risk'].get('predicted_churn_30d', 0)
            if predicted_churn > 3:
                long_term_strategies.append({
                    'strategy': 'Implement retention improvement program',
                    'priority': 'High',
                    'timeline': '1-3 months',
                    'description': f'Systematic approach to prevent {predicted_churn} predicted churns'
                })
        
        return immediate_actions, long_term_strategies
    
    def _results_to_dict(self, results: Any) -> Optional[Dict[str, Any]]:
        """Convert analysis results to dictionary"""
        
        if results is None:
            return None
        
        try:
            # Try dataclass conversion first
            if hasattr(results, '__dataclass_fields__'):
                return asdict(results)
            else:
                # Handle other result types
                return {
                    'type': type(results).__name__,
                    'data': str(results)  # Fallback string representation
                }
        except Exception as e:
            self.logger.warning(f"Failed to convert results to dict: {e}")
            return {'error': str(e)}
    
    def _cleanup_old_reports(self):
        """Remove reports older than retention period"""
        
        cutoff_date = datetime.now() - timedelta(days=self.report_retention_days)
        
        # Filter out old reports
        self.report_history = [
            report for report in self.report_history 
            if report.timestamp > cutoff_date
        ]
    
    def get_latest_report(self) -> Optional[CommunityAnalyticsReport]:
        """Get the most recent analytics report"""
        
        return self.report_history[-1] if self.report_history else None
    
    def get_report_history_summary(self) -> Dict[str, Any]:
        """Get summary of report history"""
        
        if not self.report_history:
            return {'total_reports': 0}
        
        latest_report = self.report_history[-1]
        
        # Calculate trends over time
        scores = [report.overall_community_score for report in self.report_history[-6:]]  # Last 6 reports
        
        trend = "improving" if len(scores) >= 2 and scores[-1] > scores[0] else "declining" if len(scores) >= 2 and scores[-1] < scores[0] else "stable"
        
        return {
            'total_reports': len(self.report_history),
            'latest_report_date': latest_report.timestamp.isoformat(),
            'latest_repository': latest_report.repository,
            'latest_score': latest_report.overall_community_score,
            'latest_grade': latest_report.community_grade,
            'score_trend': trend,
            'average_score': statistics.mean(scores) if scores else 0,
            'score_variance': statistics.variance(scores) if len(scores) > 1 else 0
        }
    
    async def generate_focused_analysis(
        self,
        client: GitHubAPIClient,
        owner: str,
        repo: str,
        analysis_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate focused analysis for a specific area.
        
        Args:
            client: GitHub API client
            owner: Repository owner
            repo: Repository name
            analysis_type: Type of analysis ('lifecycle', 'engagement', 'health', 'retention', 'network')
            **kwargs: Additional parameters for specific analysis
            
        Returns:
            Dict containing focused analysis results
        """
        
        lookback_days = kwargs.get('lookback_days', 90)
        
        if analysis_type == 'lifecycle':
            results = await self.lifecycle_tracker.analyze_member_lifecycle(client, owner, repo, lookback_days)
        elif analysis_type == 'engagement':
            results = await self.engagement_scorer.calculate_engagement_scores(client, owner, repo, lookback_days)
        elif analysis_type == 'health':
            results = await self.health_indicator.calculate_community_health(client, owner, repo, lookback_days)
        elif analysis_type == 'retention':
            results = await self.retention_analyzer.analyze_contributor_retention(client, owner, repo, lookback_days)
        elif analysis_type == 'network':
            results = await self.network_analyzer.analyze_social_network(client, owner, repo, lookback_days)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        return self._results_to_dict(results) or {'error': 'Analysis failed'}

import math
import statistics