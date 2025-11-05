"""
Growth Analysis Engine - Main Module

This module provides a unified interface to all growth analysis capabilities.
"""

from .core import GrowthAnalyzer, GrowthMetrics, GrowthPattern
from .predictors import GrowthPredictor, PredictionResult, ModelPerformance
from .anomaly_detector import AnomalyDetector, AnomalyResult, AnomalyPattern
from .benchmarking import BenchmarkAnalyzer, RepositoryProfile, BenchmarkResult, CompetitiveAnalysis
from .forecasting import TrendForecaster, ForecastPoint, TrendAnalysis
from .recommendations import StrategyRecommender, StrategicPlan, StrategyRecommendation

from .examples import (
    generate_sample_growth_data,
    generate_sample_peer_repositories,
    run_comprehensive_growth_analysis,
    demonstrate_individual_components,
    run_performance_test
)

__version__ = "1.0.0"
__all__ = [
    # Core components
    "GrowthAnalyzer",
    "GrowthMetrics", 
    "GrowthPattern",
    
    # Predictive modeling
    "GrowthPredictor",
    "PredictionResult",
    "ModelPerformance",
    
    # Anomaly detection
    "AnomalyDetector",
    "AnomalyResult",
    "AnomalyPattern",
    
    # Benchmarking
    "BenchmarkAnalyzer",
    "RepositoryProfile",
    "BenchmarkResult",
    "CompetitiveAnalysis",
    
    # Forecasting
    "TrendForecaster",
    "ForecastPoint",
    "TrendAnalysis",
    
    # Strategy recommendations
    "StrategyRecommender",
    "StrategicPlan",
    "StrategyRecommendation",
    
    # Examples and utilities
    "generate_sample_growth_data",
    "generate_sample_peer_repositories",
    "run_comprehensive_growth_analysis",
    "demonstrate_individual_components",
    "run_performance_test"
]


