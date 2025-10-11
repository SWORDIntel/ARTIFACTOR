"""
Download Performance Optimizer
High-performance concurrent download processing with async patterns and intelligent retry logic
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

@dataclass
class DownloadMetrics:
    """Download performance metrics"""
    total_downloads: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0
    total_bytes: int = 0
    total_time: float = 0.0
    avg_speed: float = 0.0  # bytes per second
    concurrent_peak: int = 0
    current_concurrent: int = 0
    retry_count: int = 0

@dataclass
class DownloadTask:
    """Individual download task configuration"""
    url: str
    output_path: Path
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    max_retries: int = 3
    chunk_size: int = 8192
    priority: int = 0  # Higher number = higher priority
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DownloadResult:
    """Download operation result"""
    task: DownloadTask
    success: bool
    file_path: Optional[Path] = None
    file_size: int = 0
    download_time: float = 0.0
    speed: float = 0.0  # bytes per second
    error: Optional[str] = None
    retries_used: int = 0
    response_code: int = 0

class ConcurrentDownloader:
    """High-performance concurrent downloader with intelligent queuing"""

    def __init__(
        self,
        max_concurrent: int = 10,
        connection_limit: int = 100,
        timeout: float = 30.0,
        retry_delay: float = 1.0,
        max_retry_delay: float = 30.0
    ):
        self.max_concurrent = max_concurrent
        self.connection_limit = connection_limit
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retry_delay = max_retry_delay

        # Download queues (priority-based)
        self.high_priority_queue: asyncio.Queue = asyncio.Queue()
        self.normal_priority_queue: asyncio.Queue = asyncio.Queue()
        self.low_priority_queue: asyncio.Queue = asyncio.Queue()

        # Active downloads tracking
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.download_results: Dict[str, DownloadResult] = {}  # Track completed results
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # HTTP session management
        self.session: Optional[aiohttp.ClientSession] = None

        # Performance tracking
        self.metrics = DownloadMetrics()

        # Progress callbacks
        self.progress_callbacks: List[Callable] = []

        # Worker tasks
        self.workers: List[asyncio.Task] = []
        self.running = False

        # Thread pool for file I/O
        self.file_executor = ThreadPoolExecutor(max_workers=5)

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the downloader"""
        # Create HTTP session with optimizations
        connector = aiohttp.TCPConnector(
            limit=self.connection_limit,
            limit_per_host=20,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            ttl_dns_cache=300
        )

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'ARTIFACTOR/3.0 ConcurrentDownloader'}
        )

        # Start worker tasks
        self.running = True
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._download_worker(f"worker-{i}"))
            self.workers.append(worker)

        logger.info(f"Concurrent downloader initialized with {self.max_concurrent} workers")

    async def shutdown(self):
        """Shutdown the downloader"""
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Close HTTP session
        if self.session:
            await self.session.close()

        # Shutdown thread pool
        self.file_executor.shutdown(wait=True)

        logger.info("Concurrent downloader shutdown complete")

    async def download(
        self,
        url: str,
        output_path: Union[str, Path],
        priority: int = 0,
        **kwargs
    ) -> DownloadResult:
        """Add download task and wait for completion"""
        task = DownloadTask(
            url=url,
            output_path=Path(output_path),
            priority=priority,
            **kwargs
        )

        # Add to appropriate queue
        await self._add_to_queue(task)

        # Wait for completion
        return await self._wait_for_completion(task)

    async def download_batch(
        self,
        downloads: List[Tuple[str, Path]],
        priority: int = 0,
        **kwargs
    ) -> List[DownloadResult]:
        """Download multiple files concurrently"""
        tasks = []
        for url, output_path in downloads:
            task = DownloadTask(
                url=url,
                output_path=Path(output_path),
                priority=priority,
                **kwargs
            )
            tasks.append(task)
            await self._add_to_queue(task)

        # Wait for all completions
        results = []
        for task in tasks:
            result = await self._wait_for_completion(task)
            results.append(result)

        return results

    async def _add_to_queue(self, task: DownloadTask):
        """Add task to appropriate priority queue"""
        task_id = self._generate_task_id(task)

        async with self._lock:
            self.active_downloads[task_id] = task

        # Add to priority queue
        if task.priority > 5:
            await self.high_priority_queue.put(task)
        elif task.priority > 0:
            await self.normal_priority_queue.put(task)
        else:
            await self.low_priority_queue.put(task)

    async def _get_next_task(self) -> Optional[DownloadTask]:
        """Get next task from queues (priority order)"""
        try:
            # Try high priority first
            return await asyncio.wait_for(
                self.high_priority_queue.get(),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            pass

        try:
            # Try normal priority
            return await asyncio.wait_for(
                self.normal_priority_queue.get(),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            pass

        try:
            # Try low priority
            return await asyncio.wait_for(
                self.low_priority_queue.get(),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            return None

    async def _download_worker(self, worker_id: str):
        """Worker task for processing downloads"""
        logger.debug(f"Download worker {worker_id} started")

        while self.running:
            try:
                # Get next task
                task = await self._get_next_task()
                if not task:
                    continue

                # Process download
                async with self.semaphore:
                    await self._process_download(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

        logger.debug(f"Download worker {worker_id} stopped")

    async def _process_download(self, task: DownloadTask) -> DownloadResult:
        """Process individual download with retry logic"""
        start_time = time.time()
        task_id = self._generate_task_id(task)

        # Update metrics
        async with self._lock:
            self.metrics.current_concurrent += 1
            self.metrics.concurrent_peak = max(
                self.metrics.concurrent_peak,
                self.metrics.current_concurrent
            )

        try:
            result = await self._download_with_retry(task)

            # Update success metrics
            async with self._lock:
                if result.success:
                    self.metrics.successful_downloads += 1
                    self.metrics.total_bytes += result.file_size
                else:
                    self.metrics.failed_downloads += 1

                self.metrics.total_downloads += 1
                download_time = time.time() - start_time
                self.metrics.total_time += download_time

                # Calculate average speed
                if self.metrics.total_time > 0:
                    self.metrics.avg_speed = self.metrics.total_bytes / self.metrics.total_time

            # Notify progress callbacks
            await self._notify_progress_callbacks(result)

            # Store result for retrieval
            async with self._lock:
                self.download_results[task_id] = result

            return result

        finally:
            # Cleanup
            async with self._lock:
                self.metrics.current_concurrent -= 1
                self.active_downloads.pop(task_id, None)

    async def _download_with_retry(self, task: DownloadTask) -> DownloadResult:
        """Download with exponential backoff retry logic"""
        last_error = None
        retry_delay = self.retry_delay

        for attempt in range(task.max_retries + 1):
            try:
                return await self._perform_download(task, attempt)

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Download attempt {attempt + 1} failed for {task.url}: {e}")

                # Update retry metrics
                async with self._lock:
                    self.metrics.retry_count += 1

                if attempt < task.max_retries:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(min(retry_delay, self.max_retry_delay))
                    retry_delay *= 2

        # All retries failed
        return DownloadResult(
            task=task,
            success=False,
            error=last_error,
            retries_used=task.max_retries
        )

    async def _perform_download(self, task: DownloadTask, attempt: int) -> DownloadResult:
        """Perform actual download operation"""
        start_time = time.time()

        if not self.session:
            raise RuntimeError("Downloader not initialized")

        # Prepare output directory
        task.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Start download
        async with self.session.get(task.url, headers=task.headers) as response:
            response.raise_for_status()

            # Get file size if available
            content_length = response.headers.get('content-length')
            total_size = int(content_length) if content_length else 0

            # Download with progress tracking
            downloaded = 0
            chunks = []

            async for chunk in response.content.iter_chunked(task.chunk_size):
                chunks.append(chunk)
                downloaded += len(chunk)

                # Call progress callback if available
                if task.callback:
                    try:
                        if asyncio.iscoroutinefunction(task.callback):
                            await task.callback(downloaded, total_size)
                        else:
                            task.callback(downloaded, total_size)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")

            # Write file (in thread pool to avoid blocking)
            file_data = b''.join(chunks)
            await asyncio.get_event_loop().run_in_executor(
                self.file_executor,
                self._write_file,
                task.output_path,
                file_data
            )

            # Calculate metrics
            download_time = time.time() - start_time
            file_size = len(file_data)
            speed = file_size / max(download_time, 0.001)

            return DownloadResult(
                task=task,
                success=True,
                file_path=task.output_path,
                file_size=file_size,
                download_time=download_time,
                speed=speed,
                retries_used=attempt,
                response_code=response.status
            )

    def _write_file(self, file_path: Path, data: bytes):
        """Write file data to disk (thread-safe)"""
        try:
            with open(file_path, 'wb') as f:
                f.write(data)
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise

    async def _wait_for_completion(self, task: DownloadTask) -> DownloadResult:
        """Wait for task completion and retrieve result"""
        task_id = self._generate_task_id(task)
        max_wait_time = task.timeout * (task.max_retries + 1) + 10  # Extra buffer

        start_wait = time.time()

        # Poll for completion
        while True:
            async with self._lock:
                # Check if result is available
                if task_id in self.download_results:
                    result = self.download_results.pop(task_id)
                    return result

                # Check if task is no longer active but no result
                if task_id not in self.active_downloads:
                    # Task was removed but no result - likely an error
                    logger.warning(f"Task {task_id} completed but no result found")
                    return DownloadResult(
                        task=task,
                        success=False,
                        error="Task completed but result not found"
                    )

            # Check timeout
            if time.time() - start_wait > max_wait_time:
                logger.error(f"Timeout waiting for task {task_id} completion")
                return DownloadResult(
                    task=task,
                    success=False,
                    error=f"Timeout waiting for completion after {max_wait_time}s"
                )

            await asyncio.sleep(0.1)

    async def _notify_progress_callbacks(self, result: DownloadResult):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def _generate_task_id(self, task: DownloadTask) -> str:
        """Generate unique task ID"""
        content = f"{task.url}:{task.output_path}:{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()

    def add_progress_callback(self, callback: Callable):
        """Add progress callback"""
        self.progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable):
        """Remove progress callback"""
        try:
            self.progress_callbacks.remove(callback)
        except ValueError:
            pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get download performance metrics"""
        return {
            'total_downloads': self.metrics.total_downloads,
            'successful_downloads': self.metrics.successful_downloads,
            'failed_downloads': self.metrics.failed_downloads,
            'success_rate': (
                self.metrics.successful_downloads / max(self.metrics.total_downloads, 1) * 100
            ),
            'total_bytes': self.metrics.total_bytes,
            'avg_speed_mbps': self.metrics.avg_speed / (1024 * 1024),  # MB/s
            'concurrent_peak': self.metrics.concurrent_peak,
            'current_concurrent': self.metrics.current_concurrent,
            'retry_count': self.metrics.retry_count,
            'queue_sizes': {
                'high_priority': self.high_priority_queue.qsize(),
                'normal_priority': self.normal_priority_queue.qsize(),
                'low_priority': self.low_priority_queue.qsize()
            }
        }

    def get_active_downloads(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active downloads"""
        return {
            task_id: {
                'url': task.url,
                'output_path': str(task.output_path),
                'priority': task.priority,
                'metadata': task.metadata
            }
            for task_id, task in self.active_downloads.items()
        }

class ArtifactDownloadOptimizer:
    """Specialized optimizer for Claude artifact downloads"""

    def __init__(self, downloader: ConcurrentDownloader):
        self.downloader = downloader
        self.artifact_cache: Dict[str, Path] = {}

    async def download_artifact(
        self,
        artifact_url: str,
        output_dir: Path,
        artifact_type: str = "unknown"
    ) -> DownloadResult:
        """Download Claude artifact with optimization"""
        # Generate filename based on content type and URL
        filename = self._generate_artifact_filename(artifact_url, artifact_type)
        output_path = output_dir / filename

        # Check cache first
        cache_key = hashlib.md5(artifact_url.encode()).hexdigest()
        if cache_key in self.artifact_cache:
            cached_path = self.artifact_cache[cache_key]
            if cached_path.exists():
                logger.info(f"Using cached artifact: {cached_path}")
                return DownloadResult(
                    task=DownloadTask(url=artifact_url, output_path=output_path),
                    success=True,
                    file_path=cached_path,
                    file_size=cached_path.stat().st_size
                )

        # Download with high priority for artifacts
        result = await self.downloader.download(
            url=artifact_url,
            output_path=output_path,
            priority=10,  # High priority for artifacts
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )

        # Cache successful downloads
        if result.success and result.file_path:
            self.artifact_cache[cache_key] = result.file_path

        return result

    def _generate_artifact_filename(self, url: str, artifact_type: str) -> str:
        """Generate appropriate filename for artifact"""
        parsed = urlparse(url)

        # Extract filename from URL if possible
        if parsed.path:
            path_parts = parsed.path.split('/')
            if path_parts[-1]:
                return path_parts[-1]

        # Generate filename based on type
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = int(time.time())

        extensions = {
            'python': '.py',
            'javascript': '.js',
            'html': '.html',
            'css': '.css',
            'json': '.json',
            'text': '.txt',
            'markdown': '.md'
        }

        ext = extensions.get(artifact_type.lower(), '.txt')
        return f"artifact_{timestamp}_{url_hash}{ext}"

# Global instances
concurrent_downloader = ConcurrentDownloader()
artifact_optimizer = ArtifactDownloadOptimizer(concurrent_downloader)

# Utility functions
async def download_file(url: str, output_path: Union[str, Path], **kwargs) -> DownloadResult:
    """Download single file with optimization"""
    if not concurrent_downloader.running:
        await concurrent_downloader.initialize()

    return await concurrent_downloader.download(url, output_path, **kwargs)

async def download_files(downloads: List[Tuple[str, Path]], **kwargs) -> List[DownloadResult]:
    """Download multiple files concurrently"""
    if not concurrent_downloader.running:
        await concurrent_downloader.initialize()

    return await concurrent_downloader.download_batch(downloads, **kwargs)

async def download_claude_artifact(
    artifact_url: str,
    output_dir: Union[str, Path],
    artifact_type: str = "unknown"
) -> DownloadResult:
    """Download Claude artifact with specialized optimization"""
    if not concurrent_downloader.running:
        await concurrent_downloader.initialize()

    return await artifact_optimizer.download_artifact(
        artifact_url,
        Path(output_dir),
        artifact_type
    )