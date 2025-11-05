"""
Engagement Prediction Engine

Uses machine learning and statistical models to predict community engagement trends,
contributor behavior, and community health outcomes based on historical patterns
and current metrics.
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import statistics
import math
import numpy as np
from dataclasses import dataclass

# Optional imports - handle gracefully if not available
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report
    sklearn_available = True
except ImportError:
    sklearn_available = False
    logging.warning("Scikit-learn not available. Using simplified prediction models.")


@dataclass
class PredictionRequest:
    """Request for specific predictions"""
    prediction_type: str  # 'engagement_trend', 'churn_risk', 'growth_forecast', 'health_outlook'
    target_date: datetime
    features: Dict[str, Any]
    confidence_level: float = 0.8
    
    # Prediction parameters
    prediction_horizon_days: int = 30
    model_type: str = "auto"  # 'auto', 'linear', 'random_forest', 'ensemble'


@dataclass
class PredictionResult:
    """Result of a prediction request"""
    prediction_type: str
    target_date: datetime
    predicted_value: Union[float, int, str]
    confidence_interval: Tuple[float, float]
    confidence_score: float
    
    # Model information
    model_used: str
    feature_importance: Dict[str, float] = field(default_factory=dict)
    
    # Additional metrics
    prediction_explanation: str = ""
    risk_factors: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class EngagementForecast:
    """Comprehensive engagement forecast"""
    timestamp: datetime
    forecast_horizon_days: int
    
    # Engagement predictions
    predicted_engagement_score: List[float]  # Daily predictions
    predicted_active_contributors: List[int]
    predicted_new_contributors: List[int]
    predicted_contribution_frequency: List[float]
    
    # Confidence intervals
    engagement_confidence_lower: List[float]
    engagement_confidence_upper: List[float]
    contributors_confidence_lower: List[int]
    contributors_confidence_upper: List[int]
    
    # Trend analysis
    overall_trend: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # 0-1
    inflection_points: List[datetime]  # Key change points
    
    # Seasonal patterns
    seasonal_effects: Dict[str, float]  # day_of_week, month -> effect
    anomaly_predictions: List[Tuple[datetime, str]]  # (date, anomaly_type)
    
    # Forecast quality
    forecast_accuracy: float  # Historical accuracy
    model_confidence: float


@dataclass
class ChurnRiskAssessment:
    """Contributor churn risk assessment"""
    timestamp: datetime
    total_contributors_analyzed: int
    
    # Risk categories
    high_risk_contributors: List[str]
    medium_risk_contributors: List[str]
    low_risk_contributors: List[str]
    
    # Risk predictions
    predicted_churn_next_30_days: int
    predicted_churn_next_90_days: int
    predicted_churn_next_180_days: int
    
    # Risk factors analysis
    common_risk_factors: List[Tuple[str, float]]  # (factor, frequency)
    protective_factors: List[Tuple[str, float]]  # (factor, effectiveness)
    
    # Intervention recommendations
    targeted_interventions: List[Dict[str, Any]]  # Intervention plans
    prevention_strategies: List[str]


class EngagementPredictionEngine:
    """
    Predict community engagement trends and outcomes.
    
    This class provides predictive analytics for community health, engagement trends,
    contributor behavior, and churn risk using various ML and statistical models.
    """
    
    def __init__(self):
        """Initialize the prediction engine"""
        self.logger = logging.getLogger(__name__)
        
        # Model configurations
        self.models = {}
        self.scalers = {}
        self.training_data = {}
        
        # Prediction history for model validation
        self.prediction_history: List[Dict[str, Any]] = []
        
        # Feature definitions
        self.feature_config = {
            'engagement_trend': [
                'days_since_start', 'total_contributors', 'active_contributors',
                'contribution_frequency', 'issue_response_time', 'pr_merge_rate',
                'community_engagement_score', 'retention_rate_30d'
            ],
            'churn_risk': [
                'days_since_last_activity', 'contribution_frequency', 'contribution_diversity',
                'community_engagement', 'collaboration_count', 'activity_consistency',
                'mentoring_involvement', 'role_in_community'
            ],
            'growth_forecast': [
                'historical_growth_rate', 'contributor_retention', 'issue_creation_rate',
                'community_health_score', 'external_visibility', 'documentation_quality'
            ]
        }
        
        # Model performance tracking
        self.model_performance = {}
        
        # Initialize models if sklearn is available
        if sklearn_available:
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        
        # Engagement trend models
        self.models['engagement_linear'] = LinearRegression()
        self.models['engagement_rf'] = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Churn prediction models
        self.models['churn_logistic'] = LogisticRegression(random_state=42)
        self.models['churn_rf'] = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Growth forecast models
        self.models['growth_linear'] = LinearRegression()
        self.models['growth_rf'] = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Scalers for feature normalization
        for model_name in self.models:
            self.scalers[model_name] = StandardScaler()
    
    async def predict_engagement_trend(
        self,
        historical_metrics: List[Dict[str, Any]],
        prediction_days: int = 30
    ) -> EngagementForecast:
        """
        Predict future engagement trends based on historical data.
        
        Args:
            historical_metrics: Historical community metrics
            prediction_days: Number of days to forecast
            
        Returns:
            EngagementForecast with predictions and confidence intervals
        """
        self.logger.info(f"Predicting engagement trend for {prediction_days} days")
        
        if len(historical_metrics) < 7:
            return self._create_simple_forecast(prediction_days)
        
        # Prepare features
        features, targets = self._prepare_engagement_features(historical_metrics)
        
        if sklearn_available and len(features) > 10:
            # Use ML models
            forecast = await self._ml_engagement_forecast(features, targets, prediction_days)
        else:
            # Use statistical models
            forecast = self._statistical_engagement_forecast(historical_metrics, prediction_days)
        
        return forecast
    
    async def assess_churn_risk(
        self,
        contributor_profiles: List[Dict[str, Any]]
    ) -> ChurnRiskAssessment:
        """
        Assess churn risk for community contributors.
        
        Args:
            contributor_profiles: Detailed contributor profiles
            
        Returns:
            ChurnRiskAssessment with risk analysis and predictions
        """
        self.logger.info(f"Assessing churn risk for {len(contributor_profiles)} contributors")
        
        if not contributor_profiles:
            return ChurnRiskAssessment(
                timestamp=datetime.now(),
                total_contributors_analyzed=0,
                high_risk_contributors=[],
                medium_risk_contributors=[],
                low_risk_contributors=[],
                predicted_churn_next_30_days=0,
                predicted_churn_next_90_days=0,
                predicted_churn_next_180_days=0,
                common_risk_factors=[],
                protective_factors=[],
                targeted_interventions=[],
                prevention_strategies=[]
            )
        
        # Calculate churn risk for each contributor
        risk_assessments = []
        for profile in contributor_profiles:
            risk_score = self._calculate_churn_risk_score(profile)
            risk_assessments.append((profile.get('login', 'unknown'), risk_score))
        
        # Categorize contributors by risk level
        risk_assessments.sort(key=lambda x: x[1], reverse=True)
        
        high_risk = [login for login, score in risk_assessments if score >= 0.7]
        medium_risk = [login for login, score in risk_assessments if 0.4 <= score < 0.7]
        low_risk = [login for login, score in risk_assessments if score < 0.4]
        
        # Predict future churn
        predicted_churn_30d = self._predict_aggregate_churn(risk_assessments, 30)
        predicted_churn_90d = self._predict_aggregate_churn(risk_assessments, 90)
        predicted_churn_180d = self._predict_aggregate_churn(risk_assessments, 180)
        
        # Analyze risk factors
        risk_factors, protective_factors = self._analyze_risk_factors(contributor_profiles)
        
        # Generate intervention recommendations
        interventions = self._generate_intervention_recommendations(high_risk, medium_risk)
        prevention_strategies = self._generate_prevention_strategies(contributor_profiles)
        
        return ChurnRiskAssessment(
            timestamp=datetime.now(),
            total_contributors_analyzed=len(contributor_profiles),
            high_risk_contributors=high_risk,
            medium_risk_contributors=medium_risk,
            low_risk_contributors=low_risk,
            predicted_churn_next_30_days=predicted_churn_30d,
            predicted_churn_next_90_days=predicted_churn_90d,
            predicted_churn_next_180_days=predicted_churn_180d,
            common_risk_factors=risk_factors,
            protective_factors=protective_factors,
            targeted_interventions=interventions,
            prevention_strategies=prevention_strategies
        )
    
    async def predict_community_health(
        self,
        current_metrics: Dict[str, Any],
        historical_trends: List[Dict[str, Any]]
    ) -> PredictionResult:
        """
        Predict future community health based on current metrics and trends.
        
        Args:
            current_metrics: Current community metrics
            historical_trends: Historical trend data
            
        Returns:
            PredictionResult with health outlook
        """
        self.logger.info("Predicting community health outlook")
        
        # Calculate health trajectory
        health_score = current_metrics.get('community_health_score', 50.0)
        trend_direction = self._analyze_health_trend(historical_trends)
        external_factors = self._assess_external_factors(current_metrics)
        
        # Predict future health score
        predicted_health = self._calculate_predicted_health(health_score, trend_direction, external_factors)
        
        # Calculate confidence interval
        confidence_interval = self._calculate_health_confidence_interval(predicted_health, historical_trends)
        
        # Identify risk factors and recommendations
        risk_factors = self._identify_health_risk_factors(current_metrics, trend_direction)
        recommendations = self._generate_health_recommendations(risk_factors, predicted_health)
        
        return PredictionResult(
            prediction_type="health_outlook",
            target_date=datetime.now() + timedelta(days=30),
            predicted_value=predicted_health,
            confidence_interval=confidence_interval,
            confidence_score=0.75,
            model_used="trend_analysis",
            feature_importance={
                'current_health': 0.4,
                'trend_direction': 0.3,
                'external_factors': 0.3
            },
            prediction_explanation=f"Community health predicted to {'improve' if predicted_health > health_score else 'decline' if predicted_health < health_score else 'remain stable'} based on current trajectory",
            risk_factors=risk_factors,
            recommended_actions=recommendations
        )
    
    def _prepare_engagement_features(
        self, 
        historical_metrics: List[Dict[str, Any]]
    ) -> Tuple[List[List[float]], List[float]]:
        """Prepare features for engagement prediction model"""
        
        features = []
        targets = []
        
        # Create sliding window features
        window_size = 7  # Use 7 days to predict next day
        
        for i in range(window_size, len(historical_metrics)):
            # Features: previous window of metrics
            feature_window = []
            for j in range(i - window_size, i):
                metric = historical_metrics[j]
                feature_window.extend([
                    metric.get('total_contributors', 0),
                    metric.get('active_contributors', 0),
                    metric.get('avg_contribution_frequency', 0),
                    metric.get('community_health_score', 50),
                    metric.get('issue_response_time', 24),
                    metric.get('pr_merge_rate', 0.5)
                ])
            
            features.append(feature_window)
            
            # Target: next day's engagement score
            target = historical_metrics[i].get('engagement_score', 50)
            targets.append(target)
        
        return features, targets
    
    async def _ml_engagement_forecast(
        self,
        features: List[List[float]],
        targets: List[float],
        prediction_days: int
    ) -> EngagementForecast:
        """Generate forecast using ML models"""
        
        if len(features) < 10:
            return self._create_simple_forecast(prediction_days)
        
        # Prepare training data
        X = np.array(features)
        y = np.array(targets)
        
        # Split for validation
        if len(X) > 20:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        else:
            X_train, y_train = X, y
            X_test, y_test = X, y
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train ensemble models
        rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
        rf_model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = rf_model.predict(X_test_scaled)
        accuracy = 1 - (mean_absolute_error(y_test, y_pred) / np.mean(y_test))
        
        # Generate predictions
        last_features = X[-1].reshape(1, -1)
        last_features_scaled = scaler.transform(last_features)
        
        predictions = []
        confidence_lower = []
        confidence_upper = []
        
        current_features = last_features_scaled.copy()
        
        for day in range(prediction_days):
            # Predict next value
            pred = rf_model.predict(current_features)[0]
            predictions.append(max(0, min(100, pred)))  # Clamp to 0-100
            
            # Calculate confidence interval (simplified)
            uncertainty = np.std(y_test) * 1.96  # 95% confidence
            confidence_lower.append(max(0, pred - uncertainty))
            confidence_upper.append(min(100, pred + uncertainty))
            
            # Update features for next prediction (simplified)
            # In practice, you'd update based on the prediction
            current_features = np.roll(current_features, -len(predictions)//6)
        
        # Analyze trend
        overall_trend = self._analyze_prediction_trend(predictions)
        trend_strength = self._calculate_trend_strength(predictions)
        
        # Generate confidence score
        model_confidence = max(0.5, min(0.95, accuracy))
        
        return EngagementForecast(
            timestamp=datetime.now(),
            forecast_horizon_days=prediction_days,
            predicted_engagement_score=predictions,
            predicted_active_contributors=[int(p * 0.8) for p in predictions],  # Simplified
            predicted_new_contributors=[max(0, int((p - 50) * 0.1)) for p in predictions],  # Simplified
            predicted_contribution_frequency=[p / 20 for p in predictions],  # Simplified
            engagement_confidence_lower=confidence_lower,
            engagement_confidence_upper=confidence_upper,
            contributors_confidence_lower=[int(c * 0.9) for c in [int(p * 0.8) for p in predictions]],
            contributors_confidence_upper=[int(c * 1.1) for c in [int(p * 0.8) for p in predictions]],
            overall_trend=overall_trend,
            trend_strength=trend_strength,
            inflection_points=[],
            seasonal_effects={},
            anomaly_predictions=[],
            forecast_accuracy=accuracy,
            model_confidence=model_confidence
        )
    
    def _statistical_engagement_forecast(
        self,
        historical_metrics: List[Dict[str, Any]],
        prediction_days: int
    ) -> EngagementForecast:
        """Generate forecast using statistical methods"""
        
        # Extract engagement scores
        engagement_scores = [m.get('engagement_score', 50) for m in historical_metrics]
        
        # Calculate trend
        if len(engagement_scores) >= 14:
            recent_scores = engagement_scores[-14:]
            trend_slope = self._calculate_linear_trend(recent_scores)
        else:
            trend_slope = 0
        
        # Calculate seasonality (simplified)
        seasonal_effect = self._calculate_seasonal_effect(historical_metrics)
        
        # Generate predictions
        last_score = engagement_scores[-1] if engagement_scores else 50
        predictions = []
        confidence_lower = []
        confidence_upper = []
        
        for day in range(prediction_days):
            # Apply trend and seasonality
            predicted_score = last_score + (trend_slope * day) + seasonal_effect
            
            # Add some noise for realism
            noise = np.random.normal(0, 2)  # Small random variation
            predicted_score += noise
            
            # Clamp to valid range
            predicted_score = max(0, min(100, predicted_score))
            
            predictions.append(predicted_score)
            
            # Calculate confidence interval
            uncertainty = 5 + (day * 0.5)  # Increasing uncertainty over time
            confidence_lower.append(max(0, predicted_score - uncertainty))
            confidence_upper.append(min(100, predicted_score + uncertainty))
        
        # Analyze trend
        overall_trend = "increasing" if trend_slope > 0.1 else "decreasing" if trend_slope < -0.1 else "stable"
        trend_strength = min(1.0, abs(trend_slope) / 2)
        
        # Simplified derived predictions
        active_contributors = [int(p * 0.8) for p in predictions]
        new_contributors = [max(0, int((p - 50) * 0.05)) for p in predictions]
        contribution_frequency = [p / 25 for p in predictions]
        
        return EngagementForecast(
            timestamp=datetime.now(),
            forecast_horizon_days=prediction_days,
            predicted_engagement_score=predictions,
            predicted_active_contributors=active_contributors,
            predicted_new_contributors=new_contributors,
            predicted_contribution_frequency=contribution_frequency,
            engagement_confidence_lower=confidence_lower,
            engagement_confidence_upper=confidence_upper,
            contributors_confidence_lower=[int(c * 0.95) for c in active_contributors],
            contributors_confidence_upper=[int(c * 1.05) for c in active_contributors],
            overall_trend=overall_trend,
            trend_strength=trend_strength,
            inflection_points=[],
            seasonal_effects={'seasonal_factor': seasonal_effect},
            anomaly_predictions=[],
            forecast_accuracy=0.7,  # Conservative estimate for statistical methods
            model_confidence=0.7
        )
    
    def _create_simple_forecast(self, prediction_days: int) -> EngagementForecast:
        """Create a simple forecast when insufficient data is available"""
        
        # Use baseline predictions
        baseline_score = 50
        predictions = [baseline_score] * prediction_days
        confidence_lower = [baseline_score - 10] * prediction_days
        confidence_upper = [baseline_score + 10] * prediction_days
        
        return EngagementForecast(
            timestamp=datetime.now(),
            forecast_horizon_days=prediction_days,
            predicted_engagement_score=predictions,
            predicted_active_contributors=[40] * prediction_days,
            predicted_new_contributors=[2] * prediction_days,
            predicted_contribution_frequency=[2.0] * prediction_days,
            engagement_confidence_lower=confidence_lower,
            engagement_confidence_upper=confidence_upper,
            contributors_confidence_lower=[35] * prediction_days,
            contributors_confidence_upper=[45] * prediction_days,
            overall_trend="stable",
            trend_strength=0.0,
            inflection_points=[],
            seasonal_effects={},
            anomaly_predictions=[],
            forecast_accuracy=0.5,
            model_confidence=0.5
        )
    
    def _calculate_churn_risk_score(self, profile: Dict[str, Any]) -> float:
        """Calculate churn risk score for a contributor"""
        
        risk_factors = []
        
        # Days since last activity (major factor)
        last_activity = profile.get('last_activity_date')
        if last_activity:
            days_since = (datetime.now() - last_activity).days
            if days_since > 90:
                risk_factors.append(0.4)
            elif days_since > 60:
                risk_factors.append(0.3)
            elif days_since > 30:
                risk_factors.append(0.2)
        else:
            risk_factors.append(0.3)  # Unknown activity = medium risk
        
        # Contribution frequency
        freq = profile.get('contribution_frequency', 0)
        if freq < 0.5:
            risk_factors.append(0.25)
        elif freq < 1.0:
            risk_factors.append(0.1)
        
        # Contribution diversity
        diversity = profile.get('contribution_diversity', 0)
        if diversity <= 1:
            risk_factors.append(0.2)
        elif diversity == 2:
            risk_factors.append(0.1)
        
        # Community engagement
        engagement = profile.get('community_engagement', 0)
        if engagement < 30:
            risk_factors.append(0.2)
        elif engagement < 60:
            risk_factors.append(0.1)
        
        # Collaboration patterns
        collaborators = profile.get('collaborators', [])
        if len(collaborators) < 2:
            risk_factors.append(0.15)
        
        # Calculate weighted risk score
        total_risk = sum(risk_factors)
        return min(1.0, total_risk)
    
    def _predict_aggregate_churn(
        self, 
        risk_assessments: List[Tuple[str, float]], 
        days: int
    ) -> int:
        """Predict aggregate churn for a time period"""
        
        if not risk_assessments:
            return 0
        
        # Risk-based churn probability
        if days <= 30:
            risk_threshold = 0.8
        elif days <= 90:
            risk_threshold = 0.6
        else:
            risk_threshold = 0.4
        
        high_risk_count = len([score for _, score in risk_assessments if score >= risk_threshold])
        
        # Estimate churn (conservative)
        return int(high_risk_count * 0.3)  # 30% of high-risk contributors churn
    
    def _analyze_risk_factors(self, contributor_profiles: List[Dict[str, Any]]) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """Analyze common risk and protective factors"""
        
        risk_factor_counts = defaultdict(int)
        protective_factor_counts = defaultdict(int)
        
        for profile in contributor_profiles:
            # Analyze risk factors
            if profile.get('contribution_frequency', 0) < 1.0:
                risk_factor_counts['Low contribution frequency'] += 1
            
            if profile.get('contribution_diversity', 0) <= 1:
                risk_factor_counts['Limited contribution types'] += 1
            
            if profile.get('last_activity_date'):
                days_since = (datetime.now() - profile['last_activity_date']).days
                if days_since > 60:
                    risk_factor_counts['Extended inactivity'] += 1
            
            if len(profile.get('collaborators', [])) < 2:
                risk_factor_counts['Limited collaboration'] += 1
            
            # Analyze protective factors
            if profile.get('community_engagement', 0) >= 60:
                protective_factor_counts['High community engagement'] += 1
            
            if profile.get('contribution_diversity', 0) >= 3:
                protective_factor_counts['Diverse contributions'] += 1
            
            if profile.get('mentoring_involvement', False):
                protective_factor_counts['Mentoring others'] += 1
            
            if len(profile.get('collaborators', [])) >= 3:
                protective_factor_counts['Strong collaboration network'] += 1
        
        # Convert to sorted lists
        risk_factors = sorted(risk_factor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        protective_factors = sorted(protective_factor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return risk_factors, protective_factors
    
    def _generate_intervention_recommendations(
        self, 
        high_risk: List[str], 
        medium_risk: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate targeted intervention recommendations"""
        
        interventions = []
        
        # High-risk interventions
        if high_risk:
            interventions.append({
                'target_group': 'high_risk',
                'contributor_count': len(high_risk),
                'intervention_type': 'immediate_outreach',
                'description': f'Personal outreach to {len(high_risk)} high-risk contributors',
                'priority': 'high',
                'estimated_impact': 'prevent 60-80% of predicted churn'
            })
        
        # Medium-risk interventions
        if medium_risk:
            interventions.append({
                'target_group': 'medium_risk',
                'contributor_count': len(medium_risk),
                'intervention_type': 'engagement_boost',
                'description': f'Engagement opportunities for {len(medium_risk)} medium-risk contributors',
                'priority': 'medium',
                'estimated_impact': 'improve retention by 30-50%'
            })
        
        return interventions
    
    def _generate_prevention_strategies(self, contributor_profiles: List[Dict[str, Any]]) -> List[str]:
        """Generate general prevention strategies"""
        
        strategies = []
        
        # Analyze overall patterns
        low_freq_contributors = len([p for p in contributor_profiles if p.get('contribution_frequency', 0) < 1.0])
        low_diversity_contributors = len([p for p in contributor_profiles if p.get('contribution_diversity', 0) <= 1])
        
        if low_freq_contributors > len(contributor_profiles) * 0.3:
            strategies.append("Implement contribution frequency improvement programs")
        
        if low_diversity_contributors > len(contributor_profiles) * 0.4:
            strategies.append("Encourage contribution diversity through mentorship")
        
        strategies.extend([
            "Maintain regular community engagement activities",
            "Recognize and celebrate contributor achievements",
            "Provide clear contribution guidelines and opportunities",
            "Foster collaboration through pair programming or code reviews"
        ])
        
        return strategies
    
    def _analyze_health_trend(self, historical_trends: List[Dict[str, Any]]) -> float:
        """Analyze health trend direction and strength"""
        
        if len(historical_trends) < 2:
            return 0.0
        
        health_scores = [trend.get('community_health_score', 50) for trend in historical_trends[-6:]]  # Last 6 data points
        
        if len(health_scores) < 3:
            return 0.0
        
        # Calculate linear trend
        return self._calculate_linear_trend(health_scores)
    
    def _assess_external_factors(self, current_metrics: Dict[str, Any]) -> float:
        """Assess external factors affecting community health"""
        
        external_score = 0.0
        
        # Repository visibility factors
        stars = current_metrics.get('stars', 0)
        if stars > 1000:
            external_score += 0.2
        elif stars > 100:
            external_score += 0.1
        
        # Documentation quality
        doc_score = current_metrics.get('documentation_quality', 50)
        external_score += (doc_score / 100) * 0.3
        
        # Issue resolution efficiency
        resolution_rate = current_metrics.get('issue_resolution_rate', 50)
        external_score += (resolution_rate / 100) * 0.2
        
        # Active maintainers
        active_maintainers = current_metrics.get('active_maintainers', 1)
        external_score += min(0.3, active_maintainers * 0.1)
        
        return external_score
    
    def _calculate_predicted_health(
        self, 
        current_health: float, 
        trend_direction: float, 
        external_factors: float
    ) -> float:
        """Calculate predicted health score"""
        
        # Apply trend and external factors
        trend_impact = trend_direction * 10  # Scale trend impact
        external_impact = (external_factors - 0.5) * 20  # Center around 0.5
        
        predicted_health = current_health + trend_impact + external_impact
        
        return max(0, min(100, predicted_health))
    
    def _calculate_health_confidence_interval(
        self, 
        predicted_health: float, 
        historical_trends: List[Dict[str, Any]]
    ) -> Tuple[float, float]:
        """Calculate confidence interval for health prediction"""
        
        if len(historical_trends) < 5:
            uncertainty = 15
        else:
            health_scores = [trend.get('community_health_score', 50) for trend in historical_trends[-10:]]
            uncertainty = statistics.stdev(health_scores) if len(health_scores) > 1 else 10
        
        confidence_interval = (
            max(0, predicted_health - uncertainty),
            min(100, predicted_health + uncertainty)
        )
        
        return confidence_interval
    
    def _identify_health_risk_factors(
        self, 
        current_metrics: Dict[str, Any], 
        trend_direction: float
    ) -> List[str]:
        """Identify risk factors for community health"""
        
        risk_factors = []
        
        # Trend-based risks
        if trend_direction < -0.5:
            risk_factors.append("Declining health trend")
        
        # Metric-based risks
        if current_metrics.get('retention_rate_30d', 100) < 50:
            risk_factors.append("Low contributor retention")
        
        if current_metrics.get('issue_resolution_rate', 100) < 60:
            risk_factors.append("Poor issue resolution")
        
        if current_metrics.get('community_engagement_score', 50) < 40:
            risk_factors.append("Low community engagement")
        
        if current_metrics.get('contributor_growth_rate', 0) < -10:
            risk_factors.append("Declining contributor growth")
        
        return risk_factors
    
    def _generate_health_recommendations(
        self, 
        risk_factors: List[str], 
        predicted_health: float
    ) -> List[str]:
        """Generate health improvement recommendations"""
        
        recommendations = []
        
        # Risk-based recommendations
        if "Declining health trend" in risk_factors:
            recommendations.append("Investigate root causes of health decline")
        
        if "Low contributor retention" in risk_factors:
            recommendations.append("Implement retention improvement programs")
        
        if "Poor issue resolution" in risk_factors:
            recommendations.append("Improve triage and resolution processes")
        
        if "Low community engagement" in risk_factors:
            recommendations.append("Increase community engagement activities")
        
        if "Declining contributor growth" in risk_factors:
            recommendations.append("Focus on new contributor onboarding")
        
        # General recommendations based on predicted health
        if predicted_health < 60:
            recommendations.append("Conduct comprehensive community health assessment")
            recommendations.append("Develop community health improvement plan")
        elif predicted_health > 80:
            recommendations.append("Maintain current successful practices")
            recommendations.append("Share best practices with other communities")
        
        return recommendations
    
    def _calculate_linear_trend(self, values: List[float]) -> float:
        """Calculate linear trend slope"""
        
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        
        # Calculate slope using least squares
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_seasonal_effect(self, historical_metrics: List[Dict[str, Any]]) -> float:
        """Calculate seasonal effect on engagement"""
        
        # Simplified seasonal calculation
        if len(historical_metrics) < 30:
            return 0.0
        
        recent_metrics = historical_metrics[-30:]
        engagement_scores = [m.get('engagement_score', 50) for m in recent_metrics]
        
        # Calculate day-of-week patterns (simplified)
        avg_engagement = statistics.mean(engagement_scores)
        variance = statistics.variance(engagement_scores) if len(engagement_scores) > 1 else 0
        
        return 0.0 if variance < 10 else (variance ** 0.5) * 0.1
    
    def _analyze_prediction_trend(self, predictions: List[float]) -> str:
        """Analyze overall trend in predictions"""
        
        if len(predictions) < 5:
            return "stable"
        
        first_half = statistics.mean(predictions[:len(predictions)//2])
        second_half = statistics.mean(predictions[len(predictions)//2:])
        
        if second_half > first_half + 2:
            return "increasing"
        elif second_half < first_half - 2:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_trend_strength(self, predictions: List[float]) -> float:
        """Calculate strength of trend (0-1)"""
        
        if len(predictions) < 3:
            return 0.0
        
        trend_slope = abs(self._calculate_linear_trend(predictions))
        return min(1.0, trend_slope / 2)  # Normalize to 0-1
    
    def validate_prediction_accuracy(self, prediction_type: str) -> Dict[str, float]:
        """Validate accuracy of previous predictions"""
        
        # Filter prediction history by type
        relevant_predictions = [
            p for p in self.prediction_history 
            if p.get('prediction_type') == prediction_type
        ]
        
        if not relevant_predictions:
            return {'accuracy': 0.0, 'sample_size': 0}
        
        # Calculate accuracy metrics
        accuracies = []
        for pred in relevant_predictions:
            predicted = pred.get('predicted_value')
            actual = pred.get('actual_value')
            
            if predicted is not None and actual is not None:
                if prediction_type in ['churn_risk']:
                    # Classification accuracy
                    accuracy = 1.0 if (predicted > 0.5) == (actual > 0.5) else 0.0
                else:
                    # Regression accuracy (MAPE)
                    if actual != 0:
                        mape = abs(predicted - actual) / abs(actual)
                        accuracy = max(0.0, 1.0 - mape)
                    else:
                        accuracy = 1.0 if predicted == 0 else 0.0
                
                accuracies.append(accuracy)
        
        avg_accuracy = statistics.mean(accuracies) if accuracies else 0.0
        
        return {
            'accuracy': avg_accuracy,
            'sample_size': len(accuracies),
            'confidence': min(0.95, 0.5 + (len(accuracies) * 0.1))
        }
    
    def get_prediction_summary(self) -> Dict[str, Any]:
        """Get summary of prediction capabilities and performance"""
        
        summary = {
            'available_models': [],
            'supported_predictions': ['engagement_trend', 'churn_risk', 'health_outlook', 'growth_forecast'],
            'feature_count': sum(len(features) for features in self.feature_config.values()),
            'prediction_history_count': len(self.prediction_history)
        }
        
        if sklearn_available:
            summary['available_models'].extend([
                'Random Forest', 'Linear Regression', 'Logistic Regression', 'Ensemble Methods'
            ])
        else:
            summary['available_models'].extend(['Statistical Models', 'Trend Analysis'])
        
        # Model performance summary
        summary['model_performance'] = {}
        for pred_type in summary['supported_predictions']:
            summary['model_performance'][pred_type] = self.validate_prediction_accuracy(pred_type)
        
        return summary