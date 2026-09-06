import logging

from fastapi import APIRouter, Header, HTTPException, Request

from creatorflow.config import settings
from creatorflow.bot.client import process_update

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    """Receives Telegram updates. Verifies the secret token Telegram echoes back on every
    request (set once via setWebhook) so random internet traffic can't feed in fake updates."""
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="invalid secret token")

    payload = await request.json()
    try:
        await process_update(payload)
    except Exception:
        logger.exception("[telegram webhook] failed to process update")

    # Always 200 — Telegram retries (and can eventually drop the webhook) on non-2xx responses.
    return {"ok": True}
