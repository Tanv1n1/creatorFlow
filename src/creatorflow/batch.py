"""Entrypoint for the hourly batch worker (Cloud Run Job). Drains every queued job, runs the
pipeline, and DMs each user the result — then exits. Run locally with `python -m creatorflow.batch`."""
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from creatorflow.db.engine import init_db  # noqa: E402
from creatorflow.db.repos import job_repo  # noqa: E402
from creatorflow.services.pipeline import process_job  # noqa: E402
from creatorflow.bot.notify import notify_result  # noqa: E402


async def run_batch() -> None:
    await init_db()
    jobs = await job_repo.list_pending()
    if not jobs:
        logger.info("[batch] nothing queued")
        return

    logger.info(f"[batch] processing {len(jobs)} job(s)")
    for job in jobs:
        try:
            await process_job(job.id)
        except Exception:
            logger.exception(f"[batch] job {job.id} raised (already recorded as failed)")

        result = await job_repo.get(job.id)
        if result is None:
            continue
        try:
            await notify_result(result)
        except Exception:
            logger.exception(f"[batch] failed to notify user for job {job.id}")

    logger.info("[batch] done")


if __name__ == "__main__":
    asyncio.run(run_batch())
