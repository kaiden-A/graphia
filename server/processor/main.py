from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from core.errors import install_error_handlers
from core.logging import configure_logging
from processor.router import router

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.internal_token.strip():
        raise RuntimeError("INTERNAL_TOKEN must be set.")
    if settings.is_production and settings.internal_token == "dev-internal-token-change-me":
        logger.warning("INTERNAL_TOKEN is still the development default.")
    executor = ThreadPoolExecutor(
        max_workers=max(1, settings.processor_max_workers),
        thread_name_prefix="graphia-job",
    )
    app.state.executor = executor
    yield
    executor.shutdown(wait=True, cancel_futures=False)


app = FastAPI(
    title=f"{settings.app_name} Processor",
    version="0.1.0",
    description="Internal conversion processor.",
    lifespan=lifespan,
)
install_error_handlers(app)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "graphia-processor", "status": "ok"}
