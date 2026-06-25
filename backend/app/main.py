from fastapi import FastAPI

from app.api.routes.fetch import router as fetch_router
from app.api.routes.health import router as health_router
from app.api.routes.translate import router as translate_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(title="translator-jp", version="0.1.0")
    app.include_router(health_router, prefix="/api")
    app.include_router(fetch_router, prefix="/api")
    app.include_router(translate_router, prefix="/api")

    return app


app = create_app()
