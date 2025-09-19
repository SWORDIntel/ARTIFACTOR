"""
ML Inference Pipeline for ARTIFACTOR v3.0
Performance-optimized pipeline with caching and async processing
"""

import asyncio
import logging
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import hashlib
import time
from pathlib import Path
import threading
from dataclasses import dataclass, asdict
from enum import Enum

# Async and caching
import aioredis
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import weakref

# Performance monitoring
import psutil
import gc
from collections import defaultdict, deque

# Database integration
from sqlalchemy.ext.asyncio import AsyncSession

# Import our ML services
from .ml_classifier import ml_classifier, MLContentClassifier
from .semantic_search import semantic_search_service, SemanticSearchService
from .smart_tagging import smart_tagging_service, SmartTaggingService

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """Pipeline processing stages"""
    PREPROCESSING = "preprocessing"
    CLASSIFICATION = "classification"
    TAGGING = "tagging"
    EMBEDDING = "embedding"
    POSTPROCESSING = "postprocessing"

@dataclass
class ProcessingRequest:
    """Request for ML processing"""
    request_id: str
    content: str
    title: str = ""
    description: str = ""
    file_type: str = ""
    language: str = ""
    user_id: Optional[str] = None
    priority: int = 1  # 1=high, 2=medium, 3=low
    callback: Optional[Callable] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ProcessingResult:
    """Result of ML processing"""
    request_id: str
    success: bool
    classification: Optional[Dict[str, Any]] = None
    tags: Optional[List[Dict[str, Any]]] = None
    embeddings: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: float = 0
    cache_hit: bool = False
    stages_completed: List[str] = None

    def __post_init__(self):
        if self.stages_completed is None:
            self.stages_completed = []

