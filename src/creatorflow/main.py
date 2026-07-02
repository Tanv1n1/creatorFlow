import asyncio
import logging
import threading
import uvicorn

from creatorflow.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def _run_api():
    from creatorflow.api.app import app
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level="warning")


async def main():
    # API runs in a background thread — it's I/O-bound but not async-compatible with the bot loop
    t = threading.Thread(target=_run_api, daemon=True)
    t.start()

    from creatorflow.bot.client import start_bot
    await start_bot()


if __name__ == "__main__":
    asyncio.run(main())
