"""
Trend Forecasting with Confidence Intervals

This module provides advanced trend forecasting capabilities including
statistical trend analysis, time series decomposition, and confidence interval estimation.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import defaultdict
import warnings

try:
    from scipy import stats
    from scipy.optimize import curve_fit
    import warnings
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy not available, using simple trend analysis")


@dataclass
class ForecastPoint:
    """Data class for a single forecast point."""
    date: datetime
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    trend_direction: str
    trend_strength: float
    confidence_level: float


@dataclass
class TrendAnalysis:
    """Data class for trend analysis results."""
    metric: str
    overall_trend: str
    trend_strength: float
    growth_rate: float
    seasonality_detected: bool
    trend_changes: List[Dict[str, Any]]
    forecast_points: List[ForecastPoint]
    model_quality: Dict[str, float]
    confidence_assessment: str


class TrendForecaster:
    """
    Advanced trend forecasting engine with multiple modeling approaches
    and comprehensive confidence interval estimation.
    """
    
    def __init__(self):
        self.trend_models = {}
        self.seasonal_patterns = {}
        self.forecast_cache = {}
        
    def analyze_and_forecast(self, growth_data: List, target_metric: str = 'stars',
                           forecast_days: int = 30, confidence_level: float = 0.95,
                           models: Optional[List[str]] = None) -> TrendAnalysis:
        """
        Perform comprehensive trend analysis and forecasting.
        
        Args:
            growth_data: List of growth metrics
            target_metric: Metric to analyze and forecast
            forecast_days: Number of days to forecast
            confidence_level: Confidence level for intervals
            models: List of models to use ('linear', 'exponential', 'polynomial', 'seasonal')
            
        Returns:
            Comprehensive trend analysis results
        """
        if len(growth_data) < 10:
            raise ValueError("Insufficient data for trend analysis. Need at least 10 data points.")
        
        models = models or ['linear', 'exponential', 'seasonal']
        
        # Prepare time series data
        ts_data = self._prepare_time_series(growth_data, target_metric)
        
        if len(ts_data) < 10:
            raise ValueError("Insufficient valid data points for analysis.")
        
        # Perform trend analysis
        trend_components = self._decompose_trend(ts_data)
        
        # Fit multiple models
        model_results = self._fit_forecasting_models(ts_data, models)
        
        # Select best model
        best_model_name, best_model_result = self._select_best_model(model_results)
        
        # Generate forecasts
        forecast_points = self._generate_forecasts(
            best_model_result, ts_data, forecast_days, confidence_level
        )
        
        # Analyze trend changes
        trend_changes = self._detect_trend_changes(ts_data, target_metric)
        
        # Assess seasonality
        seasonality_results = self._analyze_seasonality(ts_data)
        
        # Calculate overall trend strength and direction
        overall_trend, trend_strength, growth_rate = self._calculate_overall_trend(ts_data)
        
        # Model quality assessment
        model_quality = {
            'r_squared': best_model_result.get('r_squared', 0),
            'aic': best_model_result.get('aic', float('inf')),
            'rmse': best_model_result.get('rmse', float('inf')),
            'model_name': best_model_name
        }
        
        # Confidence assessment
        confidence_assessment = self._assess_forecast_confidence(
            model_quality, len(ts_data), trend_strength
        )
        
        return TrendAnalysis(
            metric=target_metric,
            overall_trend=overall_trend,
            trend_strength=trend_strength,
            growth_rate=growth_rate,
            seasonality_detected=seasonality_results['detected'],
            trend_changes=trend_changes,
            forecast_points=forecast_points,
            model_quality=model_quality,
            confidence_assessment=confidence_assessment
        )
    
    def _prepare_time_series(self, growth_data: List, target_metric: str) -> pd.DataFrame:
        """Prepare time series data for analysis."""
        # Extract relevant data
        df_data = []
        for data_point in growth_data:
            value = getattr(data_point, target_metric, None)
            if value is not None and value >= 0:  # Exclude negative values
                df_data.append({
                    'date': data_point.date,
                    'value': value
                })
        
        if not df_data:
            raise ValueError(f"No valid data found for metric {target_metric}")
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('date').reset_index(drop=True)
        
        # Convert dates to ordinal for numerical analysis
        df['date_ordinal'] = df['date'].dt.dayofyear
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        
        return df
    
    def _decompose_trend(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """Decompose time series into trend, seasonal, and residual components."""
        try:
            # Simple moving average trend
            window = min(7, len(ts_data) // 4)
            if window >= 2:
                ts_data['trend'] = ts_data['value'].rolling(window=window, center=True).mean()
                ts_data['detrended'] = ts_data['value'] - ts_data['trend']
            else:
                # For short series, use linear trend
                x = ts_data['days_since_start'].values
                y = ts_data['value'].values
                slope, intercept = np.polyfit(x, y, 1)
                ts_data['trend'] = intercept + slope * x
                ts_data['detrended'] = y - ts_data['trend']
            
            # Calculate residual
            ts_data['residual'] = ts_data['value'] - ts_data['trend']
            
            return {
                'trend_values': ts_data['trend'].values,
                'detrended_values': ts_data['detrended'].values,
                'residual_values': ts_data['residual'].values,
                'trend_slope': slope if 'slope' in locals() else 0
            }
            
        except Exception as e:
            warnings.warn(f"Trend decomposition failed: {str(e)}")
            return {
                'trend_values': np.zeros(len(ts_data)),
                'detrended_values': ts_data['value'].values,
                'residual_values': np.zeros(len(ts_data)),
                'trend_slope': 0
            }
    
    def _fit_forecasting_models(self, ts_data: pd.DataFrame, 
                              models: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fit multiple forecasting models to the data."""
        results = {}
        
        x = ts_data['days_since_start'].values
        y = ts_data['value'].values
        
        # Linear model
        if 'linear' in models:
            try:
                linear_result = self._fit_linear_model(x, y)
                results['linear'] = linear_result
            except Exception as e:
                warnings.warn(f"Linear model fitting failed: {str(e)}")
        
        # Exponential model
        if 'exponential' in models:
            try:
                exp_result = self._fit_exponential_model(x, y)
                results['exponential'] = exp_result
            except Exception as e:
                warnings.warn(f"Exponential model fitting failed: {str(e)}")
        
        # Polynomial model
        if 'polynomial' in models:
            try:
                poly_result = self._fit_polynomial_model(x, y)
                results['polynomial'] = poly_result
            except Exception as e:
                warnings.warn(f"Polynomial model fitting failed: {str(e)}")
        
        # Seasonal model
        if 'seasonal' in models:
            try:
                seasonal_result = self._fit_seasonal_model(ts_data)
                results['seasonal'] = seasonal_result
            except Exception as e:
                warnings.warn(f"Seasonal model fitting failed: {str(e)}")
        
        return results
    
    def _fit_linear_model(self, x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Fit linear regression model."""
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Calculate predictions and residuals
            y_pred = intercept + slope * x
            residuals = y - y_pred
            
            # Model quality metrics
            mse = np.mean(residuals ** 2)
            rmse = np.sqrt(mse)
            r_squared = r_value ** 2
            
            # AIC calculation (approximation)
            n = len(y)
            aic = n * np.log(mse) + 2 * 2  # 2 parameters
            
            return {
                'params': {'slope': slope, 'intercept': intercept},
                'predict_func': lambda x_val: intercept + slope * x_val,
                'r_squared': r_squared,
                'rmse': rmse,
                'aic': aic,
                'residuals': residuals,
                'p_value': p_value
            }
            
        except Exception as e:
            warnings.warn(f"Linear model fitting error: {str(e)}")
            return self._fit_constant_model(y)
    
    def _fit_exponential_model(self, x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Fit exponential growth model."""
        try:
            # Filter out zero and negative values
            valid_mask = y > 0
            if not np.any(valid_mask):
                return self._fit_linear_model(x, y)
            
            x_valid = x[valid_mask]
            y_valid = y[valid_mask]
            
            # Exponential function: y = a * exp(b * x)
            def exp_func(x, a, b):
                return a * np.exp(b * x)
            
            # Initial guess
            initial_guess = [y_valid[0], 0.01]
            
            # Fit the model
            popt, pcov = curve_fit(exp_func, x_valid, y_valid, p0=initial_guess, maxfev=5000)
            
            a, b = popt
            
            # Calculate predictions
            y_pred = exp_func(x, a, b)
            residuals = y - y_pred
            
            # Model quality metrics
            mse = np.mean(residuals ** 2)
            rmse = np.sqrt(mse)
            
            # R-squared calculation
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # AIC calculation
            n = len(y)
            aic = n * np.log(mse) + 2 * 2
            
            return {
                'params': {'a': a, 'b': b},
                'predict_func': lambda x_val: exp_func(x_val, a, b),
                'r_squared': r_squared,
                'rmse': rmse,
                'aic': aic,
                'residuals': residuals
            }
            
        except Exception as e:
            warnings.warn(f"Exponential model fitting error: {str(e)}")
            return self._fit_linear_model(x, y)
    
    def _fit_polynomial_model(self, x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Fit polynomial regression model."""
        try:
            # Try different polynomial degrees
            best_degree = 2
            best_r2 = -1
            best_result = None
            
            for degree in range(1, min(4, len(x) // 3)):  # Limit complexity
                try:
                    coefficients = np.polyfit(x, y, degree)
                    
                    # Calculate predictions
                    y_pred = np.polyval(coefficients, x)
                    residuals = y - y_pred
                    
                    # Calculate R-squared
                    ss_res = np.sum(residuals ** 2)
                    ss_tot = np.sum((y - np.mean(y)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    
                    # AIC calculation
                    mse = np.mean(residuals ** 2)
                    n = len(y)
                    aic = n * np.log(mse) + 2 * (degree + 1)
                    
                    if r_squared > best_r2:
                        best_r2 = r_squared
                        best_degree = degree
                        best_result = {
                            'params': {'degree': degree, 'coefficients': coefficients},
                            'predict_func': lambda x_val: np.polyval(coefficients, x_val),
                            'r_squared': r_squared,
                            'rmse': np.sqrt(mse),
                            'aic': aic,
                            'residuals': residuals
                        }
                        
                except Exception:
                    continue
            
            return best_result if best_result else self._fit_linear_model(x, y)
            
        except Exception as e:
            warnings.warn(f"Polynomial model fitting error: {str(e)}")
            return self._fit_linear_model(x, y)
    
    def _fit_seasonal_model(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """Fit seasonal decomposition model."""
        try:
            # Extract components
            x = ts_data['days_since_start'].values
            y = ts_data['value'].values
            
            # Detect weekly seasonality
            day_of_week = pd.to_datetime(ts_data['date']).dt.dayofweek.values
            weekly_means = {}
            for dow in range(7):
                dow_values = y[day_of_week == dow]
                if len(dow_values) > 0:
                    weekly_means[dow] = np.mean(dow_values)
            
            # Detect monthly seasonality
            month = pd.to_datetime(ts_data['date']).dt.month.values
            monthly_means = {}
            for m in range(1, 13):
                month_values = y[month == m]
                if len(month_values) > 0:
                    monthly_means[m] = np.mean(month_values)
            
            # Fit trend + seasonal model
            trend_coef = np.polyfit(x, y, 1)  # Linear trend
            
            # Calculate seasonal predictions
            y_pred = np.polyval(trend_coef, x)
            
            # Add seasonal adjustments
            for i, (dow, month_val) in enumerate(zip(day_of_week, month)):
                seasonal_adj = 0
                if dow in weekly_means:
                    overall_mean = np.mean(y)
                    seasonal_adj += weekly_means[dow] - overall_mean
                if month_val in monthly_means:
                    overall_mean = np.mean(y)
                    seasonal_adj += monthly_means[month_val] - overall_mean
                
                y_pred[i] += seasonal_adj
            
            residuals = y - y_pred
            
            # Model quality metrics
            mse = np.mean(residuals ** 2)
            rmse = np.sqrt(mse)
            
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # AIC calculation
            n = len(y)
            aic = n * np.log(mse) + 2 * (len(weekly_means) + len(monthly_means) + 2)
            
            return {
                'params': {
                    'trend_coef': trend_coef,
                    'weekly_pattern': weekly_means,
                    'monthly_pattern': monthly_means
                },
                'predict_func': lambda x_val, date_val: self._seasonal_predict(
                    x_val, date_val, trend_coef, weekly_means, monthly_means
                ),
                'r_squared': r_squared,
                'rmse': rmse,
                'aic': aic,
                'residuals': residuals
            }
            
        except Exception as e:
            warnings.warn(f"Seasonal model fitting error: {str(e)}")
            return self._fit_linear_model(x, y)
    
    def _seasonal_predict(self, x_val: float, date_val: datetime, trend_coef: np.ndarray,
                         weekly_pattern: Dict[int, float], monthly_pattern: Dict[int, float]) -> float:
        """Make prediction using seasonal model."""
        # Base trend prediction
        trend_pred = np.polyval(trend_coef, x_val)
        
        # Seasonal adjustments
        day_of_week = date_val.weekday()
        month = date_val.month
        
        seasonal_adj = 0
        if day_of_week in weekly_pattern:
            seasonal_adj += weekly_pattern[day_of_week] - np.mean(list(weekly_pattern.values()))
        if month in monthly_pattern:
            seasonal_adj += monthly_pattern[month] - np.mean(list(monthly_pattern.values()))
        
        return trend_pred + seasonal_adj
    
    def _fit_constant_model(self, y: np.ndarray) -> Dict[str, Any]:
        """Fit simple constant model as fallback."""
        constant = np.mean(y)
        residuals = y - constant
        
        mse = np.mean(residuals ** 2)
        rmse = np.sqrt(mse)
        
        return {
            'params': {'constant': constant},
            'predict_func': lambda x: np.full_like(x, constant),
            'r_squared': 0,
            'rmse': rmse,
            'aic': len(y) * np.log(mse) + 2,
            'residuals': residuals
        }
    
    def _select_best_model(self, model_results: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """Select the best model based on information criteria and fit quality."""
        if not model_results:
            raise ValueError("No models were successfully fitted")
        
        # Calculate composite score: lower AIC is better, higher R² is better
        best_score = float('inf')
        best_model_name = None
        best_result = None
        
        for model_name, result in model_results.items():
            # Normalize metrics for comparison
            r_squared = result.get('r_squared', 0)
            aic = result.get('aic', float('inf'))
            rmse = result.get('rmse', float('inf'))
            
            # Composite score (lower is better)
            score = aic + (1 - r_squared) * 100 + rmse
            
            if score < best_score:
                best_score = score
                best_model_name = model_name
                best_result = result
        
        return best_model_name, best_result
    
    def _generate_forecasts(self, model_result: Dict[str, Any], ts_data: pd.DataFrame,
                          forecast_days: int, confidence_level: float) -> List[ForecastPoint]:
        """Generate forecast points with confidence intervals."""
        last_date = ts_data['date'].max()
        last_x = ts_data['days_since_start'].max()
        
        # Calculate residual standard deviation for confidence intervals
        residuals = model_result.get('residuals', np.array([]))
        if len(residuals) > 1:
            residual_std = np.std(residuals)
        else:
            residual_std = np.std(ts_data['value']) * 0.1  # Fallback
        
        # Z-score for confidence interval
        alpha = 1 - confidence_level
        z_score = stats.norm.ppf(1 - alpha / 2) if SCIPY_AVAILABLE else 1.96
        
        forecast_points = []
        
        for day in range(1, forecast_days + 1):
            forecast_date = last_date + timedelta(days=day)
            forecast_x = last_x + day
            
            # Make point prediction
            if model_result['params'] and 'constant' in model_result['params']:
                # Constant model
                predicted_value = model_result['params']['constant']
            else:
                # Other models
                predicted_value = model_result['predict_func'](forecast_x, forecast_date)
            
            # Calculate confidence intervals
            # Wider intervals for longer forecasts (uncertainty grows)
            time_factor = np.sqrt(day / forecast_days)
            adjusted_std = residual_std * time_factor
            margin_of_error = z_score * adjusted_std
            
            confidence_lower = max(0, predicted_value - margin_of_error)
            confidence_upper = predicted_value + margin_of_error
            
            # Determine trend direction and strength
            trend_direction, trend_strength = self._analyze_trend_at_point(
                forecast_x, ts_data, model_result
            )
            
            forecast_point = ForecastPoint(
                date=forecast_date,
                predicted_value=predicted_value,
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                confidence_level=confidence_level
            )
            
            forecast_points.append(forecast_point)
        
        return forecast_points
    
    def _analyze_trend_at_point(self, forecast_x: float, ts_data: pd.DataFrame,
                              model_result: Dict[str, Any]) -> Tuple[str, float]:
        """Analyze trend direction and strength at a specific point."""
        # Get recent trend slope
        recent_data = ts_data.tail(min(7, len(ts_data)))
        if len(recent_data) >= 2:
            x_recent = recent_data['days_since_start'].values
            y_recent = recent_data['value'].values
            
            try:
                slope, _, _, _, _ = stats.linregress(x_recent, y_recent) if SCIPY_AVAILABLE else np.polyfit(x_recent, y_recent, 1)
                trend_slope = slope
            except:
                trend_slope = 0
        else:
            trend_slope = 0
        
        # Determine direction
        if trend_slope > 0.01:
            direction = "increasing"
        elif trend_slope < -0.01:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Calculate strength (normalized slope)
        recent_mean = ts_data['value'].tail(min(10, len(ts_data))).mean()
        if recent_mean > 0:
            strength = min(abs(trend_slope) / recent_mean, 1.0)
        else:
            strength = 0.0
        
        return direction, strength
    
    def _detect_trend_changes(self, ts_data: pd.DataFrame, metric: str) -> List[Dict[str, Any]]:
        """Detect significant trend changes in the time series."""
        trend_changes = []
        
        if len(ts_data) < 10:
            return trend_changes
        
        # Calculate rolling trend slopes
        window_size = min(7, len(ts_data) // 3)
        slopes = []
        
        for i in range(window_size, len(ts_data) - window_size):
            window_data = ts_data.iloc[i - window_size:i + window_size + 1]
            x = window_data['days_since_start'].values
            y = window_data['value'].values
            
            try:
                if SCIPY_AVAILABLE:
                    slope, _, _, _, _ = stats.linregress(x, y)
                else:
                    slope = np.polyfit(x, y, 1)[0]
                slopes.append({
                    'index': i,
                    'date': ts_data.iloc[i]['date'],
                    'slope': slope
                })
            except:
                continue
        
        # Detect significant slope changes
        for i in range(1, len(slopes)):
            prev_slope = slopes[i-1]['slope']
            curr_slope = slopes[i]['slope']
            
            # Check for significant change
            slope_change = abs(curr_slope - prev_slope)
            avg_slope = (abs(prev_slope) + abs(curr_slope)) / 2
            
            if avg_slope > 0 and slope_change / avg_slope > 0.5:  # 50% change threshold
                change_type = "acceleration" if (prev_slope < curr_slope) else "deceleration"
                
                trend_changes.append({
                    'date': slopes[i]['date'].isoformat(),
                    'change_type': change_type,
                    'previous_slope': prev_slope,
                    'current_slope': curr_slope,
                    'magnitude': slope_change,
                    'description': f"Trend {change_type}: slope changed from {prev_slope:.4f} to {curr_slope:.4f}"
                })
        
        return trend_changes
    
    def _analyze_seasonality(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze seasonal patterns in the time series."""
        results = {
            'detected': False,
            'weekly_pattern': None,
            'monthly_pattern': None,
            'seasonal_strength': 0,
            'description': ''
        }
        
        if len(ts_data) < 14:  # Need at least 2 weeks for weekly pattern
            results['description'] = "Insufficient data for seasonality analysis"
            return results
        
        try:
            # Weekly pattern analysis
            ts_data['day_of_week'] = pd.to_datetime(ts_data['date']).dt.dayofweek
            weekly_stats = ts_data.groupby('day_of_week')['value'].agg(['mean', 'std'])
            
            # Calculate coefficient of variation for weekly pattern
            weekly_mean = weekly_stats['mean'].mean()
            weekly_variance = weekly_stats['mean'].var()
            
            if weekly_mean > 0:
                weekly_cv = np.sqrt(weekly_variance) / weekly_mean
                results['weekly_pattern'] = weekly_stats.to_dict()
                
                if weekly_cv > 0.1:  # 10% coefficient of variation
                    results['detected'] = True
            
            # Monthly pattern analysis
            if len(ts_data) > 30:  # Need at least a month for monthly pattern
                ts_data['month'] = pd.to_datetime(ts_data['date']).dt.month
                monthly_stats = ts_data.groupby('month')['value'].agg(['mean', 'std'])
                
                monthly_mean = monthly_stats['mean'].mean()
                monthly_variance = monthly_stats['mean'].var()
                
                if monthly_mean > 0:
                    monthly_cv = np.sqrt(monthly_variance) / monthly_mean
                    results['monthly_pattern'] = monthly_stats.to_dict()
                    
                    if monthly_cv > 0.15:  # 15% coefficient of variation
                        results['detected'] = True
            
            # Calculate overall seasonal strength
            seasonal_strength = max(weekly_cv if 'weekly_cv' in locals() else 0,
                                  monthly_cv if 'monthly_cv' in locals() else 0)
            results['seasonal_strength'] = seasonal_strength
            
            if results['detected']:
                patterns = []
                if 'weekly_cv' in locals() and weekly_cv > 0.1:
                    patterns.append("weekly")
                if 'monthly_cv' in locals() and monthly_cv > 0.15:
                    patterns.append("monthly")
                results['description'] = f"Seasonal patterns detected: {', '.join(patterns)}"
            else:
                results['description'] = "No significant seasonal patterns detected"
                
        except Exception as e:
            results['description'] = f"Seasonality analysis failed: {str(e)}"
        
        return results
    
    def _calculate_overall_trend(self, ts_data: pd.DataFrame) -> Tuple[str, float, float]:
        """Calculate overall trend direction, strength, and growth rate."""
        x = ts_data['days_since_start'].values
        y = ts_data['value'].values
        
        try:
            if SCIPY_AVAILABLE:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            else:
                slope, intercept = np.polyfit(x, y, 1)
                r_value = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
                p_value = 0.05  # Simplified
                std_err = 0
        except:
            slope, intercept, r_value, p_value, std_err = 0, 0, 0, 1, 0
        
        # Determine trend direction
        if slope > 0.001:
            direction = "increasing"
        elif slope < -0.001:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Calculate trend strength (R-squared)
        trend_strength = r_value ** 2 if not np.isnan(r_value) else 0
        
        # Calculate growth rate
        if len(y) >= 2:
            start_value = y[0]
            end_value = y[-1]
            if start_value > 0:
                total_growth_rate = (end_value - start_value) / start_value
                # Annualized growth rate
                time_span_days = x[-1] - x[0]
                if time_span_days > 0:
                    growth_rate = (1 + total_growth_rate) ** (365.25 / time_span_days) - 1
                else:
                    growth_rate = 0
            else:
                growth_rate = 0
        else:
            growth_rate = 0
        
        return direction, trend_strength, growth_rate
    
    def _assess_forecast_confidence(self, model_quality: Dict[str, float], 
                                  data_points: int, trend_strength: float) -> str:
        """Assess the overall confidence level of the forecast."""
        r_squared = model_quality.get('r_squared', 0)
        aic = model_quality.get('aic', float('inf'))
        
        # Data sufficiency factor
        data_factor = min(data_points / 50, 1.0)  # Optimal at 50+ points
        
        # Model fit factor
        fit_factor = r_squared
        
        # Trend strength factor
        trend_factor = trend_strength
        
        # Overall confidence score
        confidence_score = (data_factor + fit_factor + trend_factor) / 3
        
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "medium"
        elif confidence_score >= 0.4:
            return "low"
        else:
            return "very_low"
    
    def get_forecast_summary(self, trend_analysis: TrendAnalysis) -> Dict[str, Any]:
        """
        Get a comprehensive summary of forecast results.
        
        Args:
            trend_analysis: Complete trend analysis results
            
        Returns:
            Dictionary containing forecast summary
        """
        summary = {
            'metric': trend_analysis.metric,
            'overall_assessment': {
                'trend_direction': trend_analysis.overall_trend,
                'trend_strength': trend_analysis.trend_strength,
                'growth_rate': trend_analysis.growth_rate,
                'seasonality_detected': trend_analysis.seasonality_detected
            },
            'forecast_range': {
                'start_date': trend_analysis.forecast_points[0].date.isoformat(),
                'end_date': trend_analysis.forecast_points[-1].date.isoformat(),
                'forecast_days': len(trend_analysis.forecast_points)
            },
            'confidence_metrics': {
                'assessment': trend_analysis.confidence_assessment,
                'model_quality': trend_analysis.model_quality
            },
            'trend_changes_detected': len(trend_analysis.trend_changes),
            'key_insights': []
        }
        
        # Generate key insights
        if trend_analysis.overall_trend == "increasing" and trend_analysis.trend_strength > 0.7:
            summary['key_insights'].append("Strong upward trend with high confidence")
        elif trend_analysis.overall_trend == "decreasing" and trend_analysis.trend_strength > 0.7:
            summary['key_insights'].append("Strong downward trend requires attention")
        elif trend_analysis.trend_strength < 0.3:
            summary['key_insights'].append("Weak trend - high uncertainty in predictions")
        
        if trend_analysis.seasonality_detected:
            summary['key_insights'].append("Significant seasonal patterns detected - consider in planning")
        
        if trend_analysis.confidence_assessment == "high":
            summary['key_insights'].append("Forecast has high confidence based on historical data quality")
        elif trend_analysis.confidence_assessment in ["low", "very_low"]:
            summary['key_insights'].append("Forecast confidence is low - consider gathering more data")
        
        # Add trend change insights
        for change in trend_analysis.trend_changes:
            summary['key_insights'].append(f"Trend {change['change_type']} detected on {change['date']}")
        
        return summary