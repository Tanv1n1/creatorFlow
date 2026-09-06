import logging

from telegram import Update
from telegram.ext import Application, ContextTypes

from creatorflow.config import settings
from creatorflow.bot.handlers import onboarding, upload, settings as settings_handlers

logger = logging.getLogger(__name__)

_application: Application | None = None


def create_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    onboarding.register(app)
    upload.register(app)
    settings_handlers.register(app)
    app.add_error_handler(_on_error)

    return app


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("[bot] unhandled error while processing update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong on my end handling that. Please try again, or use /help."
            )
        except Exception:
            logger.exception("[bot] failed to notify user about the earlier error")


async def get_application() -> Application:
    """Builds (once per process) and initializes the PTB Application for webhook-mode dispatch."""
    global _application
    if _application is None:
        _application = create_app()
        await _application.initialize()
    return _application


async def process_update(update_data: dict) -> None:
    """Feeds a single Telegram update (received via webhook) through the PTB handler pipeline."""
    app = await get_application()
    update = Update.de_json(update_data, app.bot)
    await app.process_update(update)
