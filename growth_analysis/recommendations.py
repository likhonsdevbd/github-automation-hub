"""
Growth Strategy Recommendations Based on Analysis Patterns

This module generates actionable strategy recommendations based on
growth pattern analysis, predictions, anomalies, benchmarks, and forecasts.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import defaultdict
import warnings

# Import other growth analysis modules
from .core import GrowthPattern, GrowthMetrics
from .predictors import PredictionResult, ModelPerformance
from .anomaly_detector import AnomalyResult, AnomalyPattern
from .benchmarking import CompetitiveAnalysis, BenchmarkResult
from .forecasting import TrendAnalysis, ForecastPoint


@dataclass
class StrategyRecommendation:
    """Data class for a single strategy recommendation."""
    category: str
    priority: str
    title: str
    description: str
    rationale: str
    action_items: List[str]
    expected_impact: str
    implementation_difficulty: str
    timeframe: str
    metrics_to_monitor: List[str]
    confidence_score: float


@dataclass
class StrategicPlan:
    """Data class for comprehensive strategic planning."""
    repository: str
    current_status: str
    overall_score: float
    strategic_priorities: List[str]
    immediate_actions: List[StrategyRecommendation]
    medium_term_actions: List[StrategyRecommendation]
    long_term_actions: List[StrategyRecommendation]
    success_metrics: List[str]
    risk_mitigation: List[str]
    resource_requirements: Dict[str, Any]


class StrategyRecommender:
    """
    Advanced strategy recommendation engine that synthesizes insights
    from all analysis modules to generate actionable recommendations.
    """
    
    def __init__(self):
        self.recommendation_templates = self._initialize_templates()
        self.impact_models = self._initialize_impact_models()
        
    def generate_strategic_plan(self, repo_name: str,
                               growth_patterns: List[GrowthPattern],
                               predictions: List[PredictionResult],
                               anomalies: List[AnomalyResult],
                               anomaly_patterns: List[AnomalyPattern],
                               competitive_analysis: Optional[CompetitiveAnalysis] = None,
                               trend_analysis: Optional[TrendAnalysis] = None) -> StrategicPlan:
        """
        Generate a comprehensive strategic plan based on all analysis results.
        
        Args:
            repo_name: Repository identifier
            growth_patterns: Detected growth patterns
            predictions: Prediction results
            anomalies: Detected anomalies
            anomaly_patterns: Anomaly patterns
            competitive_analysis: Benchmarking results
            trend_analysis: Trend analysis results
            
        Returns:
            Comprehensive strategic plan
        """
        # Analyze current status
        current_status = self._assess_current_status(
            growth_patterns, anomalies, anomaly_patterns, competitive_analysis, trend_analysis
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            growth_patterns, anomalies, anomaly_patterns, competitive_analysis, trend_analysis
        )
        
        # Identify strategic priorities
        strategic_priorities = self._identify_strategic_priorities(
            growth_patterns, anomalies, competitive_analysis, trend_analysis
        )
        
        # Generate recommendations by timeframe
        immediate_actions = self._generate_immediate_actions(
            anomalies, anomaly_patterns, current_status, competitive_analysis
        )
        
        medium_term_actions = self._generate_medium_term_actions(
            growth_patterns, competitive_analysis, trend_analysis
        )
        
        long_term_actions = self._generate_long_term_actions(
            predictions, competitive_analysis, trend_analysis
        )
        
        # Define success metrics
        success_metrics = self._define_success_metrics(
            growth_patterns, competitive_analysis, trend_analysis
        )
        
        # Risk mitigation strategies
        risk_mitigation = self._generate_risk_mitigation(
            anomalies, anomaly_patterns, predictions
        )
        
        # Resource requirements
        resource_requirements = self._estimate_resource_requirements(
            immediate_actions, medium_term_actions, long_term_actions
        )
        
        return StrategicPlan(
            repository=repo_name,
            current_status=current_status,
            overall_score=overall_score,
            strategic_priorities=strategic_priorities,
            immediate_actions=immediate_actions,
            medium_term_actions=medium_term_actions,
            long_term_actions=long_term_actions,
            success_metrics=success_metrics,
            risk_mitigation=risk_mitigation,
            resource_requirements=resource_requirements
        )
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize recommendation templates."""
        return {
            "anomaly_response": {
                "high_impact": {
                    "title": "Address Critical Anomalies",
                    "description": "Immediate action required to address critical anomalies detected in repository metrics.",
                    "action_items": [
                        "Investigate root cause of anomalous activity",
                        "Check for infrastructure issues or external factors",
                        "Implement monitoring to prevent future occurrences",
                        "Communicate with community about any changes"
                    ],
                    "expected_impact": "Stabilize metrics and restore normal growth patterns",
                    "implementation_difficulty": "medium",
                    "timeframe": "1-7 days"
                },
                "medium_impact": {
                    "title": "Monitor and Investigate Anomalies",
                    "description": "Monitor detected anomalies and investigate potential causes.",
                    "action_items": [
                        "Set up enhanced monitoring for affected metrics",
                        "Document anomaly patterns for future reference",
                        "Review recent changes and external factors",
                        "Prepare contingency plans if trends continue"
                    ],
                    "expected_impact": "Gain insights into metric behavior and prevent escalation",
                    "implementation_difficulty": "low",
                    "timeframe": "3-14 days"
                }
            },
            "growth_acceleration": {
                "underperforming": {
                    "title": "Accelerate Growth Trajectory",
                    "description": "Implement strategies to accelerate repository growth based on peer benchmarking.",
                    "action_items": [
                        "Analyze top-performing peer repositories for best practices",
                        "Improve documentation and examples",
                        "Enhance community engagement initiatives",
                        "Optimize repository presentation and marketing"
                    ],
                    "expected_impact": "Increase growth rate to match or exceed peer performance",
                    "implementation_difficulty": "high",
                    "timeframe": "30-90 days"
                },
                "plateaued": {
                    "title": "Break Growth Plateau",
                    "description": "Address stagnation in repository growth and implement revitalization strategies.",
                    "action_items": [
                        "Conduct community survey to identify needs",
                        "Plan major feature releases or improvements",
                        "Reinvigorate community engagement efforts",
                        "Explore new distribution and marketing channels"
                    ],
                    "expected_impact": "Restore growth momentum and increase engagement",
                    "implementation_difficulty": "high",
                    "timeframe": "60-120 days"
                }
            },
            "competitive_positioning": {
                "lagging": {
                    "title": "Improve Competitive Position",
                    "description": "Address competitive disadvantages identified through benchmarking analysis.",
                    "action_items": [
                        "Conduct detailed competitive analysis",
                        "Identify unique value propositions to emphasize",
                        "Improve areas where competition outperforms",
                        "Develop differentiation strategy"
                    ],
                    "expected_impact": "Close competitive gap and improve market position",
                    "implementation_difficulty": "high",
                    "timeframe": "90-180 days"
                },
                "strong": {
                    "title": "Maintain Competitive Advantage",
                    "description": "Leverage competitive strengths while addressing potential vulnerabilities.",
                    "action_items": [
                        "Document and systematize successful practices",
                        "Monitor competitor activities closely",
                        "Invest in areas that provide sustainable advantage",
                        "Build stronger community and ecosystem"
                    ],
                    "expected_impact": "Maintain and expand competitive lead",
                    "implementation_difficulty": "medium",
                    "timeframe": "60-120 days"
                }
            },
            "trend_optimization": {
                "declining": {
                    "title": "Reverse Negative Trends",
                    "description": "Implement urgent measures to address declining trends in key metrics.",
                    "action_items": [
                        "Identify and address root causes of decline",
                        "Implement immediate stabilization measures",
                        "Launch recovery campaign for community engagement",
                        "Review and adjust strategy based on trend analysis"
                    ],
                    "expected_impact": "Stabilize and reverse declining trends",
                    "implementation_difficulty": "high",
                    "timeframe": "30-60 days"
                },
                "volatility": {
                    "title": "Reduce Growth Volatility",
                    "description": "Implement measures to create more stable and predictable growth patterns.",
                    "action_items": [
                        "Establish regular release and communication schedules",
                        "Implement quality assurance measures",
                        "Build community engagement programs",
                        "Develop contingency plans for various scenarios"
                    ],
                    "expected_impact": "Create more stable and sustainable growth patterns",
                    "implementation_difficulty": "medium",
                    "timeframe": "60-90 days"
                }
            }
        }
    
    def _initialize_impact_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize impact assessment models."""
        return {
            "stars": {
                "visibility_multiplier": 1.2,
                "community_engagement_impact": 0.8,
                "documentation_quality_impact": 0.6,
                "release_frequency_impact": 0.4
            },
            "forks": {
                "contribution_friendliness_impact": 1.0,
                "code_quality_impact": 0.7,
                "license_clarity_impact": 0.5,
                "community_responsiveness_impact": 0.8
            },
            "watchers": {
                "update_frequency_impact": 0.9,
                "feature_roadmap_impact": 0.6,
                "community_activity_impact": 0.8,
                "stability_impact": 0.7
            },
            "issues": {
                "response_time_impact": 1.0,
                "documentation_quality_impact": 0.6,
                "test_coverage_impact": 0.8,
                "community_support_impact": 0.7
            }
        }
    
    def _assess_current_status(self, growth_patterns: List[GrowthPattern],
                             anomalies: List[AnomalyResult],
                             anomaly_patterns: List[AnomalyPattern],
                             competitive_analysis: Optional[CompetitiveAnalysis],
                             trend_analysis: Optional[TrendAnalysis]) -> str:
        """Assess the current status of the repository."""
        status_factors = []
        
        # Analyze growth patterns
        if growth_patterns:
            pattern_types = [p.pattern_type for p in growth_patterns]
            
            if any(pt in ['exponential_growth', 'linear_growth'] for pt in pattern_types):
                status_factors.append("positive_growth")
            elif 'growth_plateau' in pattern_types:
                status_factors.append("plateaued")
            elif any(pt in ['growth_deceleration', 'negative_growth'] for pt in pattern_types):
                status_factors.append("declining")
        
        # Analyze anomalies
        high_severity_anomalies = [a for a in anomalies if a.severity in ['critical', 'high']]
        if high_severity_anomalies:
            status_factors.append("critical_issues")
        elif anomalies:
            status_factors.append("minor_issues")
        
        # Analyze competitive position
        if competitive_analysis:
            if competitive_analysis.overall_score >= 0.8:
                status_factors.append("competitive_leader")
            elif competitive_analysis.overall_score >= 0.6:
                status_factors.append("competitive")
            elif competitive_analysis.overall_score < 0.4:
                status_factors.append("competitive_lagging")
        
        # Analyze trends
        if trend_analysis:
            if trend_analysis.overall_trend == "increasing" and trend_analysis.trend_strength > 0.7:
                status_factors.append("strong_trends")
            elif trend_analysis.overall_trend == "decreasing":
                status_factors.append("negative_trends")
            elif trend_analysis.confidence_assessment in ['low', 'very_low']:
                status_factors.append("high_uncertainty")
        
        # Determine overall status
        if "critical_issues" in status_factors:
            return "critical_issues_detected"
        elif "declining" in status_factors or "negative_trends" in status_factors:
            return "declining_performance"
        elif "competitive_lagging" in status_factors:
            return "competitive_disadvantage"
        elif "plateaued" in status_factors:
            return "growth_plateau"
        elif "positive_growth" in status_factors and "strong_trends" in status_factors:
            return "strong_performance"
        elif "competitive_leader" in status_factors:
            return "market_leadership"
        else:
            return "mixed_performance"
    
    def _calculate_overall_score(self, growth_patterns: List[GrowthPattern],
                               anomalies: List[AnomalyResult],
                               anomaly_patterns: List[AnomalyPattern],
                               competitive_analysis: Optional[CompetitiveAnalysis],
                               trend_analysis: Optional[TrendAnalysis]) -> float:
        """Calculate overall performance score."""
        scores = []
        
        # Score from growth patterns
        if growth_patterns:
            pattern_scores = []
            for pattern in growth_patterns:
                if pattern.pattern_type in ['exponential_growth', 'linear_growth']:
                    pattern_scores.append(0.9 * pattern.confidence)
                elif pattern.pattern_type in ['growth_plateau', 'growth_deceleration']:
                    pattern_scores.append(0.3 * pattern.confidence)
                else:
                    pattern_scores.append(0.6 * pattern.confidence)
            scores.append(np.mean(pattern_scores))
        
        # Score from anomalies (penalty for high severity anomalies)
        if anomalies:
            anomaly_scores = []
            for anomaly in anomalies:
                if anomaly.severity == 'critical':
                    anomaly_scores.append(0.1 * anomaly.confidence)
                elif anomaly.severity == 'high':
                    anomaly_scores.append(0.3 * anomaly.confidence)
                elif anomaly.severity == 'medium':
                    anomaly_scores.append(0.7 * anomaly.confidence)
                else:
                    anomaly_scores.append(0.9 * anomaly.confidence)
            scores.append(np.mean(anomaly_scores))
        else:
            scores.append(0.8)  # No anomalies is good
        
        # Score from competitive analysis
        if competitive_analysis:
            scores.append(competitive_analysis.overall_score)
        
        # Score from trend analysis
        if trend_analysis:
            trend_score = trend_analysis.trend_strength
            if trend_analysis.overall_trend == "increasing":
                trend_score *= 1.2
            elif trend_analysis.overall_trend == "decreasing":
                trend_score *= 0.5
            scores.append(min(trend_score, 1.0))
        
        return np.mean(scores) if scores else 0.5
    
    def _identify_strategic_priorities(self, growth_patterns: List[GrowthPattern],
                                     anomalies: List[AnomalyResult],
                                     competitive_analysis: Optional[CompetitiveAnalysis],
                                     trend_analysis: Optional[TrendAnalysis]) -> List[str]:
        """Identify key strategic priorities."""
        priorities = []
        
        # Priority 1: Address critical issues
        critical_anomalies = [a for a in anomalies if a.severity == 'critical']
        if critical_anomalies:
            priorities.append("Resolve critical anomalies immediately")
        
        # Priority 2: Growth optimization
        if growth_patterns:
            if any(p.pattern_type == 'growth_plateau' for p in growth_patterns):
                priorities.append("Break growth plateau and accelerate momentum")
            elif any(p.pattern_type == 'growth_deceleration' for p in growth_patterns):
                priorities.append("Address growth deceleration and restore momentum")
        
        # Priority 3: Competitive positioning
        if competitive_analysis:
            if competitive_analysis.overall_score < 0.5:
                priorities.append("Improve competitive positioning through strategic differentiation")
            elif competitive_analysis.market_position == "lagging":
                priorities.append("Close competitive gap with industry leaders")
        
        # Priority 4: Trend management
        if trend_analysis:
            if trend_analysis.overall_trend == "decreasing":
                priorities.append("Reverse negative trends and stabilize growth")
            elif trend_analysis.confidence_assessment in ['low', 'very_low']:
                priorities.append("Improve forecast reliability through better data and processes")
        
        # Priority 5: Long-term sustainability
        priorities.append("Build sustainable growth engines and community engagement")
        
        return priorities
    
    def _generate_immediate_actions(self, anomalies: List[AnomalyResult],
                                  anomaly_patterns: List[AnomalyPattern],
                                  current_status: str,
                                  competitive_analysis: Optional[CompetitiveAnalysis]) -> List[StrategyRecommendation]:
        """Generate immediate action recommendations (0-30 days)."""
        recommendations = []
        
        # Address critical anomalies
        critical_anomalies = [a for a in anomalies if a.severity == 'critical']
        if critical_anomalies:
            template = self.recommendation_templates["anomaly_response"]["high_impact"]
            
            rec = StrategyRecommendation(
                category="crisis_management",
                priority="critical",
                title=template["title"],
                description=f"Critical anomalies detected in {len(critical_anomalies)} metrics requiring immediate attention.",
                rationale=f"Detected {len(critical_anomalies)} critical anomalies that could significantly impact repository health.",
                action_items=template["action_items"],
                expected_impact=template["expected_impact"],
                implementation_difficulty=template["implementation_difficulty"],
                timeframe=template["timeframe"],
                metrics_to_monitor=list(set(a.metric for a in critical_anomalies)),
                confidence_score=0.9
            )
            recommendations.append(rec)
        
        # Address medium severity anomalies
        medium_anomalies = [a for a in anomalies if a.severity == 'medium']
        if medium_anomalies:
            template = self.recommendation_templates["anomaly_response"]["medium_impact"]
            
            rec = StrategyRecommendation(
                category="monitoring",
                priority="medium",
                title="Enhanced Monitoring and Investigation",
                description=f"Monitor {len(medium_anomalies)} anomalous metrics for patterns and causes.",
                rationale="Medium severity anomalies require monitoring to prevent escalation.",
                action_items=[
                    "Implement enhanced monitoring dashboards",
                    "Document anomaly patterns and triggers",
                    "Set up alerting for unusual metric changes",
                    "Schedule regular anomaly review meetings"
                ],
                expected_impact="Improved visibility into metric behavior and early problem detection",
                implementation_difficulty="low",
                timeframe="7-21 days",
                metrics_to_monitor=list(set(a.metric for a in medium_anomalies)),
                confidence_score=0.7
            )
            recommendations.append(rec)
        
        # Address competitive disadvantages
        if competitive_analysis and competitive_analysis.overall_score < 0.5:
            # Simple quick wins for competitive improvement
            rec = StrategyRecommendation(
                category="competitive_improvement",
                priority="high",
                title="Implement Quick Competitive Wins",
                description="Address obvious competitive disadvantages with immediate improvements.",
                rationale="Quick wins can provide immediate competitive benefits while building momentum.",
                action_items=[
                    "Update repository description and README for clarity",
                    "Improve contribution guidelines and issue templates",
                    "Add more comprehensive documentation and examples",
                    "Optimize repository tags and categorization"
                ],
                expected_impact="Improved visibility and contribution ease",
                implementation_difficulty="low",
                timeframe="14-30 days",
                metrics_to_monitor=["stars", "forks", "watchers"],
                confidence_score=0.8
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_medium_term_actions(self, growth_patterns: List[GrowthPattern],
                                    competitive_analysis: Optional[CompetitiveAnalysis],
                                    trend_analysis: Optional[TrendAnalysis]) -> List[StrategyRecommendation]:
        """Generate medium-term action recommendations (1-6 months)."""
        recommendations = []
        
        # Address growth plateaus
        plateau_patterns = [p for p in growth_patterns if p.pattern_type == 'growth_plateau']
        if plateau_patterns:
            template = self.recommendation_templates["growth_acceleration"]["plateaued"]
            
            rec = StrategyRecommendation(
                category="growth_acceleration",
                priority="high",
                title=template["title"],
                description="Implement comprehensive strategy to break growth plateau.",
                rationale=f"Detected {len(plateau_patterns)} plateau patterns indicating stagnation.",
                action_items=template["action_items"],
                expected_impact=template["expected_impact"],
                implementation_difficulty=template["implementation_difficulty"],
                timeframe=template["timeframe"],
                metrics_to_monitor=["stars", "forks", "watchers", "commits"],
                confidence_score=0.7
            )
            recommendations.append(rec)
        
        # Address underperformance
        if competitive_analysis and competitive_analysis.overall_score < 0.6:
            template = self.recommendation_templates["competitive_positioning"]["lagging"]
            
            rec = StrategyRecommendation(
                category="competitive_strategy",
                priority="medium",
                title=template["title"],
                description="Implement comprehensive competitive improvement strategy.",
                rationale="Benchmarking shows significant competitive disadvantages requiring strategic action.",
                action_items=template["action_items"],
                expected_impact=template["expected_impact"],
                implementation_difficulty=template["implementation_difficulty"],
                timeframe=template["timeframe"],
                metrics_to_monitor=["overall_score", "market_position"],
                confidence_score=0.6
            )
            recommendations.append(rec)
        
        # Trend volatility management
        if trend_analysis and trend_analysis.confidence_assessment == 'low':
            template = self.recommendation_templates["trend_optimization"]["volatility"]
            
            rec = StrategyRecommendation(
                category="stability",
                priority="medium",
                title="Reduce Growth Volatility",
                description="Implement measures to create more stable and predictable growth patterns.",
                rationale="Low forecast confidence indicates high volatility requiring stabilization efforts.",
                action_items=template["action_items"],
                expected_impact=template["expected_impact"],
                implementation_difficulty=template["implementation_difficulty"],
                timeframe=template["timeframe"],
                metrics_to_monitor=["trend_strength", "growth_rate"],
                confidence_score=0.6
            )
            recommendations.append(rec)
        
        # Community engagement enhancement
        rec = StrategyRecommendation(
            category="community_building",
            priority="medium",
            title="Enhance Community Engagement Programs",
            description="Build stronger community through structured engagement initiatives.",
            rationale="Strong community engagement is fundamental to sustainable growth.",
            action_items=[
                "Launch regular community calls or webinars",
                "Create community showcase programs",
                "Implement contributor recognition systems",
                "Develop community-driven roadmap planning"
            ],
            expected_impact="Increased community engagement and contributor retention",
            implementation_difficulty="medium",
            timeframe="60-120 days",
            metrics_to_monitor=["commits", "pull_requests", "contributors"],
            confidence_score=0.7
        )
        recommendations.append(rec)
        
        return recommendations
    
    def _generate_long_term_actions(self, predictions: List[PredictionResult],
                                  competitive_analysis: Optional[CompetitiveAnalysis],
                                  trend_analysis: Optional[TrendAnalysis]) -> List[StrategyRecommendation]:
        """Generate long-term action recommendations (6+ months)."""
        recommendations = []
        
        # Sustainable growth strategy
        if predictions and len(predictions) > 30:
            predicted_trend = "positive" if predictions[0].predicted_value > predictions[-1].predicted_value else "negative"
            
            rec = StrategyRecommendation(
                category="strategic_planning",
                priority="high",
                title="Build Sustainable Growth Engine",
                description=f"Develop long-term strategy based on {len(predictions)}-day growth predictions.",
                rationale="Long-term predictions indicate need for sustainable growth infrastructure.",
                action_items=[
                    "Develop comprehensive 12-month growth strategy",
                    "Build scalable community management systems",
                    "Implement data-driven decision making processes",
                    "Create feedback loops for continuous improvement"
                ],
                expected_impact="Sustainable long-term growth aligned with predicted trends",
                implementation_difficulty="high",
                timeframe="180-365 days",
                metrics_to_monitor=["overall_score", "sustainability_metrics"],
                confidence_score=0.6
            )
            recommendations.append(rec)
        
        # Market leadership strategy
        if competitive_analysis and competitive_analysis.market_position in ["leader", "strong_competitor"]:
            template = self.recommendation_templates["competitive_positioning"]["strong"]
            
            rec = StrategyRecommendation(
                category="market_leadership",
                priority="medium",
                title=template["title"],
                description="Leverage competitive strengths to maintain and expand market position.",
                rationale="Strong competitive position provides opportunity for market leadership strategies.",
                action_items=template["action_items"],
                expected_impact=template["expected_impact"],
                implementation_difficulty=template["implementation_difficulty"],
                timeframe=template["timeframe"],
                metrics_to_monitor=["market_position", "competitive_gap"],
                confidence_score=0.7
            )
            recommendations.append(rec)
        
        # Innovation and differentiation
        rec = StrategyRecommendation(
            category="innovation",
            priority="medium",
            title="Drive Innovation and Differentiation",
            description="Invest in innovation to create sustainable competitive advantages.",
            rationale="Continuous innovation is essential for long-term success in competitive markets.",
            action_items=[
                "Establish innovation lab or research initiatives",
                "Invest in cutting-edge features and capabilities",
                "Build strategic partnerships and ecosystems",
                "Develop intellectual property and thought leadership"
            ],
            expected_impact="Enhanced competitive differentiation and market leadership",
            implementation_difficulty="high",
            timeframe="240-480 days",
            metrics_to_monitor=["innovation_metrics", "differentiation_score"],
            confidence_score=0.5
        )
        recommendations.append(rec)
        
        return recommendations
    
    def _define_success_metrics(self, growth_patterns: List[GrowthPattern],
                              competitive_analysis: Optional[CompetitiveAnalysis],
                              trend_analysis: Optional[TrendAnalysis]) -> List[str]:
        """Define key success metrics for tracking progress."""
        metrics = []
        
        # Core growth metrics
        core_metrics = ["stars", "forks", "watchers", "commits", "pull_requests"]
        metrics.extend(core_metrics)
        
        # Derived metrics
        derived_metrics = [
            "growth_rate", "trend_strength", "forecast_confidence",
            "competitive_score", "community_engagement_score"
        ]
        metrics.extend(derived_metrics)
        
        # Quality metrics
        quality_metrics = [
            "issue_resolution_time", "contributor_retention", "documentation_quality_score"
        ]
        metrics.extend(quality_metrics)
        
        return metrics
    
    def _generate_risk_mitigation(self, anomalies: List[AnomalyResult],
                                anomaly_patterns: List[AnomalyPattern],
                                predictions: List[PredictionResult]) -> List[str]:
        """Generate risk mitigation strategies."""
        risks = []
        
        # Anomaly-related risks
        if anomalies:
            anomaly_types = set(a.metric for a in anomalies)
            if 'critical' in [a.severity for a in anomalies]:
                risks.append("Critical anomalies could indicate systemic issues requiring immediate intervention")
            
            if len(anomaly_patterns) > 2:
                risks.append("Multiple anomaly patterns detected - implement comprehensive monitoring")
        
        # Prediction-related risks
        if predictions:
            recent_predictions = predictions[:7]  # Next week
            if any(p.trend_direction == "decreasing" for p in recent_predictions):
                risks.append("Predicted declining trends require proactive intervention strategies")
        
        # General risks
        risks.extend([
            "High growth could strain infrastructure and community resources",
            "Competitive changes could impact market position",
            "External factors (economic, regulatory) could affect growth patterns",
            "Resource constraints could limit strategy implementation"
        ])
        
        # Mitigation strategies
        mitigation_strategies = [
            "Implement comprehensive monitoring and alerting systems",
            "Develop contingency plans for various growth scenarios",
            "Build scalable infrastructure and community management processes",
            "Maintain strategic reserves and flexible resource allocation",
            "Regular strategy review and adaptation processes"
        ]
        
        return mitigation_strategies
    
    def _estimate_resource_requirements(self, immediate_actions: List[StrategyRecommendation],
                                      medium_term_actions: List[StrategyRecommendation],
                                      long_term_actions: List[StrategyRecommendation]) -> Dict[str, Any]:
        """Estimate resource requirements for implementation."""
        
        # Calculate effort by difficulty and timeframe
        effort_mapping = {
            "low": {"immediate": 1, "medium": 2, "long": 3},
            "medium": {"immediate": 2, "medium": 4, "long": 6},
            "high": {"immediate": 3, "medium": 6, "long": 9}
        }
        
        total_effort = 0
        
        # Immediate actions
        for action in immediate_actions:
            difficulty = action.implementation_difficulty
            total_effort += effort_mapping.get(difficulty, {}).get("immediate", 2)
        
        # Medium term actions
        for action in medium_term_actions:
            difficulty = action.implementation_difficulty
            total_effort += effort_mapping.get(difficulty, {}).get("medium", 4)
        
        # Long term actions
        for action in long_term_actions:
            difficulty = action.implementation_difficulty
            total_effort += effort_mapping.get(difficulty, {}).get("long", 6)
        
        # Estimate resource categories
        return {
            "total_effort_points": total_effort,
            "estimated_timeline_months": len(long_term_actions) * 6,
            "resource_categories": {
                "development_effort": f"{total_effort * 0.6:.1f} FTE-months",
                "community_management": f"{total_effort * 0.2:.1f} FTE-months",
                "analysis_and_planning": f"{total_effort * 0.2:.1f} FTE-months"
            },
            "priority_allocation": {
                "immediate_critical": "40%",
                "medium_term_strategic": "35%",
                "long_term_investment": "25%"
            }
        }
    
    def get_strategy_summary(self, strategic_plan: StrategicPlan) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the strategic plan.
        
        Args:
            strategic_plan: Complete strategic plan
            
        Returns:
            Dictionary containing strategy summary
        """
        return {
            "repository": strategic_plan.repository,
            "overall_assessment": {
                "current_status": strategic_plan.current_status,
                "performance_score": strategic_plan.overall_score,
                "status_description": self._interpret_status(strategic_plan.current_status)
            },
            "strategic_focus": {
                "primary_priorities": strategic_plan.strategic_priorities[:3],
                "total_recommendations": len(strategic_plan.immediate_actions) + 
                                      len(strategic_plan.medium_term_actions) + 
                                      len(strategic_plan.long_term_actions),
                "effort_allocation": strategic_plan.resource_requirements
            },
            "implementation_roadmap": {
                "immediate_actions": len(strategic_plan.immediate_actions),
                "medium_term_actions": len(strategic_plan.medium_term_actions),
                "long_term_actions": len(strategic_plan.long_term_actions),
                "estimated_completion": "12-18 months"
            },
            "success_metrics": len(strategic_plan.success_metrics),
            "risk_level": self._assess_risk_level(strategic_plan.risk_mitigation),
            "next_steps": [
                "Review and prioritize immediate actions",
                "Assign resources and responsibilities",
                "Establish monitoring and tracking systems",
                "Schedule regular review checkpoints"
            ]
        }
    
    def _interpret_status(self, status: str) -> str:
        """Interpret current status for human-readable summary."""
        status_interpretations = {
            "critical_issues_detected": "Repository facing critical issues requiring immediate attention",
            "declining_performance": "Performance is declining and needs intervention",
            "competitive_disadvantage": "Repository is lagging behind competitors",
            "growth_plateau": "Growth has stagnated and needs revitalization",
            "strong_performance": "Repository showing strong and consistent performance",
            "market_leadership": "Repository holds strong market leadership position",
            "mixed_performance": "Repository shows mixed performance across different areas"
        }
        return status_interpretations.get(status, "Status requires assessment and interpretation")
    
    def _assess_risk_level(self, risk_mitigation: List[str]) -> str:
        """Assess overall risk level based on mitigation strategies."""
        high_risk_indicators = ["critical", "systemic", "infrastructure"]
        risk_score = sum(1 for risk in risk_mitigation if any(indicator in risk.lower() for indicator in high_risk_indicators))
        
        if risk_score >= 3:
            return "high"
        elif risk_score >= 1:
            return "medium"
        else:
            return "low"