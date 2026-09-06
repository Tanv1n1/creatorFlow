"""Sends Telegram messages directly over the Bot HTTP API — used only by the batch worker
(src/creatorflow/batch.py), which has no long-lived PTB Application/event loop to send through."""
import logging

import httpx

from creatorflow.config import settings
from creatorflow.db.models.job import Job, JobStatus
from creatorflow.db.repos import user_repo
from creatorflow.bot.messages import progress as progress_msg, results as results_msg

logger = logging.getLogger(__name__)


async def _send(client: httpx.AsyncClient, chat_id: str, text: str, **kwargs) -> None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    r = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown", **kwargs})
    if r.status_code != 200:
        logger.error(f"[notify] sendMessage to {chat_id} failed ({r.status_code}): {r.text[:300]}")


async def notify_result(job: Job) -> None:
    """Called once per job after the batch run finishes it, to DM the user the outcome."""
    if job.status not in (JobStatus.DONE, JobStatus.FAILED):
        return

    chat_id = job.telegram_chat_id
    async with httpx.AsyncClient(timeout=30) as client:
        if job.status == JobStatus.FAILED:
            await _send(client, chat_id, progress_msg.build_failed(job))
            return

        profile = (await user_repo.get_or_create(job.telegram_user_id)).profile
        await _send(client, chat_id, results_msg.build_main(job, profile), disable_web_page_preview=True)

        for text in filter(None, [
            results_msg.build_detail(job),
            results_msg.build_tips(job, profile),
            results_msg.build_captions(job),
            results_msg.build_thumbnails(job),
        ]):
            await _send(client, chat_id, text)
