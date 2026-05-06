"""
Background image generation queue.
Processes generation requests asynchronously so the bot doesn't block.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot

from models import Database
from services.image_service import ImageService

logger = logging.getLogger(__name__)


@dataclass
class GenerationJob:
    user_id: int
    telegram_id: int
    gen_id: int
    prompt: str
    style_prefix: str
    size: str


class GenerationQueue:
    """Async queue for image generation tasks."""

    def __init__(
        self,
        bot: Bot,
        db: Database,
        image_service: ImageService,
        max_workers: int = 3,
    ):
        self.bot = bot
        self.db = db
        self.image_service = image_service
        self.max_workers = max_workers
        self._queue: asyncio.Queue[GenerationJob] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start background workers."""
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(task)
        logger.info("generation queue started: %d workers", self.max_workers)

    async def stop(self) -> None:
        """Gracefully stop workers."""
        for _ in self._workers:
            await self._queue.put(None)  # sentinel
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info("generation queue stopped")

    async def enqueue(self, job: GenerationJob) -> None:
        """Add a generation job to the queue."""
        await self._queue.put(job)
        logger.info(
            "enqueued: user=%d prompt=%s queue_size=%d",
            job.telegram_id, job.prompt[:30], self._queue.qsize(),
        )

    async def _worker(self, name: str) -> None:
        """Background worker that processes generation jobs."""
        logger.info("%s started", name)
        while True:
            job = await self._queue.get()
            if job is None:
                break
            try:
                await self._process(job)
            except Exception:
                logger.exception("%s: generation failed for user=%d", name, job.telegram_id)
            finally:
                self._queue.task_done()

    async def _process(self, job: GenerationJob) -> None:
        """Process a single generation job."""
        full_prompt = f"{job.style_prefix} {job.prompt}".strip() if job.style_prefix else job.prompt

        result = await self.image_service.generate(full_prompt, size=job.size)

        await self.db.update_generation(job.gen_id, result["url"], "done")

        try:
            await self.bot.send_photo(
                chat_id=job.telegram_id,
                photo=result["url"],
                caption=(
                    f"✅ Готово!\n"
                    f"🎨 Провайдер: {result.get('provider', 'unknown')}\n"
                    f"📐 Размер: {job.size}"
                ),
            )
        except Exception:
            logger.exception("failed to send result to user=%d", job.telegram_id)
