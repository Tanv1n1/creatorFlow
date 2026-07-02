import asyncio
import logging

from telegram.ext import Application

from creatorflow.config import settings
from creatorflow.db.engine import init_db
from creatorflow.services import queue as job_queue
from creatorflow.services.pipeline import process_job
from creatorflow.bot.handlers import onboarding, upload, settings as settings_handlers

logger = logging.getLogger(__name__)


def create_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    onboarding.register(app)
    upload.register(app)
    settings_handlers.register(app)

    return app


async def _on_startup(app: Application):
    await init_db()
    await job_queue.recover_pending()
    asyncio.create_task(job_queue.worker_loop(process_job))
    me = await app.bot.get_me()
    logger.info(f"[bot] logged in as @{me.username} (id={me.id})")


async def start_bot():
    app = create_app()
    app.post_init = _on_startup

    async with app:
        await app.start()
        await app.updater.start_polling()
        logger.info("[bot] polling started")
        try:
            await asyncio.Event().wait()  # run forever
        finally:
            await app.updater.stop()
            await app.stop()
