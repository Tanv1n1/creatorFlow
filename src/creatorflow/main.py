import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from creatorflow.api.app import app  # noqa: E402 — the ingest service entrypoint (Telegram webhook + jobs API)

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    from creatorflow.config import settings

    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level="info")
