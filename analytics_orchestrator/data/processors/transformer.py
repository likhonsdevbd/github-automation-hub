"""
Data transformation processor for analytics pipeline
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
import re
import json
import math
from dataclasses import dataclass
from enum import Enum


class TransformationType(Enum):
    """Transformation type enumeration"""
    NORMALIZE = "normalize"
    SCALE = "scale"
    FILTER = "filter"
    ENRICH = "enrich"
    DERIVE = "derive"
    AGGREGATE = "aggregate"
    CLEAN = "clean"
    CONVERT = "convert"


@dataclass
class TransformationRule:
    """Transformation rule structure"""
    type: TransformationType
    field: str
    operation: str
    parameters: Dict[str, Any] = None
    condition: Optional[str] = None


class DataTransformer:
    """
    Data transformation processor that applies various transformations to data points
    """
    
    def __init__(self):
        """Initialize data transformer"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Data transformer initialized")
        
        # Built-in transformation functions
        self.transform_functions = {
            'normalize': self._normalize_values,
            'scale': self._scale_values,
            'filter': self._filter_values,
            'enrich': self._enrich_data,
            'derive': self._derive_fields,
            'aggregate': self._aggregate_values,
            'clean': self._clean_data,
            'convert': self._convert_types
        }
    
    async def transform(self, data_points: List) -> List:
        """
        Apply default transformations to data points
        
        Args:
            data_points: List of data point objects
            
        Returns:
            List of transformed data points
        """
        try:
            if not data_points:
                return []
            
            transformed_points = []
            
            for point in data_points:
                try:
                    transformed_point = await self._transform_single_point(point)
                    transformed_points.append(transformed_point)
                except Exception as e:
                    self.logger.error(f"Failed to transform data point: {str(e)}")
                    # Keep original point if transformation fails
                    transformed_points.append(point)
                    continue
            
            self.logger.debug(f"Transformed {len(data_points)} data points")
            return transformed_points
            
        except Exception as e:
            self.logger.error(f"Data transformation failed: {str(e)}")
            return data_points  # Return original if transformation fails
    
    async def _transform_single_point(self, point) -> object:
        """Transform a single data point"""
        try:
            # Create a copy of the point to avoid modifying original
            if hasattr(point, '__dict__'):
                # For objects, create a copy
                import copy
                transformed_point = copy.deepcopy(point)
                
                # Apply basic transformations
                transformed_point = await self._clean_point(transformed_point)
                transformed_point = await self._normalize_point(transformed_point)
                transformed_point = await self._enrich_point(transformed_point)
                
                return transformed_point
            else:
                # For dictionaries or other types, return as is for basic case
                return point
                
        except Exception as e:
            self.logger.error(f"Failed to transform single point: {str(e)}")
            return point
    
    async def _clean_point(self, point) -> object:
        """Clean a data point"""
        try:
            # Clean invalid values
            if hasattr(point, 'value'):
                # Remove NaN and infinite values
                if isinstance(point.value, (int, float)):
                    if math.isnan(point.value) or math.isinf(point.value):
                        point.value = 0
            
            # Clean tags
            if hasattr(point, 'tags') and point.tags:
                # Remove empty tags
                cleaned_tags = {
                    k: v for k, v in point.tags.items()
                    if v is not None and str(v).strip() != ''
                }
                point.tags = cleaned_tags
            
            # Clean metadata
            if hasattr(point, 'metadata') and point.metadata:
                # Remove empty metadata
                cleaned_metadata = {
                    k: v for k, v in point.metadata.items()
                    if v is not None and str(v).strip() != ''
                }
                point.metadata = cleaned_metadata
            
            return point
            
        except Exception as e:
            self.logger.debug(f"Failed to clean point: {str(e)}")
            return point
    
    async def _normalize_point(self, point) -> object:
        """Normalize a data point"""
        try:
            # Normalize metric names (remove special characters, lowercase)
            if hasattr(point, 'metric_name'):
                point.metric_name = self._normalize_metric_name(point.metric_name)
            
            # Normalize source names
            if hasattr(point, 'source'):
                point.source = point.source.lower().strip()
            
            # Normalize tags
            if hasattr(point, 'tags') and point.tags:
                normalized_tags = {}
                for key, value in point.tags.items():
                    norm_key = key.lower().strip().replace(' ', '_')
                    norm_value = str(value).lower().strip()
                    normalized_tags[norm_key] = norm_value
                point.tags = normalized_tags
            
            return point
            
        except Exception as e:
            self.logger.debug(f"Failed to normalize point: {str(e)}")
            return point
    
    async def _enrich_point(self, point) -> object:
        """Enrich a data point with additional data"""
        try:
            # Add timestamp metadata
            if hasattr(point, 'timestamp'):
                if not hasattr(point, 'metadata') or point.metadata is None:
                    point.metadata = {}
                
                point.metadata['timestamp_iso'] = point.timestamp.isoformat()
                point.metadata['timestamp_unix'] = int(point.timestamp.timestamp())
                point.metadata['hour_of_day'] = point.timestamp.hour
                point.metadata['day_of_week'] = point.timestamp.weekday()
                point.metadata['is_weekend'] = point.timestamp.weekday() >= 5
            
            # Add value metadata
            if hasattr(point, 'value') and isinstance(point.value, (int, float)):
                if not hasattr(point, 'metadata') or point.metadata is None:
                    point.metadata = {}
                
                # Categorize values
                abs_value = abs(point.value)
                if abs_value < 1:
                    category = 'very_low'
                elif abs_value < 10:
                    category = 'low'
                elif abs_value < 100:
                    category = 'medium'
                elif abs_value < 1000:
                    category = 'high'
                else:
                    category = 'very_high'
                
                point.metadata['value_category'] = category
                point.metadata['value_abs'] = abs_value
                point.metadata['value_sign'] = 'positive' if point.value >= 0 else 'negative'
            
            # Add source metadata
            if hasattr(point, 'source'):
                if not hasattr(point, 'metadata') or point.metadata is None:
                    point.metadata = {}
                
                # Parse source type
                source_parts = point.source.split('_')
                point.metadata['source_type'] = source_parts[0] if source_parts else 'unknown'
                point.metadata['source_component'] = '_'.join(source_parts[1:]) if len(source_parts) > 1 else 'main'
            
            return point
            
        except Exception as e:
            self.logger.debug(f"Failed to enrich point: {str(e)}")
            return point
    
    def _normalize_metric_name(self, metric_name: str) -> str:
        """Normalize metric name"""
        try:
            # Convert to lowercase
            normalized = metric_name.lower().strip()
            
            # Replace spaces and special characters with underscores
            normalized = re.sub(r'[^\w]', '_', normalized)
            
            # Remove multiple consecutive underscores
            normalized = re.sub(r'_+', '_', normalized)
            
            # Remove leading/trailing underscores
            normalized = normalized.strip('_')
            
            return normalized
            
        except Exception as e:
            self.logger.debug(f"Failed to normalize metric name {metric_name}: {str(e)}")
            return metric_name
    
    async def apply_custom_transformations(self, data_points: List, rules: List[TransformationRule]) -> List:
        """Apply custom transformation rules to data points"""
        try:
            if not data_points or not rules:
                return data_points
            
            transformed_points = []
            
            for point in data_points:
                try:
                    transformed_point = point
                    
                    for rule in rules:
                        # Check condition
                        if rule.condition and not await self._evaluate_condition(transformed_point, rule.condition):
                            continue
                        
                        # Apply transformation
                        transform_func = self.transform_functions.get(rule.type.value)
                        if transform_func:
                            transformed_point = await transform_func(transformed_point, rule)
                    
                    transformed_points.append(transformed_point)
                    
                except Exception as e:
                    self.logger.error(f"Failed to apply custom transformation: {str(e)}")
                    transformed_points.append(point)  # Keep original if transformation fails
            
            self.logger.debug(f"Applied {len(rules)} custom transformations to {len(data_points)} points")
            return transformed_points
            
        except Exception as e:
            self.logger.error(f"Custom transformation failed: {str(e)}")
            return data_points
    
    async def _evaluate_condition(self, point, condition: str) -> bool:
        """Evaluate a condition on a data point"""
        try:
            # Simple condition evaluation - can be extended for more complex logic
            # This is a basic implementation
            
            if 'value' in condition:
                if hasattr(point, 'value'):
                    try:
                        # Simple comparisons
                        if '> 0' in condition:
                            return point.value > 0
                        elif '>= 0' in condition:
                            return point.value >= 0
                        elif '< 0' in condition:
                            return point.value < 0
                        elif '<= 0' in condition:
                            return point.value <= 0
                    except (TypeError, ValueError):
                        return False
            
            # Default to True if no conditions match
            return True
            
        except Exception as e:
            self.logger.debug(f"Failed to evaluate condition: {str(e)}")
            return True
    
    # Built-in transformation functions
    async def _normalize_values(self, point, rule: TransformationRule) -> object:
        """Normalize numeric values"""
        if hasattr(point, 'value') and isinstance(point.value, (int, float)):
            try:
                # Apply normalization based on parameters
                if rule.parameters:
                    method = rule.parameters.get('method', 'min_max')
                    
                    if method == 'min_max' and 'min' in rule.parameters and 'max' in rule.parameters:
                        min_val = rule.parameters['min']
                        max_val = rule.parameters['max']
                        if max_val > min_val:
                            point.value = (point.value - min_val) / (max_val - min_val)
                    
                    elif method == 'z_score' and 'mean' in rule.parameters and 'std' in rule.parameters:
                        mean = rule.parameters['mean']
                        std = rule.parameters['std']
                        if std > 0:
                            point.value = (point.value - mean) / std
                
                return point
            except Exception as e:
                self.logger.debug(f"Normalize values failed: {str(e)}")
        
        return point
    
    async def _scale_values(self, point, rule: TransformationRule) -> object:
        """Scale numeric values"""
        if hasattr(point, 'value') and isinstance(point.value, (int, float)):
            try:
                if rule.parameters:
                    factor = rule.parameters.get('factor', 1.0)
                    offset = rule.parameters.get('offset', 0.0)
                    point.value = point.value * factor + offset
                
                return point
            except Exception as e:
                self.logger.debug(f"Scale values failed: {str(e)}")
        
        return point
    
    async def _filter_values(self, point, rule: TransformationRule) -> object:
        """Filter data points based on criteria"""
        # This function returns the point if it passes the filter
        # The actual filtering is handled by the caller based on the return value
        try:
            if rule.parameters:
                # Value range filter
                if 'min_value' in rule.parameters and hasattr(point, 'value'):
                    if point.value < rule.parameters['min_value']:
                        return None  # Filter out
                
                if 'max_value' in rule.parameters and hasattr(point, 'value'):
                    if point.value > rule.parameters['max_value']:
                        return None  # Filter out
                
                # Source filter
                if 'source_pattern' in rule.parameters and hasattr(point, 'source'):
                    pattern = rule.parameters['source_pattern']
                    if not re.match(pattern, point.source):
                        return None  # Filter out
                
                # Tag filter
                if 'tag_requirements' in rule.parameters and hasattr(point, 'tags'):
                    requirements = rule.parameters['tag_requirements']
                    for key, value in requirements.items():
                        if point.tags.get(key) != value:
                            return None  # Filter out
            
            return point
        except Exception as e:
            self.logger.debug(f"Filter values failed: {str(e)}")
            return point
    
    async def _enrich_data(self, point, rule: TransformationRule) -> object:
        """Enrich data with additional information"""
        try:
            if not hasattr(point, 'metadata') or point.metadata is None:
                point.metadata = {}
            
            if rule.parameters:
                # Add static metadata
                for key, value in rule.parameters.items():
                    if key.startswith('add_'):
                        metadata_key = key[4:]  # Remove 'add_' prefix
                        point.metadata[metadata_key] = value
                
                # Add calculated metadata
                if 'calculate' in rule.parameters:
                    calc_config = rule.parameters['calculate']
                    if 'field' in calc_config and hasattr(point, calc_config['field']):
                        field_value = getattr(point, calc_config['field'])
                        if calc_config.get('operation') == 'log' and isinstance(field_value, (int, float)) and field_value > 0:
                            point.metadata[f"log_{calc_config['field']}"] = math.log(field_value)
            
            return point
        except Exception as e:
            self.logger.debug(f"Enrich data failed: {str(e)}")
            return point
    
    async def _derive_fields(self, point, rule: TransformationRule) -> object:
        """Derive new fields from existing data"""
        try:
            if rule.parameters:
                source_field = rule.parameters.get('source_field')
                target_field = rule.parameters.get('target_field', f"derived_{rule.parameters.get('operation', 'value')}")
                operation = rule.parameters.get('operation', 'identity')
                
                if source_field and hasattr(point, source_field):
                    source_value = getattr(point, source_field)
                    
                    derived_value = source_value
                    if operation == 'abs' and isinstance(source_value, (int, float)):
                        derived_value = abs(source_value)
                    elif operation == 'sqrt' and isinstance(source_value, (int, float)) and source_value >= 0:
                        derived_value = math.sqrt(source_value)
                    elif operation == 'log' and isinstance(source_value, (int, float)) and source_value > 0:
                        derived_value = math.log(source_value)
                    elif operation == 'round' and isinstance(source_value, (int, float)):
                        decimals = rule.parameters.get('decimals', 0)
                        derived_value = round(source_value, decimals)
                    
                    # Add derived field to metadata
                    if not hasattr(point, 'metadata') or point.metadata is None:
                        point.metadata = {}
                    point.metadata[target_field] = derived_value
            
            return point
        except Exception as e:
            self.logger.debug(f"Derive fields failed: {str(e)}")
            return point
    
    async def _aggregate_values(self, point, rule: TransformationRule) -> object:
        """Aggregate values (placeholder for future implementation)"""
        # This would typically be handled by the aggregator processor
        # This is a placeholder for consistency
        return point
    
    async def _clean_data(self, point, rule: TransformationRule) -> object:
        """Clean and validate data"""
        try:
            if rule.parameters:
                # Remove outliers
                if rule.parameters.get('remove_outliers', False) and hasattr(point, 'value'):
                    threshold = rule.parameters.get('outlier_threshold', 3.0)
                    # Simple outlier detection based on value magnitude
                    if isinstance(point.value, (int, float)) and abs(point.value) > threshold * 1000:
                        point.value = rule.parameters.get('outlier_replacement', 0)
                
                # Validate ranges
                if 'value_range' in rule.parameters and hasattr(point, 'value'):
                    min_val, max_val = rule.parameters['value_range']
                    if not (min_val <= point.value <= max_val):
                        point.value = max(min_val, min(point.value, max_val))
            
            # Apply basic cleaning
            point = await self._clean_point(point)
            
            return point
        except Exception as e:
            self.logger.debug(f"Clean data failed: {str(e)}")
            return point
    
    async def _convert_types(self, point, rule: TransformationRule) -> object:
        """Convert data types"""
        try:
            if rule.parameters:
                # Convert value type
                if 'value_type' in rule.parameters and hasattr(point, 'value'):
                    target_type = rule.parameters['value_type']
                    if target_type == 'int':
                        point.value = int(point.value)
                    elif target_type == 'float':
                        point.value = float(point.value)
                    elif target_type == 'str':
                        point.value = str(point.value)
                    elif target_type == 'bool':
                        point.value = bool(point.value)
                
                # Convert timestamp
                if 'timestamp_format' in rule.parameters and hasattr(point, 'timestamp'):
                    timestamp_format = rule.parameters['timestamp_format']
                    if timestamp_format == 'unix':
                        point.timestamp = datetime.fromtimestamp(point.value)
                    elif timestamp_format == 'iso':
                        point.timestamp = datetime.fromisoformat(str(point.value))
            
            return point
        except Exception as e:
            self.logger.debug(f"Convert types failed: {str(e)}")
            return point
    
    async def batch_transform(self, data_points: List, 
                            transformations: Dict[str, Callable]) -> List:
        """Apply batch transformations using custom functions"""
        try:
            transformed_points = []
            
            for point in data_points:
                transformed_point = point
                
                for transform_name, transform_func in transformations.items():
                    try:
                        transformed_point = await transform_func(transformed_point)
                    except Exception as e:
                        self.logger.error(f"Batch transform {transform_name} failed: {str(e)}")
                        continue  # Continue with next transform
                
                transformed_points.append(transformed_point)
            
            self.logger.debug(f"Applied {len(transformations)} batch transformations to {len(data_points)} points")
            return transformed_points
            
        except Exception as e:
            self.logger.error(f"Batch transformation failed: {str(e)}")
            return data_points
    
    async def get_transformation_statistics(self, original_points: List, transformed_points: List) -> Dict[str, Any]:
        """Get statistics about transformations applied"""
        try:
            stats = {
                'original_count': len(original_points),
                'transformed_count': len(transformed_points),
                'filtered_out': len(original_points) - len(transformed_points),
                'transformation_success_rate': len(transformed_points) / len(original_points) if original_points else 0,
                'applied_transformations': [],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Basic transformation analysis
            if original_points and transformed_points:
                # Check for data quality improvements
                original_valid = sum(1 for p in original_points if hasattr(p, 'value') and p.value is not None)
                transformed_valid = sum(1 for p in transformed_points if hasattr(p, 'value') and p.value is not None)
                
                stats['data_quality'] = {
                    'original_valid_count': original_valid,
                    'transformed_valid_count': transformed_valid,
                    'quality_improvement': transformed_valid - original_valid
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get transformation statistics: {str(e)}")
            return {}


if __name__ == "__main__":
    # Example usage
    import asyncio
    from datetime import datetime, timedelta
    
    async def main():
        # Create sample data points
        from core.data_pipeline import create_data_point
        
        data_points = []
        for i in range(10):
            data_points.append(create_data_point(
                f'Metric {i}',
                50 + i * 10,
                f'service_{i % 2}',
                tags={'env': 'prod', 'version': f'v{i % 3}'},
                timestamp=datetime.utcnow()
            ))
        
        # Initialize transformer
        transformer = DataTransformer()
        
        # Test basic transformation
        print("Testing basic transformation...")
        transformed = await transformer.transform(data_points)
        print(f"Transformed {len(transformed)} data points")
        
        # Test custom transformation rules
        print("\nTesting custom transformation rules...")
        rules = [
            TransformationRule(
                type=TransformationType.FILTER,
                field='value',
                operation='range',
                parameters={'min_value': 50, 'max_value': 100}
            ),
            TransformationRule(
                type=TransformationType.ENRICH,
                field='metadata',
                operation='add',
                parameters={'add_environment': 'production', 'add_processed_by': 'transformer'}
            )
        ]
        
        custom_transformed = await transformer.apply_custom_transformations(data_points, rules)
        print(f"Custom transformed {len(custom_transformed)} data points")
        
        # Get transformation statistics
        print("\nGetting transformation statistics...")
        stats = await transformer.get_transformation_statistics(data_points, custom_transformed)
        print(f"Transformation statistics: {stats}")
    
    asyncio.run(main())