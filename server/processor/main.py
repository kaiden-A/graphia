from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

from converters.ghostscript import ghostscript_available, resolve_ghostscript
from converters.libreoffice import resolve_soffice, soffice_available
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

    binary = resolve_soffice(settings.soffice_bin)
    if binary is None:
        logger.warning(
            "LibreOffice was not found (SOFFICE_BIN=%r). "
            "DOCX, PPTX, XLSX, and Markdown to PDF will fail until it is installed.",
            settings.soffice_bin,
        )
    else:
        logger.info("LibreOffice is available at %s", binary)

    ghostscript = resolve_ghostscript(settings.ghostscript_bin)
    if ghostscript is None:
        logger.warning(
            "Ghostscript was not found (GHOSTSCRIPT_BIN=%r). "
            "Compress PDF will fail until it is installed.",
            settings.ghostscript_bin,
        )
    else:
        logger.info("Ghostscript is available at %s", ghostscript)

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
def root() -> dict[str, str | bool]:
    return {
        "service": "graphia-processor",
        "status": "ok",
        "soffice": soffice_available(settings.soffice_bin),
        "ghostscript": ghostscript_available(settings.ghostscript_bin),
    }
