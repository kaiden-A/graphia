from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.cli_router import router as cli_router
from app.routers.conversions_router import router as conversions_router
from app.routers.health_router import router as health_router
from app.routers.metadata_router import router as metadata_router
from core.config import settings
from core.errors import install_error_handlers
from core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.is_production and settings.app_secret == "dev-only-change-me":
        logger.warning("APP_SECRET is still the development default.")
    if settings.is_production and settings.internal_token == "dev-internal-token-change-me":
        logger.warning("INTERNAL_TOKEN is still the development default.")
    if not settings.zitadel_configured:
        logger.warning("Zitadel is not configured; sign-in will be unavailable.")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Graphia public API.",
    lifespan=lifespan,
)
install_error_handlers(app)

app.include_router(health_router)
app.include_router(metadata_router)
app.include_router(auth_router)
app.include_router(cli_router)
app.include_router(conversions_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "graphia-api", "status": "ok"}
