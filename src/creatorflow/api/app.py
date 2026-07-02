from fastapi import FastAPI
from creatorflow.api.routes import jobs, health


def create_app() -> FastAPI:
    app = FastAPI(title="CreatorFlow API", version="1.0.0", docs_url="/docs")
    app.include_router(health.router)
    app.include_router(jobs.router, prefix="/jobs")
    return app


app = create_app()
