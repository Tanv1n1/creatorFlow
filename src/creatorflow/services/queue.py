import asyncio
import logging
from typing import Callable, Awaitable

from creatorflow.db.models.job import JobStatus
from creatorflow.db.repos import job_repo

logger = logging.getLogger(__name__)

_queue: asyncio.Queue[str] = asyncio.Queue()


async def enqueue(job_id: str) -> None:
    await _queue.put(job_id)
    logger.info(f"[queue] enqueued {job_id}")


async def recover_pending() -> None:
    jobs = await job_repo.list_pending()
    for job in jobs:
        await job_repo.set_status(job.id, JobStatus.QUEUED)
        await _queue.put(job.id)
    if jobs:
        logger.info(f"[queue] recovered {len(jobs)} jobs")


async def worker_loop(process_fn: Callable[[str], Awaitable[None]]) -> None:
    logger.info("[queue] worker started")
    while True:
        job_id = await _queue.get()
        try:
            await process_fn(job_id)
        except Exception as e:
            logger.exception(f"[queue] unhandled error in {job_id}: {e}")
            await job_repo.fail(job_id, str(e))
        finally:
            _queue.task_done()