class GrowthAnalysisEngine:
    """
    Unified interface to all growth analysis components.
    
    This class provides a high-level API for the complete growth analysis workflow,
    combining pattern analysis, predictions, anomaly detection, benchmarking,
    forecasting, and strategy recommendations.
    """
    
    def __init__(self):
        self.analyzer = GrowthAnalyzer()
        self.predictor = GrowthPredictor()
        self.detector = AnomalyDetector()
        self.benchmarker = BenchmarkAnalyzer()
        self.forecaster = TrendForecaster()
        self.recommender = StrategyRecommender()
        
        self.growth_data = []
        self.repository_profiles = {}
        self.analysis_results = {}
    
    def add_repository_data(self, repository_name: str, 
                           growth_data: list,
                           repository_profile: RepositoryProfile = None):
        """
        Add repository data for analysis.
        
        Args:
            repository_name: Unique identifier for the repository
            growth_data: List of GrowthMetrics objects
            repository_profile: Optional RepositoryProfile for benchmarking
        """
        self.growth_data = growth_data
        self.repository_profiles[repository_name] = repository_profile
        
        # Add to components
        self.analyzer.add_growth_data(growth_data)
        if repository_profile:
            self.benchmarker.add_repository_data(repository_profile, growth_data)
    
    def add_peer_repositories(self, peer_data: dict):
        """
        Add peer repositories for benchmarking.
        
        Args:
            peer_data: Dictionary mapping repository names to (RepositoryProfile, growth_data) tuples
        """
        for repo_name, (profile, growth_data) in peer_data.items():
            self.benchmarker.add_repository_data(profile, growth_data)
    
    def run_complete_analysis(self, target_repository: str = None,
                            forecast_days: int = 30,
                            confidence_level: float = 0.95) -> dict:
        """
        Run complete growth analysis workflow.
        
        Args:
            target_repository: Repository to analyze (required for benchmarking)
            forecast_days: Number of days to forecast
            confidence_level: Confidence level for predictions and forecasts
            
        Returns:
            Complete analysis results dictionary
        """
        if not self.growth_data:
            raise ValueError("No growth data available. Add repository data first.")
        
        results = {
            'timestamp': str(pd.Timestamp.now()),
            'data_summary': {
                'data_points': len(self.growth_data),
                'date_range': {
                    'start': self.growth_data[0].date.isoformat(),
                    'end': self.growth_data[-1].date.isoformat()
                }
            }
        }
        
        print("🔍 Analyzing growth patterns...")
        # 1. Growth Pattern Analysis
        patterns = self.analyzer.analyze_growth_patterns()
        results['growth_patterns'] = [self._pattern_to_dict(p) for p in patterns]
        results['growth_summary'] = self.analyzer.get_growth_summary()
        
        print("🔮 Building predictive models...")
        # 2. Predictive Modeling
        try:
            model_performance = self.predictor.train_models(self.growth_data)
            predictions = self.predictor.predict(self.growth_data[-1], 
                                               days_ahead=forecast_days,
                                               confidence_level=confidence_level)
            
            results['predictive_modeling'] = {
                'model_performance': {name: {
                    'r2_score': perf.r2_score,
                    'mae': perf.mae,
                    'rmse': perf.rmse,
                    'mape': perf.mape,
                    'training_time': perf.training_time
                } for name, perf in model_performance.items()},
                'predictions': [self._prediction_to_dict(p) for p in predictions],
                'summary': self.predictor.get_prediction_summary()
            }
        except Exception as e:
            print(f"Predictive modeling failed: {e}")
            results['predictive_modeling'] = {'error': str(e)}
        
        print("🚨 Detecting anomalies...")
        # 3. Anomaly Detection
        anomalies, anomaly_patterns = self.detector.detect_anomalies(self.growth_data)
        results['anomaly_detection'] = {
            'anomalies': [self._anomaly_to_dict(a) for a in anomalies],
            'anomaly_patterns': [self._anomaly_pattern_to_dict(p) for p in anomaly_patterns],
            'summary': self.detector.get_anomaly_summary()
        }
        
        if target_repository:
            print("📈 Benchmarking against peers...")
            # 4. Competitive Benchmarking
            try:
                competitive_analysis = self.benchmarker.benchmark_repository(target_repository)
                results['competitive_benchmarking'] = self._competitive_analysis_to_dict(competitive_analysis)
            except Exception as e:
                print(f"Benchmarking failed: {e}")
                results['competitive_benchmarking'] = {'error': str(e)}
        
        print("📉 Forecasting trends...")
        # 5. Trend Forecasting
        try:
            trend_analysis = self.forecaster.analyze_and_forecast(
                self.growth_data,
                target_metric='stars',
                forecast_days=forecast_days,
                confidence_level=confidence_level
            )
            results['trend_forecasting'] = {
                'trend_analysis': self._trend_analysis_to_dict(trend_analysis),
                'summary': self.forecaster.get_forecast_summary(trend_analysis)
            }
        except Exception as e:
            print(f"Trend forecasting failed: {e}")
            results['trend_forecasting'] = {'error': str(e)}
        
        print("💡 Generating strategy recommendations...")
        # 6. Strategy Recommendations
        try:
            predictions_list = results.get('predictive_modeling', {}).get('predictions', [])
            anomalies_list = results.get('anomaly_detection', {}).get('anomalies', [])
            anomaly_patterns_list = results.get('anomaly_detection', {}).get('anomaly_patterns', [])
            
            strategic_plan = self.recommender.generate_strategic_plan(
                repo_name=target_repository or "repository",
                growth_patterns=patterns,
                predictions=[self._dict_to_prediction(p) for p in predictions_list] if predictions_list else [],
                anomalies=[self._dict_to_anomaly(a) for a in anomalies_list] if anomalies_list else [],
                anomaly_patterns=[self._dict_to_anomaly_pattern(ap) for ap in anomaly_patterns_list] if anomaly_patterns_list else [],
                competitive_analysis=self._dict_to_competitive_analysis(
                    results.get('competitive_benchmarking', {})
                ) if 'competitive_benchmarking' in results and 'error' not in results['competitive_benchmarking'] else None,
                trend_analysis=self._dict_to_trend_analysis(
                    results.get('trend_forecasting', {}).get('trend_analysis', {})
                ) if 'trend_forecasting' in results and 'error' not in results['trend_forecasting'] else None
            )
            
            results['strategy_recommendations'] = {
                'strategic_plan': self._strategic_plan_to_dict(strategic_plan),
                'summary': self.recommender.get_strategy_summary(strategic_plan)
            }
        except Exception as e:
            print(f"Strategy recommendations failed: {e}")
            results['strategy_recommendations'] = {'error': str(e)}
        
        # Store results
        self.analysis_results = results
        
        print("✅ Complete analysis finished!")
        return results
    
    def get_quick_insights(self) -> dict:
        """Get quick insights from the most recent analysis."""
        if not self.analysis_results:
            return {'error': 'No analysis results available. Run analysis first.'}
        
        results = self.analysis_results
        
        insights = {
            'overall_assessment': 'Unknown',
            'key_findings': [],
            'immediate_actions': [],
            'trends_to_watch': []
        }
        
        # Extract key insights from each component
        if 'growth_summary' in results:
            summary = results['growth_summary']
            if 'patterns_detected' in summary:
                insights['key_findings'].append(f"Detected {summary['patterns_detected']} growth patterns")
        
        if 'anomaly_detection' in results:
            anomalies = results['anomaly_detection']['summary']
            if 'total_anomalies' in anomalies and anomalies['total_anomalies'] > 0:
                insights['immediate_actions'].append(f"Address {anomalies['total_anomalies']} detected anomalies")
        
        if 'predictive_modeling' in results:
            predictions = results['predictive_modeling']
            if 'predictions' in predictions and predictions['predictions']:
                forecast = predictions['predictions'][-1]
                trend = "growth" if forecast['predicted_value'] > predictions['predictions'][0]['predicted_value'] else "decline"
                insights['trends_to_watch'].append(f"Expected {trend} in coming period")
        
        return insights
    
    def export_results(self, filename: str = None) -> str:
        """Export analysis results to JSON file."""
        if not self.analysis_results:
            raise ValueError("No analysis results to export. Run analysis first.")
        
        import json
        from datetime import datetime
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"growth_analysis_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            return f"Results exported to {filename}"
        except Exception as e:
            return f"Export failed: {e}"
    
    # Helper methods for data conversion
    def _pattern_to_dict(self, pattern: GrowthPattern) -> dict:
        return {
            'pattern_type': pattern.pattern_type,
            'confidence': pattern.confidence,
            'description': pattern.description,
            'start_date': pattern.start_date.isoformat(),
            'end_date': pattern.end_date.isoformat() if pattern.end_date else None,
            'metrics': pattern.metrics,
            'statistics': pattern.statistics,
            'recommendations': pattern.recommendations
        }
    
    def _prediction_to_dict(self, prediction: PredictionResult) -> dict:
        return {
            'date': prediction.date.isoformat(),
            'predicted_value': prediction.predicted_value,
            'confidence_lower': prediction.confidence_lower,
            'confidence_upper': prediction.confidence_upper,
            'confidence_level': prediction.confidence_level,
            'model_used': prediction.model_used,
            'feature_importance': prediction.feature_importance
        }
    
    def _anomaly_to_dict(self, anomaly: AnomalyResult) -> dict:
        return {
            'date': anomaly.date.isoformat(),
            'metric': anomaly.metric,
            'value': anomaly.value,
            'expected_value': anomaly.expected_value,
            'anomaly_score': anomaly.anomaly_score,
            'severity': anomaly.severity,
            'description': anomaly.description,
            'confidence': anomaly.confidence,
            'recommendation': anomaly.recommendation
        }
    
    def _anomaly_pattern_to_dict(self, pattern: AnomalyPattern) -> dict:
        return {
            'pattern_type': pattern.pattern_type,
            'start_date': pattern.start_date.isoformat(),
            'end_date': pattern.end_date.isoformat() if pattern.end_date else None,
            'affected_metrics': pattern.affected_metrics,
            'severity': pattern.severity,
            'confidence': pattern.confidence,
            'description': pattern.description,
            'impact_estimate': pattern.impact_estimate,
            'recommendations': pattern.recommendations
        }
    
    def _competitive_analysis_to_dict(self, analysis: CompetitiveAnalysis) -> dict:
        return {
            'repository_name': analysis.repository_name,
            'overall_score': analysis.overall_score,
            'strengths': analysis.strengths,
            'weaknesses': analysis.weaknesses,
            'market_position': analysis.market_position,
            'peer_repositories': analysis.peer_repositories,
            'benchmark_results': [self._benchmark_result_to_dict(br) for br in analysis.benchmark_results],
            'growth_opportunities': analysis.growth_opportunities,
            'risk_areas': analysis.risk_areas
        }
    
    def _benchmark_result_to_dict(self, result: BenchmarkResult) -> dict:
        return {
            'metric': result.metric,
            'target_value': result.target_value,
            'percentile_rank': result.percentile_rank,
            'z_score': result.z_score,
            'performance_rating': result.performance_rating,
            'gap_from_median': result.gap_from_median,
            'recommendations': result.recommendations
        }
    
    def _trend_analysis_to_dict(self, analysis: TrendAnalysis) -> dict:
        return {
            'metric': analysis.metric,
            'overall_trend': analysis.overall_trend,
            'trend_strength': analysis.trend_strength,
            'growth_rate': analysis.growth_rate,
            'seasonality_detected': analysis.seasonality_detected,
            'trend_changes': analysis.trend_changes,
            'forecast_points': [self._forecast_point_to_dict(fp) for fp in analysis.forecast_points],
            'model_quality': analysis.model_quality,
            'confidence_assessment': analysis.confidence_assessment
        }
    
    def _forecast_point_to_dict(self, point: ForecastPoint) -> dict:
        return {
            'date': point.date.isoformat(),
            'predicted_value': point.predicted_value,
            'confidence_lower': point.confidence_lower,
            'confidence_upper': point.confidence_upper,
            'trend_direction': point.trend_direction,
            'trend_strength': point.trend_strength,
            'confidence_level': point.confidence_level
        }
    
    def _strategic_plan_to_dict(self, plan: StrategicPlan) -> dict:
        return {
            'repository': plan.repository,
            'current_status': plan.current_status,
            'overall_score': plan.overall_score,
            'strategic_priorities': plan.strategic_priorities,
            'immediate_actions': [self._strategy_recommendation_to_dict(ar) for ar in plan.immediate_actions],
            'medium_term_actions': [self._strategy_recommendation_to_dict(ar) for ar in plan.medium_term_actions],
            'long_term_actions': [self._strategy_recommendation_to_dict(ar) for ar in plan.long_term_actions],
            'success_metrics': plan.success_metrics,
            'risk_mitigation': plan.risk_mitigation,
            'resource_requirements': plan.resource_requirements
        }
    
    def _strategy_recommendation_to_dict(self, rec: StrategyRecommendation) -> dict:
        return {
            'category': rec.category,
            'priority': rec.priority,
            'title': rec.title,
            'description': rec.description,
            'rationale': rec.rationale,
            'action_items': rec.action_items,
            'expected_impact': rec.expected_impact,
            'implementation_difficulty': rec.implementation_difficulty,
            'timeframe': rec.timeframe,
            'metrics_to_monitor': rec.metrics_to_monitor,
            'confidence_score': rec.confidence_score
        }
    
    # Dictionary to object conversion methods
    def _dict_to_prediction(self, data: dict) -> PredictionResult:
        return PredictionResult(
            date=pd.to_datetime(data['date']),
            predicted_value=data['predicted_value'],
            confidence_lower=data['confidence_lower'],
            confidence_upper=data['confidence_upper'],
            confidence_level=data['confidence_level'],
            model_used=data['model_used'],
            feature_importance=data.get('feature_importance')
        )
    
    def _dict_to_anomaly(self, data: dict) -> AnomalyResult:
        return AnomalyResult(
            date=pd.to_datetime(data['date']),
            metric=data['metric'],
            value=data['value'],
            expected_value=data['expected_value'],
            anomaly_score=data['anomaly_score'],
            severity=data['severity'],
            description=data['description'],
            confidence=data['confidence'],
            recommendation=data['recommendation']
        )
    
    def _dict_to_anomaly_pattern(self, data: dict) -> AnomalyPattern:
        return AnomalyPattern(
            pattern_type=data['pattern_type'],
            start_date=pd.to_datetime(data['start_date']),
            end_date=pd.to_datetime(data['end_date']) if data['end_date'] else None,
            affected_metrics=data['affected_metrics'],
            severity=data['severity'],
            confidence=data['confidence'],
            description=data['description'],
            impact_estimate=data.get('impact_estimate'),
            recommendations=data['recommendations']
        )
    
    def _dict_to_competitive_analysis(self, data: dict) -> CompetitiveAnalysis:
        # Simplified conversion - in practice, you'd need to reconstruct all objects
        return CompetitiveAnalysis(
            repository_name=data['repository_name'],
            overall_score=data['overall_score'],
            strengths=data['strengths'],
            weaknesses=data['weaknesses'],
            market_position=data['market_position'],
            peer_repositories=data['peer_repositories'],
            benchmark_results=[],  # Would need to convert benchmark results
            growth_opportunities=data['growth_opportunities'],
            risk_areas=data['risk_areas']
        )
    
    def _dict_to_trend_analysis(self, data: dict) -> TrendAnalysis:
        return TrendAnalysis(
            metric=data['metric'],
            overall_trend=data['overall_trend'],
            trend_strength=data['trend_strength'],
            growth_rate=data['growth_rate'],
            seasonality_detected=data['seasonality_detected'],
            trend_changes=data['trend_changes'],
            forecast_points=[self._dict_to_forecast_point(fp) for fp in data['forecast_points']],
            model_quality=data['model_quality'],
            confidence_assessment=data['confidence_assessment']
        )
    
    def _dict_to_forecast_point(self, data: dict) -> ForecastPoint:
        return ForecastPoint(
            date=pd.to_datetime(data['date']),
            predicted_value=data['predicted_value'],
            confidence_lower=data['confidence_lower'],
            confidence_upper=data['confidence_upper'],
            trend_direction=data['trend_direction'],
            trend_strength=data['trend_strength'],
            confidence_level=data['confidence_level']
        )


