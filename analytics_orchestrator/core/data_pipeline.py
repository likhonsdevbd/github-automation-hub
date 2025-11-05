"""
Data pipeline orchestration for analytics system
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import uuid
from collections import deque, defaultdict
import time
from enum import Enum

from .stores.time_series import TimeSeriesStore
from .stores.metrics import MetricsStore
from .stores.cache import CacheStore
from .processors.aggregator import DataAggregator
from .processors.transformer import DataTransformer
from .processors.analyzer import DataAnalyzer


class PipelineStatus(Enum):
    """Data pipeline status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class ProcessingMode(Enum):
    """Data processing mode enumeration"""
    BATCH = "batch"
    STREAM = "stream"
    MICRO_BATCH = "micro_batch"


@dataclass
class DataPoint:
    """Data point structure"""
    id: str
    timestamp: datetime
    source: str
    metric_name: str
    value: Union[int, float, str, bool]
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0


@dataclass
class DataBatch:
    """Data batch structure"""
    id: str
    source: str
    timestamp: datetime
    data_points: List[DataPoint] = field(default_factory=list)
    processed: bool = False
    error: Optional[str] = None
    processing_time: Optional[float] = None


@dataclass
class ProcessingJob:
    """Processing job structure"""
    id: str
    job_type: str
    data_batch: DataBatch
    processors: List[str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DataPipeline:
    """
    Data pipeline orchestrator that manages data collection, processing, and storage
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize data pipeline"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Pipeline status
        self._status = PipelineStatus.STOPPED
        self._running = False
        
        # Configuration
        self.batch_size = config.get('batch_size', 100)
        self.processing_interval = config.get('processing_interval', 60)
        self.retention_days = config.get('retention_days', 30)
        
        # Data stores
        self.time_series_store = TimeSeriesStore(config.get('storage_backends', {}).get('time_series', {}))
        self.metrics_store = MetricsStore(config.get('storage_backends', {}).get('metrics', {}))
        self.cache_store = CacheStore(config.get('storage_backends', {}).get('cache', {}))
        
        # Data processors
        self.aggregator = DataAggregator()
        self.transformer = DataTransformer()
        self.analyzer = DataAnalyzer()
        
        # Data queues
        self._input_queue = deque()
        self._processing_queue = deque()
        self._output_queue = deque()
        
        # Processing jobs
        self._jobs: Dict[str, ProcessingJob] = {}
        
        # Statistics
        self._stats = {
            'data_points_processed': 0,
            'batches_processed': 0,
            'processing_errors': 0,
            'start_time': None,
            'last_batch_size': 0,
            'queue_sizes': {
                'input': 0,
                'processing': 0,
                'output': 0
            }
        }
        
        # Processing workers
        self._workers = []
        self._shutdown_event = asyncio.Event()
        
        self.logger.info("Data pipeline initialized")
    
    async def start(self):
        """Start the data pipeline"""
        if self._running:
            self.logger.warning("Data pipeline is already running")
            return
        
        self.logger.info("Starting data pipeline...")
        self._status = PipelineStatus.STARTING
        self._running = True
        self._stats['start_time'] = datetime.utcnow()
        
        try:
            # Initialize data stores
            await self.time_series_store.initialize()
            await self.metrics_store.initialize()
            await self.cache_store.initialize()
            
            # Start processing workers
            num_workers = self.config.get('num_workers', 3)
            for i in range(num_workers):
                worker = asyncio.create_task(self._processing_worker(f"worker-{i}"))
                self._workers.append(worker)
            
            # Start maintenance tasks
            asyncio.create_task(self._cleanup_expired_data())
            asyncio.create_task(self._monitor_queue_sizes())
            asyncio.create_task(self._update_statistics())
            
            self._status = PipelineStatus.RUNNING
            self.logger.info("Data pipeline started successfully")
            
        except Exception as e:
            self._status = PipelineStatus.ERROR
            self._running = False
            self.logger.error(f"Failed to start data pipeline: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the data pipeline"""
        if not self._running:
            return
        
        self.logger.info("Stopping data pipeline...")
        self._running = False
        self._status = PipelineStatus.STOPPED
        
        # Signal shutdown to workers
        self._shutdown_event.set()
        
        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        # Shutdown data stores
        await self.time_series_store.shutdown()
        await self.metrics_store.shutdown()
        await self.cache_store.shutdown()
        
        self.logger.info("Data pipeline stopped")
    
    def is_running(self) -> bool:
        """Check if pipeline is running"""
        return self._running and self._status == PipelineStatus.RUNNING
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        uptime = None
        if self._stats['start_time']:
            uptime = (datetime.utcnow() - self._stats['start_time']).total_seconds()
        
        return {
            'status': self._status.value,
            'running': self._running,
            'uptime_seconds': uptime,
            'statistics': self._stats.copy(),
            'queue_sizes': self._stats['queue_sizes'].copy(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def ingest_data(self, data_points: List[DataPoint], source: str = "unknown") -> str:
        """Ingest data points into pipeline"""
        if not self.is_running():
            raise RuntimeError("Data pipeline is not running")
        
        # Create data batch
        batch_id = str(uuid.uuid4())
        data_batch = DataBatch(
            id=batch_id,
            source=source,
            timestamp=datetime.utcnow(),
            data_points=data_points
        )
        
        # Add to input queue
        self._input_queue.append(data_batch)
        
        # Update queue size stat
        self._stats['queue_sizes']['input'] = len(self._input_queue)
        
        self.logger.debug(f"Ingested {len(data_points)} data points from {source}, batch_id: {batch_id}")
        
        return batch_id
    
    async def ingest_data_point(self, data_point: DataPoint, source: str = "unknown") -> str:
        """Ingest a single data point"""
        return await self.ingest_data([data_point], source)
    
    async def schedule_processing(self, data_batch: DataBatch, processors: List[str] = None) -> str:
        """Schedule processing for a data batch"""
        if processors is None:
            processors = ['transform', 'aggregate', 'analyze']
        
        job_id = str(uuid.uuid4())
        processing_job = ProcessingJob(
            id=job_id,
            job_type='data_processing',
            data_batch=data_batch,
            processors=processors
        )
        
        self._jobs[job_id] = processing_job
        self._processing_queue.append(processing_job)
        
        # Update queue size stat
        self._stats['queue_sizes']['processing'] = len(self._processing_queue)
        
        self.logger.debug(f"Scheduled processing job {job_id} for batch {data_batch.id}")
        
        return job_id
    
    async def store_component_metrics(self, component_name: str, metrics: Dict[str, Any]) -> str:
        """Store metrics from a component"""
        data_points = []
        
        # Convert metrics to data points
        for metric_name, metric_value in metrics.items():
            data_point = DataPoint(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                source=component_name,
                metric_name=metric_name,
                value=metric_value,
                tags={'component': component_name}
            )
            data_points.append(data_point)
        
        return await self.ingest_data(data_points, component_name)
    
    async def store_system_metrics(self, metrics: Dict[str, Any]) -> str:
        """Store system metrics"""
        data_points = []
        
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float, str, bool)):
                data_point = DataPoint(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow(),
                    source='system',
                    metric_name=metric_name,
                    value=metric_value,
                    tags={'category': 'system'}
                )
                data_points.append(data_point)
        
        return await self.ingest_data(data_points, 'system')
    
    async def store_report(self, report_type: str, report_data: Dict[str, Any]) -> str:
        """Store a report in the pipeline"""
        data_points = []
        
        # Convert report to data points
        data_point = DataPoint(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            source=report_type,
            metric_name='report_generated',
            value=True,
            tags={'report_type': report_type},
            metadata=report_data
        )
        data_points.append(data_point)
        
        return await self.ingest_data(data_points, report_type)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get data pipeline health status"""
        # Check store health
        time_series_healthy = await self.time_series_store.is_healthy()
        metrics_healthy = await self.metrics_store.is_healthy()
        cache_healthy = await self.cache_store.is_healthy()
        
        # Calculate overall health score
        healthy_stores = sum([time_series_healthy, metrics_healthy, cache_healthy])
        health_score = (healthy_stores / 3.0) * 100
        
        # Check queue health
        max_queue_size = self.config.get('max_queue_size', 1000)
        queue_health = 100.0
        if len(self._input_queue) > max_queue_size:
            queue_health = 50.0
        elif len(self._input_queue) > max_queue_size * 0.8:
            queue_health = 75.0
        
        # Overall health
        overall_health = (health_score + queue_health) / 2.0
        
        return {
            'healthy': overall_health > 50.0,
            'health_score': overall_health,
            'status': self._status.value,
            'stores': {
                'time_series': time_series_healthy,
                'metrics': metrics_healthy,
                'cache': cache_healthy
            },
            'queues': {
                'input_size': len(self._input_queue),
                'processing_size': len(self._processing_queue),
                'output_size': len(self._output_queue)
            },
            'processing_rate': self._stats['data_points_processed'],
            'error_rate': self._stats['processing_errors'],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_last_batch_size(self) -> int:
        """Get size of last processed batch"""
        return self._stats['last_batch_size']
    
    def get_queue_size(self) -> int:
        """Get total queue size"""
        return len(self._input_queue) + len(self._processing_queue) + len(self._output_queue)
    
    async def _processing_worker(self, worker_id: str):
        """Processing worker task"""
        self.logger.debug(f"Starting processing worker {worker_id}")
        
        while self._running:
            try:
                # Get job from processing queue
                if self._processing_queue:
                    job = self._processing_queue.pleft()
                    self._stats['queue_sizes']['processing'] = len(self._processing_queue)
                    
                    # Process job
                    await self._process_job(job, worker_id)
                else:
                    # No jobs, wait a bit
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Error in processing worker {worker_id}: {str(e)}")
                self._stats['processing_errors'] += 1
                await asyncio.sleep(1)
        
        self.logger.debug(f"Processing worker {worker_id} stopped")
    
    async def _process_job(self, job: ProcessingJob, worker_id: str):
        """Process a data processing job"""
        job.started_at = datetime.utcnow()
        job.status = "running"
        
        try:
            self.logger.debug(f"Processing job {job.id} with worker {worker_id}")
            
            # Apply processors in sequence
            result = {
                'data_batch_id': job.data_batch.id,
                'processors_applied': [],
                'metrics': {}
            }
            
            for processor_name in job.processors:
                try:
                    if processor_name == 'transform':
                        job.data_batch.data_points = await self.transformer.transform(
                            job.data_batch.data_points
                        )
                        result['processors_applied'].append('transform')
                    
                    elif processor_name == 'aggregate':
                        aggregated_data = await self.aggregator.aggregate(
                            job.data_batch.data_points
                        )
                        result['metrics'].update(aggregated_data)
                        result['processors_applied'].append('aggregate')
                    
                    elif processor_name == 'analyze':
                        analysis = await self.analyzer.analyze(job.data_batch.data_points)
                        result['metrics'].update(analysis)
                        result['processors_applied'].append('analyze')
                    
                    else:
                        self.logger.warning(f"Unknown processor: {processor_name}")
                
                except Exception as e:
                    self.logger.error(f"Processor {processor_name} failed: {str(e)}")
                    raise
            
            # Store processed data
            await self._store_processed_data(job.data_batch, result)
            
            # Mark job as completed
            job.completed_at = datetime.utcnow()
            job.status = "completed"
            job.result = result
            
            # Update statistics
            self._stats['data_points_processed'] += len(job.data_batch.data_points)
            self._stats['batches_processed'] += 1
            self._stats['last_batch_size'] = len(job.data_batch.data_points)
            
            job.data_batch.processed = True
            job.data_batch.processing_time = (
                job.completed_at - job.started_at
            ).total_seconds()
            
            # Move to output queue
            self._output_queue.append(job)
            self._stats['queue_sizes']['output'] = len(self._output_queue)
            
            self.logger.debug(f"Job {job.id} completed successfully")
            
        except Exception as e:
            # Mark job as failed
            job.completed_at = datetime.utcnow()
            job.status = "failed"
            job.error = str(e)
            
            job.data_batch.error = str(e)
            self._stats['processing_errors'] += 1
            
            self.logger.error(f"Job {job.id} failed: {str(e)}")
    
    async def _store_processed_data(self, data_batch: DataBatch, result: Dict[str, Any]):
        """Store processed data in appropriate stores"""
        try:
            # Store time series data
            for data_point in data_batch.data_points:
                await self.time_series_store.store_data_point(data_point)
            
            # Store metrics data
            metrics_data = {
                'batch_id': data_batch.id,
                'source': data_batch.source,
                'timestamp': data_batch.timestamp.isoformat(),
                'data_points_count': len(data_batch.data_points),
                'processing_time': data_batch.processing_time,
                'metrics': result.get('metrics', {})
            }
            
            await self.metrics_store.store_metrics(data_batch.source, metrics_data)
            
            # Update cache
            cache_key = f"recent_batches:{data_batch.source}"
            await self.cache_store.set(cache_key, metrics_data, ttl=3600)
            
        except Exception as e:
            self.logger.error(f"Failed to store processed data: {str(e)}")
            raise
    
    async def _cleanup_expired_data(self):
        """Background task to clean up expired data"""
        while self._running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(days=self.retention_days)
                
                # Clean up expired data from stores
                await self.time_series_store.cleanup_expired(cutoff_time)
                await self.metrics_store.cleanup_expired(cutoff_time)
                
                # Clean up old cache entries
                await self.cache_store.cleanup_expired()
                
                # Clean up old processing jobs
                expired_jobs = [
                    job_id for job_id, job in self._jobs.items()
                    if job.completed_at and job.completed_at < cutoff_time
                ]
                
                for job_id in expired_jobs:
                    del self._jobs[job_id]
                
                self.logger.debug("Completed cleanup of expired data")
                
                # Sleep for cleanup interval
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(3600)
    
    async def _monitor_queue_sizes(self):
        """Background task to monitor queue sizes"""
        while self._running:
            try:
                self._stats['queue_sizes'] = {
                    'input': len(self._input_queue),
                    'processing': len(self._processing_queue),
                    'output': len(self._output_queue)
                }
                
                # Check for queue overflow
                max_queue_size = self.config.get('max_queue_size', 1000)
                
                if len(self._input_queue) > max_queue_size:
                    self.logger.warning(f"Input queue overflow: {len(self._input_queue)} items")
                
                if len(self._processing_queue) > max_queue_size:
                    self.logger.warning(f"Processing queue overflow: {len(self._processing_queue)} items")
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring queue sizes: {str(e)}")
                await asyncio.sleep(30)
    
    async def _update_statistics(self):
        """Background task to update statistics"""
        while self._running:
            try:
                # Calculate processing rate
                now = datetime.utcnow()
                if self._stats['start_time']:
                    elapsed = (now - self._stats['start_time']).total_seconds()
                    if elapsed > 0:
                        processing_rate = self._stats['data_points_processed'] / elapsed
                        self._stats['processing_rate_per_second'] = processing_rate
                
                # Update cache with current stats
                await self.cache_store.set(
                    'pipeline_statistics',
                    self._stats,
                    ttl=300  # 5 minutes
                )
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"Error updating statistics: {str(e)}")
                await asyncio.sleep(60)
    
    async def get_recent_data(self, source: str, hours: int = 24) -> List[DataPoint]:
        """Get recent data points from a source"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return await self.time_series_store.get_data(source, cutoff_time)
    
    async def get_metrics_summary(self, source: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for a source"""
        return await self.metrics_store.get_summary(source, hours)
    
    async def query_data(self, query: Dict[str, Any]) -> List[DataPoint]:
        """Query data points based on criteria"""
        return await self.time_series_store.query(query)


# Data factory functions

def create_data_point(
    metric_name: str,
    value: Union[int, float, str, bool],
    source: str,
    tags: Dict[str, str] = None,
    metadata: Dict[str, Any] = None
) -> DataPoint:
    """Create a data point"""
    return DataPoint(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        source=source,
        metric_name=metric_name,
        value=value,
        tags=tags or {},
        metadata=metadata or {}
    )


def create_metric_data_point(
    metric_name: str,
    value: Union[int, float],
    source: str,
    component: str = None,
    timestamp: datetime = None
) -> DataPoint:
    """Create a metric data point"""
    tags = {}
    if component:
        tags['component'] = component
    
    return DataPoint(
        id=str(uuid.uuid4()),
        timestamp=timestamp or datetime.utcnow(),
        source=source,
        metric_name=metric_name,
        value=value,
        tags=tags
    )


if __name__ == "__main__":
    # Example usage
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Pipeline')
    parser.add_argument('--config', default='config/config.yaml', help='Configuration file path')
    
    args = parser.parse_args()
    
    async def main():
        # Load configuration
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create and start pipeline
        pipeline = DataPipeline(config.get('data_pipeline', {}))
        
        try:
            await pipeline.start()
            
            # Example data ingestion
            data_points = [
                create_data_point('cpu_usage', 45.2, 'system'),
                create_data_point('memory_usage', 67.8, 'system'),
                create_data_point('requests_per_second', 123, 'api')
            ]
            
            batch_id = await pipeline.ingest_data(data_points, 'example')
            print(f"Ingested batch: {batch_id}")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await pipeline.stop()
    
    asyncio.run(main())