class MLInferencePipeline:
    """
    High-performance ML inference pipeline with intelligent caching
    """

    def __init__(self, cache_config: Optional[Dict[str, Any]] = None):
        # Core services
        self.classifier = ml_classifier
        self.search_service = semantic_search_service
        self.tagging_service = smart_tagging_service

        # Processing queues
        self.high_priority_queue = asyncio.Queue(maxsize=100)
        self.medium_priority_queue = asyncio.Queue(maxsize=200)
        self.low_priority_queue = asyncio.Queue(maxsize=500)

        # Caching
        self.redis_cache = None
        self.memory_cache = {}
        self.cache_config = cache_config or {
            'memory_cache_size': 1000,
            'memory_cache_ttl': 3600,  # 1 hour
            'redis_cache_ttl': 86400,  # 24 hours
            'enable_redis': True,
            'redis_url': 'redis://localhost:6379'
        }

        # Processing pools
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.background_executor = ThreadPoolExecutor(max_workers=4)

        # Performance monitoring
        self.metrics = {
            'requests_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_processing_time': 0,
            'stage_times': defaultdict(list),
            'error_count': 0,
            'queue_sizes': defaultdict(int),
            'throughput_per_minute': deque(maxlen=60)
        }

        # Processing workers
        self.workers_running = False
        self.worker_tasks = []

        # Memory management
        self.gc_threshold = 100  # Run GC after this many requests
        self.gc_counter = 0

        # Cache eviction
        self.cache_access_times = {}
        self.cache_cleanup_interval = 300  # 5 minutes

    async def initialize(self):
        """Initialize the ML pipeline"""
        try:
            logger.info("Initializing ML Inference Pipeline...")

            # Initialize ML services
            await self.classifier.initialize()
            await self.search_service.initialize()
            await self.tagging_service.initialize()

            # Initialize Redis cache if enabled
            if self.cache_config.get('enable_redis', True):
                await self._initialize_redis_cache()

            # Start background workers
            await self._start_workers()

            # Start cache cleanup task
            asyncio.create_task(self._cache_cleanup_task())

            # Start metrics collection
            asyncio.create_task(self._metrics_collection_task())

            logger.info("ML Inference Pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing ML pipeline: {e}")
            raise

    async def _initialize_redis_cache(self):
        """Initialize Redis cache connection"""
        try:
            self.redis_cache = await aioredis.from_url(
                self.cache_config['redis_url'],
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_cache.ping()
            logger.info("Redis cache initialized successfully")

        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}")
            self.redis_cache = None

    async def _start_workers(self):
        """Start background processing workers"""
        self.workers_running = True

        # Create workers for different priority queues
        self.worker_tasks = [
            asyncio.create_task(self._worker("high", self.high_priority_queue)),
            asyncio.create_task(self._worker("medium", self.medium_priority_queue)),
            asyncio.create_task(self._worker("low", self.low_priority_queue))
        ]

        logger.info("Background workers started")

    async def _worker(self, priority: str, queue: asyncio.Queue):
        """Background worker for processing requests"""
        while self.workers_running:
            try:
                request = await asyncio.wait_for(queue.get(), timeout=1.0)
                await self._process_request_internal(request)
                queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in {priority} priority worker: {e}")
                await asyncio.sleep(1)

    async def process_artifact(
        self,
        content: str,
        title: str = "",
        description: str = "",
        file_type: str = "",
        language: str = "",
        user_id: Optional[str] = None,
        priority: int = 1,
        use_cache: bool = True
    ) -> ProcessingResult:
        """
        Process artifact through ML pipeline

        Args:
            content: Artifact content
            title: Artifact title
            description: Artifact description
            file_type: File type
            language: Programming language
            user_id: User ID for caching context
            priority: Processing priority (1=high, 2=medium, 3=low)
            use_cache: Whether to use caching

        Returns:
            ProcessingResult with ML analysis
        """
        start_time = time.time()

        # Generate request ID
        request_id = hashlib.md5(
            f"{content[:1000]}{title}{description}{file_type}{language}{user_id}".encode()
        ).hexdigest()

        try:
            # Check cache first if enabled
            if use_cache:
                cached_result = await self._get_cached_result(request_id)
                if cached_result:
                    self.metrics['cache_hits'] += 1
                    cached_result.cache_hit = True
                    return cached_result

            # Create processing request
            request = ProcessingRequest(
                request_id=request_id,
                content=content,
                title=title,
                description=description,
                file_type=file_type,
                language=language,
                user_id=user_id,
                priority=priority
            )

            # Process request based on priority
            if priority == 1:  # High priority - process immediately
                result = await self._process_request_internal(request)
            else:
                # Add to queue for background processing
                result = await self._queue_request(request)

            # Cache result if successful
            if result.success and use_cache:
                await self._cache_result(request_id, result)

            # Update metrics
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self.metrics['requests_processed'] += 1
            self.metrics['cache_misses'] += 1
            self._update_avg_processing_time(processing_time)

            return result

        except Exception as e:
            logger.error(f"Error processing artifact: {e}")
            self.metrics['error_count'] += 1

            return ProcessingResult(
                request_id=request_id,
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def _process_request_internal(self, request: ProcessingRequest) -> ProcessingResult:
        """Internal request processing with all ML stages"""
        stages_completed = []
        stage_results = {}

        try:
            # Stage 1: Preprocessing
            start_stage = time.time()
            preprocessed_data = await self._preprocess_content(request)
            self.metrics['stage_times'][PipelineStage.PREPROCESSING.value].append(
                (time.time() - start_stage) * 1000
            )
            stages_completed.append(PipelineStage.PREPROCESSING.value)

            # Stage 2: Classification
            start_stage = time.time()
            classification_result = await self.classifier.classify_content(
                request.content, request.title, request.description
            )
            stage_results['classification'] = classification_result
            self.metrics['stage_times'][PipelineStage.CLASSIFICATION.value].append(
                (time.time() - start_stage) * 1000
            )
            stages_completed.append(PipelineStage.CLASSIFICATION.value)

            # Stage 3: Smart Tagging
            start_stage = time.time()
            tagging_result = await self.tagging_service.generate_tags(
                request.content, request.title, request.description,
                request.file_type, request.language
            )
            stage_results['tagging'] = tagging_result
            self.metrics['stage_times'][PipelineStage.TAGGING.value].append(
                (time.time() - start_stage) * 1000
            )
            stages_completed.append(PipelineStage.TAGGING.value)

            # Stage 4: Embedding Generation
            start_stage = time.time()
            embeddings = classification_result.get('embeddings')
            if not embeddings:
                # Generate embeddings if not available from classification
                full_text = f"{request.title} {request.description} {request.content}"
                embeddings = await self.search_service._generate_embeddings(full_text)
            stage_results['embeddings'] = embeddings
            self.metrics['stage_times'][PipelineStage.EMBEDDING.value].append(
                (time.time() - start_stage) * 1000
            )
            stages_completed.append(PipelineStage.EMBEDDING.value)

            # Stage 5: Postprocessing
            start_stage = time.time()
            final_result = await self._postprocess_results(stage_results, request)
            self.metrics['stage_times'][PipelineStage.POSTPROCESSING.value].append(
                (time.time() - start_stage) * 1000
            )
            stages_completed.append(PipelineStage.POSTPROCESSING.value)

            # Memory management
            await self._manage_memory()

            return ProcessingResult(
                request_id=request.request_id,
                success=True,
                classification=final_result.get('classification'),
                tags=final_result.get('tags'),
                embeddings=final_result.get('embeddings'),
                metadata=final_result.get('metadata'),
                stages_completed=stages_completed
            )

        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            return ProcessingResult(
                request_id=request.request_id,
                success=False,
                error=str(e),
                stages_completed=stages_completed
            )

    async def _preprocess_content(self, request: ProcessingRequest) -> Dict[str, Any]:
        """Preprocess content for ML analysis"""
        def preprocess():
            # Clean and normalize content
            cleaned_content = request.content.strip()

            # Extract basic statistics
            stats = {
                'character_count': len(cleaned_content),
                'word_count': len(cleaned_content.split()),
                'line_count': len(cleaned_content.split('\n')),
                'estimated_complexity': 'low'  # Will be updated by ML models
            }

            return {
                'cleaned_content': cleaned_content,
                'stats': stats,
                'full_text': f"{request.title} {request.description} {cleaned_content}".strip()
            }

        return await asyncio.get_event_loop().run_in_executor(
            self.executor, preprocess
        )

    async def _postprocess_results(
        self, stage_results: Dict[str, Any], request: ProcessingRequest
    ) -> Dict[str, Any]:
        """Postprocess and combine results from all stages"""
        def postprocess():
            # Combine classification and tagging results
            classification = stage_results.get('classification', {})
            tagging = stage_results.get('tagging', {})
            embeddings = stage_results.get('embeddings')

            # Enhanced metadata
            metadata = {
                'processing_timestamp': datetime.now().isoformat(),
                'content_stats': {
                    'size_bytes': len(request.content.encode('utf-8')),
                    'estimated_read_time': max(len(request.content.split()) / 200, 0.5)
                },
                'ml_confidence': {
                    'classification': classification.get('language', {}).get('confidence', 0),
                    'tagging': len(tagging.get('tags', [])) / 10.0  # Normalize tag count
                }
            }

            # Quality score calculation
            quality_factors = [
                classification.get('quality', {}).get('confidence', 0.5),
                1.0 if tagging.get('tags') else 0.3,
                1.0 if embeddings else 0.5,
                0.8 if len(request.content) > 100 else 0.4
            ]
            metadata['quality_score'] = sum(quality_factors) / len(quality_factors)

            return {
                'classification': classification,
                'tags': tagging.get('tags', []),
                'embeddings': embeddings,
                'metadata': metadata
            }

        return await asyncio.get_event_loop().run_in_executor(
            self.executor, postprocess
        )

    async def _queue_request(self, request: ProcessingRequest) -> ProcessingResult:
        """Queue request for background processing"""
        if request.priority == 2:
            await self.medium_priority_queue.put(request)
            self.metrics['queue_sizes']['medium'] += 1
        else:
            await self.low_priority_queue.put(request)
            self.metrics['queue_sizes']['low'] += 1

        # For queued requests, return a pending result
        return ProcessingResult(
            request_id=request.request_id,
            success=True,
            metadata={'status': 'queued', 'priority': request.priority}
        )

    async def _get_cached_result(self, request_id: str) -> Optional[ProcessingResult]:
        """Get result from cache"""
        try:
            # Check memory cache first
            if request_id in self.memory_cache:
                cache_entry = self.memory_cache[request_id]
                if datetime.now().timestamp() - cache_entry['timestamp'] < self.cache_config['memory_cache_ttl']:
                    self.cache_access_times[request_id] = datetime.now()
                    return cache_entry['result']

            # Check Redis cache
            if self.redis_cache:
                cached_data = await self.redis_cache.get(f"ml_result:{request_id}")
                if cached_data:
                    result_dict = json.loads(cached_data)
                    return ProcessingResult(**result_dict)

            return None

        except Exception as e:
            logger.warning(f"Error retrieving cached result: {e}")
            return None

    async def _cache_result(self, request_id: str, result: ProcessingResult):
        """Cache processing result"""
        try:
            # Store in memory cache
            if len(self.memory_cache) < self.cache_config['memory_cache_size']:
                self.memory_cache[request_id] = {
                    'result': result,
                    'timestamp': datetime.now().timestamp()
                }
                self.cache_access_times[request_id] = datetime.now()

            # Store in Redis cache
            if self.redis_cache:
                result_dict = asdict(result)
                await self.redis_cache.setex(
                    f"ml_result:{request_id}",
                    self.cache_config['redis_cache_ttl'],
                    json.dumps(result_dict, default=str)
                )

        except Exception as e:
            logger.warning(f"Error caching result: {e}")

    async def _manage_memory(self):
        """Manage memory usage and garbage collection"""
        self.gc_counter += 1

        if self.gc_counter >= self.gc_threshold:
            # Run garbage collection
            await asyncio.get_event_loop().run_in_executor(
                self.background_executor, gc.collect
            )
            self.gc_counter = 0

            # Log memory usage
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            logger.debug(f"Memory usage after GC: {memory_usage:.2f} MB")

    async def _cache_cleanup_task(self):
        """Background task for cache cleanup"""
        while True:
            try:
                await asyncio.sleep(self.cache_cleanup_interval)

                # Clean up expired memory cache entries
                current_time = datetime.now()
                expired_keys = []

                for key, access_time in self.cache_access_times.items():
                    if (current_time - access_time).total_seconds() > self.cache_config['memory_cache_ttl']:
                        expired_keys.append(key)

                for key in expired_keys:
                    self.memory_cache.pop(key, None)
                    self.cache_access_times.pop(key, None)

                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")

    async def _metrics_collection_task(self):
        """Background task for metrics collection"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute

                # Calculate throughput
                current_requests = self.metrics['requests_processed']
                self.metrics['throughput_per_minute'].append(current_requests)

                # Update queue sizes
                self.metrics['queue_sizes']['high'] = self.high_priority_queue.qsize()
                self.metrics['queue_sizes']['medium'] = self.medium_priority_queue.qsize()
                self.metrics['queue_sizes']['low'] = self.low_priority_queue.qsize()

            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")

    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time"""
        current_avg = self.metrics['avg_processing_time']
        total_requests = self.metrics['requests_processed']

        if total_requests == 1:
            self.metrics['avg_processing_time'] = processing_time
        else:
            self.metrics['avg_processing_time'] = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics"""
        cache_hit_rate = 0
        if self.metrics['requests_processed'] > 0:
            cache_hit_rate = self.metrics['cache_hits'] / (
                self.metrics['cache_hits'] + self.metrics['cache_misses']
            )

        # Calculate average stage times
        avg_stage_times = {}
        for stage, times in self.metrics['stage_times'].items():
            if times:
                avg_stage_times[stage] = sum(times) / len(times)

        return {
            'performance': {
                'requests_processed': self.metrics['requests_processed'],
                'avg_processing_time_ms': round(self.metrics['avg_processing_time'], 2),
                'cache_hit_rate': round(cache_hit_rate, 3),
                'error_rate': round(
                    self.metrics['error_count'] / max(self.metrics['requests_processed'], 1), 3
                ),
                'throughput_last_minute': list(self.metrics['throughput_per_minute'])[-1] if self.metrics['throughput_per_minute'] else 0
            },
            'cache': {
                'memory_cache_size': len(self.memory_cache),
                'redis_available': self.redis_cache is not None,
                'cache_hits': self.metrics['cache_hits'],
                'cache_misses': self.metrics['cache_misses']
            },
            'queues': dict(self.metrics['queue_sizes']),
            'stage_performance': avg_stage_times,
            'system': {
                'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                'workers_running': self.workers_running,
                'active_worker_count': len(self.worker_tasks)
            }
        }

    async def batch_process(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[ProcessingResult]:
        """Process multiple artifacts in batch with concurrency control"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single(request_data):
            async with semaphore:
                return await self.process_artifact(**request_data)

        # Process all requests concurrently
        tasks = [process_single(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ProcessingResult(
                    request_id=f"batch_{i}",
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def shutdown(self):
        """Shutdown the pipeline gracefully"""
        logger.info("Shutting down ML Inference Pipeline...")

        # Stop workers
        self.workers_running = False

        # Wait for workers to finish
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        # Close Redis connection
        if self.redis_cache:
            await self.redis_cache.close()

        # Shutdown executors
        self.executor.shutdown(wait=True)
        self.background_executor.shutdown(wait=True)

        # Cleanup ML services
        await self.classifier.cleanup()
        await self.search_service.cleanup()
        await self.tagging_service.cleanup()

        logger.info("ML Inference Pipeline shutdown complete")

# Global instance
ml_pipeline = MLInferencePipeline()