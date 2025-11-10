"""
Data Pipeline - Efficient data collection, processing, and state management
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import pandas as pd
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class DataPoint:
    """Single data point with metadata"""
    timestamp: datetime
    metric_name: str
    value: float
    host: str
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "value": self.value,
            "host": self.host,
            "tags": self.tags or {}
        }


class DataBuffer:
    """
    Efficient circular buffer for storing metrics
    Automatically rotates old data
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)
        self.metric_stats: Dict[str, Dict[str, float]] = {}
    
    def add(self, data_point: DataPoint):
        """Add data point to buffer"""
        self.buffer.append(data_point)
        self._update_stats(data_point)
    
    def add_batch(self, data_points: List[DataPoint]):
        """Add batch of data points"""
        for dp in data_points:
            self.add(dp)
    
    def _update_stats(self, dp: DataPoint):
        """Update running statistics"""
        if dp.metric_name not in self.metric_stats:
            self.metric_stats[dp.metric_name] = {
                "min": dp.value,
                "max": dp.value,
                "sum": 0,
                "count": 0,
                "last_update": dp.timestamp
            }
        
        stats = self.metric_stats[dp.metric_name]
        stats["min"] = min(stats["min"], dp.value)
        stats["max"] = max(stats["max"], dp.value)
        stats["sum"] += dp.value
        stats["count"] += 1
        stats["last_update"] = dp.timestamp
    
    def get_recent(
        self,
        metric_name: Optional[str] = None,
        hours: int = 1
    ) -> List[DataPoint]:
        """Get recent data points"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if metric_name:
            return [
                dp for dp in self.buffer
                if dp.metric_name == metric_name and dp.timestamp >= cutoff_time
            ]
        else:
            return [dp for dp in self.buffer if dp.timestamp >= cutoff_time]
    
    def get_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for metric"""
        return self.metric_stats.get(metric_name)
    
    def get_dataframe(
        self,
        metric_name: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Convert buffer to pandas DataFrame"""
        if not self.buffer:
            return None
        
        data = [dp.to_dict() for dp in self.buffer]
        
        if metric_name:
            data = [d for d in data if d["metric_name"] == metric_name]
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()
        self.metric_stats.clear()
    
    def size(self) -> int:
        """Get buffer size"""
        return len(self.buffer)


class DataPipeline:
    """
    Main data pipeline orchestration
    Handles collection, validation, processing, and storage
    """
    
    def __init__(self, batch_size: int = 100, flush_interval: int = 5):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = DataBuffer(max_size=10000)
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.metrics = {
            "points_received": 0,
            "points_processed": 0,
            "batches_flushed": 0,
            "errors": 0
        }
    
    async def start(self):
        """Start pipeline"""
        self.is_running = True
        logger.info("✅ Data pipeline started")
        
        # Start background tasks
        await asyncio.gather(
            self._processing_loop(),
            self._flush_loop(),
            return_exceptions=True
        )
    
    async def stop(self):
        """Stop pipeline"""
        self.is_running = False
        logger.info("✅ Data pipeline stopped")
    
    async def add_data_point(self, data_point: DataPoint) -> bool:
        """Add single data point"""
        try:
            await self.processing_queue.put(data_point)
            self.metrics["points_received"] += 1
            return True
        except Exception as e:
            logger.error(f"Error adding data point: {str(e)}")
            self.metrics["errors"] += 1
            return False
    
    async def add_batch(self, data_points: List[DataPoint]) -> bool:
        """Add batch of data points"""
        try:
            for dp in data_points:
                await self.add_data_point(dp)
            return True
        except Exception as e:
            logger.error(f"Error adding batch: {str(e)}")
            self.metrics["errors"] += 1
            return False
    
    async def _processing_loop(self):
        """Process incoming data points"""
        while self.is_running:
            try:
                data_point = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                # Validate and process
                if self._validate(data_point):
                    self.buffer.add(data_point)
                    self.metrics["points_processed"] += 1
            
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                self.metrics["errors"] += 1
    
    async def _flush_loop(self):
        """Periodically flush buffer to storage"""
        while self.is_running:
            try:
                await asyncio.sleep(self.flush_interval)
                
                if self.buffer.size() > 0:
                    # Here you would save to database/storage
                    logger.debug(f"Flushing {self.buffer.size()} data points")
                    self.metrics["batches_flushed"] += 1
            
            except Exception as e:
                logger.error(f"Flush error: {str(e)}")
                self.metrics["errors"] += 1
    
    def _validate(self, data_point: DataPoint) -> bool:
        """Validate data point"""
        if not isinstance(data_point.value, (int, float)):
            return False
        
        if not isinstance(data_point.metric_name, str):
            return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        return {
            **self.metrics,
            "buffer_size": self.buffer.size(),
            "queue_size": self.processing_queue.qsize()
        }
    
    def get_buffer(self) -> DataBuffer:
        """Get data buffer"""
        return self.buffer


# Global pipeline instance
_pipeline: Optional[DataPipeline] = None


async def get_data_pipeline() -> DataPipeline:
    """Get or create global data pipeline"""
    global _pipeline
    
    if _pipeline is None:
        _pipeline = DataPipeline()
        await _pipeline.start()
    
    return _pipeline
