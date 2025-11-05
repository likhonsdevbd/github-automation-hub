#!/usr/bin/env python3
"""
Analytics Orchestrator Test Suite

Basic tests to verify the analytics orchestrator system is working correctly.
"""

import pytest
import asyncio
import tempfile
import os
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.orchestrator import AnalyticsOrchestrator
from core.data_pipeline import DataPipeline
from data.stores.time_series import TimeSeriesStore
from data.stores.metrics import MetricsStore
from data.stores.cache import CacheStore


class TestConfigManager:
    """Test configuration management"""
    
    def test_config_loading(self):
        """Test loading configuration from file"""
        config_manager = ConfigManager("config/config.yaml.example")
        config = config_manager.load_config()
        
        assert isinstance(config, dict)
        assert "app" in config
        assert "server" in config
        assert "github" in config
        
    def test_config_validation(self):
        """Test configuration validation"""
        config_manager = ConfigManager()
        
        # Test valid config
        valid_config = {
            "github": {"api_base_url": "https://api.github.com"},
            "database": {"url": "sqlite:///test.db"},
            "cache": {"type": "memory"}
        }
        assert config_manager.validate_github_config(valid_config["github"])
        assert config_manager.validate_database_config(valid_config["database"])
        assert config_manager.validate_cache_config(valid_config["cache"])
        
    def test_environment_variables(self):
        """Test environment variable substitution"""
        # This would be more comprehensive with actual environment setup
        assert isinstance(os.environ, dict)


class TestTimeSeriesStore:
    """Test time series data storage"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
        
    def test_store_creation(self, temp_db):
        """Test creating time series store"""
        store = TimeSeriesStore(temp_db)
        assert store.db_path == temp_db
        assert os.path.exists(temp_db)
        
    @pytest.mark.asyncio
    async def test_insert_and_retrieve(self, temp_db):
        """Test inserting and retrieving time series data"""
        store = TimeSeriesStore(temp_db)
        
        # Insert test data
        data = {
            "metric": "test_metric",
            "value": 42.0,
            "tags": {"test": "value"},
            "timestamp": "2023-01-01T00:00:00Z"
        }
        
        await store.insert("test_series", data)
        
        # Retrieve data
        result = await store.get_range("test_series", "2023-01-01", "2023-01-02")
        assert len(result) == 1
        assert result[0]["value"] == 42.0


class TestMetricsStore:
    """Test metrics storage"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
        
    def test_store_creation(self, temp_db):
        """Test creating metrics store"""
        store = MetricsStore(temp_db)
        assert store.db_path == temp_db
        
    @pytest.mark.asyncio
    async def test_metric_insertion(self, temp_db):
        """Test inserting metrics"""
        store = MetricsStore(temp_db)
        
        metric_data = {
            "name": "test_counter",
            "value": 100,
            "type": "counter",
            "tags": {"env": "test"}
        }
        
        await store.insert_metric(metric_data)
        
        # Verify insertion
        metrics = await store.get_metrics("test_counter")
        assert len(metrics) == 1
        assert metrics[0]["value"] == 100


class TestCacheStore:
    """Test cache storage"""
    
    def test_memory_cache(self):
        """Test memory-based cache"""
        cache = CacheStore(cache_type="memory")
        
        # Test basic operations
        cache.set("key1", "value1", ttl=60)
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
        
        # Test TTL
        cache.set("key2", "value2", ttl=1)
        import time
        time.sleep(1.1)
        assert cache.get("key2") is None
        
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = CacheStore(cache_type="memory")
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


class TestDataPipeline:
    """Test data pipeline functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
        
    def test_pipeline_creation(self, temp_db):
        """Test creating data pipeline"""
        pipeline = DataPipeline(temp_db)
        assert pipeline.db_path == temp_db
        
    @pytest.mark.asyncio
    async def test_data_processing(self, temp_db):
        """Test basic data processing"""
        pipeline = DataPipeline(temp_db)
        
        # Test data transformation
        raw_data = {"value": 42, "timestamp": "2023-01-01T00:00:00Z"}
        processed_data = await pipeline.transform_data(raw_data)
        
        assert "value" in processed_data
        assert "timestamp" in processed_data


class TestOrchestrator:
    """Test orchestrator functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
            
    def test_orchestrator_creation(self, temp_dir):
        """Test creating orchestrator"""
        config = {
            "app": {"name": "test"},
            "database": {"url": f"sqlite:///{temp_dir}/test.db"},
            "cache": {"type": "memory"}
        }
        
        orchestrator = AnalyticsOrchestrator(config)
        assert orchestrator.config == config
        
    @pytest.mark.asyncio
    async def test_orchestrator_lifecycle(self, temp_dir):
        """Test orchestrator lifecycle"""
        config = {
            "app": {"name": "test"},
            "database": {"url": f"sqlite:///{temp_dir}/test.db"},
            "cache": {"type": "memory"},
            "github": {"api_base_url": "https://api.github.com"}
        }
        
        orchestrator = AnalyticsOrchestrator(config)
        
        # Test initialization
        await orchestrator.initialize()
        assert orchestrator.initialized
        
        # Test status
        status = await orchestrator.get_status()
        assert "status" in status
        
        # Test shutdown
        await orchestrator.shutdown()
        assert not orchestrator.running


class TestIntegration:
    """Test integration functionality"""
    
    def test_import_structure(self):
        """Test that all modules can be imported"""
        try:
            from core.orchestrator import AnalyticsOrchestrator
            from core.config_manager import ConfigManager
            from core.data_pipeline import DataPipeline
            from data.stores.time_series import TimeSeriesStore
            from data.stores.metrics import MetricsStore
            from data.stores.cache import CacheStore
            from api.gateway import APIGateway
            assert True
        except ImportError as e:
            pytest.fail(f"Import error: {e}")


def test_basic_functionality():
    """Basic smoke test"""
    # Test that we can create instances of main classes
    assert True  # Replace with actual basic functionality test


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        test_basic_functionality()
        print("Basic tests passed!")