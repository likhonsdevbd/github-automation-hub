"""
Utility functions for the reporting system
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import yaml
import pandas as pd
import numpy as np


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str):
    """
    Save configuration to YAML file
    
    Args:
        config: Configuration dictionary
        config_path: Path to save the configuration
    """
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    except Exception as e:
        logging.error(f"Failed to save config to {config_path}: {e}")


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Calculate percentage change between two values
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Percentage change
    """
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def generate_date_range(period: str, end_date: Optional[datetime] = None) -> Dict[str, datetime]:
    """
    Generate date range based on period
    
    Args:
        period: Period type (daily, weekly, monthly, quarterly, yearly)
        end_date: End date (defaults to now)
        
    Returns:
        Dictionary with start and end dates
    """
    if end_date is None:
        end_date = datetime.utcnow()
    
    if period == "daily":
        start_date = end_date - timedelta(days=1)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=1)
    elif period == "monthly":
        start_date = end_date - timedelta(days=30)
    elif period == "quarterly":
        start_date = end_date - timedelta(days=90)
    elif period == "yearly":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=1)
    
    return {"start": start_date, "end": end_date}


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def parse_cron_expression(cron_expr: str) -> Dict[str, Any]:
    """
    Parse cron expression into components
    
    Args:
        cron_expr: Cron expression string
        
    Returns:
        Dictionary with cron components
    """
    parts = cron_expr.split()
    if len(parts) < 5:
        raise ValueError("Invalid cron expression")
    
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day_of_month": parts[2],
        "month": parts[3],
        "day_of_week": parts[4]
    }


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for flattened keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Unflatten dictionary
    
    Args:
        d: Flattened dictionary
        sep: Separator used in flattened keys
        
    Returns:
        Nested dictionary
    """
    result = {}
    for k, v in d.items():
        keys = k.split(sep)
        current = result
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = v
    return result


def generate_unique_id(prefix: str = '') -> str:
    """
    Generate unique ID with optional prefix
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    import uuid
    unique_part = str(uuid.uuid4())[:8]
    return f"{prefix}{timestamp}_{unique_part}" if prefix else f"{timestamp}_{unique_part}"


def create_dataframe_from_records(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Create pandas DataFrame from records list
    
    Args:
        records: List of record dictionaries
        
    Returns:
        DataFrame
    """
    if not records:
        return pd.DataFrame()
    
    return pd.DataFrame(records)


def summarize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for DataFrame
    
    Args:
        df: DataFrame to summarize
        
    Returns:
        Summary statistics dictionary
    """
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "memory_usage": df.memory_usage(deep=True).sum()
    }
    
    # Add numeric summaries if numeric columns exist
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) > 0:
        summary["numeric_summary"] = df[numeric_columns].describe().to_dict()
    
    # Add categorical summaries if categorical columns exist
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_columns) > 0:
        summary["categorical_summary"] = {
            col: df[col].value_counts().head(10).to_dict()
            for col in categorical_columns
        }
    
    return summary


def format_currency(amount: float, currency: str = 'USD', locale: str = 'en_US') -> str:
    """
    Format currency amount
    
    Args:
        amount: Amount to format
        currency: Currency code
        locale: Locale for formatting
        
    Returns:
        Formatted currency string
    """
    import locale as locale_module
    try:
        locale_module.setlocale(locale_module.LC_ALL, locale)
        return locale_module.currency(amount, grouping=True)
    except:
        return f"{currency} {amount:,.2f}"


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    seconds = int(seconds)
    days = seconds // (24 * 3600)
    seconds = seconds % (24 * 3600)
    hours = seconds // 3600
    seconds = seconds % 3600
    minutes = seconds // 60
    seconds = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 and not parts:  # Only show seconds if no other parts
        parts.append(f"{seconds}s")
    
    return " ".join(parts) if parts else "0s"


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Retry function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        
    Returns:
        Function result or raises last exception
    """
    import time
    
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logging.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                logging.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception


def validate_config_structure(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate configuration structure
    
    Args:
        config: Configuration dictionary
        required_keys: List of required top-level keys
        
    Returns:
        True if valid, False otherwise
    """
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        logging.error(f"Missing required config keys: {missing_keys}")
        return False
    return True


def setup_logging(config: Dict[str, Any]):
    """
    Set up logging configuration
    
    Args:
        config: Logging configuration
    """
    log_level = config.get('log_level', 'INFO')
    log_file = config.get('log_file')
    log_max_size_mb = config.get('log_max_size_mb', 100)
    log_backup_count = config.get('log_backup_count', 5)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        ensure_directory(os.path.dirname(log_file))
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_max_size_mb * 1024 * 1024,
            backupCount=log_backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def calculate_trend(data: List[float]) -> Dict[str, Any]:
    """
    Calculate trend in data
    
    Args:
        data: List of numeric values
        
    Returns:
        Trend analysis dictionary
    """
    if len(data) < 2:
        return {"trend": "insufficient_data"}
    
    # Simple linear trend calculation
    x = list(range(len(data)))
    y = data
    
    # Calculate slope using least squares
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)
    
    if n * sum_x2 - sum_x * sum_x == 0:
        slope = 0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    
    # Determine trend direction
    if slope > 0.1:
        trend = "increasing"
    elif slope < -0.1:
        trend = "decreasing"
    else:
        trend = "stable"
    
    # Calculate percentage change
    first_value = data[0]
    last_value = data[-1]
    pct_change = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
    
    return {
        "trend": trend,
        "slope": slope,
        "percentage_change": pct_change,
        "first_value": first_value,
        "last_value": last_value
    }


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str]) -> Dict[str, Any]:
    """
    Mask sensitive data in dictionary
    
    Args:
        data: Dictionary containing data
        sensitive_keys: List of keys to mask
        
    Returns:
        Dictionary with sensitive data masked
    """
    masked_data = data.copy()
    
    for key in sensitive_keys:
        if key in masked_data:
            value = str(masked_data[key])
            if len(value) <= 4:
                masked_data[key] = "*" * len(value)
            else:
                masked_data[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    return masked_data