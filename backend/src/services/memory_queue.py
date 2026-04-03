import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MemoryTask:
    id: str
    content: str
    user_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MemoryQueue:
    def __init__(self, memory_service_factory, max_workers: int = 3):
        self.queue: deque[MemoryTask] = deque()
        self.tasks: Dict[str, MemoryTask] = {}
        self.lock = Lock()
        self.memory_service_factory = memory_service_factory
        self.max_workers = max_workers
        self._running = False
        self._workers: list = []
        self._cleanup_task: Optional[asyncio.Task] = None

    def add_task(
        self,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        task = MemoryTask(
            id=task_id,
            content=content,
            user_id=user_id,
            metadata=metadata,
        )
        with self.lock:
            self.queue.append(task)
            self.tasks[task_id] = task
        logger.info(f"[Queue] Task {task_id} added to queue, queue size: {len(self.queue)}")
        return task_id

    def get_task(self, task_id: str) -> Optional[MemoryTask]:
        return self.tasks.get(task_id)

    def get_queue_size(self) -> int:
        with self.lock:
            return len(self.queue)

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
            processing = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PROCESSING)
            completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
            failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
            return {
                "queue_size": len(self.queue),
                "total_tasks": len(self.tasks),
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            }

    async def _process_task(self, task: MemoryTask):
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now()
        logger.info(f"[Queue] Processing task {task.id}")

        try:
            service = self.memory_service_factory()
            await service.initialize()
            result = await service.add_memory(
                content=task.content,
                user_id=task.user_id,
                metadata=task.metadata,
            )
            task.result = result
            task.status = TaskStatus.COMPLETED
            logger.info(f"[Queue] Task {task.id} completed successfully")
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            logger.error(f"[Queue] Task {task.id} failed: {e}")
        finally:
            task.completed_at = datetime.now()

    async def _worker(self, worker_id: int):
        logger.info(f"[Queue] Worker {worker_id} started")
        while self._running:
            try:
                task = None
                with self.lock:
                    if self.queue:
                        task = self.queue.popleft()

                if task:
                    await self._process_task(task)
                else:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Queue] Worker {worker_id} error: {e}")
                await asyncio.sleep(0.5)

        logger.info(f"[Queue] Worker {worker_id} stopped")

    async def start(self):
        if self._running:
            return

        self._running = True
        logger.info(f"[Queue] Starting queue processor with {self.max_workers} workers")

        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

    async def stop(self):
        if not self._running:
            return

        logger.info("[Queue] Stopping queue processor")
        self._running = False

        for worker in self._workers:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

        self._workers.clear()
        logger.info("[Queue] Queue processor stopped")

    def clear_completed_tasks(self, max_age_seconds: int = 3600):
        now = datetime.now()
        with self.lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    if task.completed_at and (now - task.completed_at).total_seconds() > max_age_seconds:
                        to_remove.append(task_id)

            for task_id in to_remove:
                del self.tasks[task_id]

            if to_remove:
                logger.info(f"[Queue] Cleared {len(to_remove)} old tasks")
