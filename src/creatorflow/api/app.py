from fastapi import FastAPI
from creatorflow.api.routes import jobs, health, telegram
from creatorflow.db.engine import init_db
from creatorflow.bot.client import get_application


def create_app() -> FastAPI:
    app = FastAPI(title="CreatorFlow API", version="1.0.0", docs_url="/docs")
    app.include_router(health.router)
    app.include_router(jobs.router, prefix="/jobs")
    app.include_router(telegram.router, prefix="/telegram")

    @app.on_event("startup")
    async def _startup():
        await init_db()
        await get_application()  # warm up the PTB Application so the first webhook call isn't slow

    return app


app = create_app()
