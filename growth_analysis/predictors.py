"""
Predictive Modeling for Repository Growth

This module implements machine learning models for predicting
future repository growth based on historical patterns and trends.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import defaultdict
import warnings

# Try to import scikit-learn, fall back to simple implementations if not available
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split, cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available, using simple linear models")


@dataclass
class PredictionResult:
    """Data class for prediction results."""
    date: datetime
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    confidence_level: float
    model_used: str
    feature_importance: Optional[Dict[str, float]] = None


@dataclass
class ModelPerformance:
    """Data class for model performance metrics."""
    model_name: str
    r2_score: float
    mae: float
    rmse: float
    mape: float
    training_time: float
    feature_importance: Optional[Dict[str, float]] = None


class GrowthPredictor:
    """
    Advanced growth prediction engine using multiple modeling approaches.
    """
    
    def __init__(self):
        self.models = {}
        self.model_performance = {}
        self.feature_scalers = {}
        self.trained_features = []
        
    def prepare_features(self, growth_data: List, lookback_days: int = 30) -> pd.DataFrame:
        """
        Prepare features for machine learning models.
        
        Args:
            growth_data: List of growth metrics
            lookback_days: Number of days to look back for features
            
        Returns:
            DataFrame with engineered features
        """
        df = pd.DataFrame([{
            'date': d.date,
            'stars': d.stars,
            'forks': d.forks,
            'watchers': d.watchers,
            'issues': d.issues,
            'pull_requests': d.pull_requests,
            'commits': d.commits
        } for d in growth_data])
        
        df = df.sort_values('date').reset_index(drop=True)
        
        # Create time-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Create lag features for each metric
        metrics = ['stars', 'forks', 'watchers', 'issues', 'pull_requests', 'commits']
        
        for metric in metrics:
            # Rolling averages
            for window in [3, 7, 14]:
                df[f'{metric}_ma_{window}'] = df[metric].rolling(window=window).mean()
                df[f'{metric}_ma_{window}_ratio'] = df[metric] / df[f'{metric}_ma_{window}']
            
            # Lag features
            for lag in range(1, min(8, len(df))):
                df[f'{metric}_lag_{lag}'] = df[metric].shift(lag)
            
            # Growth rates
            for period in [1, 3, 7]:
                df[f'{metric}_growth_{period}d'] = df[metric].pct_change(periods=period)
        
        # Interaction features
        df['star_fork_ratio'] = df['stars'] / (df['forks'] + 1)  # +1 to avoid division by zero
        df['issue_pr_ratio'] = df['issues'] / (df['pull_requests'] + 1)
        df['activity_score'] = df['commits'] + df['pull_requests']
        
        # Time since start
        start_date = df['date'].min()
        df['days_since_start'] = (df['date'] - start_date).dt.days
        
        # Remove rows with NaN values
        df = df.dropna()
        
        return df
    
    def train_models(self, growth_data: List, target_metric: str = 'stars') -> Dict[str, ModelPerformance]:
        """
        Train multiple prediction models.
        
        Args:
            growth_data: List of growth metrics
            target_metric: Metric to predict (stars, forks, etc.)
            
        Returns:
            Dictionary of trained models and their performance
        """
        if len(growth_data) < 20:
            raise ValueError("Insufficient data for training. Need at least 20 data points.")
        
        # Prepare features
        df = self.prepare_features(growth_data)
        
        if len(df) < 10:
            raise ValueError("Insufficient clean data after feature engineering.")
        
        # Prepare training data
        feature_columns = [col for col in df.columns if col not in ['date', target_metric]]
        X = df[feature_columns]
        y = df[target_metric]
        
        self.trained_features = feature_columns
        
        models_performance = {}
        
        # Simple Linear Model
        try:
            linear_model = self._train_linear_model(X, y)
            performance = self._evaluate_model(linear_model, X, y, 'linear', feature_columns)
            models_performance['linear'] = performance
            self.models['linear'] = linear_model
        except Exception as e:
            warnings.warn(f"Failed to train linear model: {str(e)}")
        
        # Polynomial Model
        if SKLEARN_AVAILABLE and len(df) > 50:
            try:
                poly_model = self._train_polynomial_model(X, y)
                performance = self._evaluate_model(poly_model, X, y, 'polynomial', feature_columns)
                models_performance['polynomial'] = performance
                self.models['polynomial'] = poly_model
            except Exception as e:
                warnings.warn(f"Failed to train polynomial model: {str(e)}")
        
        # Random Forest Model
        if SKLEARN_AVAILABLE and len(df) > 100:
            try:
                rf_model = self._train_random_forest_model(X, y)
                performance = self._evaluate_model(rf_model, X, y, 'random_forest', feature_columns)
                models_performance['random_forest'] = performance
                self.models['random_forest'] = rf_model
            except Exception as e:
                warnings.warn(f"Failed to train random forest model: {str(e)}")
        
        # Simple Trend Model (always available)
        try:
            trend_model = self._train_trend_model(df, target_metric)
            performance = self._evaluate_trend_model(trend_model, df, target_metric)
            models_performance['trend'] = performance
            self.models['trend'] = trend_model
        except Exception as e:
            warnings.warn(f"Failed to train trend model: {str(e)}")
        
        self.model_performance = models_performance
        return models_performance
    
    def _train_linear_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train a simple linear regression model."""
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(X, y)
            return {'model': model, 'type': 'sklearn_linear'}
        else:
            # Simple manual linear regression
            X_array = X.values
            y_array = y.values
            
            # Add bias term
            X_with_bias = np.column_stack([np.ones(X_array.shape[0]), X_array])
            
            # Calculate coefficients using normal equation
            try:
                coefficients = np.linalg.solve(
                    X_with_bias.T @ X_with_bias,
                    X_with_bias.T @ y_array
                )
                return {'coefficients': coefficients, 'type': 'manual_linear'}
            except np.linalg.LinAlgError:
                # Fallback to simple average growth
                return {'avg_growth': y_array[-1] - y_array[0], 'type': 'simple_trend'}
    
    def _train_polynomial_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train a polynomial regression model."""
        if not SKLEARN_AVAILABLE:
            return self._train_linear_model(X, y)
        
        poly_features = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly_features.fit_transform(X)
        
        model = LinearRegression()
        model.fit(X_poly, y)
        
        return {
            'model': model,
            'poly_features': poly_features,
            'type': 'polynomial'
        }
    
    def _train_random_forest_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train a Random Forest model."""
        if not SKLEARN_AVAILABLE:
            return self._train_linear_model(X, y)
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X, y)
        
        return {'model': model, 'type': 'random_forest'}
    
    def _train_trend_model(self, df: pd.DataFrame, target_metric: str) -> Dict[str, Any]:
        """Train a simple trend-based model."""
        metric_values = df[target_metric].values
        days_since_start = df['days_since_start'].values
        
        # Calculate trend
        if len(metric_values) > 1:
            # Simple linear trend
            slope = (metric_values[-1] - metric_values[0]) / (len(metric_values) - 1)
            intercept = metric_values[0]
            
            # Calculate volatility
            residuals = []
            for i in range(1, len(metric_values)):
                predicted = intercept + slope * days_since_start[i]
                residuals.append(metric_values[i] - predicted)
            
            volatility = np.std(residuals) if residuals else 0
            
            return {
                'slope': slope,
                'intercept': intercept,
                'volatility': volatility,
                'type': 'trend'
            }
        else:
            return {'constant': metric_values[0], 'type': 'constant'}
    
    def _evaluate_model(self, model_dict: Dict[str, Any], X: pd.DataFrame, y: pd.Series, 
                       model_name: str, features: List[str]) -> ModelPerformance:
        """Evaluate model performance."""
        start_time = datetime.now()
        
        try:
            if model_dict['type'] == 'sklearn_linear':
                y_pred = model_dict['model'].predict(X)
                feature_importance = dict(zip(features, model_dict['model'].coef_))
            elif model_dict['type'] == 'polynomial':
                X_poly = model_dict['poly_features'].transform(X)
                y_pred = model_dict['model'].predict(X_poly)
                feature_importance = dict(zip(
                    model_dict['poly_features'].get_feature_names_out(X.columns),
                    model_dict['model'].coef_
                ))
            elif model_dict['type'] == 'random_forest':
                y_pred = model_dict['model'].predict(X)
                feature_importance = dict(zip(features, model_dict['model'].feature_importances_))
            else:
                y_pred = np.full(len(y), y.mean())
                feature_importance = None
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate metrics
            mae = mean_absolute_error(y, y_pred) if SKLEARN_AVAILABLE else np.mean(np.abs(y - y_pred))
            mse = mean_squared_error(y, y_pred) if SKLEARN_AVAILABLE else np.mean((y - y_pred) ** 2)
            rmse = np.sqrt(mse)
            r2 = r2_score(y, y_pred) if SKLEARN_AVAILABLE else 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2))
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((y - y_pred) / y)) * 100 if not np.any(y == 0) else 0
            
            return ModelPerformance(
                model_name=model_name,
                r2_score=r2,
                mae=mae,
                rmse=rmse,
                mape=mape,
                training_time=training_time,
                feature_importance=feature_importance
            )
            
        except Exception as e:
            warnings.warn(f"Error evaluating {model_name}: {str(e)}")
            return ModelPerformance(
                model_name=model_name,
                r2_score=0,
                mae=float('inf'),
                rmse=float('inf'),
                mape=float('inf'),
                training_time=0
            )
    
    def _evaluate_trend_model(self, model_dict: Dict[str, Any], df: pd.DataFrame, 
                             target_metric: str) -> ModelPerformance:
        """Evaluate trend model performance."""
        start_time = datetime.now()
        
        metric_values = df[target_metric].values
        days_since_start = df['days_since_start'].values
        
        try:
            if model_dict['type'] == 'trend':
                y_pred = model_dict['intercept'] + model_dict['slope'] * days_since_start
            else:
                y_pred = np.full(len(metric_values), model_dict['constant'])
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            mae = np.mean(np.abs(metric_values - y_pred))
            mse = np.mean((metric_values - y_pred) ** 2)
            rmse = np.sqrt(mse)
            r2 = 1 - (np.sum((metric_values - y_pred) ** 2) / np.sum((metric_values - np.mean(metric_values)) ** 2))
            mape = np.mean(np.abs((metric_values - y_pred) / metric_values)) * 100 if not np.any(metric_values == 0) else 0
            
            return ModelPerformance(
                model_name='trend',
                r2_score=r2,
                mae=mae,
                rmse=rmse,
                mape=mape,
                training_time=training_time,
                feature_importance={'trend': model_dict.get('slope', 0)}
            )
            
        except Exception as e:
            warnings.warn(f"Error evaluating trend model: {str(e)}")
            return ModelPerformance(
                model_name='trend',
                r2_score=0,
                mae=float('inf'),
                rmse=float('inf'),
                mape=float('inf'),
                training_time=0
            )
    
    def predict(self, last_data: Any, days_ahead: int = 30, 
               confidence_level: float = 0.95) -> List[PredictionResult]:
        """
        Predict future growth for specified number of days.
        
        Args:
            last_data: Latest growth data point
            days_ahead: Number of days to predict ahead
            confidence_level: Confidence level for intervals (0.95 = 95%)
            
        Returns:
            List of prediction results
        """
        if not self.models:
            raise ValueError("No trained models available. Train models first.")
        
        predictions = []
        
        # Get the best performing model
        best_model_name = self._get_best_model()
        best_model = self.models[best_model_name]
        
        # Generate future dates
        last_date = last_data.date if hasattr(last_data, 'date') else datetime.now()
        
        for day in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=day)
            
            # Create features for future prediction
            future_features = self._create_future_features(last_data, day)
            
            # Make prediction
            predicted_value = self._predict_with_model(best_model, future_features)
            
            # Calculate confidence intervals
            lower, upper = self._calculate_confidence_intervals(
                predicted_value, best_model_name, confidence_level
            )
            
            prediction = PredictionResult(
                date=future_date,
                predicted_value=predicted_value,
                confidence_lower=lower,
                confidence_upper=upper,
                confidence_level=confidence_level,
                model_used=best_model_name
            )
            
            predictions.append(prediction)
        
        return predictions
    
    def _get_best_model(self) -> str:
        """Get the best performing model based on R2 score."""
        if not self.model_performance:
            return 'trend'  # Fallback
        
        best_model = max(
            self.model_performance.items(),
            key=lambda x: x[1].r2_score
        )
        
        return best_model[0]
    
    def _create_future_features(self, last_data: Any, days_ahead: int) -> pd.DataFrame:
        """Create features for future prediction."""
        # This is a simplified version - in practice, you'd need more sophisticated
        # feature engineering for future predictions
        features = {
            'stars': last_data.stars,
            'forks': last_data.forks,
            'watchers': last_data.watchers,
            'issues': last_data.issues,
            'pull_requests': last_data.pull_requests,
            'commits': last_data.commits,
            'day_of_week': (last_data.date + timedelta(days=days_ahead)).weekday(),
            'month': (last_data.date + timedelta(days=days_ahead)).month,
            'quarter': ((last_data.date + timedelta(days=days_ahead)).month - 1) // 3 + 1,
            'is_weekend': ((last_data.date + timedelta(days=days_ahead)).weekday() in [5, 6]).astype(int),
            'days_since_start': (last_data.date + timedelta(days=days_ahead) - last_data.date).days
        }
        
        # Add simple lag features (using current values)
        for lag in range(1, 8):
            features[f'stars_lag_{lag}'] = last_data.stars
            features[f'forks_lag_{lag}'] = last_data.forks
            features[f'watchers_lag_{lag}'] = last_data.watchers
        
        return pd.DataFrame([features])
    
    def _predict_with_model(self, model_dict: Dict[str, Any], features: pd.DataFrame) -> float:
        """Make a prediction using the specified model."""
        try:
            if model_dict['type'] == 'sklearn_linear':
                return float(model_dict['model'].predict(features)[0])
            elif model_dict['type'] == 'polynomial':
                X_poly = model_dict['poly_features'].transform(features)
                return float(model_dict['model'].predict(X_poly)[0])
            elif model_dict['type'] == 'random_forest':
                return float(model_dict['model'].predict(features)[0])
            elif model_dict['type'] == 'trend':
                return model_dict['intercept'] + model_dict['slope'] * features['days_since_start'].iloc[0]
            else:
                return features['stars'].iloc[0]  # Fallback to current value
        except Exception as e:
            warnings.warn(f"Prediction error: {str(e)}")
            return features['stars'].iloc[0]  # Fallback
    
    def _calculate_confidence_intervals(self, predicted_value: float, 
                                      model_name: str, confidence_level: float) -> Tuple[float, float]:
        """Calculate confidence intervals for predictions."""
        if model_name in self.model_performance:
            performance = self.model_performance[model_name]
            
            # Use RMSE as standard error estimate
            std_error = performance.rmse
            
            # Calculate z-score for confidence level
            alpha = 1 - confidence_level
            z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
            
            margin_error = z_score * std_error
            
            lower = max(0, predicted_value - margin_error)  # Don't allow negative values
            upper = predicted_value + margin_error
            
            return lower, upper
        
        # Default intervals
        margin = predicted_value * 0.1  # 10% default margin
        return max(0, predicted_value - margin), predicted_value + margin
    
    def get_prediction_summary(self) -> Dict[str, Any]:
        """
        Get a summary of prediction capabilities and model performance.
        
        Returns:
            Dictionary containing prediction summary
        """
        summary = {
            'available_models': list(self.models.keys()),
            'model_performance': {},
            'best_model': None,
            'total_training_data_points': len(self.trained_features),
            'features_used': self.trained_features
        }
        
        if self.model_performance:
            # Convert model performance to dict for JSON serialization
            for name, performance in self.model_performance.items():
                summary['model_performance'][name] = {
                    'r2_score': performance.r2_score,
                    'mae': performance.mae,
                    'rmse': performance.rmse,
                    'mape': performance.mape,
                    'training_time': performance.training_time
                }
            
            # Find best model
            best_performance = max(
                self.model_performance.values(),
                key=lambda x: x.r2_score
            )
            summary['best_model'] = best_performance.model_name
        
        return summary