def create_growth_engine():
    """Factory function to create a growth analysis engine instance."""
    return GrowthAnalysisEngine()


# Quick start example
def quick_start_example():
    """Quick start example demonstrating the growth analysis engine."""
    from .examples import generate_sample_growth_data, generate_sample_peer_repositories
    
    # Create engine
    engine = create_growth_engine()
    
    # Add sample data
    growth_data = generate_sample_growth_data(days=90, start_stars=200)
    engine.add_repository_data("demo-repo", growth_data)
    
    # Add peer repositories
    peer_repos = generate_sample_peer_repositories()
    peer_data = {}
    for peer in peer_repos[:3]:
        peer_growth = generate_sample_growth_data(days=60, start_stars=peer.stars // 5)
        peer_data[f"{peer.owner}/{peer.name}"] = (peer, peer_growth)
    
    engine.add_peer_repositories(peer_data)
    
    # Run complete analysis
    results = engine.run_complete_analysis(target_repository="demo-repo")
    
    # Get quick insights
    insights = engine.get_quick_insights()
    
    return results, insights


if __name__ == "__main__":
    print("Growth Analysis Engine - Quick Start")
    results, insights = quick_start_example()
    print("Analysis complete!")
    print(f"Found {len(results['growth_patterns'])} growth patterns")
    print(f"Detected {results['anomaly_detection']['summary']['total_anomalies']} anomalies")
    print(f"Overall score: {results['strategy_recommendations']['summary']['overall_assessment']['performance_score']:.2f}")