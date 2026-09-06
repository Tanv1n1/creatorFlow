from datetime import datetime

from sqlalchemy import select, update

from creatorflow.db.engine import AsyncSessionLocal
from creatorflow.db.models.job import Job, JobStatus


async def create(
    *,
    telegram_user_id: str,
    telegram_chat_id: str,
    input_r2_key: str,
    telegram_message_id: str | None = None,
) -> Job:
    async with AsyncSessionLocal() as s:
        job = Job(
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
            telegram_message_id=telegram_message_id,
            input_r2_key=input_r2_key,
        )
        s.add(job)
        await s.commit()
        await s.refresh(job)
        return job


async def get(job_id: str) -> Job | None:
    async with AsyncSessionLocal() as s:
        return await s.get(Job, job_id)


async def set_status(job_id: str, status: JobStatus) -> None:
    async with AsyncSessionLocal() as s:
        await s.execute(update(Job).where(Job.id == job_id).values(status=status))
        await s.commit()


async def update_fields(job_id: str, **kwargs) -> None:
    async with AsyncSessionLocal() as s:
        await s.execute(update(Job).where(Job.id == job_id).values(**kwargs))
        await s.commit()


async def complete(job_id: str, output_r2_key: str, thumbnail_timestamps: list) -> None:
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(Job).where(Job.id == job_id).values(
                status=JobStatus.DONE,
                output_r2_key=output_r2_key,
                thumbnail_timestamps=thumbnail_timestamps,
                completed_at=datetime.utcnow(),
            )
        )
        await s.commit()


async def fail(job_id: str, error: str) -> None:
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(Job).where(Job.id == job_id).values(
                status=JobStatus.FAILED,
                error_message=error,
            )
        )
        await s.commit()


async def cancel(job_id: str) -> bool:
    """Cancels a job only if it hasn't been picked up by the batch worker yet. Returns whether it was cancelled."""
    async with AsyncSessionLocal() as s:
        result = await s.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == JobStatus.QUEUED)
            .values(status=JobStatus.CANCELLED)
        )
        await s.commit()
        return result.rowcount > 0


async def list_pending() -> list[Job]:
    recoverable = {
        JobStatus.QUEUED, JobStatus.DOWNLOADING, JobStatus.TRANSCRIBING,
        JobStatus.TRANSLATING, JobStatus.ANALYZING, JobStatus.PLANNING_EDITS,
        JobStatus.RENDERING, JobStatus.GENERATING_ASSETS,
    }
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(Job).where(Job.status.in_(recoverable)))
        return result.scalars().all()


async def list_by_user(telegram_user_id: str, limit: int = 10) -> list[Job]:
    async with AsyncSessionLocal() as s:
        result = await s.execute(
            select(Job)
            .where(Job.telegram_user_id == telegram_user_id)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
